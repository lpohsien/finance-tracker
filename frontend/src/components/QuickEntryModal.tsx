import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { X, AlertCircle } from 'lucide-react';
import { TransactionDetailModal } from './TransactionDetailModal';

interface Category {
  id: string;
  name: string;
  keywords: string[];
  color: string;
}

interface TransactionResponse {
    id: string;
    amount: number;
    description: string;
    bank: string;
    category: string;
    timestamp: string;
    type: string;
    account: string;
    status: string;
    text_summary?: string;
}

interface QuickEntryModalProps {
  onClose: () => void;
  categories: Category[]; // We use this for client-side hint
  onAdd: (data: { amount: number; category: string; transaction_msg: string; bank_name: string; timestamp: string; remarks: string }) => Promise<any>;
  isAdding: boolean;
}

export function QuickEntryModal({ onClose, categories, onAdd, isAdding }: QuickEntryModalProps) {
  const [transactionMsg, setTransactionMsg] = useState('');
  const [remarks, setRemarks] = useState('');
  const [bankName, setBankName] = useState('UOB');
  const [timestamp, setTimestamp] = useState(() => {
    // Default to current local time, formatted for datetime-local (YYYY-MM-DDTHH:mm)
    const now = new Date();
    const tzOffset = now.getTimezoneOffset() * 60000;
    const localISOTime = (new Date(now.getTime() - tzOffset)).toISOString().slice(0, 16);
    return localISOTime;
  });

  const [parsed, setParsed] = useState<{ amount: number; category: string; } | null>(null);
  const [result, setResult] = useState<TransactionResponse | null>(null);
  const [errorDetails, setErrorDetails] = useState<string | null>(null);

  useEffect(() => {
    // Basic Client-Side Parsing for feedback
    const regex = /(\d+(?:\.\d+)?)/;
    const match = transactionMsg.match(regex);
    
    if (match) {
      const amount = parseFloat(match[1]);
      
      let detectedCategory = 'Others';
      let found = false;

      // Priority 1: Remarks
      if (remarks) {
        for (const cat of categories) {
          if (cat.keywords && cat.keywords.some(kw => remarks.toLowerCase().includes(kw.toLowerCase()))) {
            detectedCategory = cat.name;
            found = true;
            break;
          }
        }
      }

      // Priority 2: Transaction Message (if not found in remarks)
      if (!found) {
        for (const cat of categories) {
          if (cat.keywords && cat.keywords.some(kw => transactionMsg.toLowerCase().includes(kw.toLowerCase()))) {
            detectedCategory = cat.name;
            break;
          }
        }
      }

      setParsed({ amount, category: detectedCategory });

    } else {
      setParsed(null);
    }
  }, [transactionMsg, remarks, categories]);

  const handleSubmit = async () => {
    if (parsed) {
      setErrorDetails(null);
      try {
        const response = await onAdd({ 
          amount: parsed.amount, 
          category: parsed.category, 
          transaction_msg: transactionMsg, 
          bank_name: bankName, 
          timestamp: timestamp.replace('T', ' '), // Format to "YYYY-MM-DD HH:mm" for backend compatibility
          remarks: remarks 
        });
        setResult(response.data);
      } catch (e: any) {
        console.error(e);
        const msg = e.response?.data?.detail || e.message || 'An error occurred';
        setErrorDetails(msg);
      }
    }
  };

  const handleReset = () => {
      setResult(null);
      setErrorDetails(null);
      setTransactionMsg('');
      setRemarks('');
      setParsed(null);
      // Reset timestamp to current
      const now = new Date();
      const tzOffset = now.getTimezoneOffset() * 60000;
      const localISOTime = (new Date(now.getTime() - tzOffset)).toISOString().slice(0, 16);
      setTimestamp(localISOTime);
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[100] flex items-center justify-center p-6 animate-in fade-in duration-200">
      <div className="bg-white dark:bg-slate-900 w-full max-w-sm rounded-[32px] overflow-hidden shadow-2xl animate-in zoom-in-95 duration-200">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold dark:text-white">Quick Entry</h3>
            <button onClick={onClose} className="p-2 bg-gray-50 dark:bg-slate-800 hover:bg-gray-100 dark:hover:bg-slate-700 dark:text-gray-400 rounded-full transition-colors">
                <X size={20} />
            </button>
          </div>
          
          {result ? (
              <TransactionDetailModal
                  transaction={result}
                  onClose={onClose}
                  title="Transaction Added!"
                  headerColorClass="bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400"
                  footer={
                    <div className="grid grid-cols-2 gap-3 w-full">
                        <Button variant="outline" onClick={handleReset} className="w-full">
                            Add Another
                        </Button>
                        <Button onClick={onClose} className="w-full">
                            Done
                        </Button>
                    </div>
                  }
              />
          ) : (
          <div className="space-y-4">
            
            {errorDetails && (
                <div className="p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-300 rounded-xl text-sm flex gap-3 items-start animate-in zoom-in-95">
                     <AlertCircle size={18} className="shrink-0 mt-0.5" />
                     <div className="flex-1">
                         <p className="font-bold text-xs uppercase mb-1">Error Adding Transaction</p>
                         <p>{errorDetails}</p>
                     </div>
                </div>
            )}

            {/* Bank Selection */}
            <div className="space-y-1">
                 <label className="text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase">Bank</label>
                 <select 
                    className="w-full p-3 bg-gray-50 dark:bg-slate-800 rounded-xl border-none focus:ring-2 focus:ring-blue-100 dark:focus:ring-blue-900 outline-none text-sm dark:text-white"
                    value={bankName}
                    onChange={(e) => setBankName(e.target.value)}
                 >
                    <option value="UOB">UOB</option>
                 </select>
            </div>

            {/* Transaction Message */}
            <div className="space-y-1">
              <label className="text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase">Input Transaction Message</label>
              <textarea 
                autoFocus
                placeholder="e.g. A transaction of SGD 5.90 was made with your UOB Card ending 0750 on 20/01/26 at ..."
                className="w-full p-4 bg-gray-50 dark:bg-slate-800 rounded-2xl border-none focus:ring-2 focus:ring-blue-100 dark:focus:ring-blue-900 outline-none h-20 resize-none text-base dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-600"
                value={transactionMsg}
                onChange={(e) => setTransactionMsg(e.target.value)}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSubmit(); // Optional: submit on Enter?
                    }
                }}
              />
            </div>

             {/* Remarks */}
             <div className="space-y-1">
              <label className="text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase">Remarks</label>
              <input 
                type="text"
                placeholder="e.g. Afternoon coffee - Ice Latte"
                className="w-full p-3 bg-gray-50 dark:bg-slate-800 rounded-xl border-none focus:ring-2 focus:ring-blue-100 dark:focus:ring-blue-900 outline-none text-base dark:text-white"
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        handleSubmit();
                    }
                }}
              />
            </div>

            {/* Timestamp */}
            <div className="space-y-1">
                 <label className="text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase">Date & Time</label>
                 <input 
                    type="datetime-local"
                    className="w-full p-3 bg-gray-50 dark:bg-slate-800 rounded-xl border-none focus:ring-2 focus:ring-blue-100 dark:focus:ring-blue-900 outline-none text-base dark:text-white"
                    value={timestamp}
                    onChange={(e) => setTimestamp(e.target.value)}
                 />
            </div>

            {parsed ? (
              <div className="p-4 bg-blue-50 dark:bg-blue-900/30 rounded-2xl border border-blue-100 dark:border-blue-900 flex items-center justify-between">
                <div>
                  <p className="text-[10px] text-blue-500 dark:text-blue-400 font-bold uppercase">Detected</p>
                  <p className="text-sm font-semibold dark:text-blue-100">{parsed.category}</p>
                </div>
                <div className="text-right">
                  <p className="text-xl font-bold text-blue-600 dark:text-blue-300">${parsed.amount.toFixed(2)}</p>
                </div>
              </div>
            ) : (
                <div className="p-4 text-center text-gray-400 dark:text-gray-500 text-sm italic">
                Enter a message with an amount...
              </div>
            )}

            <Button 
              className="w-full py-4 text-lg shadow-blue-100 dark:shadow-blue-900/20 shadow-lg rounded-xl"
              onClick={handleSubmit}
              disabled={!parsed || isAdding}
            >
              {isAdding ? 'Adding...' : 'Add Transaction'}
            </Button>

          </div>
          )}
        </div>
      </div>
    </div>
  );
}
