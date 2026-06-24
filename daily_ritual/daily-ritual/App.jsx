import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { account } from './services/appwrite';
import { useStore } from './store/useStore';
import Login from './components/Auth/Login';
import Signup from './components/Auth/Signup';
import Dashboard from './components/Dashboard';
import Navbar from './components/Navbar';
 
function App() {
  const { user, setUser, isLoading, setLoading } = useStore();
 
  useEffect(() => {
    checkAuth();
  }, []);
 
  async function checkAuth() {
    setLoading(true);
    try {
      const currentUser = await account.get();
      setUser(currentUser);
      console.log('User authenticated:', currentUser);
    } catch (error) {
      console.log('Not authenticated');
      setUser(null);
    } finally {
      setLoading(false);
    }
  }
 
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <div className="text-white">Loading...</div>
      </div>
    );
  }
 
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-black text-white">
        {user && <Navbar />}
        <Routes>
          <Route path="/login" element={user ? <Navigate to="/" /> : <Login />} />
          <Route path="/signup" element={user ? <Navigate to="/" /> : <Signup />} />
          <Route path="/" element={user ? <Dashboard /> : <Navigate to="/login" />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
 
export default App;
 