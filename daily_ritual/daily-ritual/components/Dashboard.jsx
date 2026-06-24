import { useState, useEffect } from 'react';
import { useStore } from '../store/useStore';
import WorkoutTracker from './Workout/WorkoutTracker';
import PlanGenerator from './AI/PlanGenerator';
 
export default function Dashboard() {
  const { user } = useStore();
  const [activeTab, setActiveTab] = useState('workout');
 
  if (!user) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }
 
  return (
    <div className="min-h-screen bg-black text-white pb-24">
      {/* Header */}
      <div className="bg-gradient-to-b from-gray-900 to-black p-6 border-b border-gray-800">
        <h1 className="text-3xl font-bold">✦ Daily Ritual</h1>
        <p className="text-gray-400">Welcome, {user.name}!</p>
      </div>
 
      {/* Tabs */}
      <div className="sticky top-0 bg-black/80 backdrop-blur border-b border-gray-800 p-4">
        <div className="flex gap-4 max-w-md">
          <button
            onClick={() => setActiveTab('workout')}
            className={`px-4 py-2 rounded transition ${
              activeTab === 'workout'
                ? 'bg-cyan-500 text-black'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            🧘 Workout
          </button>
          <button
            onClick={() => setActiveTab('ai')}
            className={`px-4 py-2 rounded transition ${
              activeTab === 'ai'
                ? 'bg-cyan-500 text-black'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            ✦ AI Plan
          </button>
        </div>
      </div>
 
      {/* Content */}
      <div className="max-w-2xl mx-auto p-6">
        {activeTab === 'workout' && <WorkoutTracker />}
        {activeTab === 'ai' && <PlanGenerator />}
      </div>
    </div>
  );
}
 