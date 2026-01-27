import { Button } from './ui/button';
import { X, CheckCircle2, Copy } from 'lucide-react';
import React from 'react';

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

export function TransactionDetailModal({ transaction, onClose, title, headerIcon, headerColorClass, footer }: TransactionDetailModalProps) {
  const displayTitle = title || "Transaction Details";

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
                {title && (
                <div className="flex flex-col items-center justify-center py-4">
                    <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-4 ${headerColorClass || 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'}`}>
                        {headerIcon || <CheckCircle2 size={32} />}
                    </div>
                    <h4 className="text-lg font-bold text-center dark:text-white">{displayTitle}</h4>
                </div>
                )}

                <div className="bg-gray-50 dark:bg-slate-800/50 rounded-2xl p-4 space-y-3 border border-gray-100 dark:border-slate-800">
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Transaction ID</span>
                        <div className="flex items-center gap-2">
                             <span className="font-mono text-xs dark:text-white">{transaction.id.slice(0, 8)}...</span>
                        </div>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Bank</span>
                        <span className="font-medium dark:text-white">{transaction.bank}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Amount</span>
                        <span className={`font-bold ${transaction.amount < 0 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}`}>
                              {transaction.amount < 0 ? '-' : ''}${Math.abs(transaction.amount).toFixed(2)}
                        </span>
                    </div>
                        <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Category</span>
                        <span className="font-medium dark:text-white">{transaction.category}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Date</span>
                        <span className="font-medium dark:text-white">{new Date(transaction.timestamp).toLocaleDateString()} {new Date(transaction.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                    </div>
                        <div className="flex flex-col gap-1 text-sm border-t border-dashed border-gray-200 dark:border-slate-700 pt-2 mt-2">
                        <span className="text-gray-500">Description</span>
                        <span className="font-medium dark:text-white italic text-xs">{transaction.description}</span>
                    </div>
                        {/* Warning / Status */}
                        {transaction.status && (
                        <div className="flex justify-between text-sm items-center pt-2">
                        <span className="text-gray-500">Status</span>
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${transaction.status === 'Verified' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                            {transaction.status}
                        </span>
                    </div>
                    )}
                </div>

                <div className="grid grid-cols-1 gap-3">
                    {footer || (
                        <Button onClick={onClose} className="w-full">
                            Close
                        </Button>
                    )}
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}
