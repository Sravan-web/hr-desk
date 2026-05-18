import { create } from 'zustand';
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
