import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Tabs, TabsContent } from '@/components/ui/tabs';
import Overview from '@/components/Overview';
import Analysis from '@/components/Analysis';
import Settings from '@/components/Settings';
import Layout from '@/components/Layout';

export default function Dashboard() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("overview");

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab} onLogout={handleLogout}>
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsContent value="overview" className="space-y-4 m-0 outline-none">
          <Overview />
        </TabsContent>

        <TabsContent value="transactions" className="space-y-4 m-0 outline-none">
          <Analysis />
        </TabsContent>

        <TabsContent value="settings" className="space-y-4 m-0 outline-none">
          <Settings />
        </TabsContent>
      </Tabs>
    </Layout>
  );
}

