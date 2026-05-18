import React, { useState } from 'react';
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
