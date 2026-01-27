import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Plus, Trash2 } from 'lucide-react';

export default function Settings() {
  const queryClient = useQueryClient();
  const [apiKey, setApiKey] = useState('');
  const [exportToken, setExportToken] = useState('');
  const [newCat, setNewCat] = useState('');
  const [monthlyBudget, setMonthlyBudget] = useState<number>(0);

  const { data: config, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: async () => {
      const res = await api.get('/api/config');
      return res.data;
    }
  });

  // Effect to set initial budget state when config loads
  useState(() => {
    if (config?.budgets?.['Monthly']) {
        setMonthlyBudget(config.budgets['Monthly']);
    }
  });

  const apiKeyMutation = useMutation({
    mutationFn: (key: string) => api.post('/api/config/apikey', { api_key: key }),
    onSuccess: () => {
      setApiKey('');
      queryClient.invalidateQueries({ queryKey: ['config'] });
      alert('API Key updated');
    }
  });

  const generateTokenMutation = useMutation({
    mutationFn: () => api.post('/auth/export-token'),
    onSuccess: (data) => {
      setExportToken(data.data.access_token);
    }
  });

  // Config Mutations
  const updateBudgetMutation = useMutation({
      mutationFn: (amount: number) => api.post('/api/config/budgets', { category: 'Monthly', amount }),
      onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['config'] });
          alert('Budget Updated');
      }
  });

  const addCategoryMutation = useMutation({
      mutationFn: (category: string) => api.post('/api/config/categories', { categories: [category] }),
      onSuccess: () => {
          setNewCat('');
          queryClient.invalidateQueries({ queryKey: ['config'] });
      }
  });

  const deleteCategoryMutation = useMutation({
      mutationFn: (category: string) => api.delete('/api/config/categories', { data: { categories: [category] } }),
      onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['config'] });
      }
  });


  if (isLoading) return <div className="p-8 text-center text-gray-400">Loading settings...</div>;

  const categories = config?.categories || [];

  return (
    <div className="space-y-6 animate-in fade-in duration-300 pb-10">
      
      {/* Budget */}
      <Card>
        <CardHeader>
           <CardTitle>Monthly Budget</CardTitle>
        </CardHeader>
        <CardContent>
            <div className="flex items-center space-x-4">
            <input 
                type="number" 
                placeholder={config?.budgets?.['Monthly'] ? config.budgets['Monthly'].toString() : "Set budget..."}
                onChange={(e) => setMonthlyBudget(Number(e.target.value))}
                className="flex-1 p-3 bg-gray-50 dark:bg-slate-900 rounded-xl font-bold text-lg border-none focus:ring-2 focus:ring-blue-100 dark:focus:ring-blue-900 outline-none dark:text-white"
            />
            <Button variant="secondary" onClick={() => updateBudgetMutation.mutate(monthlyBudget)}>Set</Button>
            </div>
        </CardContent>
      </Card>

      {/* Categories */}
      <div className="space-y-4">
        <h3 className="font-bold px-2 text-gray-800 dark:text-white">Categories & Keywords</h3>
        {categories.map((cat: string) => (
          <Card key={cat} className="p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <div className="w-3 h-3 rounded-full mr-2 bg-blue-500" />
                <span className="font-semibold text-sm dark:text-white">{cat}</span>
              </div>
              <button 
                onClick={() => deleteCategoryMutation.mutate(cat)}
                className="text-gray-400 hover:text-red-500 p-1"
                >
                <Trash2 size={14} />
              </button>
            </div>
            <div className="flex flex-wrap gap-1">
              {config?.keywords?.[cat]?.map((kw: string) => (
                <span key={kw} className="px-2 py-0.5 bg-gray-100 dark:bg-slate-800 text-[10px] text-gray-500 dark:text-gray-400 rounded-md">
                  {kw}
                </span>
              ))}
              {(!config?.keywords?.[cat] || config.keywords[cat].length === 0) && (
                  <span className="text-[10px] text-gray-400 dark:text-gray-500 italic">No keywords</span>
              )}
            </div>
          </Card>
        ))}
        
        <div className="flex space-x-2">
          <input 
            type="text" 
            placeholder="New category..." 
            className="flex-1 p-3 bg-white dark:bg-slate-900 border border-gray-100 dark:border-slate-800 rounded-xl dark:text-white"
            value={newCat}
            onChange={(e) => setNewCat(e.target.value)}
          />
          <Button onClick={() => addCategoryMutation.mutate(newCat)}><Plus size={20} /></Button>
        </div>
      </div>

      {/* Technical Settings */}
      <div className="pt-8 border-t border-gray-100 dark:border-slate-800">
        <h3 className="font-bold px-2 mb-4 text-gray-800 dark:text-white">Advanced Integration</h3>
        
        <div className="space-y-4">
            <Card>
                <CardHeader>
                <CardTitle className="text-lg">Google API Key</CardTitle>
                <CardDescription>Required for LLM parsing.</CardDescription>
                </CardHeader>
                <CardContent>
                <div className="space-y-2">
                    <p className="text-sm">Status: {config?.api_key_set ? '✅ Set' : '❌ Not Set'}</p>
                    <div className="flex gap-2">
                    <Input
                        type="password"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        placeholder="Enter Gemini API Key"
                    />
                    <Button onClick={() => apiKeyMutation.mutate(apiKey)}>Save</Button>
                    </div>
                </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                <CardTitle className="text-lg">Apple Shortcuts Integration</CardTitle>
                <CardDescription>Generate a long-lived token for your shortcuts.</CardDescription>
                </CardHeader>
                <CardContent>
                <Button variant="secondary" onClick={() => generateTokenMutation.mutate()}>Generate Export Token</Button>
                {exportToken && (
                    <div className="mt-4">
                    <Label>Your Token (Copy immediately):</Label>
                    <div className="p-2 bg-slate-100 dark:bg-slate-800 rounded break-all font-mono text-xs mt-1 select-all">
                        {exportToken}
                    </div>
                    </div>
                )}
                </CardContent>
            </Card>
        </div>
      </div>
    </div>
  );
}
