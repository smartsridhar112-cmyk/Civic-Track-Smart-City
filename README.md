# CivicTrack — Smart City Complaint & Resolution System

Django REST Framework + JWT + MySQL backend, with a React + Tailwind CSS starter frontend.

## 1. MySQL setup

Run in MySQL Workbench:

```sql
CREATE DATABASE civictrack CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'civic_user'@'localhost' IDENTIFIED BY 'change-this-password';
GRANT ALL PRIVILEGES ON civictrack.* TO 'civic_user'@'localhost';
FLUSH PRIVILEGES;
```

Copy `backend/.env.example` to `backend/.env`, then update the database password and secret key.

## 2. Backend setup (PowerShell)

```powershell
cd backend
python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py makemigrations accounts
python manage.py makemigrations complaints
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate again.

## 3. Frontend setup (second terminal)

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL, normally http://localhost:5173. Backend API is at http://127.0.0.1:8000.

## Google Maps complaint locations

Copy `frontend/.env.example` to `frontend/.env` and set `VITE_GOOGLE_MAPS_API_KEY` to a Google Maps JavaScript API key. Enable the Maps JavaScript API for the key and restrict it to your app's website origins. Restart the Vite dev server after changing the key. Citizens can click the map or use their current location when submitting a complaint; saved coordinates are shown as a Google Maps link. Apply the coordinate fields with `python manage.py migrate` from `backend`.

## API endpoints

- `POST /api/auth/register/` citizen registration
- `POST /api/auth/register-officer/` officer account request with a department (created inactive until an administrator approves it)
- `POST /api/auth/login/` JWT token obtain
- `POST /api/auth/token/refresh/` refresh access token
- `GET /api/auth/me/` current profile
- `GET /api/auth/departments/` departments
- `GET /api/auth/users/` administrator-only user list
- `PATCH /api/auth/users/<id>/` administrator changes role/department/active status
- `GET /api/complaints/` list complaints visible to logged-in user
- `POST /api/complaints/` citizen submits complaint (multipart form-data for photo)
- `POST /api/complaints/<id>/status/` officer/admin status update
- `PATCH /api/complaints/<id>/assign/` administrator assigns officer

## Workflow

1. Register a citizen from the frontend.
2. In Django admin, map each department to its complaint category.
3. An officer requests an account from the Officer Portal sign-in screen, selects a department, and waits for administrator activation.
4. A citizen submits a complaint. CivicTrack routes it to the department mapped to that category and assigns an active officer from that department.
5. If no active officer is available for the mapped department, an administrator assigns the complaint through the API or Django admin.
6. The assigned officer starts work, then marks the complaint resolved with remarks and a resolution photo in the portal.

## Notes

- Do not commit `.env` or production secrets to source control.
- This is a development starter; add production deployment settings, upload limits, tests, and token refresh handling before deploying.
- The React UI does not include an administrator assignment page; complaint assignment is available through the API or Django admin.
