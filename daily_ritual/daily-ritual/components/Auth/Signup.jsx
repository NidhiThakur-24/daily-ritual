import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { account } from '../../services/appwrite';
import { useStore } from '../../store/useStore';
import { ID } from 'appwrite';
 
export default function Signup() {
  const navigate = useNavigate();
  const { setUser, setLoading } = useStore();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
 
  async function handleSignup(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
 
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }
 
    try {
      // Create account
      await account.create(
        ID.unique(),
        email,
        password,
        name
      );
 
      // Auto-login
      await account.createEmailPasswordSession(email, password);
      const user = await account.get();
      setUser(user);
 
      navigate('/');
    } catch (err) {
      console.error('Signup error:', err);
      setError(err.message || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }
 
  return (
    <div className="min-h-screen flex items-center justify-center bg-black">
      <div className="bg-gray-900 p-8 rounded-lg w-full max-w-md border border-gray-800">
        <h1 className="text-3xl font-bold text-white mb-2">✦ Daily Ritual</h1>
        <p className="text-gray-400 mb-6">Create your account</p>
 
        <form onSubmit={handleSignup} className="space-y-4">
          <div>
            <label className="text-gray-300 text-sm block mb-2">Name</label>
            <input
              type="text"
              placeholder="Your name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full p-3 bg-gray-800 rounded border border-gray-700 text-white placeholder-gray-500 focus:border-cyan-500 outline-none"
              required
            />
          </div>
 
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
 
          <div>
            <label className="text-gray-300 text-sm block mb-2">Confirm Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full p-3 bg-gray-800 rounded border border-gray-700 text-white placeholder-gray-500 focus:border-cyan-500 outline-none"
              required
            />
          </div>
 
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/50 rounded text-red-400 text-sm">
              {error}
            </div>
          )}
 
          <button
            type="submit"
            className="w-full bg-cyan-500 text-black font-bold p-3 rounded hover:bg-cyan-400 transition"
          >
            Create Account
          </button>
        </form>
 
        <p className="text-center text-gray-400 mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-cyan-500 hover:text-cyan-400">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}