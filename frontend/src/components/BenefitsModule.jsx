import React, { useState } from 'react';
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
