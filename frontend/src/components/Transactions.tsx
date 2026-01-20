import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';

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
      // Split from the END since bank message may contain commas
      // Format: bank_message,bank_name,timestamp,remarks
      // We know: remarks, timestamp, and bank_name don't contain commas
      // So split by comma, take last 3 parts, and join the rest as bank_message

      const parts = text.split(',');
      if (parts.length < 3) {
        throw new Error("Format: message,bank,timestamp,remarks");
      }

      // Extract from the end: remarks (optional), timestamp, bank_name
      const remarks = parts.length >= 4 ? parts.pop()!.trim() : '';
      const timestamp = parts.pop()!.trim();
      const bank_name = parts.pop()!.trim();
      // Everything remaining is the bank_message
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

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Add Transaction (Smart Parse)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label>Format: <code>message,bank,timestamp,remarks</code></Label>
            <Input
              value={smartParseText}
              onChange={(e) => setSmartParseText(e.target.value)}
              placeholder="e.g. You paid SGD 10...,UOB,2025-01-01T10:00:00,Lunch"
            />
            <Button onClick={() => parseMutation.mutate(smartParseText)} disabled={parseMutation.isPending}>
              {parseMutation.isPending ? 'Parsing...' : 'Add'}
            </Button>
            {parseError && <p className="text-red-500 text-sm">{parseError}</p>}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
            <div className="flex justify-between">
                <CardTitle>Recent Transactions</CardTitle>
                <Button variant="outline" size="sm" onClick={async () => {
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
                }}>Export CSV</Button>
            </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                <tr>
                  <th className="px-4 py-2">ID</th>
                  <th className="px-4 py-2">Date</th>
                  <th className="px-4 py-2">Bank</th>
                  <th className="px-4 py-2">Description</th>
                  <th className="px-4 py-2">Category</th>
                  <th className="px-4 py-2">Amount</th>
                  <th className="px-4 py-2">Action</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((t: any) => (
                  <tr key={t.id} className="bg-white border-b">
                    <td className="px-4 py-2">{t.id}</td>
                    <td className="px-4 py-2">{new Date(t.timestamp).toLocaleDateString()}</td>
                    <td className="px-4 py-2">{t.bank}</td>
                    <td className="px-4 py-2">{t.description}</td>
                    <td className="px-4 py-2">{t.category}</td>
                    <td className={`px-4 py-2 ${t.amount < 0 ? 'text-red-600' : 'text-green-600'}`}>
                      {t.amount.toFixed(2)}
                    </td>
                    <td className="px-4 py-2">
                      <Button variant="destructive" size="sm" onClick={() => deleteMutation.mutate(t.id)}>
                        Delete
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
