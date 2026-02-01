import { useState, useEffect } from 'react';
import { useQueryClient, useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { X, Plus, Trash } from 'lucide-react';
import { TrackingItem } from './Tracking';

interface TrackingItemModalProps {
    isOpen: boolean;
    onClose: () => void;
    initialData: TrackingItem | null;
}

export function TrackingItemModal({ isOpen, onClose, initialData }: TrackingItemModalProps) {
    const queryClient = useQueryClient();
    const [name, setName] = useState('');
    const [type, setType] = useState<'goal' | 'limit'>('limit');
    const [amount, setAmount] = useState('');
    const [period, setPeriod] = useState<'daily' | 'weekly' | 'monthly' | 'annually'>('monthly');
    const [netDisbursements, setNetDisbursements] = useState(false);
    
    // Filters
    const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
    const [accountFilters, setAccountFilters] = useState<{ bank: string, account: string, type: string }[]>([]);

    // Load initial data
    useEffect(() => {
        if (initialData) {
            setName(initialData.name);
            setType(initialData.type);
            setAmount(initialData.target_amount.toString());
            setPeriod(initialData.period);
            setNetDisbursements(initialData.net_disbursements);
            setSelectedCategories(initialData.filters.categories || []);
            // Map optional fields
            const accs = initialData.filters.accounts || [];
            if (accs.length > 0) {
                 // @ts-ignore
                setAccountFilters(accs.map(a => ({ bank: a.bank || '', account: a.account || '', type: a.type || '' })));
            } else {
                setAccountFilters([]);
            }
        } else {
            // Reset
            setName('');
            setType('limit');
            setAmount('');
            setPeriod('monthly');
            setNetDisbursements(false);
            setSelectedCategories([]);
            setAccountFilters([]);
        }
    }, [initialData, isOpen]);

    // Fetch config for Categories
    const { data: config } = useQuery({
        queryKey: ['config'],
        queryFn: async () => {
            const res = await api.get('/api/config');
            return res.data;
        },
        staleTime: 600000 
    });

    const categoryList: string[] = config?.categories || [];

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        const payload: any = {
            name,
            type,
            target_amount: parseFloat(amount),
            period,
            net_disbursements: netDisbursements,
            filters: {
                categories: selectedCategories.length > 0 ? selectedCategories : undefined,
                accounts: accountFilters.length > 0 ? accountFilters.map(a => ({
                    bank: a.bank || undefined,
                    account: a.account || undefined,
                    type: a.type || undefined
                })) : undefined
            }
        };

        try {
            if (initialData) {
                await api.put(`/api/config/tracking/${initialData.id}`, payload);
            } else {
                await api.post('/api/config/tracking', payload);
            }
            queryClient.invalidateQueries({ queryKey: ['tracking-status'] });
            onClose();
        } catch (error) {
            console.error(error);
            alert('Failed to save tracking item');
        }
    };

    const toggleCategory = (cat: string) => {
        if (selectedCategories.includes(cat)) {
            setSelectedCategories(selectedCategories.filter(c => c !== cat));
        } else {
            setSelectedCategories([...selectedCategories, cat]);
        }
    };

    const addAccountFilter = () => {
        setAccountFilters([...accountFilters, { bank: '', account: '', type: '' }]);
    };
    
    const updateAccountFilter = (index: number, field: string, value: string) => {
        const newFilters = [...accountFilters];
        // @ts-ignore
        newFilters[index][field] = value;
        setAccountFilters(newFilters);
    };

    const removeAccountFilter = (index: number) => {
        setAccountFilters(accountFilters.filter((_, i) => i !== index));
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 overflow-y-auto">
            <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                <div className="p-4 border-b flex justify-between items-center sticky top-0 bg-white dark:bg-slate-900 z-10">
                    <h3 className="text-lg font-semibold">{initialData ? 'Edit' : 'New'} Tracking Item</h3>
                    <Button variant="ghost" size="icon" onClick={onClose}><X size={20}/></Button>
                </div>
                
                <form onSubmit={handleSubmit} className="p-6 space-y-6">
                    {/* Basic Info */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>Name</Label>
                            <Input value={name} onChange={e => setName(e.target.value)} required placeholder="e.g. Monthly Food Limit" />
                        </div>
                        <div className="space-y-2">
                            <Label>Target Amount</Label>
                            <Input type="number" value={amount} onChange={e => setAmount(e.target.value)} required step="0.01" />
                        </div>
                        <div className="space-y-2">
                            <Label>Type</Label>
                            <select 
                                className="flex h-10 w-full items-center justify-between rounded-md border border-slate-200 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-950 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-800 dark:bg-slate-950 dark:ring-offset-slate-950 dark:placeholder:text-slate-400 dark:focus:ring-slate-300"
                                value={type} 
                                onChange={e => setType(e.target.value as any)}
                            >
                                <option value="limit">Limit (Cap)</option>
                                <option value="goal">Goal (Target)</option>
                            </select>
                        </div>
                        <div className="space-y-2">
                            <Label>Period</Label>
                            <select 
                                className="flex h-10 w-full items-center justify-between rounded-md border border-slate-200 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-950 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-800 dark:bg-slate-950 dark:ring-offset-slate-950 dark:placeholder:text-slate-400 dark:focus:ring-slate-300"
                                value={period} 
                                onChange={e => setPeriod(e.target.value as any)}
                            >
                                <option value="daily">Daily</option>
                                <option value="weekly">Weekly</option>
                                <option value="monthly">Monthly</option>
                                <option value="annually">Annually</option>
                            </select>
                        </div>
                    </div>

                    <div className="flex items-center space-x-2">
                        <input 
                            type="checkbox" 
                            id="netDisbursements" 
                            className="h-4 w-4 rounded border-slate-300"
                            checked={netDisbursements}
                            onChange={e => setNetDisbursements(e.target.checked)}
                        />
                        <Label htmlFor="netDisbursements">Net Disbursements (Subtract funds received/rebates)</Label>
                    </div>

                    <hr />

                    {/* Filter: Categories */}
                    <div className="space-y-3">
                        <Label className="text-base">Filter by Categories (OR)</Label>
                        <div className="flex flex-wrap gap-2">
                            {categoryList.map(cat => (
                                <button
                                    key={cat}
                                    type="button"
                                    onClick={() => toggleCategory(cat)}
                                    className={`px-3 py-1 rounded-full text-xs border transition-colors ${
                                        selectedCategories.includes(cat) 
                                        ? 'bg-slate-900 text-white border-slate-900 dark:bg-slate-100 dark:text-slate-900' 
                                        : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300 dark:bg-slate-950 dark:text-slate-300 dark:border-slate-800'
                                    }`}
                                >
                                    {cat}
                                </button>
                            ))}
                        </div>
                        {selectedCategories.length === 0 && <p className="text-xs text-slate-500">No categories selected (Matches none unless Accounts also empty)</p>}
                    </div>

                    <hr />

                    {/* Filter: Accounts */}
                    <div className="space-y-3">
                        <div className="flex justify-between items-center">
                            <Label className="text-base">Filter by Account / Type (OR)</Label>
                            <Button type="button" variant="outline" size="sm" onClick={addAccountFilter}><Plus size={14} className="mr-1"/> Add Combination</Button>
                        </div>
                        
                        {accountFilters.length === 0 && (
                            <p className="text-xs text-slate-500">No account filters.</p>
                        )}
                        
                        <div className="space-y-2">
                            {accountFilters.map((filter, idx) => (
                                <div key={idx} className="flex gap-2 items-center">
                                    <Input 
                                        placeholder="Bank (e.g. UOB)" 
                                        value={filter.bank} 
                                        onChange={e => updateAccountFilter(idx, 'bank', e.target.value)}
                                        className="h-8 text-xs"
                                    />
                                    <Input 
                                        placeholder="Acc (e.g. 0750)" 
                                        value={filter.account} 
                                        onChange={e => updateAccountFilter(idx, 'account', e.target.value)}
                                        className="h-8 text-xs"
                                    />
                                    <Input 
                                        placeholder="Type (e.g. Card)" 
                                        value={filter.type} 
                                        onChange={e => updateAccountFilter(idx, 'type', e.target.value)}
                                        className="h-8 text-xs"
                                    />
                                    <Button type="button" variant="ghost" size="icon" className="h-8 w-8 text-red-500" onClick={() => removeAccountFilter(idx)}>
                                        <Trash size={14}/>
                                    </Button>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="pt-4 flex justify-end gap-2">
                        <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
                        <Button type="submit">Save Tracking Item</Button>
                    </div>
                </form>
            </div>
        </div>
    );
}
