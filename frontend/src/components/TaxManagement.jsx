import React, { useState } from 'react';
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
