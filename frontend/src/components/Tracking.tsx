import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, Trash2, Edit, Check } from 'lucide-react';
import { TrackingItemModal } from './TrackingItemModal';

// Types (should ideally be in a types file)
type AccountFilter = {
    bank?: string;
    account?: string;
    type?: string;
};

type TrackingFilters = {
    categories?: string[];
    accounts?: AccountFilter[];
};

export type TrackingItem = {
    id: string;
    name: string;
    type: 'goal' | 'limit';
    target_amount: number;
    period: 'daily' | 'weekly' | 'monthly' | 'annually';
    net_disbursements: boolean;
    filters: TrackingFilters;
};

type TrackingStatus = TrackingItem & {
    current_amount: number;
    start_date: string;
    end_date: string;
};

export default function Tracking() {
    const queryClient = useQueryClient();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingItem, setEditingItem] = useState<TrackingItem | null>(null);
    const [monthlyBudget, setMonthlyBudget] = useState<number>(0);
    const [isBudgetSaved, setIsBudgetSaved] = useState(false);

    const { data: config } = useQuery({
        queryKey: ['config'],
        queryFn: async () => {
            const res = await api.get('/api/config');
            return res.data;
        }
    });

    useEffect(() => {
        if (config?.budgets?.['Monthly']) {
            setMonthlyBudget(config.budgets['Monthly']);
        }
    }, [config]);

    const { data: items, isLoading } = useQuery<TrackingStatus[]>({
        queryKey: ['tracking-status'],
        queryFn: async () => {
            const res = await api.get('/api/tracking/status');
            return res.data;
        }
    });

    const deleteMutation = useMutation({
        mutationFn: async (id: string) => {
            await api.delete(`/api/config/tracking/${id}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tracking-status'] });
        }
    });

    const updateBudgetMutation = useMutation({
        mutationFn: (amount: number) => api.post('/api/config/budgets', { category: 'Monthly', amount }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['config'] });
            setIsBudgetSaved(true);
            setTimeout(() => setIsBudgetSaved(false), 2000);
        }
    });

    const handleDelete = (id: string) => {
        if (confirm('Are you sure you want to delete this tracking item?')) {
            deleteMutation.mutate(id);
        }
    };

    const handleEdit = (item: TrackingStatus) => {
        // We only need the config part
        const configItem: TrackingItem = {
            id: item.id,
            name: item.name,
            type: item.type,
            target_amount: item.target_amount,
            period: item.period,
            net_disbursements: item.net_disbursements,
            filters: item.filters
        };
        setEditingItem(configItem);
        setIsModalOpen(true);
    };

    const handleCreate = () => {
        setEditingItem(null);
        setIsModalOpen(true);
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold">Tracking Goals & Limits</h2>
                <Button onClick={handleCreate} size="sm" className="gap-2">
                    <Plus size={16} /> Add New
                </Button>
            </div>

            {/* Monthly Budget Card */}
            <Card>
                <CardHeader>
                    <CardTitle>Monthly Budget Overview</CardTitle>
                    <CardDescription>Set your total monthly budget goal for the dashboard overview.</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex flex-col sm:flex-row gap-3">
                        <input 
                            type="number" 
                            placeholder={config?.budgets?.['Monthly'] ? config.budgets['Monthly'].toString() : "Set budget..."}
                            value={monthlyBudget || ''}
                            onChange={(e) => setMonthlyBudget(Number(e.target.value))}
                            className="flex-1 p-3 bg-gray-50 dark:bg-slate-900 rounded-xl font-bold text-lg border-none focus:ring-2 focus:ring-blue-100 dark:focus:ring-blue-900 outline-none dark:text-white w-full"
                        />
                        <Button 
                            variant={isBudgetSaved ? "outline" : "secondary"}
                            onClick={() => updateBudgetMutation.mutate(monthlyBudget)}
                            className={`w-full sm:w-auto ${isBudgetSaved ? "bg-green-50 border-green-200 text-green-700 hover:bg-green-100 hover:text-green-800 dark:bg-green-900/20 dark:border-green-800 dark:text-green-400 transition-colors" : "transition-colors"}`}
                        >
                            {isBudgetSaved ? <Check size={16} className="mr-2" /> : null}
                            {isBudgetSaved ? "Saved" : "Set"}
                        </Button>
                    </div>
                </CardContent>
            </Card>



            {/* Tracking Items Grid. Do not display if is loading */}
            {isLoading ? (
                <div className="p-8 text-center text-gray-400">Loading tracking items...</div>
            ) : items?.length === 0 ? (
                <div className="p-8 text-center text-gray-400">No tracking items found. Click "Add New" to create one.</div>
            ) : null}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {items?.map((item) => (
                    <TrackingCard 
                        key={item.id} 
                        item={item} 
                        onDelete={() => handleDelete(item.id)}
                        onEdit={() => handleEdit(item)}
                    />
                ))}
            </div>
            
            {isModalOpen && (
                <TrackingItemModal 
                    isOpen={isModalOpen} 
                    onClose={() => setIsModalOpen(false)} 
                    initialData={editingItem}
                />
            )}
        </div>
    );
}

function TrackingCard({ item, onDelete, onEdit }: { item: TrackingStatus, onDelete: () => void, onEdit: () => void }) {
    const percentage = (item.current_amount / item.target_amount) * 100;
    
    // Color Logic
    let barColor = 'bg-blue-500';
    if (item.type === 'limit') {
        if (percentage < 50) barColor = 'bg-green-500';
        else if (percentage < 80) barColor = 'bg-yellow-500';
        else if (percentage < 100) barColor = 'bg-orange-500';
        else barColor = 'bg-red-500';
    } else {
        // Goal
        if (percentage >= 100) barColor = 'bg-green-500';
        else barColor = 'bg-blue-500';
    }

    return (
        <Card className="relative group">
            <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                    <div>
                        <CardTitle className="text-base font-medium">{item.name}</CardTitle>
                        <CardDescription className="text-xs uppercase mt-1">
                            {item.period} {item.type}
                        </CardDescription>
                    </div>
                     <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                         <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onEdit}>
                            <Edit size={14} />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-6 w-6 text-red-500 hover:text-red-600 hover:bg-red-50" onClick={onDelete}>
                            <Trash2 size={14} />
                        </Button>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                        <span className="font-medium">
                            ${item.current_amount.toFixed(2)}
                            <span className="text-slate-500 font-normal"> / ${item.target_amount.toFixed(2)}</span>
                        </span>
                        <span className="text-slate-500">{percentage.toFixed(0)}%</span>
                    </div>
                    
                    <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden dark:bg-slate-800">
                        <div 
                            className={`h-full transition-all duration-500 ${barColor}`} 
                            style={{ width: `${percentage}%` }}
                        />
                    </div>
                    
                    {item.net_disbursements && (
                        <p className="text-xs text-slate-500 italic mt-1">
                            * Net of disbursements
                        </p>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
