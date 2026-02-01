import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Plus, Trash2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";

export default function Settings() {
  const queryClient = useQueryClient();
  const [apiKey, setApiKey] = useState('');
  const [exportToken, setExportToken] = useState('');
  const [newCat, setNewCat] = useState('');
  
  // Delete Account States
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isFinalConfirmOpen, setIsFinalConfirmOpen] = useState(false);

  const { data: config, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: async () => {
      const res = await api.get('/api/config');
      return res.data;
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
    mutationFn: () => api.post('/api/auth/export-token'),
    onSuccess: (data) => {
      setExportToken(data.data.access_token);
    }
  });

  const addCategoryMutation = useMutation({ // Removed updateBudgetMutation
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
  
  const deleteAccountMutation = useMutation({
    mutationFn: () => api.delete('/api/auth/me'),
    onSuccess: () => {
        localStorage.removeItem('token');
        window.location.href = '/login';
    },
    onError: () => {
        alert("Failed to delete account");
    }
  });

  const handleExportData = async () => {
    try {
        // Transactions
        const txRes = await api.get('/api/transactions/export?export_all=true', { responseType: 'blob' });
        const txUrl = window.URL.createObjectURL(new Blob([txRes.data]));
        const txLink = document.createElement('a');
        txLink.href = txUrl;
        txLink.setAttribute('download', 'transactions_export_all.csv');
        document.body.appendChild(txLink);
        txLink.click();
        txLink.remove();

        // Config
        const cfgRes = await api.get('/api/config/export', { responseType: 'blob' });
        const cfgUrl = window.URL.createObjectURL(new Blob([cfgRes.data]));
        const cfgLink = document.createElement('a');
        cfgLink.href = cfgUrl;
        cfgLink.setAttribute('download', 'config_export.json');
        document.body.appendChild(cfgLink);
        cfgLink.click();
        cfgLink.remove();
        
        // Do not auto-advance. Let user click Proceed when ready.
    } catch (e) {
        console.error("Export failed", e);
        alert("Export failed");
    }
  };

  if (isLoading) return <div className="p-8 text-center text-gray-400">Loading settings...</div>;

  const categories = config?.categories || [];

  return (
    <div className="space-y-6 animate-in fade-in duration-300 pb-10">
      
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

      {/* Danger Zone */}
      <div className="pt-8 border-t border-red-200 dark:border-red-900/30">
          <h3 className="font-bold px-2 mb-4 text-red-600 dark:text-red-400">Danger Zone</h3>
          <Card className="border-red-200 dark:border-red-900/30">
              <CardHeader>
                  <CardTitle className="text-lg text-red-600 dark:text-red-400">Delete Account</CardTitle>
                  <CardDescription>Permanently remove your account and all data.</CardDescription>
              </CardHeader>
              <CardContent>
                  <Button variant="destructive" onClick={() => setIsDeleteModalOpen(true)}>Delete Account</Button>
              </CardContent>
          </Card>
      </div>

      {/* Warning Modal */}
      <Dialog open={isDeleteModalOpen} onOpenChange={setIsDeleteModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Account?</DialogTitle>
            <DialogDescription>
              This action cannot be undone. This will permanently delete your account and remove your data from our servers.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-2 py-4">
               <p className="text-sm">We recommend exporting your data before proceeding.</p>
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" onClick={() => setIsDeleteModalOpen(false)}>Cancel</Button>
            <Button variant="secondary" onClick={handleExportData}>Export All Data</Button>
            <Button variant="destructive" onClick={() => { setIsDeleteModalOpen(false); setIsFinalConfirmOpen(true); }}>Proceed</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Final Confirmation Modal */}
      <Dialog open={isFinalConfirmOpen} onOpenChange={setIsFinalConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Are you absolutely sure?</DialogTitle>
            <DialogDescription>
              This is your last chance to back out. All your transactions and settings will be wiped immediately.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsFinalConfirmOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={() => deleteAccountMutation.mutate()}>Yes, Delete Account</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

    </div>
  );
}
