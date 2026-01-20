import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { X } from 'lucide-react';

interface Category {
  id: string;
  name: string;
  keywords: string[];
  color: string;
}

interface QuickEntryModalProps {
  onClose: () => void;
  categories: Category[]; // We use this for client-side hint
  onAdd: (data: { amount: number; category: string; note: string }) => void;
  isAdding: boolean;
}

export function QuickEntryModal({ onClose, categories, onAdd, isAdding }: QuickEntryModalProps) {
  const [input, setInput] = useState('');
  const [parsed, setParsed] = useState<{ amount: number; category: string; note: string } | null>(null);

  useEffect(() => {
    // Basic Client-Side Parsing for feedback
    const regex = /(\d+(?:\.\d+)?)/;
    const match = input.match(regex);
    
    if (match) {
      const amount = parseFloat(match[1]);
      // Remove the amount from the string to find keywords
      const words = input.toLowerCase().replace(match[0], '').split(/\s+/).filter(w => w.length > 0);
      
      let detectedCategory = 'Others';
      const note = words.join(' ').trim();

      // Simple keyword matching
      for (const cat of categories) {
        if (cat.keywords && cat.keywords.some(kw => input.toLowerCase().includes(kw.toLowerCase()))) {
          detectedCategory = cat.name;
          break;
        }
      }

      setParsed({ amount, category: detectedCategory, note });
    } else {
      setParsed(null);
    }
  }, [input, categories]);

  const handleSubmit = () => {
    if (parsed) {
      onAdd(parsed);
    } else if (input.trim()) {
        // Fallback for manual entry without number? or just ignore
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[100] flex items-center justify-center p-6 animate-in fade-in duration-200">
      <div className="bg-white w-full max-w-sm rounded-[32px] overflow-hidden shadow-2xl animate-in zoom-in-95 duration-200">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold">Quick Entry</h3>
            <button onClick={onClose} className="p-2 bg-gray-50 rounded-full hover:bg-gray-100 transition-colors">
                <X size={20} />
            </button>
          </div>
          
          <div className="space-y-6">
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-gray-400 uppercase">Input message</label>
              <textarea 
                autoFocus
                placeholder="e.g. 15 starbucks coffee"
                className="w-full p-4 bg-gray-50 rounded-2xl border-none focus:ring-2 focus:ring-blue-100 outline-none h-24 resize-none text-lg"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSubmit();
                    }
                }}
              />
            </div>

            {parsed ? (
              <div className="p-4 bg-blue-50 rounded-2xl border border-blue-100 flex items-center justify-between">
                <div>
                  <p className="text-[10px] text-blue-500 font-bold uppercase">Detected (Estimate)</p>
                  <p className="text-sm font-semibold">{parsed.category} • {parsed.note || 'No note'}</p>
                </div>
                <div className="text-right">
                  <p className="text-xl font-bold text-blue-600">${parsed.amount.toFixed(2)}</p>
                </div>
              </div>
            ) : (
              <div className="p-4 text-center text-gray-400 text-sm italic">
                Type an amount and keyword...
              </div>
            )}

            <Button 
              className="w-full py-6 text-lg shadow-blue-100 shadow-lg rounded-xl"
              onClick={handleSubmit}
              disabled={!parsed || isAdding}
            >
              {isAdding ? 'Adding...' : 'Add Transaction'}
            </Button>

          </div>
        </div>
      </div>
    </div>
  );
}
