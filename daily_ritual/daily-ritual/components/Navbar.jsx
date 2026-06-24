import { useNavigate } from 'react-router-dom';
import { useStore } from '../store/useStore';
 
export default function Navbar() {
  const navigate = useNavigate();
  const { user, logout } = useStore();
 
  async function handleLogout() {
    await logout();
    navigate('/login');
  }
 
  return (
    <nav className="bg-gray-900 border-b border-gray-800 p-4">
      <div className="max-w-4xl mx-auto flex items-center justify-between">
        <h1 className="text-xl font-bold">✦ Daily Ritual</h1>
        <div className="flex items-center gap-4">
          <span className="text-gray-400 text-sm">{user?.name}</span>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-500/20 text-red-400 rounded hover:bg-red-500/30 transition text-sm"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
 
 