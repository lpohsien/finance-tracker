import React, { useState, useMemo, useEffect } from 'react';
import { 
  LayoutDashboard, 
  BarChart3, 
  Settings as SettingsIcon, 
  Plus, 
  Search, 
  Trash2, 
  Edit2, 
  X,
  ChevronRight,
  Filter,
  ArrowUpRight,
  ArrowDownLeft
} from 'lucide-react';

/**
 * DEFAULT DATA & SETTINGS
 */
const DEFAULT_CATEGORIES = [
  { id: '1', name: 'Food', keywords: ['food', 'lunch', 'dinner', 'breakfast', 'meal', 'coffee', 'starbucks'], color: '#3B82F6' },
  { id: '2', name: 'Transport', keywords: ['bus', 'grab', 'uber', 'taxi', 'mrt', 'petrol'], color: '#10B981' },
  { id: '3', name: 'Shopping', keywords: ['shopee', 'lazada', 'amazon', 'clothes'], color: '#F59E0B' },
  { id: '4', name: 'Bills', keywords: ['rent', 'electric', 'water', 'phone', 'wifi'], color: '#EF4444' },
  { id: '5', name: 'Others', keywords: [], color: '#6B7280' },
];

const INITIAL_TRANSACTIONS = [
  { id: 't1', amount: 12.5, category: 'Food', note: 'Chicken Rice', date: new Date().toISOString() },
  { id: 't2', amount: 5.0, category: 'Transport', note: 'Bus fare', date: new Date().toISOString() },
  { id: 't3', amount: 45.0, category: 'Shopping', note: 'New Shirt', date: new Date(Date.now() - 86400000).toISOString() },
];

// --- Utility: iOS Style Components ---

const Card = ({ children, className = "" }) => (
  <div className={`bg-white rounded-2xl p-4 shadow-sm border border-gray-100 ${className}`}>
    {children}
  </div>
);

const Button = ({ children, onClick, variant = 'primary', className = "" }) => {
  const styles = {
    primary: 'bg-blue-600 text-white active:bg-blue-700',
    secondary: 'bg-gray-100 text-gray-900 active:bg-gray-200',
    danger: 'bg-red-50 text-red-600 active:bg-red-100',
  };
  return (
    <button 
      onClick={onClick}
      className={`px-4 py-2 rounded-xl font-medium transition-all duration-200 select-none ${styles[variant]} ${className}`}
    >
      {children}
    </button>
  );
};

// --- Main App Logic ---

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [transactions, setTransactions] = useState(INITIAL_TRANSACTIONS);
  const [categories, setCategories] = useState(DEFAULT_CATEGORIES);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [budget, setBudget] = useState(1000);

  // --- Handlers ---
  const addTransaction = (t) => setTransactions([t, ...transactions]);
  const deleteTransaction = (id) => setTransactions(transactions.filter(t => t.id !== id));

  // --- Render Sections ---
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans pb-24 max-w-md mx-auto relative shadow-2xl overflow-hidden border-x border-gray-200">
      {/* Top Header */}
      <header className="px-6 pt-12 pb-4 bg-white/80 backdrop-blur-md sticky top-0 z-10 border-b border-gray-100">
        <div className="flex justify-between items-end">
          <div>
            <p className="text-gray-500 text-sm font-medium uppercase tracking-wider">January 2024</p>
            <h1 className="text-3xl font-bold">Finance</h1>
          </div>
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold">
            LP
          </div>
        </div>
      </header>

      <main className="px-4 pt-4 space-y-6">
        {activeTab === 'overview' && (
          <Overview transactions={transactions} categories={categories} budget={budget} />
        )}
        {activeTab === 'analysis' && (
          <Analysis transactions={transactions} onDelete={deleteTransaction} />
        )}
        {activeTab === 'settings' && (
          <Settings categories={categories} setCategories={setCategories} budget={budget} setBudget={setBudget} />
        )}
      </main>

      {/* Floating Add Button */}
      <button 
        onClick={() => setIsModalOpen(true)}
        className="fixed bottom-24 right-8 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg shadow-blue-200 flex items-center justify-center active:scale-95 transition-transform z-20"
      >
        <Plus size={32} />
      </button>

      {/* Bottom Tab Bar */}
      <nav className="fixed bottom-0 left-0 right-0 max-w-md mx-auto bg-white/90 backdrop-blur-xl border-t border-gray-200 flex justify-around py-3 px-4 z-10">
        <TabItem icon={<LayoutDashboard size={22} />} label="Overview" active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} />
        <TabItem icon={<BarChart3 size={22} />} label="Analysis" active={activeTab === 'analysis'} onClick={() => setActiveTab('analysis')} />
        <TabItem icon={<SettingsIcon size={22} />} label="Settings" active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
      </nav>

      {/* Quick Entry Modal */}
      {isModalOpen && (
        <QuickEntryModal 
          onClose={() => setIsModalOpen(false)} 
          categories={categories} 
          onAdd={addTransaction}
        />
      )}
    </div>
  );
}

// --- Component: Tab Item ---
function TabItem({ icon, label, active, onClick }) {
  return (
    <button 
      onClick={onClick}
      className={`flex flex-col items-center space-y-1 transition-colors ${active ? 'text-blue-600' : 'text-gray-400'}`}
    >
      {icon}
      <span className="text-[10px] font-medium">{label}</span>
    </button>
  );
}

// --- Section: Overview ---
function Overview({ transactions, categories, budget }) {
  const totalSpent = transactions.reduce((acc, t) => acc + t.amount, 0);
  const remaining = budget - totalSpent;

  // Simple SVG Pie Chart Logic
  const data = categories.map(cat => ({
    name: cat.name,
    value: transactions.filter(t => t.category === cat.name).reduce((a, b) => a + b.amount, 0),
    color: cat.color
  })).filter(d => d.value > 0);

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">
      <Card className="bg-gradient-to-br from-blue-600 to-blue-700 text-white border-none shadow-blue-200 shadow-xl">
        <p className="opacity-80 text-sm">Remaining Budget</p>
        <h2 className="text-3xl font-bold mt-1">${remaining.toFixed(2)}</h2>
        <div className="mt-6 h-2 bg-white/20 rounded-full overflow-hidden">
          <div 
            className="h-full bg-white transition-all duration-1000" 
            style={{ width: `${Math.min((totalSpent / budget) * 100, 100)}%` }}
          />
        </div>
        <div className="flex justify-between mt-2 text-xs opacity-80">
          <span>Spent: ${totalSpent.toFixed(2)}</span>
          <span>Budget: ${budget}</span>
        </div>
      </Card>

      <div className="grid grid-cols-2 gap-4">
        <Card className="flex flex-col items-center">
          <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-600 mb-2">
            <ArrowDownLeft size={16} />
          </div>
          <p className="text-xs text-gray-500">Income</p>
          <p className="font-bold">$0.00</p>
        </Card>
        <Card className="flex flex-col items-center">
          <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center text-red-600 mb-2">
            <ArrowUpRight size={16} />
          </div>
          <p className="text-xs text-gray-500">Expense</p>
          <p className="font-bold">${totalSpent.toFixed(2)}</p>
        </Card>
      </div>

      <Card>
        <h3 className="font-bold mb-4">Expenditure Breakdown</h3>
        <div className="flex items-center justify-between">
          <div className="w-32 h-32 relative">
             <SimplePieChart data={data} />
          </div>
          <div className="flex-1 ml-6 space-y-2">
            {data.map(d => (
              <div key={d.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center">
                  <div className="w-2 h-2 rounded-full mr-2" style={{ backgroundColor: d.color }} />
                  <span className="text-gray-600">{d.name}</span>
                </div>
                <span className="font-semibold">${d.value.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </div>
      </Card>

      <div>
        <div className="flex justify-between items-center mb-4 px-2">
          <h3 className="font-bold">Recent Transactions</h3>
          <button className="text-blue-600 text-sm font-medium">See All</button>
        </div>
        <div className="space-y-3">
          {transactions.slice(0, 4).map(t => (
            <div key={t.id} className="flex items-center justify-between bg-white p-3 rounded-xl shadow-sm">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-gray-50 flex items-center justify-center text-xl">
                  {t.category === 'Food' ? '🍱' : t.category === 'Transport' ? '🚌' : '🛍️'}
                </div>
                <div>
                  <p className="font-semibold text-sm">{t.note || t.category}</p>
                  <p className="text-[10px] text-gray-400">{new Date(t.date).toLocaleDateString()}</p>
                </div>
              </div>
              <p className="font-bold text-red-500">-${t.amount.toFixed(2)}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// --- Section: Analysis ---
function Analysis({ transactions, onDelete }) {
  const [searchTerm, setSearchTerm] = useState('');
  
  const filtered = transactions.filter(t => 
    t.category.toLowerCase().includes(searchTerm.toLowerCase()) || 
    (t.note && t.note.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="space-y-4 animate-in fade-in duration-300">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
        <input 
          type="text" 
          placeholder="Search transactions..." 
          className="w-full pl-10 pr-4 py-3 bg-white border border-gray-100 rounded-2xl shadow-sm focus:ring-2 focus:ring-blue-100 outline-none transition-all"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <Card className="p-0 overflow-hidden">
        <div className="divide-y divide-gray-50">
          {filtered.length === 0 ? (
            <div className="p-8 text-center text-gray-400 text-sm">No records found.</div>
          ) : (
            filtered.map(t => (
              <div key={t.id} className="p-4 flex items-center justify-between group">
                <div className="flex items-center space-x-3">
                   <div className="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center text-sm">
                    {t.category[0]}
                   </div>
                   <div>
                     <p className="font-medium text-sm">{t.note || t.category}</p>
                     <p className="text-[10px] text-gray-400">{t.category} • {new Date(t.date).toLocaleDateString()}</p>
                   </div>
                </div>
                <div className="flex items-center space-x-3">
                  <p className="font-bold text-sm">-${t.amount.toFixed(2)}</p>
                  <button 
                    onClick={() => onDelete(t.id)}
                    className="p-2 text-gray-300 hover:text-red-500 transition-colors"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
}

// --- Section: Settings ---
function Settings({ categories, setCategories, budget, setBudget }) {
  const [newCat, setNewCat] = useState('');

  const addCategory = () => {
    if (!newCat) return;
    setCategories([...categories, { id: Date.now().toString(), name: newCat, keywords: [], color: '#'+(Math.random()*0xFFFFFF<<0).toString(16) }]);
    setNewCat('');
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300 pb-10">
      <Card>
        <h3 className="font-bold mb-4">Monthly Budget</h3>
        <div className="flex items-center space-x-4">
          <input 
            type="number" 
            value={budget}
            onChange={(e) => setBudget(Number(e.target.value))}
            className="flex-1 p-3 bg-gray-50 rounded-xl font-bold text-lg"
          />
          <Button variant="secondary">Set</Button>
        </div>
      </Card>

      <div className="space-y-4">
        <h3 className="font-bold px-2">Categories & Keywords</h3>
        {categories.map(cat => (
          <Card key={cat.id} className="p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <div className="w-3 h-3 rounded-full mr-2" style={{ backgroundColor: cat.color }} />
                <span className="font-semibold text-sm">{cat.name}</span>
              </div>
              <button className="text-gray-400"><Edit2 size={14} /></button>
            </div>
            <div className="flex flex-wrap gap-1">
              {cat.keywords.map(kw => (
                <span key={kw} className="px-2 py-0.5 bg-gray-100 text-[10px] text-gray-500 rounded-md">
                  {kw}
                </span>
              ))}
              {cat.keywords.length === 0 && <span className="text-[10px] text-gray-400 italic">No keywords</span>}
            </div>
          </Card>
        ))}
        
        <div className="flex space-x-2">
          <input 
            type="text" 
            placeholder="New category..." 
            className="flex-1 p-3 bg-white border border-gray-100 rounded-xl"
            value={newCat}
            onChange={(e) => setNewCat(e.target.value)}
          />
          <Button onClick={addCategory}><Plus size={20} /></Button>
        </div>
      </div>
    </div>
  );
}

// --- Component: Quick Entry Modal (The Parser) ---
function QuickEntryModal({ onClose, categories, onAdd }) {
  const [input, setInput] = useState('');
  const [parsed, setParsed] = useState(null);

  useEffect(() => {
    // Logic similar to handle_message in the bot
    // Extract numbers and search for keywords
    const regex = /(\d+(?:\.\d+)?)/;
    const match = input.match(regex);
    
    if (match) {
      const amount = parseFloat(match[1]);
      const words = input.toLowerCase().split(/\s+/).filter(w => w !== match[1]);
      
      let detectedCategory = 'Others';
      let note = words.join(' ').trim();

      // Simple keyword matching logic from repo
      for (const cat of categories) {
        if (cat.keywords.some(kw => input.toLowerCase().includes(kw.toLowerCase()))) {
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
      onAdd({
        id: Date.now().toString(),
        ...parsed,
        date: new Date().toISOString()
      });
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-6 animate-in fade-in duration-200">
      <div className="bg-white w-full max-w-sm rounded-[32px] overflow-hidden shadow-2xl animate-in zoom-in-95 duration-200">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold">Quick Entry</h3>
            <button onClick={onClose} className="p-2 bg-gray-50 rounded-full"><X size={20} /></button>
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
              />
            </div>

            {parsed ? (
              <div className="p-4 bg-blue-50 rounded-2xl border border-blue-100 flex items-center justify-between">
                <div>
                  <p className="text-[10px] text-blue-500 font-bold uppercase">Detected</p>
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
              className="w-full py-4 text-lg shadow-blue-100 shadow-lg"
              onClick={handleSubmit}
            >
              Add Transaction
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

// --- Helper: Basic SVG Pie Chart ---
function SimplePieChart({ data }) {
  const total = data.reduce((a, b) => a + b.value, 0);
  let accumulatedAngle = 0;

  return (
    <svg viewBox="0 0 32 32" className="w-full h-full -rotate-90">
      {data.map((slice, i) => {
        const angle = (slice.value / total) * 360;
        const x1 = Math.cos((accumulatedAngle * Math.PI) / 180) * 16 + 16;
        const y1 = Math.sin((accumulatedAngle * Math.PI) / 180) * 16 + 16;
        accumulatedAngle += angle;
        const x2 = Math.cos((accumulatedAngle * Math.PI) / 180) * 16 + 16;
        const y2 = Math.sin((accumulatedAngle * Math.PI) / 180) * 16 + 16;
        const largeArcFlag = angle > 180 ? 1 : 0;

        return (
          <path
            key={i}
            d={`M 16 16 L ${x1} ${y1} A 16 16 0 ${largeArcFlag} 1 ${x2} ${y2} Z`}
            fill={slice.color}
          />
        );
      })}
      <circle cx="16" cy="16" r="10" fill="white" />
    </svg>
  );
}