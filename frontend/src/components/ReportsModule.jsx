import React, { useState } from 'react';
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
