import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Search, Edit2, Trash2, X, Loader2 } from 'lucide-react';
import { getEmployees, getDepartments, createEmployee, updateEmployee, deactivateEmployee } from '../api';

const SC = { ACTIVE:'bg-emerald-500/10 text-emerald-400 border-emerald-500/20', INACTIVE:'bg-slate-500/10 text-slate-400 border-slate-500/20', TERMINATED:'bg-rose-500/10 text-rose-400 border-rose-500/20', ON_LEAVE:'bg-amber-500/10 text-amber-400 border-amber-500/20' };
const RC = { ADMIN:'bg-violet-500/10 text-violet-400', HR_MANAGER:'bg-blue-500/10 text-blue-400', MANAGER:'bg-cyan-500/10 text-cyan-400', EMPLOYEE:'bg-slate-500/10 text-slate-400' };

export default function EmployeeManagement() {
  const qc = useQueryClient();
  const [search, setSearch] = useState('');
  const [deptFilter, setDeptFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editEmp, setEditEmp] = useState(null);

  const { data: empData, isLoading } = useQuery({ queryKey:['employees',search,deptFilter], queryFn:() => getEmployees({search:search||undefined,department_id:deptFilter||undefined}), staleTime:30000, retry:1 });
  const { data: depts = [] } = useQuery({ queryKey:['departments'], queryFn:getDepartments, staleTime:300000, retry:1 });
  const employees = empData?.employees || [];
  const delMut = useMutation({ mutationFn:deactivateEmployee, onSuccess:() => qc.invalidateQueries({queryKey:['employees']}) });

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div><h2 className="text-3xl font-bold text-white">Employees</h2><p className="text-slate-400 mt-1">{employees.length} total</p></div>
          <button onClick={() => { setEditEmp(null); setShowForm(true); }} className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium transition-colors">
            <Plus size={18}/> Add Employee
          </button>
        </div>
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"/>
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search name, ID, email..."
              className="w-full pl-9 pr-4 py-2.5 bg-[#1e293b] border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-sm"/>
          </div>
          <select value={deptFilter} onChange={e => setDeptFilter(e.target.value)}
            className="px-4 py-2.5 bg-[#1e293b] border border-white/10 rounded-xl text-slate-300 focus:outline-none text-sm">
            <option value="">All Departments</option>
            {depts.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>
        <div className="bg-[#1e293b]/60 border border-white/5 rounded-2xl overflow-hidden">
          {isLoading ? <div className="flex items-center justify-center py-20"><Loader2 size={32} className="animate-spin text-blue-400"/></div> : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead><tr className="border-b border-white/5">
                  {['Employee','Department','Salary','Status','Role',''].map(h => <th key={h} className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase">{h}</th>)}
                </tr></thead>
                <tbody className="divide-y divide-white/5">
                  {employees.map(emp => (
                    <tr key={emp.id} className="hover:bg-white/5 transition-colors group">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                            {emp.first_name?.[0]}{emp.last_name?.[0]}
                          </div>
                          <div><div className="font-medium text-slate-200">{emp.name}</div><div className="text-xs text-slate-500">{emp.employee_id} · {emp.job_title}</div></div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-300">{emp.department||'—'}</td>
                      <td className="px-6 py-4 text-sm text-slate-300">₹{(emp.gross_salary||0).toLocaleString('en-IN')}</td>
                      <td className="px-6 py-4"><span className={'text-xs px-2.5 py-1 rounded-full border font-medium '+(SC[emp.status]||SC.ACTIVE)}>{emp.status||'ACTIVE'}</span></td>
                      <td className="px-6 py-4"><span className={'text-xs px-2.5 py-1 rounded-full font-medium '+(RC[emp.role]||RC.EMPLOYEE)}>{emp.role}</span></td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => { setEditEmp(emp); setShowForm(true); }} className="p-1.5 text-slate-400 hover:text-amber-400 hover:bg-amber-500/10 rounded-lg transition-colors"><Edit2 size={14}/></button>
                          <button onClick={() => { if(confirm('Deactivate '+emp.name+'?')) delMut.mutate(emp.id); }} className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"><Trash2 size={14}/></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
      {showForm && <EmpModal emp={editEmp} depts={depts} onClose={() => { setShowForm(false); setEditEmp(null); }} onSuccess={() => { setShowForm(false); setEditEmp(null); qc.invalidateQueries({queryKey:['employees']}); }}/>}
    </div>
  );
}

function EmpModal({ emp, depts, onClose, onSuccess }) {
  const isEdit = !!emp;
  const [form, setForm] = useState(isEdit
    ? { first_name:emp.first_name, last_name:emp.last_name, job_title:emp.job_title, department_id:emp.department_id||'', base_salary:emp.base_salary||0, role:emp.role||'EMPLOYEE' }
    : { employee_id:'', first_name:'', last_name:'', email:'', phone:'', job_title:'', department_id:'', date_of_joining:new Date().toISOString().split('T')[0], base_salary:0, hra:0, da:0, ta:3000, special_allowance:0, role:'EMPLOYEE', password:'Password@123' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault(); setLoading(true); setError('');
    try { isEdit ? await updateEmployee(emp.id, form) : await createEmployee(form); onSuccess(); }
    catch(err) { setError(err.response?.data?.detail || err.message); }
    finally { setLoading(false); }
  };

  const fields = isEdit
    ? [{k:'first_name',l:'First Name',t:'text'},{k:'last_name',l:'Last Name',t:'text'},{k:'job_title',l:'Job Title',t:'text'},{k:'base_salary',l:'Base Salary',t:'number'}]
    : [{k:'employee_id',l:'Employee ID',t:'text'},{k:'first_name',l:'First Name',t:'text'},{k:'last_name',l:'Last Name',t:'text'},{k:'email',l:'Email',t:'email'},{k:'phone',l:'Phone',t:'text'},{k:'job_title',l:'Job Title',t:'text'},{k:'date_of_joining',l:'Date of Joining',t:'date'},{k:'base_salary',l:'Base Salary',t:'number'},{k:'hra',l:'HRA',t:'number'},{k:'da',l:'DA',t:'number'},{k:'ta',l:'TA',t:'number'}];

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#1e293b] border border-white/10 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <h3 className="text-xl font-bold text-white">{isEdit?'Edit':'Add'} Employee</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white"><X size={20}/></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6">
          {error && <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm">{error}</div>}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {fields.map(f => (
              <div key={f.k}>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">{f.l}</label>
                <input type={f.t} value={form[f.k]||''} onChange={e => setForm({...form,[f.k]:f.t==='number'?parseFloat(e.target.value)||0:e.target.value})}
                  className="w-full px-3 py-2.5 bg-[#0f172a] border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-sm"/>
              </div>
            ))}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Department</label>
              <select value={form.department_id||''} onChange={e => setForm({...form,department_id:e.target.value?parseInt(e.target.value):null})}
                className="w-full px-3 py-2.5 bg-[#0f172a] border border-white/10 rounded-xl text-slate-300 focus:outline-none text-sm">
                <option value="">Select</option>
                {depts.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Role</label>
              <select value={form.role} onChange={e => setForm({...form,role:e.target.value})}
                className="w-full px-3 py-2.5 bg-[#0f172a] border border-white/10 rounded-xl text-slate-300 focus:outline-none text-sm">
                {['EMPLOYEE','MANAGER','HR_MANAGER','ADMIN'].map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
          </div>
          <div className="flex gap-3 mt-6">
            <button type="button" onClick={onClose} className="flex-1 py-2.5 border border-white/10 text-slate-300 rounded-xl hover:bg-white/5 font-medium">Cancel</button>
            <button type="submit" disabled={loading} className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium flex items-center justify-center gap-2 disabled:opacity-50">
              {loading ? <><Loader2 size={16} className="animate-spin"/>Saving...</> : (isEdit?'Update':'Create')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
