import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Lock } from 'lucide-react';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const response = await api.post('/auth/token', formData);
      localStorage.setItem('token', response.data.access_token);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50/50 p-4">
      <div className="mb-8 text-center">
        <div className="h-12 w-12 bg-blue-600 rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-blue-600/20">
            <Lock className="text-white w-6 h-6" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Welcome Back</h1>
        <p className="text-gray-500">Sign in to your finance tracker</p>
      </div>
      
      <Card className="w-full max-w-[400px] border-gray-100 shadow-xl shadow-gray-200/50">
        <CardHeader className="space-y-1">
          <CardTitle className="text-xl">Login</CardTitle>
          <CardDescription>Enter your credentials to access your account.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input 
                id="username" 
                value={username} 
                onChange={(e) => setUsername(e.target.value)} 
                required 
                placeholder="johndoe"
                className="bg-gray-50"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input 
                id="password" 
                type="password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                required 
                placeholder="••••••••"
                className="bg-gray-50"
              />
            </div>
            {error && (
                <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg border border-red-100">
                    {error}
                </div>
            )}
            <Button className="w-full h-11 text-base shadow-lg shadow-blue-500/20" type="submit">
                Sign In
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex justify-center border-t border-gray-50 pt-6 mt-2">
            <p className="text-sm text-gray-500">
                Don't have an account? <Link to="/register" className="text-blue-600 font-medium hover:underline">Register</Link>
            </p>
        </CardFooter>
      </Card>
    </div>
  );
}
