import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { account } from '../../services/appwrite';
import { useStore } from '../../store/useStore';
 
export default function Login() {
  const navigate = useNavigate();
  const { setUser, setLoading, setError, error } = useStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [localError, setLocalError] = useState('');
 
  async function handleLogin(e) {
    e.preventDefault();
    setLoading(true);
    setLocalError('');
 
    try {
      // Login with Appwrite
      const session = await account.createEmailPasswordSession(email, password);
      console.log('Session created:', session);
 
      // Get user info
      const user = await account.get();
      console.log('User fetched:', user);
      setUser(user);
 
      navigate('/');
    } catch (err) {
      console.error('Login error:', err);
      setLocalError(err.message || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }
 
  return (
    <div className="min-h-screen flex items-center justify-center bg-black">
      <div className="bg-gray-900 p-8 rounded-lg w-full max-w-md border border-gray-800">
        <h1 className="text-3xl font-bold text-white mb-2">✦ Daily Ritual</h1>
        <p className="text-gray-400 mb-6">Sign in to your account</p>
 
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="text-gray-300 text-sm block mb-2">Email</label>
            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full p-3 bg-gray-800 rounded border border-gray-700 text-white placeholder-gray-500 focus:border-cyan-500 outline-none"
              required
            />
          </div>
 
          <div>
            <label className="text-gray-300 text-sm block mb-2">Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-3 bg-gray-800 rounded border border-gray-700 text-white placeholder-gray-500 focus:border-cyan-500 outline-none"
              required
            />
          </div>
 
          {localError && (
            <div className="p-3 bg-red-500/10 border border-red-500/50 rounded text-red-400 text-sm">
              {localError}
            </div>
          )}
 
          <button
            type="submit"
            className="w-full bg-cyan-500 text-black font-bold p-3 rounded hover:bg-cyan-400 transition"
          >
            Sign In
          </button>
        </form>
 
        <p className="text-center text-gray-400 mt-6">
          Don't have an account?{' '}
          <Link to="/signup" className="text-cyan-500 hover:text-cyan-400">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
 