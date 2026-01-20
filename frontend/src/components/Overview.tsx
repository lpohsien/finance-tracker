import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts';

export default function Overview() {
  const now = new Date();

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats', now.getFullYear(), now.getMonth() + 1],
    queryFn: async () => {
      const res = await api.get('/api/stats/monthly', {
        params: { year: now.getFullYear(), month: now.getMonth() + 1 }
      });
      return res.data;
    }
  });

  const { data: dailyStats, isLoading: dailyLoading } = useQuery({
    queryKey: ['daily', now.getFullYear(), now.getMonth() + 1],
    queryFn: async () => {
        const res = await api.get('/api/stats/daily', {
            params: { year: now.getFullYear(), month: now.getMonth() + 1 }
        });
        return res.data;
    }
  });

  if (statsLoading || dailyLoading) return <div>Loading...</div>;

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

  // Pie Chart Data
  const breakdownData = Object.entries(stats.breakdown || {}).map(([name, value]: [string, any]) => ({
    name,
    value: Math.abs(value)
  })).filter(d => d.value > 0);

  // Daily Bar Chart Data
  const dailyData = Object.entries(dailyStats.daily_spending || {}).map(([day, value]: [string, any]) => ({
    day: parseInt(day),
    amount: value
  })).sort((a, b) => a.day - b.day);

  // Budget Calculation
  const totalBudget = stats.budgets?.Total || 0;
  const totalExpense = Math.abs(stats.expense);
  const budgetProgress = totalBudget > 0 ? (totalExpense / totalBudget) * 100 : 0;
  const isBudgetExceeded = totalBudget > 0 && totalExpense > totalBudget;

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Income</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">${stats.income.toFixed(2)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Expense</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">${totalExpense.toFixed(2)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Net</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${stats.income + stats.expense >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${(stats.income + stats.expense).toFixed(2)}
            </div>
          </CardContent>
        </Card>
        <Card>
           <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Budget Status</CardTitle>
          </CardHeader>
          <CardContent>
             <div className="text-2xl font-bold">
                 {totalBudget > 0 ? `${budgetProgress.toFixed(1)}%` : 'N/A'}
             </div>
             {totalBudget > 0 && (
                 <p className={`text-xs ${isBudgetExceeded ? 'text-red-500' : 'text-slate-500'}`}>
                     ${totalExpense.toFixed(2)} / ${totalBudget.toFixed(2)}
                 </p>
             )}
          </CardContent>
        </Card>
      </div>

      {/* Budget Progress Bar */}
      {totalBudget > 0 && (
          <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700">
            <div
                className={`h-2.5 rounded-full ${isBudgetExceeded ? 'bg-red-600' : 'bg-blue-600'}`}
                style={{ width: `${Math.min(budgetProgress, 100)}%` }}>
            </div>
          </div>
      )}

      {/* Charts Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Daily Spending</CardTitle>
            <CardDescription>Daily expenses for current month</CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
             <ResponsiveContainer width="100%" height="100%">
                 <BarChart data={dailyData}>
                     <CartesianGrid strokeDasharray="3 3" />
                     <XAxis dataKey="day" />
                     <YAxis />
                     <Tooltip />
                     <Bar dataKey="amount" fill="#8884d8" name="Spent" />
                 </BarChart>
             </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Category Breakdown</CardTitle>
            <CardDescription>Where your money went</CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={breakdownData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(props: any) => `${props.name} ${((props.percent || 0) * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {breakdownData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
