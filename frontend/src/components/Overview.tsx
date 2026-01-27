import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card } from '@/components/ui/card';
import { SimplePieChart } from './SimplePieChart';
import { ArrowUpRight, ArrowDownLeft } from 'lucide-react';
import { TransactionDetailModal } from './TransactionDetailModal';

interface OverviewProps {
  onNavigateToTransactions?: () => void;
}

export default function Overview({ onNavigateToTransactions }: OverviewProps) {
  const [selectedTransaction, setSelectedTransaction] = useState<any>(null);
  const now = new Date();
  const { data: stats, isLoading } = useQuery({
    queryKey: ['stats', now.getFullYear(), now.getMonth() + 1],
    queryFn: async () => {
      const res = await api.get('/api/stats/monthly', {
        params: { year: now.getFullYear(), month: now.getMonth() + 1 }
      });
      return res.data;
    }
  });

  const { data: transactions } = useQuery({
      queryKey: ['transactions', 'recent'],
      queryFn: async () => {
          const res = await api.get('/api/transactions', { params: { limit: 5 } });
          return res.data;
      }
  });

  const { data: config } = useQuery({
      queryKey: ['config'],
      queryFn: async () => {
          const res = await api.get('/api/config');
          return res.data;
      }
  });

  if (isLoading) return <div className="p-8 text-center text-gray-400">Loading overview...</div>;

  const totalSpent = Math.abs(stats.expense);
  const income = stats.income;
  const budget = config?.budgets?.['Monthly'] || 2000; // Use configured budget or default
  const remaining = budget - totalSpent;

  // Colors for chart
  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#6366F1'];
  
  const chartData = Object.entries(stats.breakdown || {})
    .map(([name, value]: [string, any], index) => ({
      name,
      value: Math.abs(value),
      color: COLORS[index % COLORS.length]
    }))
    .filter(d => d.value > 0)
    .sort((a, b) => b.value - a.value);

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
      
      {/* Budget Card */}
      <Card className="bg-gradient-to-br from-blue-600 to-blue-700 text-white border-none shadow-blue-200 shadow-xl p-6">
        <p className="opacity-80 text-sm">Remaining Budget</p>
        <h2 className="text-3xl font-bold mt-1">${remaining.toFixed(2)}</h2>
        <div className="mt-6 h-2 bg-white/20 rounded-full overflow-hidden">
          <div 
            className="h-full bg-white transition-all duration-1000" 
            style={{ width: `${Math.min((totalSpent / budget) * 100, 100)}%` }}
          />
        </div>
        <div className="flex justify-between mt-2 text-xs opacity-80">
          <span>Spent: ${totalSpent.toFixed(2)}</span>
          <span>Budget: ${budget}</span>
        </div>
      </Card>

      {/* Income / Expense Mini Cards */}
      <div className="grid grid-cols-2 gap-4">
        <Card className="flex flex-col items-center justify-center py-6">
          <div className="w-8 h-8 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center text-green-600 dark:text-green-400 mb-2">
            <ArrowDownLeft size={16} />
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400">Income</p>
          <p className="font-bold text-lg">${income.toFixed(2)}</p>
        </Card>
        <Card className="flex flex-col items-center justify-center py-6">
          <div className="w-8 h-8 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center text-red-600 dark:text-red-400 mb-2">
            <ArrowUpRight size={16} />
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400">Expense</p>
          <p className="font-bold text-lg">${totalSpent.toFixed(2)}</p>
        </Card>
      </div>

      {/* Breakdown Chart */}
      <Card className="p-6">
        <h3 className="font-bold mb-4 text-gray-800 dark:text-white">Expenditure Breakdown</h3>
        <div className="flex items-center justify-between">
          <div className="w-32 h-32 relative shrink-0">
             <SimplePieChart data={chartData} />
          </div>
          <div className="flex-1 ml-6 space-y-2">
            {chartData.slice(0, 5).map(d => (
              <div key={d.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} />
                  <span className="text-gray-600 dark:text-gray-300 font-medium truncate max-w-[80px]">{d.name}</span>
                </div>
                <span className="font-semibold dark:text-gray-200">${d.value.toFixed(2)}</span>
              </div>
            ))}
             {chartData.length > 5 && (
                 <div className="text-xs text-gray-400 dark:text-gray-500 text-right italic">+ {chartData.length - 5} more</div>
             )}
          </div>
        </div>
      </Card>

      {/* Recent Transactions */}
      <div>
        <div className="flex justify-between items-center mb-4 px-2">
          <h3 className="font-bold text-gray-800 dark:text-white">Recent Transactions</h3>
          <button 
            onClick={onNavigateToTransactions}
            className="text-blue-600 dark:text-blue-400 text-sm font-medium hover:underline transition-all"
          >
            See All
          </button>
        </div>
        <div className="space-y-3">
          {transactions?.map((t: any) => (
            <div 
                key={t.id} 
                className="flex items-center justify-between bg-white dark:bg-slate-900 p-3 rounded-xl shadow-sm border border-gray-50 dark:border-slate-800 cursor-pointer hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors"
                onClick={() => setSelectedTransaction(t)}
            >
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-gray-50 dark:bg-slate-800 flex items-center justify-center text-xl shrink-0">
                  {/* Simple emoji mapping based on first letter or hardcoded checks if we had a map */}
                  {['Food', 'Lunch', 'Dinner'].includes(t.category) ? '🍱' : 
                   ['Transport', 'Bus', 'Grab', 'Uber'].includes(t.category) ? '🚌' : 
                   ['Shopping'].includes(t.category) ? '🛍️' : '💸'}
                </div>
                <div className="min-w-0">
                  <p className="font-semibold text-sm truncate dark:text-gray-200">{t.description || t.bank}</p>
                  <p className="text-[10px] text-gray-400 dark:text-gray-500">{new Date(t.timestamp).toLocaleDateString()}</p>
                </div>
              </div>
              <p className={`font-bold text-sm ${t.amount < 0 ? 'text-red-500 dark:text-red-400' : 'text-green-500 dark:text-green-400'}`}>
                {t.amount < 0 ? '-' : '+'}${Math.abs(t.amount).toFixed(2)}
              </p>
            </div>
          ))}
        </div>
      </div>

      {selectedTransaction && (
          <TransactionDetailModal 
              transaction={selectedTransaction} 
              onClose={() => setSelectedTransaction(null)} 
          />
      )}
    </div>
  );
}
