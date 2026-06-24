import { useState } from 'react';
import { useStore } from '../../store/useStore';
 
const EXERCISES = [
  { name: 'Box Breathing', type: 'breathe', duration: '3 min', reps: '4 cycles' },
  { name: 'Cat-Cow Stretch', type: 'yoga', duration: '2 min', reps: '12 reps' },
  { name: 'Child\'s Pose', type: 'yoga', duration: '2 min', reps: 'Hold 60s × 2' },
  { name: 'Seated Spinal Twist', type: 'yoga', duration: '2 min', reps: '30s each side' },
  { name: 'Legs Up The Wall', type: 'yoga', duration: '3 min', reps: 'Hold full time' },
  { name: 'Bridge Pose', type: 'strength', duration: '3 min', reps: '3 × 10 holds' },
  { name: 'Savasana', type: 'breathe', duration: '5 min', reps: 'Full relaxation' },
];
 
export default function WorkoutTracker() {
  const { todayExercises, toggleExercise, streak, totalWorkouts } = useStore();
  const completed = Object.values(todayExercises).filter(Boolean).length;
  const progress = (completed / EXERCISES.length) * 100;
 
  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-900 p-4 rounded-lg border border-gray-800">
          <div className="text-3xl font-bold text-cyan-500">🔥 {streak}</div>
          <div className="text-gray-400 text-sm">Day streak</div>
        </div>
        <div className="bg-gray-900 p-4 rounded-lg border border-gray-800">
          <div className="text-3xl font-bold text-cyan-500">{totalWorkouts}</div>
          <div className="text-gray-400 text-sm">Total workouts</div>
        </div>
      </div>
 
      {/* Progress Ring */}
      <div className="bg-gray-900 p-6 rounded-lg border border-gray-800">
        <div className="flex items-center gap-6">
          <div className="relative w-24 h-24">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="45" fill="none" stroke="#374151" strokeWidth="8" />
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="#06B6D4"
                strokeWidth="8"
                strokeDasharray={`${progress * 2.83} 283`}
                className="transition-all duration-300"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <div className="text-2xl font-bold">{completed}/7</div>
              <div className="text-xs text-gray-400">done</div>
            </div>
          </div>
          <div>
            <h3 className="text-lg font-bold">{completed === 7 ? '🎉 Complete!' : 'Keep Going!'}</h3>
            <p className="text-gray-400 text-sm">
              {completed === 7 ? 'You crushed all exercises today!' : `${7 - completed} more to go`}
            </p>
          </div>
        </div>
      </div>
 
      {/* Exercise List */}
      <div className="space-y-2">
        <h3 className="font-bold text-lg mb-4">Today's Workout</h3>
        {EXERCISES.map((exercise, index) => (
          <div
            key={index}
            className={`p-4 rounded-lg border transition ${
              todayExercises[index]
                ? 'bg-gray-800 border-cyan-500/50 opacity-75'
                : 'bg-gray-900 border-gray-800 hover:border-gray-700'
            }`}
            onClick={() => toggleExercise(index)}
          >
            <div className="flex items-center gap-4 cursor-pointer">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                  todayExercises[index]
                    ? 'bg-cyan-500 text-black'
                    : 'bg-gray-800 text-gray-400'
                }`}
              >
                {todayExercises[index] ? '✓' : index + 1}
              </div>
              <div className="flex-1">
                <h4 className="font-bold">{exercise.name}</h4>
                <p className="text-sm text-gray-400">{exercise.duration} • {exercise.reps}</p>
              </div>
              <span className={`text-xs px-2 py-1 rounded ${
                exercise.type === 'yoga' ? 'bg-blue-500/20 text-blue-300' :
                exercise.type === 'strength' ? 'bg-red-500/20 text-red-300' :
                'bg-green-500/20 text-green-300'
              }`}>
                {exercise.type}
              </span>
            </div>
          </div>
        ))}
      </div>
 
      {completed === 7 && (
        <button className="w-full bg-cyan-500 text-black font-bold p-4 rounded-lg hover:bg-cyan-400 transition">
          ✓ Mark Today as Done
        </button>
      )}
    </div>
  );
}
 