import axios from "axios";
const api = axios.create({ baseURL: "http://127.0.0.1:8000/api" });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
export async function login(username, password) {
  const { data } = await api.post("/auth/login/", { username, password });
  localStorage.setItem("access", data.access);
  localStorage.setItem("refresh", data.refresh);
  return data;
}
export const registerCitizen = (data) => api.post("/auth/register/", data);
export const requestOfficerAccount = (data) => api.post("/auth/register-officer/", data);
export const getProfile = () => api.get("/auth/me/");
export const getDepartments = () => api.get("/auth/departments/");
export const getComplaints = (params = {}) => api.get("/complaints/", { params });
export const createComplaint = (data) => api.post("/complaints/", data);
export const updateComplaintStatus = (id, data) => api.post(`/complaints/${id}/status/`, data);
export const assignOfficer = (id, officerId) => api.patch(`/complaints/${id}/assign/`, { officer_id: officerId });
export function logout() { localStorage.removeItem("access"); localStorage.removeItem("refresh"); }
export default api;
