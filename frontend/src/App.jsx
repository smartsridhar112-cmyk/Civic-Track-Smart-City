import { useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, ClipboardList, LogOut, MapPin, Plus, RefreshCw, Send } from "lucide-react";
import { login, registerCitizen, requestOfficerAccount, getProfile, getDepartments, getComplaints, createComplaint, updateComplaintStatus, logout } from "./services/api";

const categories = ["ROAD", "GARBAGE", "WATER", "ELECTRICITY", "DRAINAGE", "OTHER"];
const statusColors = { SUBMITTED: "bg-blue-100 text-blue-800", IN_PROGRESS: "bg-amber-100 text-amber-800", RESOLVED: "bg-green-100 text-green-800", REJECTED: "bg-red-100 text-red-800" };

export default function App() {
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState("login");
  const [auth, setAuth] = useState({ username: "", email: "", first_name: "", last_name: "", phone: "", password: "", password_confirm: "", department: "" });
  const [departments, setDepartments] = useState([]);
  const [form, setForm] = useState({ title: "", description: "", category: "ROAD", location: "", image: null });
  const [complaints, setComplaints] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [resolvingId, setResolvingId] = useState(null);
  const [resolution, setResolution] = useState({ remarks: "", image: null });
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("");
  const [error, setError] = useState("");
  const [authSuccess, setAuthSuccess] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);
  const isStaff = user && (user.role === "OFFICER" || user.role === "ADMIN" || user.is_superuser);

  async function loadComplaints() {
    const params = {};
    if (search.trim()) params.search = search.trim();
    if (filter) params.status = filter;
    const { data } = await getComplaints(params);
    setComplaints(data.results ?? data);
  }
  async function loadProfile() {
    const { data } = await getProfile();
    setUser(data);
    const { data: list } = await getComplaints();
    setComplaints(list.results ?? list);
  }
  useEffect(() => {
    if (localStorage.getItem("access")) loadProfile().catch(() => { logout(); setUser(null); });
  }, []);
  useEffect(() => {
    if (authMode === "officer-register") {
      getDepartments().then(({ data }) => setDepartments(data.results ?? data)).catch(() => setDepartments([]));
    }
  }, [authMode]);
  async function handleAuth(e) {
    e.preventDefault(); setError(""); setAuthSuccess(""); setLoading(true);
    try {
      if (authMode === "register") { await registerCitizen(auth); await login(auth.username, auth.password); }
      else if (authMode === "officer-register") {
        const { department, ...officerDetails } = auth;
        await requestOfficerAccount({ ...officerDetails, department });
        setAuthMode("officer");
        setAuthSuccess("Your officer account request was submitted. An administrator must activate it before you can sign in.");
        return;
      }
      else await login(auth.username, auth.password);
      if (authMode === "login" || authMode === "officer") {
        const { data: profile } = await getProfile();
        const expectedRole = authMode === "officer" ? "OFFICER" : "CITIZEN";
        if (profile.role !== expectedRole) {
          logout();
          setError(authMode === "officer"
            ? "This sign-in is for officer accounts. Please use the correct account."
            : "This sign-in is for citizen accounts. Please use the Officer Portal for officer accounts.");
          return;
        }
      }
      await loadProfile();
    } catch (err) {
      const d = err.response?.data;
      setAuthSuccess("");
      setError(d ? Object.entries(d).map(([k, v]) => `${k}: ${JSON.stringify(v)}`).join(" ") : err.message || "Unable to authenticate.");
    } finally { setLoading(false); }
  }
  async function handleCreate(e) {
    e.preventDefault(); setError(""); setNotice(""); setLoading(true);
    try {
      const data = new FormData();
      ["title", "description", "category", "location"].forEach(k => data.append(k, form[k]));
      if (form.image) data.append("image", form.image);
      await createComplaint(data);
      setForm({ title: "", description: "", category: "ROAD", location: "", image: null });
      setShowForm(false); setNotice("Complaint submitted successfully."); await loadComplaints();
    } catch (err) { setError(JSON.stringify(err.response?.data ?? "Submission failed.")); }
    finally { setLoading(false); }
  }
  async function startWork(c) {
    try { await updateComplaintStatus(c.id, { status: "IN_PROGRESS", remarks: "Work has started." }); setNotice("Status updated."); await loadComplaints(); }
    catch (err) { setError(JSON.stringify(err.response?.data ?? "Status update failed.")); }
  }
  async function resolveComplaint(e, c) {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      const data = new FormData();
      data.append("status", "RESOLVED");
      data.append("remarks", resolution.remarks);
      if (resolution.image) data.append("resolution_image", resolution.image);
      await updateComplaintStatus(c.id, data);
      setNotice("Complaint marked as resolved.");
      setResolvingId(null); setResolution({ remarks: "", image: null });
      await loadComplaints();
    } catch (err) { setError(JSON.stringify(err.response?.data ?? "Unable to resolve complaint.")); }
    finally { setLoading(false); }
  }
  function signOut() { logout(); setUser(null); setAuthMode("login"); setComplaints([]); setError(""); setNotice(""); }

  if (!user) return <main className="flex min-h-screen items-center justify-center bg-slate-100 p-4"><section className="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg">
    <div className="mb-6 flex items-center gap-3"><div className={`rounded-xl p-3 text-white ${authMode.startsWith("officer") ? "bg-slate-800" : "bg-blue-700"}`}><MapPin size={26} /></div><div><h1 className="text-2xl font-bold">CivicTrack</h1><p className="text-sm text-slate-500">{authMode.startsWith("officer") ? "Officer Portal" : "Smart City Complaint System"}</p></div></div>
    <h2 className="mb-2 text-xl font-semibold">{authMode === "register" ? "Create a citizen account" : authMode === "officer-register" ? "Request an officer account" : authMode === "officer" ? "Officer sign in" : "Welcome back"}</h2>
    {authMode === "officer" && <p className="mb-5 text-sm text-slate-600">Sign in to review citizen reports and update their progress.</p>}
    {authMode === "officer-register" && <p className="mb-5 text-sm text-slate-600">Submit your details. An administrator will review and activate your account.</p>}
    {authMode === "login" && <p className="mb-5 text-sm text-slate-600">Sign in to report and track public issues.</p>}
    {authSuccess && <p className="mb-4 rounded-lg bg-green-50 p-3 text-sm text-green-800">{authSuccess}</p>}
    <form onSubmit={handleAuth} className="space-y-3">
      <input required className="w-full rounded-lg border p-3" placeholder="Username" value={auth.username} onChange={e => setAuth({ ...auth, username: e.target.value })} />
      {(authMode === "register" || authMode === "officer-register") && <><input required type="email" className="w-full rounded-lg border p-3" placeholder="Email" value={auth.email} onChange={e => setAuth({ ...auth, email: e.target.value })} /><input className="w-full rounded-lg border p-3" placeholder="First name" value={auth.first_name} onChange={e => setAuth({ ...auth, first_name: e.target.value })} /><input className="w-full rounded-lg border p-3" placeholder="Last name" value={auth.last_name} onChange={e => setAuth({ ...auth, last_name: e.target.value })} /><input className="w-full rounded-lg border p-3" placeholder="Phone" value={auth.phone} onChange={e => setAuth({ ...auth, phone: e.target.value })} /></>}
      {authMode === "officer-register" && <><select required className="w-full rounded-lg border p-3" value={auth.department} onChange={e => setAuth({ ...auth, department: e.target.value })}><option value="">Select your department</option>{departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}</select>{departments.length === 0 && <p className="text-sm text-amber-700">No departments are available. Ask an administrator to add departments before requesting an officer account.</p>}</>}
      <input required type="password" className="w-full rounded-lg border p-3" placeholder="Password" value={auth.password} onChange={e => setAuth({ ...auth, password: e.target.value })} />
      {(authMode === "register" || authMode === "officer-register") && <input required type="password" className="w-full rounded-lg border p-3" placeholder="Confirm password" value={auth.password_confirm} onChange={e => setAuth({ ...auth, password_confirm: e.target.value })} />}
      {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      <button disabled={loading} className={`w-full rounded-lg p-3 font-semibold text-white disabled:opacity-60 ${authMode.startsWith("officer") ? "bg-slate-800" : "bg-blue-700"}`}>{loading ? "Please wait..." : authMode === "register" ? "Register" : authMode === "officer-register" ? "Submit officer request" : authMode === "officer" ? "Sign in to officer portal" : "Sign in"}</button>
    </form>
    <div className="mt-5 flex flex-col gap-3 text-center text-sm">
      {authMode === "login" && <><button onClick={() => { setAuthMode("register"); setError(""); setAuthSuccess(""); }} className="text-blue-700">New citizen? Create an account</button><button onClick={() => { setAuthMode("officer"); setError(""); setAuthSuccess(""); }} className="font-semibold text-slate-700">Officer portal sign in</button></>}
      {authMode === "officer" && <><button onClick={() => { setAuthMode("officer-register"); setError(""); setAuthSuccess(""); }} className="font-semibold text-slate-700">Need an officer account? Request one</button><button onClick={() => { setAuthMode("login"); setError(""); setAuthSuccess(""); }} className="text-blue-700">Back to citizen sign in</button></>}
      {authMode === "officer-register" && <button onClick={() => { setAuthMode("officer"); setError(""); setAuthSuccess(""); }} className="text-blue-700">Already requested? Officer sign in</button>}
      {authMode === "register" && <button onClick={() => { setAuthMode("login"); setError(""); setAuthSuccess(""); }} className="text-blue-700">Already registered? Sign in</button>}
    </div>
  </section></main>;

  const counts = { total: complaints.length, submitted: complaints.filter(c => c.status === "SUBMITTED").length, progress: complaints.filter(c => c.status === "IN_PROGRESS").length, resolved: complaints.filter(c => c.status === "RESOLVED").length };
  return <div className="min-h-screen"><header className="bg-white shadow-sm"><div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4"><div className="flex items-center gap-3"><div className="rounded-lg bg-blue-700 p-2 text-white"><MapPin /></div><div><h1 className="text-xl font-bold">CivicTrack</h1><p className="text-xs text-slate-500">Smart City Complaint & Resolution</p></div></div><div className="flex items-center gap-3"><div className="text-right"><p className="font-semibold">{user.username}</p><p className="text-xs text-slate-500">{user.role}</p></div><button onClick={signOut} className="flex items-center gap-2 rounded-lg border px-3 py-2 text-sm"><LogOut size={16} /> Logout</button></div></div></header>
    <main className="mx-auto max-w-7xl px-4 py-8"><div className="mb-8 flex flex-wrap items-center justify-between gap-4"><div><h2 className="text-2xl font-bold">Complaint dashboard</h2><p className="mt-1 text-slate-500">Track reported issues and resolution progress.</p></div>{!isStaff && <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-2 rounded-lg bg-blue-700 px-4 py-3 font-semibold text-white"><Plus size={18} /> Report an issue</button>}</div>
      {notice && <p className="mb-4 rounded-lg bg-green-50 p-3 text-green-800">{notice}</p>}{error && <p className="mb-4 rounded-lg bg-red-50 p-3 text-red-800">{error}</p>}
      <section className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><Stat label="Visible complaints" value={counts.total} icon={<ClipboardList />} /><Stat label="Submitted" value={counts.submitted} icon={<AlertCircle />} /><Stat label="In progress" value={counts.progress} icon={<RefreshCw />} /><Stat label="Resolved" value={counts.resolved} icon={<CheckCircle2 />} /></section>
      {showForm && !isStaff && <section className="mb-8 rounded-2xl bg-white p-6 shadow-sm"><h3 className="mb-5 text-lg font-bold">Submit a complaint</h3><form onSubmit={handleCreate} className="grid gap-4 md:grid-cols-2">
        <input required className="rounded-lg border p-3" placeholder="Complaint title" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} /><select className="rounded-lg border p-3" value={form.category} onChange={e => setForm({ ...form, category: e.target.value })}>{categories.map(c => <option key={c}>{c}</option>)}</select>
        <input required className="rounded-lg border p-3 md:col-span-2" placeholder="Location / street" value={form.location} onChange={e => setForm({ ...form, location: e.target.value })} /><textarea required rows="4" className="rounded-lg border p-3 md:col-span-2" placeholder="Describe the problem..." value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} /><input type="file" accept="image/*" className="rounded-lg border p-3 md:col-span-2" onChange={e => setForm({ ...form, image: e.target.files?.[0] ?? null })} />
        <button disabled={loading} className="flex items-center justify-center gap-2 rounded-lg bg-blue-700 p-3 font-semibold text-white"><Send size={17} />{loading ? "Submitting..." : "Submit complaint"}</button>
      </form></section>}
      <section className="rounded-2xl bg-white p-5 shadow-sm"><div className="mb-5 flex flex-wrap items-center justify-between gap-3"><h3 className="text-lg font-bold">Complaints</h3><div className="flex flex-wrap gap-2"><input className="rounded-lg border p-2" placeholder="Search" value={search} onChange={e => setSearch(e.target.value)} /><select className="rounded-lg border p-2" value={filter} onChange={e => setFilter(e.target.value)}><option value="">All statuses</option>{["SUBMITTED", "IN_PROGRESS", "RESOLVED", "REJECTED"].map(s => <option key={s}>{s}</option>)}</select><button onClick={() => loadComplaints().catch(err => setError(JSON.stringify(err.response?.data ?? err.message)))} className="rounded-lg border p-2"><RefreshCw size={20} /></button></div></div>
        {complaints.length === 0 ? <p className="py-12 text-center text-slate-500">No complaints found.</p> : <div className="space-y-4">{complaints.map(c => <article key={c.id} className="rounded-xl border p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div><h4 className="font-bold">{c.title}</h4><p className="mt-1 text-sm text-slate-500">{c.category} · {c.location}</p></div><span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusColors[c.status]}`}>{c.status.replace("_", " ")}</span></div><p className="my-3 text-sm">{c.description}</p>{c.image && <a className="text-sm text-blue-700 underline" href={c.image.startsWith("http") ? c.image : `http://127.0.0.1:8000${c.image}`} target="_blank" rel="noreferrer">View submitted photo</a>}<div className="mt-3 flex flex-wrap justify-between gap-3 border-t pt-3 text-xs text-slate-500"><span>ID: {c.complaint_id}</span><span>{new Date(c.created_at).toLocaleString()}</span></div>{c.resolution_remarks && <div className="mt-3 rounded-lg bg-green-50 p-3 text-sm text-green-800"><b>Resolution:</b> {c.resolution_remarks}</div>}{c.resolution_image && <a className="mt-2 inline-block text-sm text-green-800 underline" href={`http://127.0.0.1:8000${c.resolution_image}`} target="_blank" rel="noreferrer">View resolution photo</a>}
          {user.role === "OFFICER" && c.assigned_officer === user.id && c.status === "SUBMITTED" && <button onClick={() => startWork(c)} className="mt-4 rounded-lg bg-amber-600 px-3 py-2 text-sm font-semibold text-white">Start work</button>}
          {user.role === "OFFICER" && c.assigned_officer === user.id && c.status === "IN_PROGRESS" && (resolvingId === c.id ? <form onSubmit={e => resolveComplaint(e, c)} className="mt-4 grid gap-3 rounded-lg bg-slate-50 p-4"><label className="text-sm font-semibold">Resolution details<textarea required rows="3" className="mt-1 w-full rounded-lg border p-3 font-normal" value={resolution.remarks} onChange={e => setResolution({ ...resolution, remarks: e.target.value })} placeholder="Describe how the issue was fixed" /></label><label className="text-sm font-semibold">Completion photo<input required type="file" accept="image/*" className="mt-1 block w-full rounded-lg border p-3 font-normal" onChange={e => setResolution({ ...resolution, image: e.target.files?.[0] ?? null })} /></label><div className="flex gap-2"><button disabled={loading} className="rounded-lg bg-green-700 px-3 py-2 text-sm font-semibold text-white">{loading ? "Saving..." : "Confirm resolved"}</button><button type="button" onClick={() => setResolvingId(null)} className="rounded-lg border px-3 py-2 text-sm">Cancel</button></div></form> : <button onClick={() => { setResolvingId(c.id); setResolution({ remarks: "", image: null }); }} className="mt-4 rounded-lg bg-green-700 px-3 py-2 text-sm font-semibold text-white">Mark as resolved</button>)}
          {c.history?.length > 0 && <details className="mt-4"><summary className="cursor-pointer text-sm font-semibold text-blue-700">View status history</summary><div className="mt-3 space-y-3">{c.history.map(h => <div key={h.id} className="border-l-2 border-blue-200 pl-3 text-sm"><p className="font-semibold">{h.new_status.replace("_", " ")}</p>{h.remarks && <p className="text-slate-600">{h.remarks}</p>}<p className="text-xs text-slate-400">{new Date(h.created_at).toLocaleString()}</p></div>)}</div></details>}</article>)}</div>}</section></main></div>;
}
function Stat({ label, value, icon }) { return <div className="rounded-2xl bg-white p-5 shadow-sm"><div className="mb-3 flex items-center justify-between text-slate-500"><span className="text-sm">{label}</span>{icon}</div><p className="text-3xl font-bold">{value}</p></div>; }
