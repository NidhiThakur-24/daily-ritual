import { useState } from 'react';
import { generateWorkoutPlan } from '../../services/ai';
import { useStore } from '../../store/useStore';
 
export default function PlanGenerator() {
  const { addPlan } = useStore();
  const [goal, setGoal] = useState('Build Muscle');
  const [level, setLevel] = useState('Beginner');
  const [days, setDays] = useState('3');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [plan, setPlan] = useState(null);
 
  async function handleGenerate() {
    setLoading(true);
    setError('');
    setPlan(null);
 
    try {
      const generatedPlan = await generateWorkoutPlan(goal, level, days, 'bodyweight', '');
      setPlan(generatedPlan);
      addPlan(generatedPlan);
    } catch (err) {
      setError(err.message);
      console.error('Generation error:', err);
    } finally {
      setLoading(false);
    }
  }
 
  if (plan) {
    return (
      <div className="space-y-6">
        <button
          onClick={() => setPlan(null)}
          className="text-gray-400 hover:text-white transition"
        >
          ← Back
        </button>
        
        <div className="bg-gray-900 p-6 rounded-lg border border-gray-800">
          <h2 className="text-3xl font-bold mb-2">{plan.planName}</h2>
          <p className="text-gray-400 mb-6">{plan.tagline}</p>
 
          <div className="bg-gray-800 p-4 rounded mb-6">
            <p className="text-sm"><strong>Nutrition:</strong> {plan.nutritionNote}</p>
          </div>
 
          <div className="space-y-4">
            {plan.days.map((day, dayIndex) => (
              <div key={dayIndex} className="bg-gray-800 p-4 rounded">
                <h3 className="font-bold mb-2">{day.day}: {day.focus}</h3>
                {day.exercises.map((ex, exIndex) => (
                  <div key={exIndex} className="text-sm text-gray-300 ml-4">
                    • {ex.name} — {ex.sets}×{ex.reps}
                  </div>
                ))}
              </div>
            ))}
          </div>
 
          <div className="mt-6 p-4 bg-gray-800 rounded">
            <p className="text-sm"><strong>Next steps:</strong> {plan.progressionTip}</p>
          </div>
        </div>
      </div>
    );
  }
 
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Generate Your Plan</h2>
 
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-bold mb-2">Goal</label>
          <select
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            className="w-full p-3 bg-gray-800 rounded border border-gray-700 text-white"
          >
            <option>Build Muscle</option>
            <option>Lose Fat</option>
            <option>Improve Flexibility</option>
            <option>Build Endurance</option>
          </select>
        </div>
 
        <div>
          <label className="block text-sm font-bold mb-2">Level</label>
          <select
            value={level}
            onChange={(e) => setLevel(e.target.value)}
            className="w-full p-3 bg-gray-800 rounded border border-gray-700 text-white"
          >
            <option>Beginner</option>
            <option>Intermediate</option>
            <option>Advanced</option>
          </select>
        </div>
 
        <div>
          <label className="block text-sm font-bold mb-2">Days per week</label>
          <select
            value={days}
            onChange={(e) => setDays(e.target.value)}
            className="w-full p-3 bg-gray-800 rounded border border-gray-700 text-white"
          >
            <option value="3">3 days</option>
            <option value="4">4 days</option>
            <option value="5">5 days</option>
            <option value="6">6 days</option>
          </select>
        </div>
 
        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/50 rounded text-red-400 text-sm">
            {error}
          </div>
        )}
 
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="w-full bg-cyan-500 text-black font-bold p-3 rounded hover:bg-cyan-400 transition disabled:opacity-50"
        >
          {loading ? '✦ Generating...' : '✦ Generate My Plan'}
        </button>
      </div>
    </div>
  );
}
 