import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Search, Trash2, Download, Upload, Filter } from 'lucide-react';
import { TransactionDetailModal } from './TransactionDetailModal';
import { ImportWizard } from './ImportWizard';

// Simple Collapsible implementation
const SimpleCollapsible = ({ children, title, open, onOpenChange }: any) => (
  <div className="border rounded-xl p-4 bg-gray-50 dark:bg-slate-800/50 border-gray-100 dark:border-slate-800">
    <div className="flex justify-between items-center cursor-pointer" onClick={() => onOpenChange(!open)}>
      <h3 className="font-semibold text-sm flex items-center gap-2">
        <Filter size={16} /> {title}
      </h3>
      <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
          {open ? '−' : '+'}
      </Button>
    </div>
    {open && <div className="mt-4">{children}</div>}
  </div>
);

export default function Analysis() {
  const queryClient = useQueryClient();
  const [selectedTransaction, setSelectedTransaction] = useState<any>(null);
  const [showImport, setShowImport] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  // Filters State
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    category: '', // Comma separated for UI simplification
    account: '',
    bank: '',
    type: '',
    search: '',
    match_case: false,
    use_regex: false
  });

  // Prefetch config just in case, though not used directly in render
  useQuery({
    queryKey: ['config'],
    queryFn: async () => (await api.get('/api/config')).data
  });

  const { data: transactions, isLoading } = useQuery({
    queryKey: ['transactions', filters],
    queryFn: async () => {
      // Build Params
      const params = new URLSearchParams();
      
      // Handle comma-separated lists from inputs
      const processList = (key: string, val: string) => {
          if (!val) return;
          val.split(',').map(s => s.trim()).filter(Boolean).forEach(v => params.append(key, v));
      };

      processList('category', filters.category);
      processList('account', filters.account);
      processList('bank', filters.bank);
      processList('type', filters.type);

      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      
      if (filters.search) {
          params.append('search', filters.search);
          if (filters.match_case) params.append('match_case', 'true');
          if (filters.use_regex) params.append('use_regex', 'true');
      }

      // Default to nothing? The backend defaults to current month if NO params.
      // If we have empty filters, we send nothing, backend defaults.
      // If we have filters, we send them.

      params.append('limit', '500'); // Increase limit for analysis view

      const res = await api.get('/api/transactions', { params: params });
      return res.data;
    },
    placeholderData: (prev : any) => prev
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/transactions/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
    }
  });

  const handleExport = async () => {
      const params = new URLSearchParams();
      const processList = (key: string, val: string) => {
          if (!val) return;
          val.split(',').map(s => s.trim()).filter(Boolean).forEach(v => params.append(key, v));
      };

      processList('category', filters.category);
      processList('account', filters.account);
      processList('bank', filters.bank);
      processList('type', filters.type);

      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      
      if (filters.search) {
          params.append('search', filters.search);
          if (filters.match_case) params.append('match_case', 'true');
          if (filters.use_regex) params.append('use_regex', 'true');
      }

      // Trigger download
      try {
        const response = await api.get('/api/transactions/export', { 
            params: params,
            responseType: 'blob' 
        });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'transactions.csv');
        document.body.appendChild(link);
        link.click();
        link.remove();
      } catch (e) {
          console.error("Export failed", e);
      }
  };

  const clearFilters = () => {
      setFilters({
        start_date: '',
        end_date: '',
        category: '',
        account: '',
        bank: '',
        type: '',
        search: '',
        match_case: false,
        use_regex: false
      });
  };

  const activeFilterCount = Object.entries(filters).filter(([k, v]) => {
      if (k === 'match_case' || k === 'use_regex') return false;
      return !!v;
  }).length;

  return (
    <div className="space-y-4 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
          <div className="relative w-full sm:w-auto flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input 
              type="text" 
              placeholder="Search description (Supports Filters)" 
              className="w-full pl-10 pr-4 py-2 bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-100 outline-none text-sm dark:text-white"
              value={filters.search}
              onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
            />
          </div>
          <div className="flex gap-2 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
               <Button 
                   variant={activeFilterCount > 0 ? "default" : "outline"} 
                   size="sm" 
                   onClick={() => setShowFilters(!showFilters)}
                   className="gap-2 shrink-0"
               >
                   <Filter size={16} /> Filters {activeFilterCount > 0 && `(${activeFilterCount})`}
               </Button>
               <Button variant="outline" size="sm" onClick={handleExport} className="gap-2 shrink-0">
                   <Download size={16} /> Export
               </Button>
               <Button onClick={() => setShowImport(true)} size="sm" className="gap-2 shrink-0 bg-blue-600 hover:bg-blue-700 text-white">
                   <Upload size={16} /> Import
               </Button>
          </div>
      </div>

      {showFilters && (
          <SimpleCollapsible title="Advanced Filters" open={showFilters} onOpenChange={setShowFilters}>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="space-y-1">
                      <Label className="text-xs text-gray-500">Date Range</Label>
                      <div className="flex gap-2">
                          <Input 
                            type="date" 
                            className="bg-white dark:bg-slate-900"
                            value={filters.start_date}
                            onChange={(e) => setFilters(prev => ({...prev, start_date: e.target.value}))} 
                          />
                          <Input 
                            type="date" 
                            className="bg-white dark:bg-slate-900"
                            value={filters.end_date}
                            onChange={(e) => setFilters(prev => ({...prev, end_date: e.target.value}))} 
                          />
                      </div>
                  </div>

                  <div className="space-y-1">
                      <Label className="text-xs text-gray-500">Entities</Label>
                      <div className="flex gap-2">
                          <Input 
                            placeholder="Bank" 
                             className="bg-white dark:bg-slate-900"
                            value={filters.bank}
                            onChange={(e) => setFilters(prev => ({...prev, bank: e.target.value}))}
                          />
                          <Input 
                            placeholder="Account" 
                             className="bg-white dark:bg-slate-900"
                            value={filters.account}
                            onChange={(e) => setFilters(prev => ({...prev, account: e.target.value}))}
                          />
                          <Input 
                            placeholder="Type: Card, Transfer..." 
                            className="bg-white dark:bg-slate-900"
                            value={filters.type}
                            onChange={(e) => setFilters(prev => ({...prev, type: e.target.value}))}
                          />
                      </div>
                  </div>

                  <div className="space-y-1">
                      <Label className="text-xs text-gray-500">Categories (comma sep)</Label>
                      <Input 
                        placeholder="Food, Transport..." 
                         className="bg-white dark:bg-slate-900"
                        value={filters.category}
                        onChange={(e) => setFilters(prev => ({...prev, category: e.target.value}))}
                      />
                  </div>

                  <div className="col-span-1 sm:col-span-2 lg:col-span-4 flex items-center gap-4 pt-2">
                       <label className="flex items-center gap-2 text-sm cursor-pointer">
                           <input 
                            type="checkbox" 
                            checked={filters.match_case}
                            onChange={(e) => setFilters(prev => ({...prev, match_case: e.target.checked}))}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                           />
                           Match Case
                       </label>
                       <label className="flex items-center gap-2 text-sm cursor-pointer">
                           <input 
                            type="checkbox" 
                            checked={filters.use_regex}
                            onChange={(e) => setFilters(prev => ({...prev, use_regex: e.target.checked}))}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                           />
                           Regex
                       </label>
                       <div className="flex-1" />
                       <Button variant="ghost" size="sm" onClick={clearFilters} className="text-red-500 hover:text-red-700 hover:bg-red-50">
                           Clear All
                       </Button>
                  </div>
              </div>
          </SimpleCollapsible>
      )}

      {/* Transactions List */}
      <Card className="p-0 overflow-hidden border-none shadow-none bg-transparent">
        <div className="space-y-3">
          {isLoading ? (
               <div className="p-8 text-center text-gray-400 text-sm">Loading data...</div>
          ) : !transactions || transactions.length === 0 ? (
            <div className="p-8 text-center text-gray-400 text-sm">
                No transactions found. 
                {activeFilterCount === 0 && " (Current Month)"}
            </div>
          ) : (
            transactions.map((t: any) => (
              <div 
                key={t.id} 
                className="p-4 bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-800 flex items-center justify-between group cursor-pointer hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors"
                onClick={() => setSelectedTransaction(t)}
              >
                <div className="flex items-center space-x-3 overflow-hidden">
                   <div className="w-10 h-10 rounded-xl bg-gray-50 dark:bg-slate-800 flex items-center justify-center text-lg shrink-0 dark:text-gray-200 uppercase font-bold text-gray-500">
                    {t.category ? t.category[0] : '?'}
                   </div>
                   <div className="min-w-0">
                     <p className="font-semibold text-sm truncate dark:text-white">{t.description || t.bank}</p>
                     <p className="text-[10px] text-gray-400">
                        <span className="bg-gray-100 dark:bg-slate-800 px-1.5 py-0.5 rounded text-gray-500 dark:text-gray-300 mr-2">{t.category}</span>
                        {new Date(t.timestamp).toLocaleDateString()}
                     </p>
                   </div>
                </div>
                <div className="flex items-center space-x-3 shrink-0">
                  <div className="text-right">
                      <p className={`font-bold text-sm ${t.amount < 0 ? 'text-slate-900 dark:text-slate-100' : 'text-green-600'}`}>
                        {t.amount > 0 ? '+' : ''}{t.amount.toFixed(2)}
                      </p>
                      <p className="text-[10px] text-gray-400">{t.account}</p>
                  </div>
                  <button 
                    onClick={(e) => {
                        e.stopPropagation();
                        deleteMutation.mutate(t.id);
                    }}
                    className="p-2 text-gray-300 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>
      
      {selectedTransaction && (
          <TransactionDetailModal 
              transaction={selectedTransaction} 
              onClose={() => setSelectedTransaction(null)} 
          />
      )}

      <ImportWizard open={showImport} onClose={() => setShowImport(false)} />
    </div>
  );
}
