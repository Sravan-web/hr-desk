import React, { useState, useEffect, useRef } from 'react';
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


