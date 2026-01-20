import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Search, Trash2 } from 'lucide-react';

export default function Analysis() {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');

  const { data: transactions, isLoading } = useQuery({
    queryKey: ['transactions', 'all'],
    queryFn: async () => {
      const res = await api.get('/api/transactions', { params: { limit: 100 } });
      return res.data;
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/transactions/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    }
  });

  if (isLoading) return <div className="p-8 text-center text-gray-400">Loading transactions...</div>;

  const filtered = transactions?.filter((t: any) => 
    (t.category && t.category.toLowerCase().includes(searchTerm.toLowerCase())) || 
    (t.description && t.description.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (t.bank && t.bank.toLowerCase().includes(searchTerm.toLowerCase()))
  ) || [];

  return (
    <div className="space-y-4 animate-in fade-in duration-300">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
        <input 
          type="text" 
          placeholder="Search transactions..." 
          className="w-full pl-10 pr-4 py-3 bg-white border border-gray-100 rounded-2xl shadow-sm focus:ring-2 focus:ring-blue-100 outline-none transition-all text-sm"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <Card className="p-0 overflow-hidden border-none shadow-none bg-transparent">
        <div className="space-y-3">
          {filtered.length === 0 ? (
            <div className="p-8 text-center text-gray-400 text-sm">No records found.</div>
          ) : (
            filtered.map((t: any) => (
              <div key={t.id} className="p-4 bg-white rounded-2xl shadow-sm border border-gray-100 flex items-center justify-between group">
                <div className="flex items-center space-x-3 overflow-hidden">
                   <div className="w-10 h-10 rounded-xl bg-gray-50 flex items-center justify-center text-lg shrink-0">
                    {t.category ? t.category[0].toUpperCase() : '?'}
                   </div>
                   <div className="min-w-0">
                     <p className="font-semibold text-sm truncate">{t.description || t.bank}</p>
                     <p className="text-[10px] text-gray-400">{t.category} • {new Date(t.timestamp).toLocaleDateString()}</p>
                   </div>
                </div>
                <div className="flex items-center space-x-3 shrink-0">
                  <p className={`font-bold text-sm ${t.type === 'expense' ? 'text-red-500' : 'text-green-500'}`}>
                    {t.type === 'expense' ? '-' : '+'}${t.amount.toFixed(2)}
                  </p>
                  <button 
                    onClick={() => deleteMutation.mutate(t.id)}
                    className="p-2 text-gray-300 hover:text-red-500 transition-colors"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
}
