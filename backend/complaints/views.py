
from typing import cast

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from accounts.models import Department, User
from .models import Complaint, ComplaintHistory
from .serializers import ComplaintSerializer, ComplaintStatusSerializer


def department_for_category(category):
    """Resolve common department naming variations for a complaint category."""
    label = Complaint.Category(category).label
    aliases = {
        Complaint.Category.ROAD: ("road", "roads", "road damage", "public works"),
        Complaint.Category.GARBAGE: ("garbage", "sanitation", "waste management", "solid waste"),
        Complaint.Category.WATER: ("water", "water supply", "water works"),
        Complaint.Category.ELECTRICITY: ("electricity", "electrical", "power"),
        Complaint.Category.DRAINAGE: ("drainage", "drain", "sewerage", "sewage"),
    }
    candidates = {category.casefold(), label.casefold(), *aliases.get(category, ())}
    departments = Department.objects.all().order_by("id")
    for department in departments:
        name = department.name.casefold().strip()
        if any(
            name == candidate or name.startswith(candidate + " ") or f" {candidate} " in f" {name} "
            for candidate in candidates
        ):
            return department
    return None


class ComplaintViewSet(viewsets.ModelViewSet):
    serializer_class = ComplaintSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        request = cast(Request, self.request)
        user = cast(User, request.user)

        qs = Complaint.objects.select_related(
            "citizen", "department", "assigned_officer"
        ).prefetch_related("history__changed_by")

        if user.is_superuser or user.role == User.Role.ADMIN:
            pass
        elif user.role == User.Role.OFFICER:
            pass
        else:
            qs = qs.filter(citizen=user)

        status_filter = request.query_params.get("status")
        category_filter = request.query_params.get("category")
        search = request.query_params.get("search")

        if status_filter:
            qs = qs.filter(status=status_filter)

        if category_filter:
            qs = qs.filter(category=category_filter)

        if search:
            qs = qs.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(location__icontains=search)
                | Q(complaint_id__icontains=search)
            )

        return qs

    def create(self, request, *args, **kwargs):
        user = cast(User, request.user)
        if user.role != User.Role.CITIZEN:
            raise PermissionDenied("Only citizens can submit complaints.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.validated_data.get("category", Complaint.Category.OTHER)
        with transaction.atomic():
            department = Department.objects.filter(
                complaint_category=category
            ).first() or department_for_category(category)
            officer = None
            if department:
                officer = User.objects.filter(
                    role=User.Role.OFFICER,
                    department_id=department.id,
                    is_active=True,
                ).order_by("id").first()

            complaint = serializer.save(
                citizen=user,
                department=department,
                assigned_officer=officer,
            )

            ComplaintHistory.objects.create(
                complaint=complaint,
                previous_status="",
                new_status=Complaint.Status.SUBMITTED,
                remarks=(
                    "Complaint submitted and assigned automatically."
                    if officer
                    else "Complaint submitted. Waiting for an administrator to assign an officer."
                ),
                changed_by=user,
            )

        return Response(
            self.get_serializer(complaint).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        raise PermissionDenied(
            "Use the status or assignment endpoints to update a complaint."
        )

    def partial_update(self, request, *args, **kwargs):
        raise PermissionDenied(
            "Use the status or assignment endpoints to update a complaint."
        )

    @action(detail=True, methods=["post"], url_path="status")
    def update_status(self, request, pk=None):
        complaint = self.get_object()
        user = cast(User, request.user)

        is_admin = user.is_superuser or user.role == User.Role.ADMIN

        if not is_admin:
            if user.role != User.Role.OFFICER:
                raise PermissionDenied(
                    "Only department officers or administrators can update complaint status."
                )

            if (
                not user.department_id
                or complaint.department_id != user.department_id
            ):
                raise PermissionDenied(
                    "You can only update complaints from your department."
                )

            if complaint.assigned_officer_id != user.id:
                raise PermissionDenied(
                    "This complaint is not assigned to you."
                )

        serializer = ComplaintStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        new_status = data["status"]
        remarks = data.get("remarks", "").strip()
        reason = data.get("rejection_reason", "").strip()
        resolution_image = data.get("resolution_image")

        transitions = {
            Complaint.Status.SUBMITTED: {
                Complaint.Status.IN_PROGRESS,
                Complaint.Status.REJECTED,
            },
            Complaint.Status.IN_PROGRESS: {
                Complaint.Status.RESOLVED,
                Complaint.Status.REJECTED,
            },
        }

        if new_status not in transitions.get(complaint.status, set()):
            raise ValidationError({
                "status": (
                    f"Cannot change status from {complaint.status} "
                    f"to {new_status}."
                )
            })

        if new_status == Complaint.Status.RESOLVED:
            if not remarks:
                raise ValidationError({
                    "remarks": "Resolution remarks are required."
                })
            if not resolution_image:
                raise ValidationError({
                    "resolution_image": "Upload a resolution photo before resolving."
                })

        if new_status == Complaint.Status.REJECTED and not reason:
            raise ValidationError({
                "rejection_reason": "A rejection reason is required."
            })

        with transaction.atomic():
            old_status = complaint.status
            complaint.status = new_status

            if new_status == Complaint.Status.RESOLVED:
                complaint.resolution_remarks = remarks
                complaint.resolution_image = resolution_image
                complaint.resolved_at = timezone.now()
            elif new_status == Complaint.Status.REJECTED:
                complaint.rejection_reason = reason

            complaint.save()

            log_remarks = (
                remarks
                if new_status == Complaint.Status.RESOLVED
                else reason
                if new_status == Complaint.Status.REJECTED
                else remarks or "Work started."
            )

            ComplaintHistory.objects.create(
                complaint=complaint,
                previous_status=old_status,
                new_status=new_status,
                remarks=log_remarks,
                changed_by=user,
            )

        return Response(self.get_serializer(complaint).data)

    @action(detail=True, methods=["patch"], url_path="assign")
    def assign_officer(self, request, pk=None):
        user = cast(User, request.user)
        if not (
            user.is_superuser
            or user.role == User.Role.ADMIN
        ):
            raise PermissionDenied(
                "Only administrators can assign complaints."
            )

        complaint = self.get_object()
        officer_id = request.data.get("officer_id")

        if not officer_id:
            raise ValidationError({
                "officer_id": "This field is required."
            })

        try:
            officer = User.objects.select_related("department").get(
                pk=officer_id,
                role=User.Role.OFFICER,
                is_active=True,
            )
        except User.DoesNotExist:
            raise ValidationError({
                "officer_id": "Active department officer not found."
            })

        if not officer.department_id:
            raise ValidationError({
                "officer_id": "The officer must belong to a department."
            })

        if (
            complaint.department_id
            and complaint.department_id != officer.department_id
        ):
            raise ValidationError({
                "officer_id": "The officer does not belong to the complaint department."
            })

        with transaction.atomic():
            complaint.department = officer.department
            complaint.assigned_officer = officer
            complaint.save(
                update_fields=[
                    "department", "assigned_officer", "updated_at"
                ]
            )

            ComplaintHistory.objects.create(
                complaint=complaint,
                previous_status=complaint.status,
                new_status=complaint.status,
                remarks=f"Assigned to officer {officer.username}.",
                changed_by=user,
            )

        return Response(self.get_serializer(complaint).data)
