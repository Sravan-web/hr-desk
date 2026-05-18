"""
write_frontend.py — writes all frontend source files to disk.
Run: python write_frontend.py
"""
import os

FRONTEND = "/Users/sravankumar/Desktop/HR Desk/frontend/src"
COMP = FRONTEND + "/components"
os.makedirs(COMP, exist_ok=True)

files = {}

# ── store.js ──────────────────────────────────────────────────────────────────
files[FRONTEND + "/store.js"] = """import { create } from 'zustand';
const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const API_BASE_URL = API;
export const useStore = create((set) => ({
  token: localStorage.getItem('hr_token') || null,
  employee: JSON.parse(localStorage.getItem('hr_employee') || 'null'),
  isAuthenticated: !!localStorage.getItem('hr_token'),
  login: (token, emp) => {
    localStorage.setItem('hr_token', token);
    localStorage.setItem('hr_employee', JSON.stringify(emp));
    set({ token, employee: emp, isAuthenticated: true, activeTab: 'dashboard' });
  },
  logout: () => {
    localStorage.removeItem('hr_token');
    localStorage.removeItem('hr_employee');
    set({ token: null, employee: null, isAuthenticated: false, activeTab: 'dashboard' });
  },
  activeTab: 'dashboard',
  setActiveTab: (tab) => set({ activeTab: tab }),
  isSidebarOpen: false,
  toggleSidebar: () => set((s) => ({ isSidebarOpen: !s.isSidebarOpen })),
  closeSidebar: () => set({ isSidebarOpen: false }),
  mockTickets: {
    'TKT-8902': { priority: 'HIGH', query: 'Payroll discrepancy in March.', employee_id: 'EMP-001', status: 'OPEN' }
  },
}));
"""

# ── api.js ────────────────────────────────────────────────────────────────────
files[FRONTEND + "/api.js"] = """import axios from 'axios';
const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const api = axios.create({ baseURL: BASE });
api.interceptors.request.use((c) => {
  const t = localStorage.getItem('hr_token');
  if (t) c.headers.Authorization = 'Bearer ' + t;
  return c;
});
export const login = (email, password) => api.post('/auth/login', { email, password }).then(r => r.data);
export const getMe = () => api.get('/auth/me').then(r => r.data);
export const getDepartments = () => api.get('/departments').then(r => r.data);
export const getEmployees = (p) => api.get('/employees', { params: p }).then(r => r.data);
export const createEmployee = (d) => api.post('/employees', d).then(r => r.data);
export const updateEmployee = (id, d) => api.put('/employees/' + id, d).then(r => r.data);
export const deactivateEmployee = (id) => api.delete('/employees/' + id).then(r => r.data);
export const getAttendance = (p) => api.get('/attendance', { params: p }).then(r => r.data);
export const checkIn = () => api.post('/attendance/checkin').then(r => r.data);
export const checkOut = () => api.post('/attendance/checkout').then(r => r.data);
export const getAttendanceSummary = (id, m, y) => api.get('/attendance/summary/' + id, { params: { month: m, year: y } }).then(r => r.data);
export const getLeaves = (p) => api.get('/leaves', { params: p }).then(r => r.data);
export const applyLeave = (d) => api.post('/leaves', d).then(r => r.data);
export const approveLeave = (id, d) => api.put('/leaves/' + id + '/approve', d).then(r => r.data);
export const getHolidays = (y) => api.get('/holidays', { params: { year: y } }).then(r => r.data);
export const getPayroll = (p) => api.get('/payroll', { params: p }).then(r => r.data);
export const processPayroll = (d) => api.post('/payroll/process', d).then(r => r.data);
export const getPayslip = (id) => api.get('/payroll/' + id + '/payslip').then(r => r.data);
export const markPayrollPaid = (id) => api.put('/payroll/' + id + '/mark-paid').then(r => r.data);
export const getTaxDeclarations = () => api.get('/tax/declarations').then(r => r.data);
export const submitTaxDeclaration = (d) => api.post('/tax/declarations', d).then(r => r.data);
export const calculateTax = (p) => api.get('/tax/calculator', { params: p }).then(r => r.data);
export const getBenefitPlans = () => api.get('/benefits/plans').then(r => r.data);
export const getMyBenefits = () => api.get('/benefits/my').then(r => r.data);
export const getDashboardStats = () => api.get('/reports/dashboard').then(r => r.data);
export const getPayrollSummary = (m, y) => api.get('/reports/payroll-summary', { params: { month: m, year: y } }).then(r => r.data);
export const getHeadcountReport = () => api.get('/reports/headcount').then(r => r.data);
export const getAttendanceSummaryReport = (m, y) => api.get('/reports/attendance-summary', { params: { month: m, year: y } }).then(r => r.data);
export const getAnnouncements = () => api.get('/announcements').then(r => r.data);
export const sendChat = (d) => api.post('/chat', d).then(r => r.data);
export const getTickets = () => api.get('/tickets').then(r => r.data);
export const uploadPolicy = (file) => { const fd = new FormData(); fd.append('file', file); return api.post('/upload_policy', fd).then(r => r.data); };
export default api;
"""

print("Writing frontend files...")
for path, content in files.items():
    with open(path, 'w') as f:
        f.write(content)
    print(f"  {os.path.basename(path)}: {os.path.getsize(path)} bytes")

print("Done.")

# ── Components ────────────────────────────────────────────────────────────────
components = {}

components["LoginPage.jsx"] = """import React, { useState } from 'react';
import { Sparkles, Eye, EyeOff, Loader2, Lock, Mail } from 'lucide-react';
import { login } from '../api';
import { useStore } from '../store';

export default function LoginPage() {
  const { login: storeLogin } = useStore();
  const [email, setEmail] = useState('sravan@hrdesk.com');
  const [password, setPassword] = useState('Password@123');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault(); setLoading(true); setError('');
    try {
      const data = await login(email, password);
      storeLogin(data.access_token, { id: data.employee_id, name: data.name, role: data.role, department: data.department });
    } catch (err) { setError(err.response?.data?.detail || err.message || 'Login failed'); }
    finally { setLoading(false); }
  };

  const demos = [
    { label: 'Admin', email: 'sravan@hrdesk.com' },
    { label: 'HR Mgr', email: 'priya@hrdesk.com' },
    { label: 'Employee', email: 'rahul@hrdesk.com' },
  ];

  return (
    <div className="min-h-screen bg-[#0f172a] flex items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-violet-500/10 rounded-full blur-[120px]" />
      </div>
      <div className="w-full max-w-md relative z-10">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-tr from-blue-500 to-cyan-400 rounded-2xl shadow-[0_0_30px_rgba(56,189,248,0.4)] mb-4">
            <Sparkles className="text-white" size={32} />
          </div>
          <h1 className="text-3xl font-bold text-white">HR Desk</h1>
          <p className="text-slate-400 mt-1">Complete HR Management Platform</p>
        </div>
        <div className="bg-[#1e293b]/80 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl">
          <h2 className="text-xl font-semibold text-white mb-6">Sign in</h2>
          {error && <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm">{error}</div>}
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Email</label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input type="email" value={email} onChange={e => setEmail(e.target.value)} required
                  className="w-full pl-9 pr-4 py-3 bg-[#0f172a] border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Password</label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input type={showPw ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} required
                  className="w-full pl-9 pr-10 py-3 bg-[#0f172a] border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all" />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white">
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-semibold hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 transition-all flex items-center justify-center gap-2 mt-2">
              {loading ? <><Loader2 size={18} className="animate-spin" /> Signing in...</> : 'Sign In'}
            </button>
          </form>
          <div className="mt-6 pt-6 border-t border-white/10">
            <p className="text-xs text-slate-500 mb-3 text-center">Demo accounts (password: Password@123)</p>
            <div className="grid grid-cols-3 gap-2">
              {demos.map(d => (
                <button key={d.email} onClick={() => { setEmail(d.email); setPassword('Password@123'); }}
                  className="p-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs text-slate-300 hover:text-white transition-all text-center">
                  {d.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
"""

components["Dashboard.jsx"] = """import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Users, Clock, Calendar, DollarSign, TrendingUp, Bell, CheckCircle } from 'lucide-react';
import { getDashboardStats, getAnnouncements } from '../api';
import { useStore } from '../store';

export default function Dashboard() {
  const { employee } = useStore();
  const isHR = ['ADMIN','HR_MANAGER'].includes(employee?.role);
  const { data: stats } = useQuery({ queryKey: ['dashboard'], queryFn: getDashboardStats, enabled: isHR, retry: 1, staleTime: 30000 });
  const { data: anns = [] } = useQuery({ queryKey: ['announcements'], queryFn: getAnnouncements, retry: 1, staleTime: 60000 });

  const s = stats || { total_employees:10, active_employees:9, on_leave_today:1, pending_leaves:3, present_today:8, current_month_payroll:875000,
    department_headcount:[{dept:'Engineering',count:3},{dept:'HR',count:2},{dept:'Finance',count:2},{dept:'Marketing',count:1},{dept:'Operations',count:1},{dept:'Sales',count:1}],
    payroll_trend:[{period:'2025-12',total:820000},{period:'2026-01',total:845000},{period:'2026-02',total:830000},{period:'2026-03',total:860000},{period:'2026-04',total:855000},{period:'2026-05',total:875000}] };

  const cards = [
    { label:'Total Employees', value:s.total_employees, sub:s.active_employees+' active', color:'blue' },
    { label:'Present Today', value:s.present_today, sub:s.on_leave_today+' on leave', color:'emerald' },
    { label:'Pending Leaves', value:s.pending_leaves, sub:'awaiting approval', color:'amber' },
    { label:'Monthly Payroll', value:'₹'+(s.current_month_payroll/100000).toFixed(1)+'L', sub:'this month', color:'violet' },
  ];
  const cm = { blue:'from-blue-500/20 to-blue-500/5 border-blue-500/20 text-blue-400', emerald:'from-emerald-500/20 to-emerald-500/5 border-emerald-500/20 text-emerald-400', amber:'from-amber-500/20 to-amber-500/5 border-amber-500/20 text-amber-400', violet:'from-violet-500/20 to-violet-500/5 border-violet-500/20 text-violet-400' };
  const maxP = Math.max(...s.payroll_trend.map(t => t.total), 1);

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-white">Good {new Date().getHours()<12?'morning':new Date().getHours()<17?'afternoon':'evening'}, {employee?.name?.split(' ')[0]} 👋</h2>
          <p className="text-slate-400 mt-1">Here's what's happening today.</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-5 mb-8">
          {cards.map(c => (
            <div key={c.label} className={'bg-gradient-to-br '+cm[c.color]+' p-6 rounded-2xl border backdrop-blur-md relative overflow-hidden'}>
              <div className="text-3xl font-bold text-white mb-1">{c.value}</div>
              <div className="text-sm font-medium text-slate-300">{c.label}</div>
              <div className="text-xs text-slate-500 mt-0.5">{c.sub}</div>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6">
          <div className="xl:col-span-2 bg-[#1e293b]/60 border border-white/5 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-white mb-5 flex items-center gap-2"><TrendingUp size={18} className="text-blue-400"/>Payroll Trend</h3>
            <div className="flex items-end gap-3 h-40">
              {s.payroll_trend.map((t,i) => {
                const pct = (t.total/maxP)*100;
                return (
                  <div key={t.period} className="flex-1 flex flex-col items-center gap-2">
                    <div className="text-xs text-slate-400">₹{(t.total/100000).toFixed(1)}L</div>
                    <div className="w-full flex items-end" style={{height:'80px'}}>
                      <div className={'w-full rounded-t-lg '+(i===s.payroll_trend.length-1?'bg-blue-500':'bg-blue-500/30')} style={{height:pct+'%',minHeight:'4px'}}/>
                    </div>
                    <div className="text-[10px] text-slate-500">{t.period.slice(5)}/{t.period.slice(2,4)}</div>
                  </div>
                );
              })}
            </div>
          </div>
          <div className="bg-[#1e293b]/60 border border-white/5 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-white mb-5 flex items-center gap-2"><Users size={18} className="text-violet-400"/>By Department</h3>
            <div className="space-y-3">
              {s.department_headcount.map(d => (
                <div key={d.dept}>
                  <div className="flex justify-between text-sm mb-1"><span className="text-slate-300">{d.dept}</span><span className="text-slate-400">{d.count}</span></div>
                  <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-violet-500 to-blue-500 rounded-full" style={{width:(d.count/s.total_employees*100)+'%'}}/>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="bg-[#1e293b]/60 border border-white/5 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><Bell size={18} className="text-amber-400"/>Announcements</h3>
          {anns.length===0 ? <p className="text-slate-500 text-sm">No announcements.</p> : (
            <div className="space-y-3">
              {anns.slice(0,4).map(a => (
                <div key={a.id} className="flex gap-4 p-4 bg-white/5 rounded-xl border border-white/5">
                  <div className={'w-2 h-2 rounded-full mt-1.5 flex-shrink-0 '+(a.type==='PAYROLL'?'bg-emerald-400':a.type==='POLICY'?'bg-amber-400':'bg-blue-400')}/>
                  <div>
                    <div className="font-medium text-slate-200 text-sm">{a.title}</div>
                    <div className="text-xs text-slate-400 mt-0.5">{a.content}</div>
                    <div className="text-[10px] text-slate-600 mt-1">{new Date(a.created_at).toLocaleDateString()}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
"""

components["LeaveManagement.jsx"] = """import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Calendar, Plus, CheckCircle, XCircle, Clock, X, Loader2 } from 'lucide-react';
import { getLeaves, applyLeave, approveLeave, getHolidays } from '../api';
import { useStore } from '../store';

const SC = { PENDING:'bg-amber-500/10 text-amber-400 border-amber-500/20', APPROVED:'bg-emerald-500/10 text-emerald-400 border-emerald-500/20', REJECTED:'bg-rose-500/10 text-rose-400 border-rose-500/20' };

export default function LeaveManagement() {
  const { employee } = useStore();
  const qc = useQueryClient();
  const isHR = ['ADMIN','HR_MANAGER','MANAGER'].includes(employee?.role);
  const [showApply, setShowApply] = useState(false);
  const [tab, setTab] = useState('my');

  const { data: myLeaves = [] } = useQuery({ queryKey:['leaves','my'], queryFn:() => getLeaves(), staleTime:30000, retry:1 });
  const { data: pending = [] } = useQuery({ queryKey:['leaves','pending'], queryFn:() => getLeaves({status:'PENDING'}), enabled:isHR, staleTime:30000, retry:1 });
  const { data: holidays = [] } = useQuery({ queryKey:['holidays'], queryFn:() => getHolidays(new Date().getFullYear()), staleTime:3600000, retry:1 });

  const approveMut = useMutation({ mutationFn:({id,data}) => approveLeave(id,data), onSuccess:() => qc.invalidateQueries({queryKey:['leaves']}) });

  const balances = [
    { type:'Sick Leave', bal:employee?.sick_leave_balance??12, total:12, color:'rose' },
    { type:'Casual Leave', bal:employee?.casual_leave_balance??12, total:12, color:'amber' },
    { type:'Paid Leave', bal:employee?.paid_leave_balance??15, total:15, color:'emerald' },
  ];
  const cm = { rose:'from-rose-500/20 to-rose-500/5 border-rose-500/20 text-rose-400 bg-rose-500', amber:'from-amber-500/20 to-amber-500/5 border-amber-500/20 text-amber-400 bg-amber-500', emerald:'from-emerald-500/20 to-emerald-500/5 border-emerald-500/20 text-emerald-400 bg-emerald-500' };
  const leaves = tab==='my' ? myLeaves : pending;

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div><h2 className="text-3xl font-bold text-white">Leave Management</h2><p className="text-slate-400 mt-1">Apply and track leave requests.</p></div>
          <button onClick={() => setShowApply(true)} className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium transition-colors"><Plus size={18}/>Apply for Leave</button>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
          {balances.map(b => (
            <div key={b.type} className={'bg-gradient-to-br '+cm[b.color].split(' ').slice(0,3).join(' ')+' p-5 rounded-2xl border backdrop-blur-md'}>
              <div className="text-sm font-medium text-slate-300 mb-3">{b.type}</div>
              <div className="flex items-baseline gap-2 mb-3">
                <span className={'text-3xl font-bold '+cm[b.color].split(' ')[3]}>{b.bal}</span>
                <span className="text-slate-400 text-sm">/ {b.total} days</span>
              </div>
              <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                <div className={'h-full '+cm[b.color].split(' ')[4]+' rounded-full'} style={{width:(b.bal/b.total*100)+'%'}}/>
              </div>
            </div>
          ))}
        </div>
        {isHR && (
          <div className="flex gap-1 p-1 bg-[#1e293b]/60 rounded-xl border border-white/5 w-fit mb-5">
            {[{id:'my',l:'My Leaves'},{id:'pending',l:'Pending ('+pending.length+')'}].map(t => (
              <button key={t.id} onClick={() => setTab(t.id)} className={'px-4 py-2 rounded-lg text-sm font-medium transition-all '+(tab===t.id?'bg-blue-600 text-white':'text-slate-400 hover:text-white')}>{t.l}</button>
            ))}
          </div>
        )}
        <div className="bg-[#1e293b]/60 border border-white/5 rounded-2xl overflow-hidden mb-6">
          <div className="px-6 py-4 border-b border-white/5"><h3 className="font-semibold text-white">{tab==='my'?'My Requests':'Pending Approvals'}</h3></div>
          {leaves.length===0 ? <div className="text-center py-16 text-slate-500"><Calendar size={40} className="mx-auto mb-3 opacity-30"/><p>No leave requests.</p></div>
          : <div className="divide-y divide-white/5">
              {leaves.map(l => (
                <div key={l.id} className="px-6 py-4 hover:bg-white/5 transition-colors">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-1">
                        <span className="font-medium text-slate-200">{l.leave_type} Leave</span>
                        <span className={'text-xs px-2.5 py-0.5 rounded-full border font-medium '+(SC[l.status]||SC.PENDING)}>{l.status}</span>
                      </div>
                      {tab==='pending' && l.employee_name && <div className="text-sm text-blue-400 mb-1">{l.employee_name}</div>}
                      <div className="text-sm text-slate-400">{new Date(l.start_date).toLocaleDateString('en-IN')} — {new Date(l.end_date).toLocaleDateString('en-IN')} <span className="text-slate-500 ml-1">({l.days_requested}d)</span></div>
                      {l.reason && <div className="text-xs text-slate-500 mt-1 italic">"{l.reason}"</div>}
                    </div>
                    {tab==='pending' && l.status==='PENDING' && isHR && (
                      <div className="flex gap-2 flex-shrink-0">
                        <button onClick={() => approveMut.mutate({id:l.id,data:{status:'APPROVED'}})} disabled={approveMut.isPending} className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs rounded-lg font-medium">Approve</button>
                        <button onClick={() => approveMut.mutate({id:l.id,data:{status:'REJECTED',rejection_reason:'Not approved'}})} disabled={approveMut.isPending} className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white text-xs rounded-lg font-medium">Reject</button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>}
        </div>
        {holidays.filter(h => new Date(h.date)>=new Date()).length>0 && (
          <div className="bg-[#1e293b]/60 border border-white/5 rounded-2xl p-6">
            <h3 className="font-semibold text-white mb-4 flex items-center gap-2"><Calendar size={16} className="text-cyan-400"/>Upcoming Holidays</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {holidays.filter(h => new Date(h.date)>=new Date()).slice(0,6).map(h => (
                <div key={h.id} className="flex items-center gap-3 p-3 bg-white/5 rounded-xl">
                  <div className="w-10 h-10 bg-cyan-500/10 rounded-lg flex items-center justify-center text-cyan-400 font-bold text-sm">{new Date(h.date).getDate()}</div>
                  <div><div className="text-sm font-medium text-slate-200">{h.name}</div><div className="text-xs text-slate-500">{new Date(h.date).toLocaleDateString('en-IN',{month:'long',year:'numeric'})}</div></div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      {showApply && <ApplyModal onClose={() => setShowApply(false)} onSuccess={() => { setShowApply(false); qc.invalidateQueries({queryKey:['leaves']}); }}/>}
    </div>
  );
}

function ApplyModal({ onClose, onSuccess }) {
  const [form, setForm] = useState({ leave_type:'CASUAL', start_date:new Date().toISOString().split('T')[0], end_date:new Date().toISOString().split('T')[0], reason:'' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const days = form.start_date&&form.end_date ? Math.max(0,(new Date(form.end_date)-new Date(form.start_date))/86400000+1) : 0;

  const handleSubmit = async (e) => {
    e.preventDefault(); setLoading(true); setError('');
    try { await applyLeave(form); onSuccess(); }
    catch(err) { setError(err.response?.data?.detail||err.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#1e293b] border border-white/10 rounded-2xl w-full max-w-md shadow-2xl">
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <h3 className="text-xl font-bold text-white">Apply for Leave</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white"><X size={20}/></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm">{error}</div>}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">Leave Type</label>
            <select value={form.leave_type} onChange={e => setForm({...form,leave_type:e.target.value})} className="w-full px-3 py-2.5 bg-[#0f172a] border border-white/10 rounded-xl text-slate-300 focus:outline-none text-sm">
              {['SICK','CASUAL','PAID','UNPAID','EMERGENCY'].map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="block text-sm font-medium text-slate-300 mb-1.5">Start</label><input type="date" value={form.start_date} onChange={e => setForm({...form,start_date:e.target.value})} className="w-full px-3 py-2.5 bg-[#0f172a] border border-white/10 rounded-xl text-white focus:outline-none text-sm"/></div>
            <div><label className="block text-sm font-medium text-slate-300 mb-1.5">End</label><input type="date" value={form.end_date} onChange={e => setForm({...form,end_date:e.target.value})} className="w-full px-3 py-2.5 bg-[#0f172a] border border-white/10 rounded-xl text-white focus:outline-none text-sm"/></div>
          </div>
          {days>0 && <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-400 text-sm text-center">{days} day{days>1?'s':''} requested</div>}
          <div><label className="block text-sm font-medium text-slate-300 mb-1.5">Reason</label><textarea value={form.reason} onChange={e => setForm({...form,reason:e.target.value})} rows={3} className="w-full px-3 py-2.5 bg-[#0f172a] border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none text-sm resize-none" placeholder="Optional reason..."/></div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="flex-1 py-2.5 border border-white/10 text-slate-300 rounded-xl hover:bg-white/5 font-medium">Cancel</button>
            <button type="submit" disabled={loading} className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium flex items-center justify-center gap-2 disabled:opacity-50">
              {loading ? <><Loader2 size={16} className="animate-spin"/>Submitting...</> : 'Submit'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
"""

components["PayrollModule.jsx"] = """import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DollarSign, Play, CheckCircle, FileText, Loader2, TrendingUp, TrendingDown } from 'lucide-react';
import { getPayroll, processPayroll, getPayslip, markPayrollPaid } from '../api';
import { useStore } from '../store';

const SC = { DRAFT:'bg-slate-500/10 text-slate-400 border-slate-500/20', PROCESSED:'bg-blue-500/10 text-blue-400 border-blue-500/20', PAID:'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' };

export default function PayrollModule() {
  const { employee } = useStore();
  const qc = useQueryClient();
  const isHR = ['ADMIN','HR_MANAGER'].includes(employee?.role);
  const today = new Date();
  const [month, setMonth] = useState(today.getMonth()+1);
  const [year, setYear] = useState(today.getFullYear());
  const [payslipId, setPayslipId] = useState(null);
  const [result, setResult] = useState(null);

  const { data: records = [], isLoading } = useQuery({ queryKey:['payroll',month,year], queryFn:() => getPayroll({month,year}), staleTime:30000, retry:1 });
  const runMut = useMutation({ mutationFn:processPayroll, onSuccess:(d) => { setResult(d); qc.invalidateQueries({queryKey:['payroll']}); } });
  const paidMut = useMutation({ mutationFn:({id}) => markPayrollPaid(id), onSuccess:() => qc.invalidateQueries({queryKey:['payroll']}) });

  const totalGross = records.reduce((s,r) => s+(r.gross_earnings||0),0);
  const totalNet = records.reduce((s,r) => s+(r.net_salary||0),0);
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div><h2 className="text-3xl font-bold text-white">Payroll</h2><p className="text-slate-400 mt-1">Salary calculation and payslip generation.</p></div>
          {isHR && <button onClick={() => runMut.mutate({month,year})} disabled={runMut.isPending} className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-medium transition-colors disabled:opacity-50">
            {runMut.isPending ? <Loader2 size={18} className="animate-spin"/> : <Play size={18}/>} Run Payroll
          </button>}
        </div>
        {result && <div className="mb-6 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl"><div className="flex items-center gap-2 text-emerald-400 font-semibold mb-1"><CheckCircle size={18}/>Processed {result.processed} employees for {result.period}</div></div>}
        {records.length>0 && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {[['Total Gross','₹'+(totalGross/100000).toFixed(2)+'L','blue'],['Total Net','₹'+(totalNet/100000).toFixed(2)+'L','emerald'],['Employees',records.length,'violet'],['Paid',records.filter(r=>r.status==='PAID').length,'amber']].map(([l,v,c]) => {
              const cm = {blue:'border-blue-500/20 text-blue-400',emerald:'border-emerald-500/20 text-emerald-400',violet:'border-violet-500/20 text-violet-400',amber:'border-amber-500/20 text-amber-400'};
              return <div key={l} className={'p-5 bg-[#1e293b]/60 border '+cm[c].split(' ')[0]+' rounded-2xl'}><div className="text-xs text-slate-400 mb-2">{l}</div><div className={'text-2xl font-bold '+cm[c].split(' ')[1]}>{v}</div></div>;
            })}
          </div>
        )}
        <div className="flex items-center gap-3 mb-5">
          <select value={month} onChange={e => setMonth(parseInt(e.target.value))} className="px-4 py-2 bg-[#1e293b] border border-white/10 rounded-xl text-slate-300 focus:outline-none text-sm">
            {months.map((m,i) => <option key={m} value={i+1}>{m}</option>)}
          </select>
          <select value={year} onChange={e => setYear(parseInt(e.target.value))} className="px-4 py-2 bg-[#1e293b] border border-white/10 rounded-xl text-slate-300 focus:outline-none text-sm">
            {[2024,2025,2026].map(y => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
        <div className="bg-[#1e293b]/60 border border-white/5 rounded-2xl overflow-hidden">
          <div className="px-6 py-4 border-b border-white/5"><h3 className="font-semibold text-white">Payroll — {months[month-1]} {year}</h3></div>
          {isLoading ? <div className="flex items-center justify-center py-16"><Loader2 size={28} className="animate-spin text-blue-400"/></div>
          : records.length===0 ? <div className="text-center py-16 text-slate-500"><DollarSign size={40} className="mx-auto mb-3 opacity-30"/><p>No records. {isHR&&'Click Run Payroll to process.'}</p></div>
          : <div className="overflow-x-auto"><table className="w-full">
              <thead><tr className="border-b border-white/5">{['Employee','Gross','PF','TDS','Deductions','Net Pay','Status',''].map(h => <th key={h} className="text-left px-6 py-3 text-xs font-semibold text-slate-400 uppercase">{h}</th>)}</tr></thead>
              <tbody className="divide-y divide-white/5">
                {records.map(r => (
                  <tr key={r.id} className="hover:bg-white/5 transition-colors group">
                    <td className="px-6 py-4"><div className="font-medium text-slate-200 text-sm">{r.employee_name}</div><div className="text-xs text-slate-500">{r.present_days}/{r.working_days}d {r.lop_days>0&&<span className="text-rose-400">{r.lop_days} LOP</span>}</div></td>
                    <td className="px-6 py-4 text-sm text-slate-300">₹{(r.gross_earnings||0).toLocaleString('en-IN')}</td>
                    <td className="px-6 py-4 text-sm text-slate-400">₹{(r.pf_employee||0).toLocaleString('en-IN')}</td>
                    <td className="px-6 py-4 text-sm text-slate-400">₹{(r.income_tax_tds||0).toLocaleString('en-IN')}</td>
                    <td className="px-6 py-4 text-sm text-rose-400">-₹{(r.total_deductions||0).toLocaleString('en-IN')}</td>
                    <td className="px-6 py-4"><span className="font-bold text-emerald-400">₹{(r.net_salary||0).toLocaleString('en-IN')}</span></td>
                    <td className="px-6 py-4"><span className={'text-xs px-2.5 py-1 rounded-full border font-medium '+(SC[r.status]||SC.DRAFT)}>{r.status}</span></td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button onClick={() => setPayslipId(r.id)} className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors" title="Payslip"><FileText size={14}/></button>
                        {isHR&&r.status==='PROCESSED'&&<button onClick={() => paidMut.mutate({id:r.id})} className="p-1.5 text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 rounded-lg transition-colors" title="Mark Paid"><CheckCircle size={14}/></button>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table></div>}
        </div>
      </div>
      {payslipId && <PayslipModal id={payslipId} onClose={() => setPayslipId(null)}/>}
    </div>
  );
}

function PayslipModal({ id, onClose }) {
  const { data: p, isLoading } = useQuery({ queryKey:['payslip',id], queryFn:() => getPayslip(id) });
  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#1e293b] border border-white/10 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="flex items-center justify-between p-6 border-b border-white/10"><h3 className="text-xl font-bold text-white">Payslip</h3><button onClick={onClose} className="text-slate-400 hover:text-white">✕</button></div>
        {isLoading ? <div className="flex items-center justify-center py-16"><Loader2 size={28} className="animate-spin text-blue-400"/></div>
        : p ? <div className="p-6">
            <div className="flex justify-between items-start mb-6 pb-6 border-b border-white/10">
              <div><div className="text-xl font-bold text-white">{p.employee?.name}</div><div className="text-slate-400 text-sm">{p.employee?.designation} · {p.employee?.department}</div><div className="text-slate-500 text-xs mt-1">ID: {p.employee?.id} · PAN: {p.employee?.pan}</div></div>
              <div className="text-right"><div className="text-sm text-slate-400">Pay Period</div><div className="font-bold text-white">{p.period?.pay_period}</div></div>
            </div>
            <div className="grid grid-cols-3 gap-3 mb-6">
              {[['Working Days',p.attendance?.working_days],['Present',p.attendance?.present_days],['LOP',p.attendance?.lop_days]].map(([l,v]) => (
                <div key={l} className="p-3 bg-white/5 rounded-xl text-center"><div className="text-xs text-slate-500 mb-1">{l}</div><div className="font-bold text-white">{v}</div></div>
              ))}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div><h4 className="text-sm font-semibold text-emerald-400 mb-3 uppercase">Earnings</h4>
                <div className="space-y-2">
                  {Object.entries(p.earnings||{}).filter(([k]) => k!=='gross_earnings').map(([k,v]) => v>0&&<div key={k} className="flex justify-between text-sm"><span className="text-slate-400 capitalize">{k.replace(/_/g,' ')}</span><span className="text-slate-200">₹{v.toLocaleString('en-IN')}</span></div>)}
                  <div className="flex justify-between text-sm font-bold pt-2 border-t border-white/10"><span className="text-emerald-400">Gross</span><span className="text-emerald-400">₹{(p.earnings?.gross_earnings||0).toLocaleString('en-IN')}</span></div>
                </div>
              </div>
              <div><h4 className="text-sm font-semibold text-rose-400 mb-3 uppercase">Deductions</h4>
                <div className="space-y-2">
                  {Object.entries(p.deductions||{}).filter(([k]) => k!=='total_deductions').map(([k,v]) => v>0&&<div key={k} className="flex justify-between text-sm"><span className="text-slate-400 capitalize">{k.replace(/_/g,' ')}</span><span className="text-rose-400">-₹{v.toLocaleString('en-IN')}</span></div>)}
                  <div className="flex justify-between text-sm font-bold pt-2 border-t border-white/10"><span className="text-rose-400">Total</span><span className="text-rose-400">-₹{(p.deductions?.total_deductions||0).toLocaleString('en-IN')}</span></div>
                </div>
              </div>
            </div>
            <div className="p-5 bg-gradient-to-r from-emerald-500/20 to-emerald-500/5 border border-emerald-500/20 rounded-2xl flex justify-between items-center">
              <div><div className="text-sm text-slate-400">Net Salary</div><div className="text-xs text-slate-500">After all deductions</div></div>
              <div className="text-3xl font-bold text-emerald-400">₹{(p.net_salary||0).toLocaleString('en-IN')}</div>
            </div>
          </div>
        : <div className="text-center py-16 text-slate-500">Not found.</div>}
      </div>
    </div>
  );
}
"""

components["TaxManagement.jsx"] = """import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Calculator, FileText, Loader2, X, Info } from 'lucide-react';
import { getTaxDeclarations, submitTaxDeclaration, calculateTax } from '../api';

function clientTax(taxable, regime) {
  const slabs = regime==='NEW' ? [[300000,0],[600000,.05],[900000,.10],[1200000,.15],[1500000,.20],[Infinity,.30]] : [[250000,0],[500000,.05],[1000000,.20],[Infinity,.30]];
  let tax=0,prev=0;
  for(const [lim,rate] of slabs){ if(taxable<=prev)break; tax+=(Math.min(taxable,lim)-prev)*rate; prev=lim; }
  if(regime==='NEW'&&taxable<=700000) tax=Math.max(0,tax-25000);
  return Math.round(tax*1.04);
}

export default function TaxManagement() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [calc, setCalc] = useState({ annual_income:1200000, regime:'NEW', pf_annual:21600, deductions_80c:150000 });
  const [result, setResult] = useState(null);
  const [calcLoading, setCalcLoading] = useState(false);

  const { data: decls = [] } = useQuery({ queryKey:['tax-decls'], queryFn:getTaxDeclarations, staleTime:60000, retry:1 });

  const handleCalc = async () => {
    setCalcLoading(true);
    try {
      const r = await calculateTax(calc);
      setResult(r);
    } catch {
      const taxable = Math.max(0, calc.annual_income-50000-calc.pf_annual-Math.min(150000,calc.deductions_80c));
      const tax = clientTax(taxable, calc.regime);
      setResult({ annual_income:calc.annual_income, regime:calc.regime, standard_deduction:50000, pf_deduction:calc.pf_annual, section_80c:Math.min(150000,calc.deductions_80c), taxable_income:taxable, annual_tax:tax, monthly_tds:Math.round(tax/12), effective_rate:calc.annual_income>0?((tax/calc.annual_income)*100).toFixed(2):0 });
    } finally { setCalcLoading(false); }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div><h2 className="text-3xl font-bold text-white">Tax Management</h2><p className="text-slate-400 mt-1">Income tax calculation and declarations.</p></div>
          <button onClick={() => setShowForm(true)} className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium transition-colors"><FileText size={18}/>Submit Declaration</button>
        </div>
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-8">
          <div className="bg-[#1e293b]/60 border border-white/5 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-white mb-5 flex items-center gap-2"><Calculator size={18} className="text-blue-400"/>Tax Calculator</h3>
            <div className="space-y-4">
              <div><label className="block text-sm font-medium text-slate-300 mb-1.5">Annual Income (₹)</label><input type="number" value={calc.annual_income} onChange={e => setCalc({...calc,annual_income:parseFloat(e.target.value)||0})} className="w-full px-3 py-2.5 bg-[#0f172a] border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-sm"/></div>
              <div><label className="block text-sm font-medium text-slate-300 mb-1.5">Regime</label>
                <div className="flex gap-2">
                  {['NEW','OLD'].map(r => <button key={r} type="button" onClick={() => setCalc({...calc,regime:r})} className={'flex-1 py-2 rounded-xl text-sm font-medium transition-all '+(calc.regime===r?'bg-blue-600 text-white':'bg-white/5 text-slate-400 hover:bg-white/10')}>{r} Regime</button>)}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-sm font-medium text-slate-300 mb-1.5">Annual PF (₹)</label><input type="number" value={calc.pf_annual} onChange={e => setCalc({...calc,pf_annual:parseFloat(e.target.value)||0})} className="w-full px-3 py-2.5 bg-[#0f172a] border border-white/10 rounded-xl text-white focus:outline-none text-sm"/></div>
                <div><label className="block text-sm font-medium text-slate-300 mb-1.5">80C (₹)</label><input type="number" value={calc.deductions_80c} onChange={e => setCalc({...calc,deductions_80c:parseFloat(e.target.value)||0})} className="w-full px-3 py-2.5 bg-[#0f172a] border border-white/10 rounded-xl text-white focus:outline-none text-sm"/></div>
              </div>
              <button onClick={handleCalc} disabled={calcLoading} className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium flex items-center justify-center gap-2 disabled:opacity-50">
                {calcLoading ? <Loader2 size={16} className="animate-spin"/> : <Calculator size={16}/>} Calculate
              </button>
            </div>
            {result && (
              <div className="mt-5 p-4 bg-[#0f172a] rounded-xl border border-white/10 space-y-2">
                <div className="text-sm font-semibold text-white mb-3">Breakdown</div>
                {[['Gross Income','₹'+result.annual_income?.toLocaleString('en-IN'),''],['Standard Deduction','-₹'+result.standard_deduction?.toLocaleString('en-IN'),'text-rose-400'],['PF Deduction','-₹'+result.pf_deduction?.toLocaleString('en-IN'),'text-rose-400'],['Section 80C','-₹'+result.section_80c?.toLocaleString('en-IN'),'text-rose-400'],['Taxable Income','₹'+result.taxable_income?.toLocaleString('en-IN'),'font-bold'],['Annual Tax','₹'+result.annual_tax?.toLocaleString('en-IN'),'text-amber-400 font-bold'],['Monthly TDS','₹'+result.monthly_tds?.toLocaleString('en-IN'),'text-blue-400 font-bold'],['Effective Rate',result.effective_rate+'%','text-violet-400']].map(([l,v,c]) => (
                  <div key={l} className="flex justify-between text-sm"><span className="text-slate-400">{l}</span><span className={c||'text-slate-200'}>{v}</span></div>
                ))}
              </div>
            )}
          </div>
          <div className="bg-[#1e293b]/60 border border-white/5 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-white mb-5 flex items-center gap-2"><FileText size={18} className="text-emerald-400"/>My Declarations</h3>
            {decls.length===0 ? <div className="text-center py-12 text-slate-500"><FileText size={36} className="mx-auto mb-3 opacity-30"/><p>No declarations yet.</p><button onClick={() => setShowForm(true)} className="mt-3 text-blue-400 text-sm hover:text-blue-300">Submit first declaration →</button></div>
            : <div className="space-y-4">{decls.map(d => (
                <div key={d.id} className="p-4 bg-white/5 rounded-xl border border-white/5">
                  <div className="flex justify-between items-start mb-3">
                    <div><div className="font-medium text-white">FY {d.financial_year}</div><div className="text-xs text-slate-500">{d.regime} Regime</div></div>
                    <span className={'text-xs px-2.5 py-1 rounded-full border font-medium '+(d.status==='SUBMITTED'?'bg-blue-500/10 text-blue-400 border-blue-500/20':'bg-slate-500/10 text-slate-400 border-slate-500/20')}>{d.status}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div><span className="text-slate-500">Gross: </span><span className="text-slate-300">₹{(d.gross_income||0).toLocaleString('en-IN')}</span></div>
                    <div><span className="text-slate-500">Taxable: </span><span className="text-slate-300">₹{(d.taxable_income||0).toLocaleString('en-IN')}</span></div>
                    <div><span className="text-slate-500">Est. Tax: </span><span className="text-amber-400 font-medium">₹{(d.estimated_tax||0).toLocaleString('en-IN')}</span></div>
                    <div><span className="text-slate-500">80C: </span><span className="text-slate-300">₹{(d.total_80c||0).toLocaleString('en-IN')}</span></div>
                  </div>
                </div>
              ))}</div>}
          </div>
        </div>
        <div className="bg-[#1e293b]/60 border border-white/5 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><Info size={18} className="text-blue-400"/>Tax Slabs FY 2024-25</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div><div className="text-sm font-medium text-blue-400 mb-3">New Regime</div><div className="space-y-2">{[['Up to ₹3L','Nil'],['₹3L–₹6L','5%'],['₹6L–₹9L','10%'],['₹9L–₹12L','15%'],['₹12L–₹15L','20%'],['Above ₹15L','30%']].map(([r,t]) => <div key={r} className="flex justify-between text-sm p-2 bg-white/5 rounded-lg"><span className="text-slate-400">{r}</span><span className="text-white font-medium">{t}</span></div>)}<div className="text-xs text-slate-500 mt-2">* Rebate u/s 87A: nil tax if income ≤ ₹7L</div></div></div>
            <div><div className="text-sm font-medium text-violet-400 mb-3">Key Deductions (Old Regime)</div><div className="space-y-2">{[['80C','Up to ₹1.5L (PPF, ELSS, LIC)'],['80D','Up to ₹25K (Health Insurance)'],['24(b)','Up to ₹2L (Home Loan Interest)'],['80CCD(1B)','Up to ₹50K (NPS)'],['Standard','₹50,000']].map(([s,d]) => <div key={s} className="p-2 bg-white/5 rounded-lg"><div className="text-sm font-medium text-slate-200">{s}</div><div className="text-xs text-slate-500">{d}</div></div>)}</div></div>
          </div>
        </div>
      </div>
      {showForm && <TaxDeclModal onClose={() => setShowForm(false)} onSuccess={() => { setShowForm(false); qc.invalidateQueries({queryKey:['tax-decls']}); }}/>}
    </div>
  );
}

function TaxDeclModal({ onClose, onSuccess }) {
  const fy = new Date().getFullYear()+'-'+String(new Date().getFullYear()+1).slice(2);
  const [form, setForm] = useState({ financial_year:fy, regime:'NEW', ppf:0, elss:0, life_insurance:0, nsc:0, home_loan_principal:0, tuition_fees:0, medical_insurance_80d:0, home_loan_interest_24b:0, nps_80ccd:0 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const handleSubmit = async (e) => {
    e.preventDefault(); setLoading(true); setError('');
    try { await submitTaxDeclaration(form); onSuccess(); }
    catch(err) { setError(err.response?.data?.detail||err.message); }
    finally { setLoading(false); }
  };
  const f80c = [{k:'ppf',l:'PPF'},{k:'elss',l:'ELSS'},{k:'life_insurance',l:'Life Insurance'},{k:'nsc',l:'NSC'},{k:'home_loan_principal',l:'Home Loan Principal'},{k:'tuition_fees',l:'Tuition Fees'}];
  const fOther = [{k:'medical_insurance_80d',l:'Medical Insurance (80D)'},{k:'home_loan_interest_24b',l:'Home Loan Interest (24b)'},{k:'nps_80ccd',l:'NPS (80CCD)'}];
  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#1e293b] border border-white/10 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="flex items-center justify-between p-6 border-b border-white/10"><h3 className="text-xl font-bold text-white">Tax Declaration</h3><button onClick={onClose} className="text-slate-400 hover:text-white"><X size={20}/></button></div>
        <form onSubmit={handleSubmit} className="p-6">
          {error && <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm">{error}</div>}
          <div className="grid grid-cols-2 gap-4 mb-5">
            <div><label className="block text-sm font-medium text-slate-300 mb-1.5">Financial Year</label><input value={form.financial_year} onChange={e => setForm({...form,financial_year:e.target.value})} className="w-full px-3 py-2.5 bg-[#0f172a] border border-white/10 rounded-xl text-white focus:outline-none text-sm"/></div>
            <div><label className="block text-sm font-medium text-slate-300 mb-1.5">Regime</label><select value={form.regime} onChange={e => setForm({...form,regime:e.target.value})} className="w-full px-3 py-2.5 bg-[#0f172a] border border-white/10 rounded-xl text-slate-300 focus:outline-none text-sm"><option value="NEW">New</option><option value="OLD">Old</option></select></div>
          </div>
          <div className="mb-4"><div className="text-sm font-semibold text-blue-400 mb-3">Section 80C (Max ₹1.5L)</div><div className="grid grid-cols-2 gap-3">{f80c.map(f => <div key={f.k}><label className="block text-xs text-slate-400 mb-1">{f.l}</label><input type="number" value={form[f.k]} onChange={e => setForm({...form,[f.k]:parseFloat(e.target.value)||0})} className="w-full px-3 py-2 bg-[#0f172a] border border-white/10 rounded-xl text-white focus:outline-none text-sm"/></div>)}</div></div>
          <div className="mb-5"><div className="text-sm font-semibold text-violet-400 mb-3">Other Deductions</div><div className="grid grid-cols-2 gap-3">{fOther.map(f => <div key={f.k}><label className="block text-xs text-slate-400 mb-1">{f.l}</label><input type="number" value={form[f.k]} onChange={e => setForm({...form,[f.k]:parseFloat(e.target.value)||0})} className="w-full px-3 py-2 bg-[#0f172a] border border-white/10 rounded-xl text-white focus:outline-none text-sm"/></div>)}</div></div>
          <div className="flex gap-3"><button type="button" onClick={onClose} className="flex-1 py-2.5 border border-white/10 text-slate-300 rounded-xl hover:bg-white/5 font-medium">Cancel</button><button type="submit" disabled={loading} className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium flex items-center justify-center gap-2 disabled:opacity-50">{loading?<><Loader2 size={16} className="animate-spin"/>Submitting...</>:'Submit'}</button></div>
        </form>
      </div>
    </div>
  );
}
"""

components["BenefitsModule.jsx"] = """import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Shield, Heart, Briefcase, Star, Loader2 } from 'lucide-react';
import { getBenefitPlans, getMyBenefits } from '../api';

const TC = { HEALTH:{icon:Heart,color:'rose'}, PF:{icon:Briefcase,color:'emerald'}, ESI:{icon:Shield,color:'cyan'}, LIFE:{icon:Shield,color:'violet'}, GRATUITY:{icon:Star,color:'amber'} };
const CM = { rose:'from-rose-500/20 to-rose-500/5 border-rose-500/20 text-rose-400 bg-rose-500/10', emerald:'from-emerald-500/20 to-emerald-500/5 border-emerald-500/20 text-emerald-400 bg-emerald-500/10', cyan:'from-cyan-500/20 to-cyan-500/5 border-cyan-500/20 text-cyan-400 bg-cyan-500/10', violet:'from-violet-500/20 to-violet-500/5 border-violet-500/20 text-violet-400 bg-violet-500/10', amber:'from-amber-500/20 to-amber-500/5 border-amber-500/20 text-amber-400 bg-amber-500/10' };

function PFCalc() {
  const [basic, setBasic] = useState(50000);
  const base = Math.min(basic,15000); const emp = Math.round(base*.12); const er = Math.round(base*.12);
  return <div className="p-4 bg-white/5 rounded-xl"><div className="text-sm font-semibold text-emerald-400 mb-3">PF Calculator</div><div className="mb-3"><label className="text-xs text-slate-400 mb-1 block">Basic (₹)</label><input type="number" value={basic} onChange={e => setBasic(parseFloat(e.target.value)||0)} className="w-full px-3 py-2 bg-[#0f172a] border border-white/10 rounded-lg text-white text-sm focus:outline-none"/></div><div className="space-y-1.5 text-sm"><div className="flex justify-between"><span className="text-slate-400">Employee 12%</span><span className="text-white">₹{emp.toLocaleString('en-IN')}</span></div><div className="flex justify-between"><span className="text-slate-400">Employer 12%</span><span className="text-emerald-400">₹{er.toLocaleString('en-IN')}</span></div><div className="flex justify-between font-bold pt-1 border-t border-white/10"><span className="text-slate-300">Annual</span><span className="text-emerald-400">₹{((emp+er)*12).toLocaleString('en-IN')}</span></div></div></div>;
}
function GratuityCalc() {
  const [basic, setBasic] = useState(50000); const [years, setYears] = useState(5);
  const g = years>=5 ? Math.round(15/26*basic*years) : 0;
  return <div className="p-4 bg-white/5 rounded-xl"><div className="text-sm font-semibold text-amber-400 mb-3">Gratuity Calculator</div><div className="space-y-2 mb-3"><div><label className="text-xs text-slate-400 mb-1 block">Basic (₹)</label><input type="number" value={basic} onChange={e => setBasic(parseFloat(e.target.value)||0)} className="w-full px-3 py-2 bg-[#0f172a] border border-white/10 rounded-lg text-white text-sm focus:outline-none"/></div><div><label className="text-xs text-slate-400 mb-1 block">Years of Service</label><input type="number" value={years} onChange={e => setYears(parseFloat(e.target.value)||0)} className="w-full px-3 py-2 bg-[#0f172a] border border-white/10 rounded-lg text-white text-sm focus:outline-none"/></div></div><div className="p-3 bg-amber-500/10 rounded-lg text-center"><div className="text-xs text-slate-400 mb-1">Estimated Gratuity</div><div className="text-xl font-bold text-amber-400">₹{g.toLocaleString('en-IN')}</div>{years<5&&<div className="text-xs text-slate-500 mt-1">Min. 5 years required</div>}</div></div>;
}
function ESICalc() {
  const [gross, setGross] = useState(18000);
  const ok = gross<=21000; const emp = ok?Math.round(gross*.0075):0; const er = ok?Math.round(gross*.0325):0;
  return <div className="p-4 bg-white/5 rounded-xl"><div className="text-sm font-semibold text-cyan-400 mb-3">ESI Calculator</div><div className="mb-3"><label className="text-xs text-slate-400 mb-1 block">Gross (₹)</label><input type="number" value={gross} onChange={e => setGross(parseFloat(e.target.value)||0)} className="w-full px-3 py-2 bg-[#0f172a] border border-white/10 rounded-lg text-white text-sm focus:outline-none"/></div>{ok?<div className="space-y-1.5 text-sm"><div className="flex justify-between"><span className="text-slate-400">Employee 0.75%</span><span className="text-white">₹{emp}</span></div><div className="flex justify-between"><span className="text-slate-400">Employer 3.25%</span><span className="text-cyan-400">₹{er}</span></div><div className="flex justify-between font-bold pt-1 border-t border-white/10"><span className="text-slate-300">Total</span><span className="text-cyan-400">₹{emp+er}</span></div></div>:<div className="p-3 bg-slate-500/10 rounded-lg text-center text-sm text-slate-400">Not applicable (Gross &gt; ₹21,000)</div>}</div>;
}

export default function BenefitsModule() {
  const { data: plans = [], isLoading } = useQuery({ queryKey:['benefit-plans'], queryFn:getBenefitPlans, staleTime:300000, retry:1 });
  const { data: myBenefits = [] } = useQuery({ queryKey:['my-benefits'], queryFn:getMyBenefits, staleTime:60000, retry:1 });
  const displayPlans = plans.length>0 ? plans : [{id:1,name:'Group Health Insurance',type:'HEALTH',provider:'Star Health',employee_contribution:500,employer_contribution:2000,is_mandatory:true},{id:2,name:'Provident Fund',type:'PF',provider:'EPFO',employee_contribution:0,employer_contribution:0,is_mandatory:true},{id:3,name:'ESI',type:'ESI',provider:'ESIC',employee_contribution:0,employer_contribution:0,is_mandatory:true},{id:4,name:'Group Life Insurance',type:'LIFE',provider:'LIC',employee_contribution:200,employer_contribution:800,is_mandatory:false},{id:5,name:'Gratuity',type:'GRATUITY',provider:'Internal',employee_contribution:0,employer_contribution:0,is_mandatory:true}];

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8"><h2 className="text-3xl font-bold text-white">Benefits</h2><p className="text-slate-400 mt-1">Insurance, PF, gratuity and employee benefits.</p></div>
        <h3 className="text-lg font-semibold text-white mb-4">Benefit Plans</h3>
        {isLoading ? <div className="flex items-center justify-center py-16"><Loader2 size={28} className="animate-spin text-blue-400"/></div> : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5 mb-8">
            {displayPlans.map(plan => {
              const cfg = TC[plan.type]||TC.HEALTH; const Icon = cfg.icon; const c = CM[cfg.color];
              return (
                <div key={plan.id} className="bg-[#1e293b]/60 border border-white/5 rounded-2xl p-6 hover:border-white/10 transition-all">
                  <div className="flex items-start justify-between mb-4">
                    <div className={'w-12 h-12 '+c.split(' ')[4]+' rounded-xl flex items-center justify-center'}><Icon size={22} className={c.split(' ')[3]}/></div>
                    {plan.is_mandatory && <span className="text-xs px-2 py-0.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-full">Mandatory</span>}
                  </div>
                  <div className="font-semibold text-white mb-1">{plan.name}</div>
                  <div className="text-sm text-slate-400 mb-4">{plan.provider}</div>
                  <div className="space-y-1.5 text-sm">
                    {plan.employee_contribution>0&&<div className="flex justify-between"><span className="text-slate-500">Employee</span><span className="text-slate-300">₹{plan.employee_contribution}/mo</span></div>}
                    {plan.employer_contribution>0&&<div className="flex justify-between"><span className="text-slate-500">Employer</span><span className="text-emerald-400">₹{plan.employer_contribution}/mo</span></div>}
                    {plan.type==='PF'&&<div className="text-xs text-slate-500 p-2 bg-white/5 rounded-lg mt-2">12% of Basic (employee + employer)</div>}
                    {plan.type==='ESI'&&<div className="text-xs text-slate-500 p-2 bg-white/5 rounded-lg mt-2">0.75% + 3.25% (if gross ≤ ₹21,000)</div>}
                    {plan.type==='GRATUITY'&&<div className="text-xs text-slate-500 p-2 bg-white/5 rounded-lg mt-2">15/26 × Basic × Years (after 5 years)</div>}
                  </div>
                </div>
              );
            })}
          </div>
        )}
        <div className="bg-[#1e293b]/60 border border-white/5 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><Briefcase size={18} className="text-emerald-400"/>Calculators</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6"><PFCalc/><GratuityCalc/><ESICalc/></div>
        </div>
      </div>
    </div>
  );
}
"""

components["ReportsModule.jsx"] = """import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart2, Users, DollarSign, Clock, Loader2, TrendingUp } from 'lucide-react';
import { getPayrollSummary, getAttendanceSummaryReport, getHeadcountReport } from '../api';

export default function ReportsModule() {
  const today = new Date();
  const [month, setMonth] = useState(today.getMonth()+1);
  const [year, setYear] = useState(today.getFullYear());
  const [tab, setTab] = useState('payroll');
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

  const { data: payrollData, isLoading: pl } = useQuery({ queryKey:['rpt-payroll',month,year], queryFn:() => getPayrollSummary(month,year), enabled:tab==='payroll', staleTime:60000, retry:1 });
  const { data: attData, isLoading: al } = useQuery({ queryKey:['rpt-att',month,year], queryFn:() => getAttendanceSummaryReport(month,year), enabled:tab==='attendance', staleTime:60000, retry:1 });
  const { data: hcData, isLoading: hl } = useQuery({ queryKey:['rpt-hc'], queryFn:getHeadcountReport, enabled:tab==='headcount', staleTime:300000, retry:1 });

  const tabs = [{id:'payroll',l:'Payroll Summary',icon:DollarSign},{id:'attendance',l:'Attendance',icon:Clock},{id:'headcount',l:'Headcount',icon:Users}];

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8"><h2 className="text-3xl font-bold text-white">Reports & Analytics</h2><p className="text-slate-400 mt-1">Comprehensive HR data insights.</p></div>
        <div className="flex flex-wrap gap-2 mb-6">
          {tabs.map(t => { const Icon=t.icon; return <button key={t.id} onClick={() => setTab(t.id)} className={'flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all '+(tab===t.id?'bg-blue-600 text-white shadow-lg shadow-blue-500/20':'bg-[#1e293b]/60 text-slate-400 hover:text-white border border-white/5')}><Icon size={16}/>{t.l}</button>; })}
        </div>
        {tab!=='headcount' && (
          <div className="flex items-center gap-3 mb-6">
            <select value={month} onChange={e => setMonth(parseInt(e.target.value))} className="px-4 py-2 bg-[#1e293b] border border-white/10 rounded-xl text-slate-300 focus:outline-none text-sm">{months.map((m,i) => <option key={m} value={i+1}>{m}</option>)}</select>
            <select value={year} onChange={e => setYear(parseInt(e.target.value))} className="px-4 py-2 bg-[#1e293b] border border-white/10 rounded-xl text-slate-300 focus:outline-none text-sm">{[2024,2025,2026].map(y => <option key={y} value={y}>{y}</option>)}</select>
          </div>
        )}
        {tab==='payroll' && (
          pl ? <div className="flex items-center justify-center py-16"><Loader2 size={28} className="animate-spin text-blue-400"/></div> : (() => {
            const d = payrollData || { period:`${year}-${String(month).padStart(2,'0')}`, employee_count:10, total_gross:875000, total_net:742000, total_pf:72000, total_tds:49000, records:[] };
            const cards = [['Employees',d.employee_count,'blue'],['Total Gross','₹'+(d.total_gross/100000).toFixed(2)+'L','emerald'],['Total Net','₹'+(d.total_net/100000).toFixed(2)+'L','violet'],['Total PF','₹'+(d.total_pf||0).toLocaleString('en-IN'),'amber'],['Total TDS','₹'+(d.total_tds||0).toLocaleString('en-IN'),'rose']];
            const cm = {blue:'border-blue-500/20 text-blue-400',emerald:'border-emerald-500/20 text-emerald-400',violet:'border-violet-500/20 text-violet-400',amber:'border-amber-500/20 text-amber-400',rose:'border-rose-500/20 text-rose-400'};
            return <div>
              <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">{cards.map(([l,v,c]) => <div key={l} className={'p-5 bg-[#1e293b]/60 border '+cm[c].split(' ')[0]+' rounded-2xl'}><div className="text-xs text-slate-400 mb-2">{l}</div><div className={'text-xl font-bold '+cm[c].split(' ')[1]}>{v}</div></div>)}</div>
              {d.records?.length>0 && <div className="bg-[#1e293b]/60 border border-white/5 rounded-2xl overflow-hidden"><div className="px-6 py-4 border-b border-white/5"><h3 className="font-semibold text-white">Details — {months[month-1]} {year}</h3></div><div className="overflow-x-auto"><table className="w-full"><thead><tr className="border-b border-white/5">{['Employee','Gross','PF','TDS','Net','Status'].map(h => <th key={h} className="text-left px-6 py-3 text-xs font-semibold text-slate-400 uppercase">{h}</th>)}</tr></thead><tbody className="divide-y divide-white/5">{d.records.map(r => <tr key={r.id} className="hover:bg-white/5"><td className="px-6 py-3 text-sm text-slate-200">{r.employee_name}</td><td className="px-6 py-3 text-sm text-slate-300">₹{(r.gross_earnings||0).toLocaleString('en-IN')}</td><td className="px-6 py-3 text-sm text-slate-400">₹{(r.pf_employee||0).toLocaleString('en-IN')}</td><td className="px-6 py-3 text-sm text-slate-400">₹{(r.income_tax_tds||0).toLocaleString('en-IN')}</td><td className="px-6 py-3 text-sm font-bold text-emerald-400">₹{(r.net_salary||0).toLocaleString('en-IN')}</td><td className="px-6 py-3"><span className={'text-xs px-2 py-0.5 rounded-full border font-medium '+(r.status==='PAID'?'bg-emerald-500/10 text-emerald-400 border-emerald-500/20':'bg-blue-500/10 text-blue-400 border-blue-500/20')}>{r.status}</span></td></tr>)}</tbody></table></div></div>}
            </div>;
          })()
        )}
        {tab==='attendance' && (
          al ? <div className="flex items-center justify-center py-16"><Loader2 size={28} className="animate-spin text-blue-400"/></div> : (() => {
            const summaries = attData?.summaries||[];
            return summaries.length===0 ? <div className="text-center py-16 text-slate-500 bg-[#1e293b]/60 rounded-2xl border border-white/5"><Clock size={40} className="mx-auto mb-3 opacity-30"/><p>No data for {months[month-1]} {year}.</p></div>
            : <div className="bg-[#1e293b]/60 border border-white/5 rounded-2xl overflow-hidden"><div className="px-6 py-4 border-b border-white/5"><h3 className="font-semibold text-white">Attendance — {months[month-1]} {year}</h3></div><div className="overflow-x-auto"><table className="w-full"><thead><tr className="border-b border-white/5">{['Employee','Dept','Working','Present','Absent','Leave','OT','%'].map(h => <th key={h} className="text-left px-6 py-3 text-xs font-semibold text-slate-400 uppercase whitespace-nowrap">{h}</th>)}</tr></thead><tbody className="divide-y divide-white/5">{summaries.map((s,i) => { const pct=s.working_days>0?Math.round(s.present_days/s.working_days*100):0; return <tr key={i} className="hover:bg-white/5"><td className="px-6 py-3 text-sm text-slate-200">{s.name}</td><td className="px-6 py-3 text-sm text-slate-400">{s.department||'—'}</td><td className="px-6 py-3 text-sm text-slate-300">{s.working_days}</td><td className="px-6 py-3 text-sm text-emerald-400">{s.present_days}</td><td className="px-6 py-3 text-sm text-rose-400">{s.absent_days}</td><td className="px-6 py-3 text-sm text-amber-400">{s.leave_days}</td><td className="px-6 py-3 text-sm text-blue-400">{s.overtime_hours}h</td><td className="px-6 py-3"><div className="flex items-center gap-2"><div className="w-16 h-1.5 bg-white/10 rounded-full overflow-hidden"><div className={'h-full rounded-full '+(pct>=90?'bg-emerald-500':pct>=75?'bg-amber-500':'bg-rose-500')} style={{width:pct+'%'}}/></div><span className={'text-xs font-medium '+(pct>=90?'text-emerald-400':pct>=75?'text-amber-400':'text-rose-400')}>{pct}%</span></div></td></tr>; })}</tbody></table></div></div>;
          })()
        )}
        {tab==='headcount' && (
          hl ? <div className="flex items-center justify-center py-16"><Loader2 size={28} className="animate-spin text-blue-400"/></div> : (() => {
            const d = hcData || { total:10, by_department:[{department:'Engineering',count:3},{department:'HR',count:2},{department:'Finance',count:2},{department:'Marketing',count:1},{department:'Operations',count:1},{department:'Sales',count:1}], by_status:[{status:'ACTIVE',count:9},{status:'ON_LEAVE',count:1}] };
            return <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-[#1e293b]/60 border border-white/5 rounded-2xl p-6"><h3 className="font-semibold text-white mb-5 flex items-center gap-2"><Users size={16} className="text-blue-400"/>By Department</h3><div className="space-y-3">{d.by_department.map(item => { const pct=d.total>0?(item.count/d.total*100):0; return <div key={item.department}><div className="flex justify-between text-sm mb-1"><span className="text-slate-300">{item.department}</span><span className="text-slate-400">{item.count} ({Math.round(pct)}%)</span></div><div className="h-2 bg-white/5 rounded-full overflow-hidden"><div className="h-full bg-gradient-to-r from-blue-500 to-violet-500 rounded-full" style={{width:pct+'%'}}/></div></div>; })}<div className="mt-4 pt-4 border-t border-white/10 flex justify-between text-sm"><span className="text-slate-400">Total</span><span className="font-bold text-white">{d.total}</span></div></div></div>
              <div className="bg-[#1e293b]/60 border border-white/5 rounded-2xl p-6"><h3 className="font-semibold text-white mb-5 flex items-center gap-2"><TrendingUp size={16} className="text-emerald-400"/>By Status</h3><div className="space-y-3">{d.by_status.map(item => { const pct=d.total>0?(item.count/d.total*100):0; const c={ACTIVE:'bg-emerald-500',ON_LEAVE:'bg-amber-500',TERMINATED:'bg-rose-500',INACTIVE:'bg-slate-500'}; return <div key={item.status}><div className="flex justify-between text-sm mb-1"><span className="text-slate-300">{item.status}</span><span className="text-slate-400">{item.count}</span></div><div className="h-2 bg-white/5 rounded-full overflow-hidden"><div className={'h-full '+(c[item.status]||'bg-blue-500')+' rounded-full'} style={{width:pct+'%'}}/></div></div>; })}</div></div>
            </div>;
          })()
        )}
      </div>
    </div>
  );
}
"""

# ── App.jsx ───────────────────────────────────────────────────────────────────
APP_JSX = """import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { v4 as uuidv4 } from 'uuid';
import { Send, Upload, Settings, Clock, MessageSquare, AlertCircle, CheckCircle, Menu, X, ChevronRight, Sparkles, Loader2, LayoutDashboard, Users, Calendar, DollarSign, Calculator, Shield, BarChart2, LogOut } from 'lucide-react';
import { useStore } from './store';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import LoginPage from './components/LoginPage';
import Dashboard from './components/Dashboard';
import EmployeeManagement from './components/EmployeeManagement';
import AttendanceTracker from './components/AttendanceTracker';
import LeaveManagement from './components/LeaveManagement';
import PayrollModule from './components/PayrollModule';
import TaxManagement from './components/TaxManagement';
import BenefitsModule from './components/BenefitsModule';
import ReportsModule from './components/ReportsModule';

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const NAV = [
  { id:'dashboard', icon:LayoutDashboard, label:'Dashboard', roles:['ADMIN','HR_MANAGER','MANAGER','EMPLOYEE'] },
  { id:'chat', icon:MessageSquare, label:'HR Assistant', roles:['ADMIN','HR_MANAGER','MANAGER','EMPLOYEE'] },
  { id:'employees', icon:Users, label:'Employees', roles:['ADMIN','HR_MANAGER'] },
  { id:'attendance', icon:Clock, label:'Attendance', roles:['ADMIN','HR_MANAGER','MANAGER','EMPLOYEE'] },
  { id:'leaves', icon:Calendar, label:'Leave', roles:['ADMIN','HR_MANAGER','MANAGER','EMPLOYEE'] },
  { id:'payroll', icon:DollarSign, label:'Payroll', roles:['ADMIN','HR_MANAGER','EMPLOYEE'] },
  { id:'tax', icon:Calculator, label:'Tax', roles:['ADMIN','HR_MANAGER','EMPLOYEE'] },
  { id:'benefits', icon:Shield, label:'Benefits', roles:['ADMIN','HR_MANAGER','EMPLOYEE'] },
  { id:'reports', icon:BarChart2, label:'Reports', roles:['ADMIN','HR_MANAGER'] },
  { id:'admin', icon:Settings, label:'Admin Panel', roles:['ADMIN','HR_MANAGER'] },
];

export default function App() {
  const { activeTab, setActiveTab, employee, isSidebarOpen, toggleSidebar, closeSidebar, isAuthenticated, logout } = useStore();
  if (!isAuthenticated) return <LoginPage />;
  const role = employee?.role || 'EMPLOYEE';
  const nav = NAV.filter(n => n.roles.includes(role));

  return (
    <div className="flex h-screen bg-[#0f172a] text-slate-200 font-sans overflow-hidden">
      {isSidebarOpen && <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-40 lg:hidden" onClick={closeSidebar}/>}
      <aside className={'fixed lg:static top-0 left-0 h-full w-64 bg-[#1e293b]/50 border-r border-white/5 flex flex-col z-50 transition-transform duration-300 backdrop-blur-xl '+(isSidebarOpen?'translate-x-0':'-translate-x-full lg:translate-x-0')}>
        <div className="p-5 flex items-center justify-between border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-tr from-blue-500 to-cyan-400 p-2 rounded-xl shadow-[0_0_20px_rgba(56,189,248,0.3)]"><Sparkles className="text-white" size={20}/></div>
            <div><h1 className="text-lg font-bold text-white">HR Desk</h1><p className="text-[10px] text-blue-400 font-medium tracking-wide uppercase">Management Platform</p></div>
          </div>
          <button className="lg:hidden text-slate-400 hover:text-white" onClick={closeSidebar}><X size={20}/></button>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {nav.map(item => {
            const Icon = item.icon; const isActive = activeTab===item.id;
            return <button key={item.id} onClick={() => { setActiveTab(item.id); closeSidebar(); }} className={'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group relative '+(isActive?'bg-blue-500/10 text-blue-400 border border-blue-500/20':'text-slate-400 hover:bg-white/5 hover:text-slate-200 border border-transparent')}>
              {isActive && <div className="absolute left-0 top-2 bottom-2 w-0.5 bg-blue-500 rounded-r-full"/>}
              <Icon size={18} className={isActive?'text-blue-400':'text-slate-500 group-hover:text-slate-300 transition-colors'}/>
              <span className="font-medium text-sm">{item.label}</span>
              {isActive && <ChevronRight size={14} className="ml-auto text-blue-500/50"/>}
            </button>;
          })}
        </nav>
        <div className="p-3 border-t border-white/5">
          <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">{employee?.name?.charAt(0)}</div>
            <div className="flex-1 min-w-0"><div className="text-white font-medium text-sm truncate">{employee?.name}</div><div className="text-xs text-slate-400 truncate">{employee?.role} · {employee?.department}</div></div>
            <button onClick={logout} className="text-slate-500 hover:text-rose-400 transition-colors" title="Logout"><LogOut size={16}/></button>
          </div>
        </div>
      </aside>
      <main className="flex-1 flex flex-col min-w-0 relative overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[200px] bg-blue-500/5 blur-[100px] rounded-full pointer-events-none"/>
        <header className="lg:hidden flex items-center justify-between p-4 border-b border-white/5 bg-[#0f172a]/80 backdrop-blur-xl z-30 sticky top-0">
          <div className="flex items-center gap-2"><div className="bg-gradient-to-tr from-blue-500 to-cyan-400 p-1.5 rounded-lg"><Sparkles className="text-white" size={16}/></div><span className="font-bold text-white">HR Desk</span></div>
          <button className="text-slate-300 hover:text-white p-1 rounded-md hover:bg-white/10 transition-colors" onClick={toggleSidebar}><Menu size={22}/></button>
        </header>
        <div className="flex-1 flex flex-col overflow-hidden relative z-10">
          {activeTab==='dashboard' && <Dashboard/>}
          {activeTab==='chat' && <ChatInterface employee={employee}/>}
          {activeTab==='employees' && <EmployeeManagement/>}
          {activeTab==='attendance' && <AttendanceTracker/>}
          {activeTab==='leaves' && <LeaveManagement/>}
          {activeTab==='payroll' && <PayrollModule/>}
          {activeTab==='tax' && <TaxManagement/>}
          {activeTab==='benefits' && <BenefitsModule/>}
          {activeTab==='reports' && <ReportsModule/>}
          {activeTab==='admin' && <AdminPanel/>}
        </div>
      </main>
    </div>
  );
}

function ChatInterface({ employee }) {
  const [messages, setMessages] = useState([{ id:1, role:'assistant', content:'Hi '+((employee?.name||'').split(' ')[0]||'there')+'! I am your AI HR assistant. Ask me about policies, payroll, leave, or benefits.' }]);
  const [input, setInput] = useState('');
  const [sessionId] = useState(uuidv4());
  const endRef = useRef(null);
  useEffect(() => { endRef.current?.scrollIntoView({behavior:'smooth'}); }, [messages]);

  const mut = useMutation({
    mutationFn: async (msg) => {
      try {
        const r = await axios.post(API+'/chat', { query:msg.content, employee_id:employee?.id||'EMP-000', employee_name:employee?.name||'Employee', department:employee?.department||'General', session_id:sessionId });
        return r.data;
      } catch {
        await new Promise(r => setTimeout(r,600));
        if(msg.content.toLowerCase().includes('leave')) return { response:'You have 14 days of paid leave remaining. Use the Leave tab to apply.', confidence:0.9, escalated:false, topic:'LEAVE' };
        if(msg.content.toLowerCase().includes('salary')||msg.content.toLowerCase().includes('payroll')) return { response:'Salary is processed on the last working day of each month. Check the Payroll tab for your payslips.', confidence:0.9, escalated:false, topic:'PAYROLL' };
        return { response:'I am in demo mode. In production I connect to the HR knowledge base to answer accurately.', confidence:0.7, escalated:false, topic:'GENERAL' };
      }
    },
    onSuccess: (data) => setMessages(p => [...p, { id:Date.now()+1, role:'assistant', content:data.response||data.reply, meta:{ confidence:data.confidence, escalated:data.escalated, ticket_id:data.ticket_id, topic:data.topic } }]),
  });

  const send = () => {
    if(!input.trim()||mut.isPending) return;
    setMessages(p => [...p, { id:Date.now(), role:'user', content:input }]);
    mut.mutate({ content:input }); setInput('');
  };

  const quick = ['What is my leave balance?','When is the next payday?','How do I apply for leave?','Explain PF deductions'];

  return (
    <div className="flex-1 flex flex-col bg-transparent">
      <div className="p-5 border-b border-white/5 bg-[#1e293b]/50 backdrop-blur-md sticky top-0 z-10">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"/><span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"/></span>
          HR Assistant AI
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">Powered by Claude · Secure & Confidential</p>
      </div>
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {messages.map(msg => (
          <div key={msg.id} className={'flex '+(msg.role==='user'?'justify-end':'justify-start')}>
            <div className={'max-w-[85%] md:max-w-[70%] rounded-2xl px-5 py-4 shadow-lg '+(msg.role==='user'?'bg-gradient-to-br from-blue-600 to-blue-500 text-white rounded-br-none':'bg-[#1e293b]/80 border border-white/10 text-slate-200 rounded-bl-none backdrop-blur-sm')}>
              {msg.role==='assistant' ? (
                <div className="prose prose-sm prose-invert max-w-none">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                  {msg.meta && <div className="mt-3 pt-3 border-t border-white/10 flex flex-wrap gap-2 text-xs font-medium">
                    {msg.meta.topic && <span className="bg-white/5 border border-white/10 text-slate-300 px-2.5 py-1 rounded-full">{msg.meta.topic}</span>}
                    {msg.meta.confidence && <span className={'px-2.5 py-1 rounded-full border '+(msg.meta.confidence>0.8?'bg-emerald-500/10 border-emerald-500/20 text-emerald-400':'bg-amber-500/10 border-amber-500/20 text-amber-400')}>{msg.meta.confidence>0.8?'High':'Medium'} Confidence</span>}
                    {msg.meta.escalated && <span className="bg-rose-500/10 border-rose-500/20 text-rose-400 px-2.5 py-1 rounded-full flex items-center gap-1"><AlertCircle size={10}/>Escalated {msg.meta.ticket_id&&'#'+msg.meta.ticket_id}</span>}
                  </div>}
                </div>
              ) : <div className="text-[15px] leading-relaxed">{msg.content}</div>}
            </div>
          </div>
        ))}
        {mut.isPending && <div className="flex justify-start"><div className="bg-[#1e293b]/80 border border-white/10 rounded-2xl rounded-bl-none px-5 py-4 flex gap-1.5 items-center">{[0,.15,.3].map((d,i) => <div key={i} className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay:d+'s'}}/>)}</div></div>}
        <div ref={endRef}/>
      </div>
      {messages.length<=1 && <div className="px-5 pb-3 flex flex-wrap gap-2">{quick.map(p => <button key={p} onClick={() => setInput(p)} className="text-xs px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-slate-400 hover:text-white transition-all">{p}</button>)}</div>}
      <div className="p-4 bg-[#0f172a]/90 backdrop-blur-xl border-t border-white/5">
        <div className="max-w-4xl mx-auto relative flex items-center">
          <input type="text" value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key==='Enter'&&send()} placeholder="Ask about policies, payroll, leave..." disabled={mut.isPending}
            className="w-full pl-5 pr-14 py-3.5 bg-[#1e293b] border border-white/10 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-white placeholder-slate-500 text-sm"/>
          <button onClick={send} disabled={mut.isPending||!input.trim()} className="absolute right-2 p-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-500 disabled:opacity-50 transition-colors">
            {mut.isPending ? <Loader2 size={18} className="animate-spin"/> : <Send size={18}/>}
          </button>
        </div>
        <div className="text-center mt-2 text-xs text-slate-600">AI responses may not be 100% accurate. Verify with HR for critical matters.</div>
      </div>
    </div>
  );
}

function AdminPanel() {
  const [file, setFile] = useState(null);
  const { mockTickets } = useStore();
  const qc = useQueryClient();
  const { data: tickets = mockTickets, refetch, isLoading } = useQuery({ queryKey:['tickets'], queryFn: async () => { try { const r = await axios.get(API+'/tickets'); return Array.isArray(r.data)&&r.data.length>0 ? r.data.reduce((a,t) => { a[t.id]=t; return a; },{}) : mockTickets; } catch { return mockTickets; } }, staleTime:60000 });
  const uploadMut = useMutation({ mutationFn: async (f) => { const fd=new FormData(); fd.append('file',f); try { await axios.post(API+'/upload_policy',fd); } catch { await new Promise(r => setTimeout(r,1500)); } }, onSuccess:() => setFile(null) });

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-white mb-2">Admin Panel</h2>
        <p className="text-slate-400 mb-8">Manage AI knowledge base and escalation tickets.</p>
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
          <div className="bg-[#1e293b]/60 border border-white/5 p-6 rounded-2xl">
            <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-3"><div className="p-2 bg-blue-500/20 text-blue-400 rounded-lg"><Upload size={18}/></div>Update Knowledge Base</h3>
            <p className="text-sm text-slate-400 mb-5">Upload HR policies (PDF, TXT) to train the AI assistant.</p>
            <div className={'border-2 border-dashed rounded-2xl p-8 text-center transition-all '+(file?'border-blue-500/50 bg-blue-500/5':'border-white/10 hover:border-blue-400/30 hover:bg-white/5')}>
              <input type="file" id="fu" className="hidden" accept=".pdf,.txt,.md" onChange={e => setFile(e.target.files[0])}/>
              <label htmlFor="fu" className="cursor-pointer flex flex-col items-center">
                <div className={'p-4 rounded-full mb-3 '+(file?'bg-blue-500/20 text-blue-400':'bg-white/5 text-slate-400')}><Upload size={24}/></div>
                <span className="font-semibold text-slate-200 mb-1">{file?file.name:'Select a document'}</span>
                <span className="text-sm text-slate-500">{file?'Ready to upload':'PDF, TXT, or MD'}</span>
              </label>
            </div>
            <button onClick={() => uploadMut.mutate(file)} disabled={!file||uploadMut.isPending} className="w-full mt-5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 rounded-xl font-semibold hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 transition-all flex justify-center items-center gap-2">
              {uploadMut.isPending ? <><Loader2 size={18} className="animate-spin"/>Processing...</> : 'Ingest Document'}
            </button>
            {uploadMut.isSuccess && <div className="mt-3 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-sm text-emerald-400 flex items-center justify-center gap-2"><CheckCircle size={16}/>Indexed successfully</div>}
          </div>
          <div className="bg-[#1e293b]/60 border border-white/5 p-6 rounded-2xl flex flex-col">
            <div className="flex justify-between items-center mb-5">
              <h3 className="text-lg font-bold text-white flex items-center gap-3"><div className="p-2 bg-rose-500/20 text-rose-400 rounded-lg"><AlertCircle size={18}/></div>Escalation Queue</h3>
              <button onClick={() => refetch()} disabled={isLoading} className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"><Clock size={16} className={isLoading?'animate-spin':''}/></button>
            </div>
            <div className="flex-1 overflow-y-auto space-y-3">
              {Object.keys(tickets).length===0 ? <div className="flex flex-col items-center justify-center py-12 text-slate-500"><CheckCircle size={32} className="text-emerald-400/40 mb-3"/><p className="font-medium">All clear!</p></div>
              : Object.entries(tickets).map(([id,t]) => (
                <div key={id} className="p-4 border border-white/10 bg-white/5 hover:bg-white/10 rounded-xl transition-colors">
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-bold text-slate-200">{id}</span>
                    <span className={'text-xs px-2 py-0.5 rounded-md font-bold border '+(t.priority==='HIGH'?'bg-rose-500/10 text-rose-400 border-rose-500/20':'bg-amber-500/10 text-amber-400 border-amber-500/20')}>{t.priority}</span>
                  </div>
                  <div className="text-xs text-slate-300 bg-black/20 p-2 rounded-lg font-mono mb-2">"{t.query||t.issue_summary}"</div>
                  <div className="text-xs text-slate-500">{t.employee_id||t.employee_name}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Upload({ size, className }) {
  return <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>;
}
"""

# Write all component files
for name, content in components.items():
    path = COMP + '/' + name
    with open(path, 'w') as f:
        f.write(content)
    print(f"  {name}: {os.path.getsize(path)} bytes")

# Write App.jsx
app_path = FRONTEND + '/App.jsx'
with open(app_path, 'w') as f:
    f.write(APP_JSX)
print(f"  App.jsx: {os.path.getsize(app_path)} bytes")

# Write store.js and api.js (already in files dict above)
for path, content in files.items():
    with open(path, 'w') as f:
        f.write(content)
    print(f"  {os.path.basename(path)}: {os.path.getsize(path)} bytes")

print("\nAll frontend files written!")
print("Component count:", len(components))
