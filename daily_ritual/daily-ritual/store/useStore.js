import { create } from 'zustand';
import { account } from '../services/appwrite';
 
export const useStore = create((set, get) => ({
  // Auth state
  user: null,
  isLoading: false,
  error: null,
 
  // Workout state
  todayExercises: {},
  streak: 0,
  totalWorkouts: 0,
  plans: [],
 
  // Actions
  setUser: (user) => set({ user }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
 
  logout: async () => {
    try {
      await account.deleteSession('current');
      set({ user: null, todayExercises: {}, plans: [], streak: 0 });
    } catch (error) {
      console.error('Logout error:', error);
    }
  },
 
  toggleExercise: (index) => set((state) => ({
    todayExercises: {
      ...state.todayExercises,
      [index]: !state.todayExercises[index]
    }
  })),
 
  addPlan: (plan) => set((state) => ({
    plans: [plan, ...state.plans]
  })),
 
  updateStreak: (newStreak) => set({ streak: newStreak }),
  updateTotalWorkouts: (total) => set({ totalWorkouts: total }),
}));
 
 
