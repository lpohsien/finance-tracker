import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { X, User, Calendar, MessageCircle } from 'lucide-react';

interface UserDetail {
  id: number;
  username: string;
  telegram_id?: number | null;
  created_at: string;
}

interface UserDetailModalProps {
  onClose: () => void;
}

export function UserDetailModal({ onClose }: UserDetailModalProps) {
  const { data: user, isLoading, error } = useQuery<UserDetail>({
    queryKey: ['me'],
    queryFn: async () => {
      const res = await api.get('/api/auth/me');
      return res.data;
    }
  });

  const joinedDate = user?.created_at 
    ? new Date(user.created_at).toLocaleDateString('default', { month: 'long', year: 'numeric' }) 
    : '-';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/20 backdrop-blur-sm animate-in fade-in duration-200" onClick={onClose}>
      <div 
        className="bg-white dark:bg-slate-950 w-full max-w-sm rounded-[32px] shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200 border border-white/20 dark:border-slate-800 relative p-6"
        onClick={e => e.stopPropagation()}
      >
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 p-2 bg-gray-100 dark:bg-slate-800 rounded-full hover:bg-gray-200 dark:hover:bg-slate-700 transition-colors"
        >
          <X size={20} className="text-gray-500 dark:text-gray-400" />
        </button>

        <div className="flex flex-col items-center mb-6 mt-2">
            <div className="w-20 h-20 bg-blue-100 dark:bg-blue-900/50 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-400 text-2xl font-bold mb-4">
                ME
            </div>
            {isLoading ? (
                <div className="h-8 w-32 bg-gray-200 dark:bg-slate-800 animate-pulse rounded-lg mb-2"></div>
            ) : (
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white capitalize">{user?.username}</h2>
            )}
            <p className="text-sm text-gray-500 dark:text-gray-400">User Profile</p>
        </div>

        {isLoading ? (
             <div className="space-y-4">
                {[1,2,3].map(i => (
                    <div key={i} className="h-14 bg-gray-50 dark:bg-slate-900 rounded-xl animate-pulse"></div>
                ))}
             </div>
        ) : (
            <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-slate-900 rounded-xl">
                    <div className="flex items-center gap-3">
                        <User className="text-gray-400 w-5 h-5" />
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-300">User Name</span>
                    </div>
                    <span className="font-mono text-sm font-bold">{user?.username}</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-slate-900 rounded-xl">
                    <div className="flex items-center gap-3">
                         <MessageCircle className="text-gray-400 w-5 h-5" />
                         <span className="text-sm font-medium text-gray-600 dark:text-gray-300">Telegram ID</span>
                    </div>
                    <span className="font-mono text-sm font-bold">{user?.telegram_id || 'Not Linked'}</span>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-slate-900 rounded-xl">
                    <div className="flex items-center gap-3">
                        <Calendar className="text-gray-400 w-5 h-5" />
                        <span className="text-sm font-medium text-gray-600 dark:text-gray-300">Joined</span>
                    </div>
                    <span className="font-mono text-sm font-bold">{joinedDate}</span>
                </div>
            </div>
        )}
        
        {error && (
             <div className="mt-4 p-3 bg-red-50 text-red-500 text-sm rounded-xl text-center">
                 Failed to load user details
             </div>
        )}
      </div>
    </div>
  );
}
