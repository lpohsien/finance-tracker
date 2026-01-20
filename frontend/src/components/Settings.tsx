import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';

export default function Settings() {
  const queryClient = useQueryClient();
  const [apiKey, setApiKey] = useState('');
  const [exportToken, setExportToken] = useState('');

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
    mutationFn: () => api.post('/auth/export-token'),
    onSuccess: (data) => {
      setExportToken(data.data.access_token);
    }
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Google API Key</CardTitle>
          <CardDescription>Required for LLM parsing.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <p className="text-sm">Status: {config.api_key_set ? '✅ Set' : '❌ Not Set'}</p>
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
          <CardTitle>Apple Shortcuts Integration</CardTitle>
          <CardDescription>Generate a long-lived token for your shortcuts.</CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={() => generateTokenMutation.mutate()}>Generate Export Token</Button>
          {exportToken && (
            <div className="mt-4">
              <Label>Your Token (Copy immediately, it won't be shown again):</Label>
              <div className="p-2 bg-slate-100 rounded break-all font-mono text-xs">
                {exportToken}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Budget & Category Management UI would go here (omitted for brevity in this plan step) */}
    </div>
  );
}
