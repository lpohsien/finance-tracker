import React, { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { X, CheckCircle2 } from 'lucide-react';
import api from '../lib/api';

interface Transaction {
    id: string;
    amount: number;
    description: string;
    bank: string;
    category: string;
    timestamp: string;
    type: string;
    account: string;
    status: string;
}

interface TransactionDetailModalProps {
    transaction: Transaction;
    onClose: () => void;
    title?: string;
    headerIcon?: React.ReactNode;
    headerColorClass?: string;
    footer?: React.ReactNode;
}

export function TransactionDetailModal({ transaction: initialTransaction, onClose, title, headerIcon, headerColorClass, footer }: TransactionDetailModalProps) {
  const queryClient = useQueryClient();
  const displayTitle = title || "Transaction Details";
  const [transaction, setTransaction] = useState(initialTransaction);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState(initialTransaction);
  const [categories, setCategories] = useState<string[]>([]);
  const [transactionTypes, setTransactionTypes] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    setTransaction(initialTransaction);
    setFormData(initialTransaction);
  }, [initialTransaction]);

  useEffect(() => {
    if (isEditing && (categories.length === 0 || transactionTypes.length === 0)) {
        api.get('/api/config').then(res => {
            setCategories(res.data.categories || []);
            setTransactionTypes(res.data.transaction_types || []);
        }).catch(console.error);
    }
  }, [isEditing, categories.length, transactionTypes.length]);

  const handleEdit = () => {
      setIsEditing(true);
      setSuccess('');
      setError('');
  };

  const handleCancel = () => {
      setIsEditing(false);
      setFormData(transaction);
      setError('');
  };

  const handleSave = async () => {
      setError('');
      if (isNaN(Number(formData.amount))) {
          setError("Amount must be a number");
          return;
      }
      if (!formData.category) {
          setError("Category is required");
          return;
      }
      
      if (categories.length > 0 && !categories.includes(formData.category)) {
           setError("Category must be one of the existing ones");
           return;
      }

      if (!formData.type) {
          setError("Type is required");
          return;
      }
      
      if (transactionTypes.length > 0 && !transactionTypes.includes(formData.type)) {
           setError("Transaction type must be one of the existing ones");
           return;
      }

      setIsLoading(true);
      try {
          const res = await api.put(`/api/transactions/${transaction.id}`, {
              ...formData,
              amount: Number(formData.amount)
          });
          setTransaction(res.data);
          setSuccess("Transaction updated!");
          // Invalidate transactions query to refresh the list in the background
          queryClient.invalidateQueries({ queryKey: ['transactions'] });
          queryClient.invalidateQueries({ queryKey: ['stats'] });
          queryClient.invalidateQueries({ queryKey: ['expenses'] });
          setIsEditing(false);
      } catch (err: any) {
          setError(err.response?.data?.detail || "Failed to update");
      } finally {
          setIsLoading(false);
      }
  };

  const handleChange = (field: string, value: any) => {
      setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[100] flex items-center justify-center p-6 animate-in fade-in duration-200">
      <div className="bg-white dark:bg-slate-900 w-full max-w-sm rounded-[32px] overflow-hidden shadow-2xl animate-in zoom-in-95 duration-200">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold dark:text-white">{displayTitle}</h3>
            <button onClick={onClose} className="p-2 bg-gray-50 dark:bg-slate-800 hover:bg-gray-100 dark:hover:bg-slate-700 dark:text-gray-400 rounded-full transition-colors">
                <X size={20} />
            </button>
          </div>
          
          <div className="space-y-6">
                {title && !isEditing && (
                <div className="flex flex-col items-center justify-center py-4">
                    <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-4 ${headerColorClass || 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'}`}>
                        {headerIcon || <CheckCircle2 size={32} />}
                    </div>
                    <h4 className="text-lg font-bold text-center dark:text-white">{displayTitle}</h4>
                </div>
                )}

                {error && <div className="text-red-500 text-sm bg-red-50 p-2 rounded">{error}</div>}
                {success && <div className="text-green-500 text-sm bg-green-50 p-2 rounded">{success}</div>}

                <div className="bg-gray-50 dark:bg-slate-800/50 rounded-2xl p-4 space-y-3 border border-gray-100 dark:border-slate-800">
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Transaction ID</span>
                        <div className="flex items-center gap-2">
                             <span className="font-mono text-xs dark:text-white">{transaction.id.slice(0, 8)}...</span>
                        </div>
                    </div>

                    <div className="flex justify-between text-sm items-center cursor-pointer" onClick={!isEditing ? handleEdit : undefined}>
                        <span className="text-gray-500">Bank</span>
                        {isEditing ? (
                            <Input value={formData.bank} onChange={e => handleChange('bank', e.target.value)} className="h-7 w-40 text-sm" />
                        ) : (
                            <span className="font-medium dark:text-white hover:text-blue-500 transition-colors">{transaction.bank}</span>
                        )}
                    </div>

                    <div className="flex justify-between text-sm items-center cursor-pointer" onClick={!isEditing ? handleEdit : undefined}>
                        <span className="text-gray-500">Account</span>
                        {isEditing ? (
                            <Input value={formData.account} onChange={e => handleChange('account', e.target.value)} className="h-7 w-40 text-sm" />
                        ) : (
                            <span className="font-medium dark:text-white hover:text-blue-500 transition-colors">{transaction.account}</span>
                        )}
                    </div>

                    <div className="flex justify-between text-sm items-center cursor-pointer" onClick={!isEditing ? handleEdit : undefined}>
                        <span className="text-gray-500">Amount</span>
                        {isEditing ? (
                            <Input 
                                type="number" 
                                value={formData.amount} 
                                onChange={e => handleChange('amount', e.target.value)} 
                                className="h-7 w-40 text-right text-sm" 
                            />
                        ) : (
                            <span className={`font-bold ${transaction.amount < 0 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'} hover:text-blue-500 transition-colors`}>
                                {transaction.amount < 0 ? '-' : ''}${Math.abs(transaction.amount).toFixed(2)}
                            </span>
                        )}
                    </div>

                    <div className="flex justify-between text-sm items-center cursor-pointer" onClick={!isEditing ? handleEdit : undefined}>
                        <span className="text-gray-500">Category</span>
                        {isEditing ? (
                            <select 
                                className="h-7 w-40 rounded-md border border-input bg-background px-2 py-0.5 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                value={formData.category} 
                                onChange={e => handleChange('category', e.target.value)}
                            >
                                <option value="">Select Category</option>
                                {categories?.map(cat => (
                                    <option key={cat} value={cat}>{cat}</option>
                                ))}
                            </select>
                        ) : (
                            <span className="font-medium dark:text-white hover:text-blue-500 transition-colors">{transaction.category}</span>
                        )}
                    </div>

                    <div className="flex justify-between text-sm items-center cursor-pointer" onClick={!isEditing ? handleEdit : undefined}>
                        <span className="text-gray-500">Type</span>
                        {isEditing ? (
                            <select 
                                className="h-7 w-40 rounded-md border border-input bg-background px-2 py-0.5 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                value={formData.type} 
                                onChange={e => handleChange('type', e.target.value)}
                            >
                                <option value="">Select Type</option>
                                {transactionTypes?.map(type => (
                                    <option key={type} value={type}>{type}</option>
                                ))}
                            </select>
                        ) : (
                            <span className="font-medium dark:text-white hover:text-blue-500 transition-colors">{transaction.type}</span>
                        )}
                    </div>

                    <div className="flex justify-between text-sm items-center cursor-pointer" onClick={!isEditing ? handleEdit : undefined}>
                        <span className="text-gray-500">Date</span>
                         {isEditing ? (
                             <Input value={formData.timestamp} onChange={e => handleChange('timestamp', e.target.value)} className="h-7 w-40 text-xs text-sm" />
                        ) : (
                            <span className="font-medium dark:text-white hover:text-blue-500 transition-colors">
                                {new Date(transaction.timestamp).toLocaleDateString()} {new Date(transaction.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                            </span>
                        )}
                    </div>

                    <div className="flex flex-col gap-1 text-sm border-t border-dashed border-gray-200 dark:border-slate-700 pt-2 mt-2 cursor-pointer" onClick={!isEditing ? handleEdit : undefined}>
                        <span className="text-gray-500">Description</span>
                        {isEditing ? (
                             <Input value={formData.description} onChange={e => handleChange('description', e.target.value)} className="h-7 text-sm" />
                        ) : (
                            <span className="font-medium dark:text-white italic text-xs hover:text-blue-500 transition-colors">{transaction.description}</span>
                        )}
                    </div>
                
                    {transaction.status && (
                        <div className="flex justify-between text-sm items-center pt-2 cursor-pointer" onClick={!isEditing ? handleEdit : undefined}>
                        <span className="text-gray-500">Status</span>
                        {isEditing ? (
                             <Input value={formData.status} onChange={e => handleChange('status', e.target.value)} className="h-7 w-40 text-sm" />
                        ) : (
                            <span className={`px-2 py-0.5 rounded text-xs font-bold ${transaction.status === 'Verified' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'} hover:text-blue-500 transition-colors`}>
                                {transaction.status}
                            </span>
                        )}
                    </div>
                    )}
                </div>

                <div className="grid grid-cols-1 gap-3">
                    {isEditing ? (
                        <div className="flex gap-2">
                             <Button onClick={handleCancel} variant="outline" className="flex-1">
                                Cancel
                            </Button>
                            <Button onClick={handleSave} className="flex-1" disabled={isLoading}>
                                {isLoading ? 'Saving...' : 'Save Changes'}
                            </Button>
                        </div>
                    ) : (
                        footer || (
                            <Button onClick={onClose} className="w-full">
                                Close
                            </Button>
                        )
                    )}
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}
