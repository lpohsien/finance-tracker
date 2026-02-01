
import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { LayoutDashboard, BarChart3, Settings as SettingsIcon, LogOut, Plus, Target } from 'lucide-react';
import { Button } from './ui/button';
import { QuickEntryModal } from './QuickEntryModal';
import { UserDetailModal } from './UserDetailModal';
import { ThemeToggle } from './ThemeToggle';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import api from '@/lib/api';

interface LayoutProps {
  children: React.ReactNode;
  activeTab: string;
  onTabChange: (tab: string) => void;
  onLogout: () => void;
}

export default function Layout({ children, activeTab, onTabChange, onLogout }: LayoutProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isUserModalOpen, setIsUserModalOpen] = useState(false);
  const queryClient = useQueryClient();

  // Fetch config for categories for the Modal
  const { data: config } = useQuery({
    queryKey: ['config'],
    queryFn: async () => {
      const res = await api.get('/api/config');
      return res.data;
    }
  });

  const categories = config?.categories?.map((c: string) => ({
      id: c,
      name: c,
      keywords: config.keywords?.[c] || [],
      color: '#3B82F6' // Placeholder
  })) || [];


  const addTransactionMutation = useMutation({
    mutationFn: async (inputData: { amount: number; category: string; transaction_msg: string; bank_name: string; timestamp: string; remarks: string }) => {
        return api.post('/api/transactions/parse', {
            bank_message: inputData.transaction_msg,
            bank_name: 'UOB',
            timestamp: inputData.timestamp ? inputData.timestamp : new Date().toISOString(),
            remarks: inputData.remarks
        });
    },
    onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['transactions'] });
        queryClient.invalidateQueries({ queryKey: ['stats'] });
        queryClient.invalidateQueries({ queryKey: ['tracking-status'] });
        // Don't close modal automatically anymore, let the modal handle success state
        // setIsModalOpen(false); 
    }
  });


  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'transactions', label: 'Analysis', icon: BarChart3 },
    { id: 'tracking', label: 'Tracking', icon: Target },
    { id: 'settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-950 text-gray-900 dark:text-gray-50 font-sans pb-24 md:pb-0 md:flex md:flex-row">
      
      {/* Sidebar for Desktop */}
      <aside className="hidden md:flex flex-col w-64 border-r border-gray-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl h-screen sticky top-0">
         <div className="p-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Finance</h1>
         </div>
         <nav className="flex-1 px-4 space-y-2">
            {navItems.map((item) => (
               <button
                  key={item.id}
                  onClick={() => onTabChange(item.id)}
                  className={cn(
                    "flex items-center gap-3 w-full px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200",
                    activeTab === item.id
                      ? "bg-blue-50 dark:bg-blue-950/50 text-blue-700 dark:text-blue-400 shadow-sm"
                      : "text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-800 hover:text-gray-900 dark:hover:text-white"
                  )}
               >
                  <item.icon className={cn("w-5 h-5", activeTab === item.id ? "text-blue-600 dark:text-blue-400" : "text-gray-400")} />
                  {item.label}
               </button>
            ))}
         </nav>
         <div className="p-4 border-t border-gray-100 dark:border-slate-800 flex items-center justify-between gap-2">
            <Button variant="ghost" className="justify-start text-red-500 flex-1 hover:bg-red-50 dark:hover:bg-red-950/30" onClick={onLogout}>
               <LogOut className="w-4 h-4 mr-2" /> Logout
            </Button>
            <ThemeToggle />
         </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 max-w-md mx-auto md:max-w-none md:mx-0 w-full relative">
        {/* Mobile Header */}
        <header className="md:hidden px-6 pt-12 pb-4 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md sticky top-0 z-10 border-b border-gray-100 dark:border-slate-800">
           <div className="flex justify-between items-end">
             <div>
                <p className="text-gray-500 dark:text-gray-400 text-sm font-medium uppercase tracking-wider">{new Date().toLocaleString('default', { month: 'long', year: 'numeric' })}</p>
                <h1 className="text-3xl font-bold">Finance</h1>
             </div>
             <div className="flex items-center gap-3">
                <ThemeToggle />
                <div 
                  className="w-10 h-10 bg-blue-100 dark:bg-blue-900/50 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold cursor-pointer hover:bg-blue-200 dark:hover:bg-blue-900 transition-colors"
                  onClick={() => setIsUserModalOpen(true)}
                >
                  ME
                </div>
             </div>
           </div>
        </header>
        
        {/* Desktop Header (Simple) */}
        <header className="hidden md:block px-8 py-6 border-b border-gray-100 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur sticky top-0 z-10">
           <div className="flex justify-between items-center">
             <h2 className="text-xl font-semibold capitalize">{activeTab}</h2>
             <div className="flex items-center gap-4">
                <Button onClick={() => setIsModalOpen(true)} size="sm" className="hidden md:flex">
                    <Plus className="mr-2 h-4 w-4" /> Add Transaction
                </Button>
                <div 
                  className="w-10 h-10 bg-blue-100 dark:bg-blue-900/50 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold cursor-pointer hover:bg-blue-200 dark:hover:bg-blue-900 transition-colors"
                  onClick={() => setIsUserModalOpen(true)}
                >
                  ME
                </div>
             </div>
           </div>
        </header>

        <div className="px-4 pt-4 md:p-8 space-y-6">
           {children}
        </div>
      </main>

       {/* Floating Add Button (Mobile Only) */}
       <button 
        onClick={() => setIsModalOpen(true)}
        className="md:hidden fixed bottom-24 right-8 w-14 h-14 bg-blue-600 text-white rounded-full shadow-blue-200 flex items-center justify-center active:scale-95 transition-transform z-40"
      >
        <Plus size={32} />
      </button>

      {/* Bottom Tab Bar (Mobile) */}
      <nav className="fixed bottom-0 left-0 right-0 max-w-md mx-auto bg-white/90 dark:bg-slate-900/90 backdrop-blur-xl border-t border-gray-200 dark:border-slate-800 flex justify-around py-3 px-4 z-50 md:hidden">
        {navItems.map((item) => (
             <button 
             key={item.id}
             onClick={() => onTabChange(item.id)}
             className={`flex flex-col items-center space-y-1 transition-colors ${activeTab === item.id ? 'text-blue-600 dark:text-blue-400' : 'text-gray-400'}`}
           >
             <item.icon size={22} />
             <span className="text-[10px] font-medium">{item.label}</span>
           </button>
        ))}
        {/* Fake item for spacing if needed, but flex justify-around is fine */}
      </nav>

      {/* Quick Entry Modal */}
      {isModalOpen && (
        <QuickEntryModal 
          onClose={() => setIsModalOpen(false)} 
          categories={categories} 
          onAdd={(data) => addTransactionMutation.mutateAsync(data)}
          isAdding={addTransactionMutation.isPending}
        />
      )}

      {/* User Detail Modal */}
      {isUserModalOpen && (
        <UserDetailModal onClose={() => setIsUserModalOpen(false)} />
      )}
    </div>
  );
}
