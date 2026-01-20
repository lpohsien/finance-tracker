import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';

export default function Analysis() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [prompt, setPrompt] = useState('');
  const [analysisResult, setAnalysisResult] = useState('');

  // Fetch Monthly Stats
  const { data: monthlyStats } = useQuery({
    queryKey: ['stats', year, month],
    queryFn: async () => {
      const res = await api.get('/api/stats/monthly', { params: { year, month } });
      return res.data;
    }
  });

  // Fetch Trend Stats
  const { data: trendStats } = useQuery({
    queryKey: ['trend'],
    queryFn: async () => {
      const res = await api.get('/api/stats/trend', { params: { months: 6 } });
      return res.data;
    }
  });

  // LLM Analysis Mutation
  const analyzeMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post('/api/stats/analyze', {
        prompt,
        year,
        month
      });
      return res.data.analysis;
    },
    onSuccess: (data) => {
      setAnalysisResult(data);
    }
  });

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658'];

  // Prepare data
  const categoryData = monthlyStats?.breakdown ? Object.entries(monthlyStats.breakdown).map(([name, value]: [string, any]) => ({
    name, value: Math.abs(value)
  })).filter(d => d.value > 0).sort((a,b) => b.value - a.value) : [];

  const accountData = monthlyStats?.account_breakdown ? Object.entries(monthlyStats.account_breakdown).map(([name, value]: [string, any]) => ({
    name, value: Math.abs(value)
  })).filter(d => d.value > 0).sort((a,b) => b.value - a.value) : [];

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-2">
        <div className="flex flex-col space-y-1">
            <Label>Year</Label>
            <Input type="number" value={year} onChange={(e) => setYear(parseInt(e.target.value))} className="w-24" />
        </div>
        <div className="flex flex-col space-y-1">
            <Label>Month</Label>
            <Input type="number" value={month} onChange={(e) => setMonth(parseInt(e.target.value))} className="w-24" />
        </div>
      </div>

      <Tabs defaultValue="charts">
        <TabsList>
            <TabsTrigger value="charts">Charts</TabsTrigger>
            <TabsTrigger value="ai">AI Insights</TabsTrigger>
        </TabsList>

        <TabsContent value="charts" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Income vs Expense Trend (6 Months)</CardTitle>
                    </CardHeader>
                    <CardContent className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={trendStats || []}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="label" />
                                <YAxis />
                                <Tooltip />
                                <Legend />
                                <Bar dataKey="income" fill="#82ca9d" name="Income" />
                                <Bar dataKey="expense" fill="#8884d8" name="Expense" />
                            </BarChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Category Breakdown</CardTitle>
                    </CardHeader>
                    <CardContent className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={categoryData}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={(props: any) => `${props.name}`}
                                    outerRadius={80}
                                    fill="#8884d8"
                                    dataKey="value"
                                >
                                    {categoryData.map((_, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Expenditure by Account</CardTitle>
                </CardHeader>
                <CardContent className="h-[300px]">
                     <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={accountData} layout="vertical" margin={{ left: 50 }}>
                             <CartesianGrid strokeDasharray="3 3" />
                             <XAxis type="number" />
                             <YAxis type="category" dataKey="name" width={150} />
                             <Tooltip />
                             <Bar dataKey="value" fill="#ffc658" name="Spent" />
                        </BarChart>
                     </ResponsiveContainer>
                </CardContent>
            </Card>
        </TabsContent>

        <TabsContent value="ai" className="space-y-4">
            <Card>
                <CardHeader>
                    <CardTitle>Ask AI</CardTitle>
                    <CardDescription>Ask questions about your spending habits for {month}/{year}.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <Input
                        placeholder="e.g. How can I save more on food?"
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                    />
                    <Button onClick={() => analyzeMutation.mutate()} disabled={analyzeMutation.isPending}>
                        {analyzeMutation.isPending ? 'Analyzing...' : 'Ask'}
                    </Button>

                    {analysisResult && (
                        <div className="mt-4 p-4 bg-slate-100 rounded-md whitespace-pre-wrap">
                            {analysisResult}
                        </div>
                    )}
                </CardContent>
            </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
