import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Clock, LogIn, LogOut, Calendar, Loader2 } from 'lucide-react';
import { getAttendance, checkIn, checkOut, getAttendanceSummary } from '../api';
import { useStore } from '../store';

const SC = { PRESENT:'text-emerald-400 bg-emerald-500/10 border-emerald-500/20', ABSENT:'text-rose-400 bg-rose-500/10 border-rose-500/20', HALF_DAY:'text-amber-400 bg-amber-500/10 border-amber-500/20', WORK_FROM_HOME:'text-blue-400 bg-blue-500/10 border-blue-500/20', ON_LEAVE:'text-violet-400 bg-violet-500/10 border-violet-500/20' };

export default function AttendanceTracker() {
  const { employee } = useStore();
  const qc = useQueryClient();
  const today = new Date();
  const [month, setMonth] = useState(today.getMonth()+1);
  const [year, setYear] = useState(today.getFullYear());
  const [msg, setMsg] = useState('');

  const { data: records = [], isLoading } = useQuery({ queryKey:['attendance',month,year], queryFn:() => getAttendance({month,year}), staleTime:30000, retry:1 });
  const { data: summary } = useQuery({ queryKey:['att-summary',month,year], queryFn:() => getAttendanceSummary(1,month,year), staleTime:30000, retry:1 });
  const s = summary || { working_days:22, present_days:20, absent_days:1, leave_days:1, overtime_hours:8 };

  const ciMut = useMutation({ mutationFn:checkIn, onSuccess:(d) => { setMsg('Checked in at '+new Date(d.time).toLocaleTimeString()); qc.invalidateQueries({queryKey:['attendance']}); }, onError:(e) => setMsg(e.response?.data?.detail||e.message) });
  const coMut = useMutation({ mutationFn:checkOut, onSuccess:(d) => { setMsg('Checked out. '+d.work_hours+'h worked'); qc.invalidateQueries({queryKey:['attendance']}); }, onError:(e) => setMsg(e.response?.data?.detail||e.message) });

  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8"><h2 className="text-3xl font-bold text-white">Attendance</h2><p className="text-slate-400 mt-1">Track daily attendance and work hours.</p></div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-8">
          <div className="bg-[#1e293b]/60 border border-white/5 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><Clock size={18} className="text-blue-400"/>Today</h3>
            <div className="text-3xl font-bold text-white mb-1">{today.toLocaleDateString('en-IN',{weekday:'long'})}</div>
            <div className="text-slate-400 mb-5">{today.toLocaleDateString('en-IN',{day:'numeric',month:'long',year:'numeric'})}</div>
            {msg && <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-400 text-sm">{msg}</div>}
            <div className="flex gap-3">
              <button onClick={() => ciMut.mutate()} disabled={ciMut.isPending} className="flex-1 flex items-center justify-center gap-2 py-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-xl font-medium transition-colors">
                {ciMut.isPending ? <Loader2 size={16} className="animate-spin"/> : <LogIn size={16}/>} Check In
              </button>
              <button onClick={() => coMut.mutate()} disabled={coMut.isPending} className="flex-1 flex items-center justify-center gap-2 py-3 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white rounded-xl font-medium transition-colors">
                {coMut.isPending ? <Loader2 size={16} className="animate-spin"/> : <LogOut size={16}/>} Check Out
              </button>
            </div>
          </div>
          <div className="bg-[#1e293b]/60 border border-white/5 rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2"><Calendar size={18} className="text-violet-400"/>Monthly Summary</h3>
            <div className="grid grid-cols-2 gap-3">
              {[['Working Days',s.working_days,'text-slate-300'],['Present',s.present_days,'text-emerald-400'],['Absent',s.absent_days,'text-rose-400'],['On Leave',s.leave_days,'text-amber-400'],['Overtime',s.overtime_hours+'h','text-blue-400'],['Attendance %',s.working_days>0?Math.round(s.present_days/s.working_days*100)+'%':'0%','text-violet-400']].map(([l,v,c]) => (
                <div key={l} className="p-3 bg-white/5 rounded-xl"><div className="text-xs text-slate-500 mb-1">{l}</div><div className={'text-xl font-bold '+c}>{v}</div></div>
              ))}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3 mb-5">
          <select value={month} onChange={e => setMonth(parseInt(e.target.value))} className="px-4 py-2 bg-[#1e293b] border border-white/10 rounded-xl text-slate-300 focus:outline-none text-sm">
            {months.map((m,i) => <option key={m} value={i+1}>{m}</option>)}
          </select>
          <select value={year} onChange={e => setYear(parseInt(e.target.value))} className="px-4 py-2 bg-[#1e293b] border border-white/10 rounded-xl text-slate-300 focus:outline-none text-sm">
            {[2024,2025,2026].map(y => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
        <div className="bg-[#1e293b]/60 border border-white/5 rounded-2xl overflow-hidden">
          <div className="px-6 py-4 border-b border-white/5"><h3 className="font-semibold text-white">Records — {months[month-1]} {year}</h3></div>
          {isLoading ? <div className="flex items-center justify-center py-16"><Loader2 size={28} className="animate-spin text-blue-400"/></div>
          : records.length===0 ? <div className="text-center py-16 text-slate-500"><Clock size={40} className="mx-auto mb-3 opacity-30"/><p>No records for this period.</p></div>
          : <div className="overflow-x-auto"><table className="w-full">
              <thead><tr className="border-b border-white/5">{['Date','Check In','Check Out','Hours','Overtime','Status'].map(h => <th key={h} className="text-left px-6 py-3 text-xs font-semibold text-slate-400 uppercase">{h}</th>)}</tr></thead>
              <tbody className="divide-y divide-white/5">
                {records.slice(0,31).map(r => (
                  <tr key={r.id} className="hover:bg-white/5 transition-colors">
                    <td className="px-6 py-3 text-sm text-slate-300">{new Date(r.date).toLocaleDateString('en-IN',{day:'numeric',month:'short',weekday:'short'})}</td>
                    <td className="px-6 py-3 text-sm text-slate-300">{r.check_in?new Date(r.check_in).toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit'}):'—'}</td>
                    <td className="px-6 py-3 text-sm text-slate-300">{r.check_out?new Date(r.check_out).toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit'}):'—'}</td>
                    <td className="px-6 py-3 text-sm text-slate-300">{r.work_hours?r.work_hours+'h':'—'}</td>
                    <td className="px-6 py-3 text-sm">{r.overtime_hours>0?<span className="text-amber-400">{r.overtime_hours}h</span>:<span className="text-slate-600">—</span>}</td>
                    <td className="px-6 py-3"><span className={'text-xs px-2.5 py-1 rounded-full border font-medium '+(SC[r.status]||SC.PRESENT)}>{r.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table></div>}
        </div>
      </div>
    </div>
  );
}
