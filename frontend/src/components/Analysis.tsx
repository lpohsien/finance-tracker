import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Search, Trash2, Download, Upload, Filter, Regex, CaseSensitive } from 'lucide-react';
import { TransactionDetailModal } from './TransactionDetailModal';
import { ImportWizard } from './ImportWizard';
import { MultiSelectModal } from './MultiSelectModal';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

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

  // Initialize default dates (Current Month)
  const now = new Date();
  const defaultStart = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`;
  const lastDate = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  const defaultEnd = `${lastDate.getFullYear()}-${String(lastDate.getMonth() + 1).padStart(2, '0')}-${String(lastDate.getDate()).padStart(2, '0')}`;

  // Filters State
  const [filters, setFilters] = useState<{
    start_date: string;
    end_date: string;
    category: string[];
    account: string[];
    bank: string[];
    type: string[];
    search: string;
    match_case: boolean;
    use_regex: boolean;
    amount_value: string;
    amount_operator: 'gt' | 'lt';
    amount_mode: 'signed' | 'absolute';
  }>({
    start_date: defaultStart,
    end_date: defaultEnd,
    category: [],
    account: [],
    bank: [],
    type: [],
    search: '',
    match_case: false,
    use_regex: false,
    amount_value: '',
    amount_operator: 'gt',
    amount_mode: 'signed'
  });

  // Fetch filter options
  const { data: filterOptions } = useQuery({
    queryKey: ['filterOptions'],
    queryFn: async () => (await api.get('/api/transactions/options')).data,
    placeholderData: { categories: [], banks: [], accounts: [], types: [] }
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
      
      const processList = (key: string, val: string[]) => {
          if (!val || val.length === 0) return;
          val.forEach(v => params.append(key, v));
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

      if (filters.amount_value) {
          params.append('amount_value', filters.amount_value);
          params.append('amount_operator', filters.amount_operator);
          params.append('amount_mode', filters.amount_mode);
      }

      params.append('limit', '100'); // Increase limit for analysis view

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
      const processList = (key: string, val: string[]) => {
          if (!val || val.length === 0) return;
          val.forEach(v => params.append(key, v));
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

      if (filters.amount_value) {
          params.append('amount_value', filters.amount_value);
          params.append('amount_operator', filters.amount_operator);
          params.append('amount_mode', filters.amount_mode);
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
        start_date: defaultStart,
        end_date: defaultEnd,
        category: [],
        account: [],
        bank: [],
        type: [],
        search: '',
        match_case: false,
        use_regex: false,
        amount_value: '',
        amount_operator: 'gt',
        amount_mode: 'signed'
      });
  };

  // Date Shortcuts
  const setDateRange = (type: 'today' | 'week' | 'month' | 'year') => {
      const today = new Date();
      const format = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      
      let start = new Date(today);
      let end = new Date(today);

      switch(type) {
          case 'today':
              // start = end = today
              break;
          case 'week':
              const day = today.getDay();
              const diff = today.getDate() - day + (day === 0 ? -6 : 1); // adjust when day is sunday
              start.setDate(diff);
              end.setDate(start.getDate() + 6);
              break;
          case 'month':
              start = new Date(today.getFullYear(), today.getMonth(), 1);
              end = new Date(today.getFullYear(), today.getMonth() + 1, 0);
              break;
          case 'year':
              start = new Date(today.getFullYear(), 0, 1);
              end = new Date(today.getFullYear(), 11, 31);
              break;
      }
      setFilters(prev => ({ ...prev, start_date: format(start), end_date: format(end) }));
  };

  const activeFilterCount = Object.entries(filters).filter(([k, v]) => {
      if (k === 'match_case' || k === 'use_regex') return false;
      if (k === 'amount_operator' || k === 'amount_mode') return false;
      if (k === 'start_date' && v === defaultStart) return false;
      if (k === 'end_date' && v === defaultEnd) return false;
      if (Array.isArray(v)) return v.length > 0;
      return !!v;
  }).length;

  return (
    <div className="space-y-4 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
          <div className="relative w-full sm:w-auto flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input 
              type="text" 
              placeholder="Search description" 
              className="w-full pl-10 pr-20 py-2 bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-100 outline-none text-sm dark:text-white"
              value={filters.search}
              onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
            />
            {/* Search Toggles */}
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
                 <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger asChild>
                             <button
                                onClick={() => setFilters(prev => ({ ...prev, match_case: !prev.match_case }))}
                                className={`p-1 rounded transition-colors ${filters.match_case ? 'text-blue-600 bg-blue-50' : 'text-gray-400 hover:text-gray-600'}`}
                             >
                                 <CaseSensitive size={18} />
                             </button>
                        </TooltipTrigger>
                        <TooltipContent>Match Case</TooltipContent>
                    </Tooltip>
                 </TooltipProvider>

                 <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger asChild>
                             <button
                                onClick={() => setFilters(prev => ({ ...prev, use_regex: !prev.use_regex }))}
                                className={`p-1 rounded transition-colors ${filters.use_regex ? 'text-blue-600 bg-blue-50' : 'text-gray-400 hover:text-gray-600'}`}
                             >
                                 <Regex size={18} />
                             </button>
                        </TooltipTrigger>
                        <TooltipContent>Use Regex</TooltipContent>
                    </Tooltip>
                 </TooltipProvider>
            </div>
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
              <div className="flex flex-wrap gap-4">
                  {/* Row 1: Date & Amount */}
                  <div className="space-y-2 col-span-1 md:col-span-2">
                       <Label className="text-xs text-gray-500">Date Range</Label>
                       <div className="flex flex-col sm:flex-row gap-2">
                            <Input 
                              type="date" 
                              className="bg-white dark:bg-slate-900 flex-1 min-w-[110px]"
                              value={filters.start_date}
                              onChange={(e) => setFilters(prev => ({...prev, start_date: e.target.value}))} 
                        />
                        <div className="flex items-center text-gray-400 justify-center">-</div>
                            <Input 
                              type="date" 
                              className="bg-white dark:bg-slate-900 flex-1 min-w-[110px]"
                              value={filters.end_date}
                              onChange={(e) => setFilters(prev => ({...prev, end_date: e.target.value}))} 
                        />
                       </div>
                       <div className="flex flex-wrap gap-2 mt-2">
                            <Button variant="outline" size="sm" className="h-7 text-xs" onClick={() => setDateRange('today')}>Today</Button>
                            <Button variant="outline" size="sm" className="h-7 text-xs" onClick={() => setDateRange('week')}>This Week</Button>
                            <Button variant="outline" size="sm" className="h-7 text-xs" onClick={() => setDateRange('month')}>This Month</Button>
                            <Button variant="outline" size="sm" className="h-7 text-xs" onClick={() => setDateRange('year')}>This Year</Button>
                       </div>
                  </div>

                  <div className="space-y-2 w-full xl:w-[calc(50%-0.5rem)]">
                       <Label className="text-xs text-gray-500">Amount</Label>
                       <div className="flex gap-2 items-center">
                            <select 
                                value={filters.amount_operator}
                                onChange={(e) => setFilters(prev => ({ ...prev, amount_operator: e.target.value as any }))}
                                className="h-10 rounded-md border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                            >
                                <option value="gt">Greater {'>'}</option>
                                <option value="lt">Less {'<'}</option>
                            </select>
                            <Input 
                                type="number" 
                                placeholder="Value..." 
                                className="bg-white dark:bg-slate-900 w-32"
                                value={filters.amount_value}
                                onChange={(e) => setFilters(prev => ({ ...prev, amount_value: e.target.value }))}
                            />
                            <label className="flex items-center gap-2 text-sm cursor-pointer ml-2 select-none border rounded-md px-3 py-2 bg-white dark:bg-slate-900 border-dashed border-gray-200">
                                <input 
                                   type="checkbox" 
                                   checked={filters.amount_mode === 'absolute'}
                                   onChange={(e) => setFilters(prev => ({ ...prev, amount_mode: e.target.checked ? 'absolute' : 'signed' }))}
                                   className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                                <span className={filters.amount_mode === 'absolute' ? "font-semibold text-blue-600" : "text-gray-500"}>Absolute (ABS)</span>
                            </label>
                       </div>
                  </div>

                  {/* Row 2: Taxonomies */}
                  <div className="space-y-2 w-full xl:w-[calc(50%-0.5rem)]">
                      <Label className="text-xs text-gray-500">Entities</Label>
                      <div className="grid grid-cols-3 gap-2 flex-1 min-w-[382px]">
                          <MultiSelectModal
                              title="Bank"
                              options={filterOptions?.banks || []}
                              selected={filters.bank}
                              onChange={(val) => setFilters(prev => ({ ...prev, bank: val }))}
                              className="bg-white dark:bg-slate-900 flex-1 min-w-[110px]"
                          />
                          <MultiSelectModal
                              title="Account"
                              options={filterOptions?.accounts || []}
                              selected={filters.account}
                              onChange={(val) => setFilters(prev => ({ ...prev, account: val }))}
                              className="bg-white dark:bg-slate-900 flex-1 min-w-[110px]"
                          />
                          <MultiSelectModal
                              title="Type"
                              options={filterOptions?.types || []}
                              selected={filters.type}
                              onChange={(val) => setFilters(prev => ({ ...prev, type: val }))}
                              className="bg-white dark:bg-slate-900 flex-1 min-w-[110px]"
                          />
                      </div>
                  </div>

                  <div className="space-y-2 w-full xl:w-[calc(50%-0.5rem)]">
                      <Label className="text-xs text-gray-500">Categories</Label>
                      <MultiSelectModal
                          title="Select Categories..."
                          options={filterOptions?.categories || []}
                          selected={filters.category}
                          onChange={(val) => setFilters(prev => ({ ...prev, category: val }))}
                          className="bg-white dark:bg-slate-900"
                      />
                  </div>
                  
                  <div className="w-full flex justify-end">
                       <Button variant="ghost" size="sm" onClick={clearFilters} className="text-red-500 hover:text-red-700 hover:bg-red-50">
                           Clear All Filters
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
