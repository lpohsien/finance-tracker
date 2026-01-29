import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { TransactionDetailModal } from '@/components/TransactionDetailModal';
import { Loader2 } from 'lucide-react';
import Layout from '@/components/Layout';

export default function TransactionDetail() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState("transactions");

    const { data: transaction, isLoading, error } = useQuery({
        queryKey: ['transaction', id],
        queryFn: async () => {
             const res = await api.get(`/api/transactions/${id}`);
             return res.data;
        },
        enabled: !!id,
        retry: false
    });

    const handleClose = () => {
        navigate('/');
    };

    const handleLogout = () => {
         localStorage.removeItem('token');
         navigate('/login');
    };

    if (isLoading) {
         return (
             <div className="flex items-center justify-center min-h-screen bg-background text-foreground">
                 <Loader2 className="h-8 w-8 animate-spin" />
             </div>
         );
    }
    
    // If error, we can still show layout but with error message
    if (error || !transaction) {
         return (
            <Layout activeTab={activeTab} onTabChange={setActiveTab} onLogout={handleLogout}>
                 <div className="flex flex-col items-center justify-center h-full gap-4 pt-20">
                     <p className="text-destructive font-medium">Transaction not found.</p>
                     <button onClick={() => navigate('/')} className="text-primary hover:underline">
                         Go to Dashboard
                     </button>
                 </div>
            </Layout>
         );
    }
    
    return (
        <Layout activeTab={activeTab} onTabChange={setActiveTab} onLogout={handleLogout}>
             {/* We can optionally render something here or just the modal */}
             <div className="p-8 text-center text-muted-foreground opacity-50">
                Viewing transaction {id}
             </div>
            <TransactionDetailModal 
                transaction={transaction} 
                onClose={handleClose} 
            />
        </Layout>
    );
}
