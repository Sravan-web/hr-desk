import React from 'react';
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
