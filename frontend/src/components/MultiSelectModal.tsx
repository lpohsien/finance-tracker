import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Search, X, Check, ChevronsUpDown } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MultiSelectProps {
  title: string;
  options: string[];
  selected: string[];
  onChange: (selected: string[]) => void;
  className?: string;
}

export function MultiSelectModal({ title, options, selected, onChange, className }: MultiSelectProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');

  const sortedSelected = [...selected].sort((a, b) => a.localeCompare(b));
  const available = options
    .filter(opt => !selected.includes(opt))
    .sort((a, b) => a.localeCompare(b));

  const displaySelected = sortedSelected.filter(opt =>
    opt.toLowerCase().includes(search.toLowerCase())
  );
  
  const displayAvailable = available.filter(opt =>
    opt.toLowerCase().includes(search.toLowerCase())
  );

  const handleSelect = (option: string) => {
    onChange([...selected, option]);
  };

  const handleDeselect = (option: string) => {
    onChange(selected.filter(item => item !== option));
  };
    
  const handleClear = () => {
    onChange([]);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn("w-full justify-between h-9", className)}
        >
           <span className="truncate">
             {selected.length === 0 ? title : `${selected.length} selected`}
           </span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[700px] h-[600px] flex flex-col gap-0 p-0 overflow-hidden bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm">
        <DialogHeader className="p-4 pb-2">
            <DialogTitle>Select {title}</DialogTitle>
        </DialogHeader>
        
        <div className="px-4 pb-4">
            <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
                <input 
                    placeholder={`Search ${title}...`}
                    className="w-full pl-9 pr-4 py-2 bg-gray-100 dark:bg-slate-800 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 border-none"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </div>
        </div>

        <div className="flex-1 grid grid-cols-2 min-h-0 divide-x dark:divide-slate-800 border-t dark:border-slate-800">
             {/* NON-SELECTED / AVAILABLE */}
             <div className="flex flex-col min-h-0 bg-gray-50/30 dark:bg-slate-900/10">
                 <div className="p-2 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider bg-gray-50 dark:bg-slate-900 border-b dark:border-slate-800 flex justify-between items-center h-9">
                    <span>Available ({displayAvailable.length})</span>
                 </div>
                 <div className="flex-1 overflow-y-auto p-2 space-y-1">
                     {displayAvailable.map(opt => (
                         <div 
                             key={opt}
                             onClick={() => handleSelect(opt)}
                             className="flex items-center justify-between px-3 py-2 text-sm bg-white dark:bg-slate-950 border border-gray-100 dark:border-slate-800 rounded-md cursor-pointer hover:border-blue-400 dark:hover:border-blue-700 hover:shadow-sm transition-all group"
                         >
                            <span className="truncate">{opt}</span>
                            <Check className="h-3 w-3 text-blue-500 opacity-0 group-hover:opacity-50" />
                         </div>
                     ))}
                     {displayAvailable.length === 0 && (
                         <div className="text-sm text-gray-400 text-center py-8 italic">
                            {search ? 'No matching available options' : 'All items selected'}
                         </div>
                     )}
                 </div>
             </div>

             {/* SELECTED */}
             <div className="flex flex-col min-h-0">
                  <div className="p-2 px-3 text-xs font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wider bg-blue-50/50 dark:bg-blue-900/10 border-b dark:border-slate-800 flex justify-between items-center h-9">
                    <span>Selected ({selected.length})</span>
                    {selected.length > 0 && (
                        <span 
                            onClick={handleClear}
                            className="cursor-pointer hover:text-red-500 hover:underline text-[10px] normal-case"
                        >
                            Clear All
                        </span>
                    )}
                 </div>
                 <div className="flex-1 overflow-y-auto p-2 space-y-1">
                     {displaySelected.map(opt => (
                         <div 
                             key={opt}
                             onClick={() => handleDeselect(opt)}
                             className="flex items-center justify-between px-3 py-2 text-sm bg-blue-50 dark:bg-blue-900/20 text-blue-900 dark:text-blue-100 border border-blue-100 dark:border-blue-900 rounded-md cursor-pointer hover:bg-red-50 hover:text-red-700 hover:border-red-200 dark:hover:bg-red-900/30 dark:hover:text-red-300 transition-all group"
                         >
                            <span className="truncate font-medium">{opt}</span>
                            <X className="h-3 w-3 opacity-50 group-hover:opacity-100" />
                         </div>
                     ))}
                      {displaySelected.length === 0 && (
                         <div className="text-sm text-gray-400 text-center py-8 italic">
                            {selected.length === 0 ? 'No items selected' : 'No matches in selection'}
                         </div>
                     )}
                 </div>
             </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
