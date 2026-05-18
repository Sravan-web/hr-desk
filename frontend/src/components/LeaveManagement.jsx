import React, { useState } from 'react';
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
