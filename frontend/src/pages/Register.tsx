import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { UserPlus } from 'lucide-react';

export default function Register() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/auth/register', { username, password });
      // Auto login or redirect to login
      navigate('/login');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed');
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50/50 p-4">
      <div className="mb-8 text-center">
        <div className="h-12 w-12 bg-indigo-600 rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-indigo-600/20">
            <UserPlus className="text-white w-6 h-6" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Create Account</h1>
        <p className="text-gray-500">Join the finance tracker today</p>
      </div>

      <Card className="w-full max-w-[400px] border-gray-100 shadow-xl shadow-gray-200/50">
        <CardHeader className="space-y-1">
          <CardTitle className="text-xl">Register</CardTitle>
          <CardDescription>Enter your details to create an account.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleRegister} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input 
                id="username" 
                value={username} 
                onChange={(e) => setUsername(e.target.value)} 
                required 
                placeholder="Choose a username"
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
                placeholder="Choose a password"
                className="bg-gray-50"
              />
            </div>
            {error && (
                <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg border border-red-100">
                    {error}
                </div>
            )}
            <Button className="w-full h-11 text-base shadow-lg shadow-indigo-500/20 bg-indigo-600 hover:bg-indigo-700" type="submit">
                Register
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex justify-center border-t border-gray-50 pt-6 mt-2">
            <p className="text-sm text-gray-500">
                Already have an account? <Link to="/login" className="text-indigo-600 font-medium hover:underline">Login</Link>
            </p>
        </CardFooter>
      </Card>
    </div>
  );
}
