import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Trash2, Download } from 'lucide-react';
import { formatDateTime } from '@/lib/utils';


export default function Transactions() {
  const queryClient = useQueryClient();
  const [smartParseText, setSmartParseText] = useState('');
  const [parseError, setParseError] = useState('');

  const { data: transactions, isLoading } = useQuery({
    queryKey: ['transactions'],
    queryFn: async () => {
      const res = await api.get('/api/transactions', { params: { limit: 50 } });
      return res.data;
    }
  });

  const parseMutation = useMutation({
    mutationFn: async (text: string) => {
      const parts = text.split(',');
      if (parts.length < 3) {
        throw new Error("Format: message,bank,timestamp,remarks");
      }
      const remarks = parts.length >= 4 ? parts.pop()!.trim() : '';
      const timestamp = parts.pop()!.trim();
      const bank_name = parts.pop()!.trim();
      const bank_message = parts.join(',').trim();

      const payload = {
        bank_message,
        bank_name,
        timestamp,
        remarks
      };

      return api.post('/api/transactions/parse', payload);
    },
    onSuccess: () => {
      setSmartParseText('');
      setParseError('');
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
    onError: (err: any) => {
      setParseError(err.message || 'Failed to parse');
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/transactions/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    }
  });

  const handleExport = async () => {
      try {
        const response = await api.get('/api/transactions/export', { responseType: 'blob' });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'transactions.csv');
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch (err) {
        console.error('Export failed:', err);
      }
  };

  if (isLoading) return <div className="p-8 text-center text-gray-500">Loading transactions...</div>;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Add Transaction (Smart Parse)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Label className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Format: message,bank,timestamp,remarks</Label>
            <div className="flex gap-2">
                <Input
                value={smartParseText}
                onChange={(e) => setSmartParseText(e.target.value)}
                placeholder="Paste transaction string..."
                className="font-mono text-sm"
                />
                <Button onClick={() => parseMutation.mutate(smartParseText)} disabled={parseMutation.isPending}>
                {parseMutation.isPending ? 'Parsing...' : 'Add'}
                </Button>
            </div>
            {parseError && <p className="text-red-500 text-sm bg-red-50 p-2 rounded-lg">{parseError}</p>}
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
         <div className="flex justify-between items-center px-1">
            <h2 className="text-xl font-semibold tracking-tight">Recent Transactions</h2>
            <Button variant="outline" size="sm" onClick={handleExport} className="gap-2">
                <Download className="w-4 h-4" /> Export
            </Button>
         </div>

        {/* Mobile View */}
        <div className="md:hidden space-y-3">
            {transactions.map((t: any) => (
                <div key={t.id} className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex flex-col gap-2">
                    <div className="flex justify-between items-start">
                        <div>
                            <div className="font-semibold text-gray-900">{t.description || "No Description"}</div>
                            <div className="text-xs text-gray-500 mt-0.5">{t.bank} • {t.category}</div>
                        </div>
                        <div className={`font-bold ${t.amount < 0 ? 'text-gray-900' : 'text-green-600'}`}>
                            {t.amount < 0 ? `- $${Math.abs(t.amount).toFixed(2)}` : `+ $${t.amount.toFixed(2)}`}
                        </div>
                    </div>
                    <div className="flex justify-between items-center pt-2 border-t border-gray-50 mt-1">
                        <span className="text-xs text-gray-400">{formatDateTime(t.timestamp)}</span>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-red-400 hover:text-red-600 hover:bg-red-50" onClick={() => deleteMutation.mutate(t.id)}>
                            <Trash2 className="w-4 h-4" />
                        </Button>
                    </div>
                </div>
            ))}
        </div>

        {/* Desktop View */}
        <div className="hidden md:block bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                <thead className="text-xs text-gray-500 uppercase bg-gray-50 border-b border-gray-100">
                    <tr>
                    <th className="px-6 py-4 font-semibold">Date</th>
                    <th className="px-6 py-4 font-semibold">Bank</th>
                    <th className="px-6 py-4 font-semibold">Description</th>
                    <th className="px-6 py-4 font-semibold">Category</th>
                    <th className="px-6 py-4 font-semibold text-right">Amount</th>
                    <th className="px-6 py-4 text-right">Action</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                    {transactions.map((t: any) => (
                    <tr key={t.id} className="hover:bg-gray-50/50 transition-colors">
                        <td className="px-6 py-4 text-gray-600 font-mono text-xs">{formatDateTime(t.timestamp)}</td>
                        <td className="px-6 py-4 text-gray-900 font-medium">{t.bank}</td>
                        <td className="px-6 py-4 text-gray-600">{t.description}</td>
                        <td className="px-6 py-4">
                            <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                                {t.category}
                            </span>
                        </td>
                        <td className={`px-6 py-4 text-right font-medium ${t.amount < 0 ? 'text-gray-900' : 'text-green-600'}`}>
                           {t.amount.toFixed(2)}
                        </td>
                        <td className="px-6 py-4 text-right">
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-400 hover:text-red-600" onClick={() => deleteMutation.mutate(t.id)}>
                            <Trash2 className="w-4 h-4" />
                        </Button>
                        </td>
                    </tr>
                    ))}
                </tbody>
                </table>
            </div>
        </div>
      </div>
    </div>
  );
}
