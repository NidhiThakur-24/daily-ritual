console.log('AI Service loaded');
 
export async function generateWorkoutPlan(goal, level, days, equipment, notes = '') {
  const apiKey = import.meta.env.VITE_GEMINI_API_KEY;
  
  if (!apiKey) {
    throw new Error('GEMINI_API_KEY is not set. Check your .env.local file');
  }
 
  const prompt = `You are an elite personal trainer with 15 years of experience.
 
Create a realistic ${days}-day workout plan based on these requirements:
- Goal: ${goal}
- Experience Level: ${level}
- Days per week: ${days}
- Equipment: ${equipment}
${notes ? `- Special notes: ${notes}` : ''}
 
CRITICAL INSTRUCTIONS:
1. Return ONLY valid JSON - no markdown, no explanations, no code fences
2. Exactly ${days} days, no more, no less
3. Each day has EXACTLY 3 exercises
4. Use this exact JSON structure:
 
{
  "planName": "string (e.g., Beginner Strength Foundation)",
  "tagline": "string (max 10 words motivational)",
  "days": [
    {
      "day": "Day 1",
      "focus": "string (e.g., Upper Body Strength)",
      "duration": "20 min",
      "exercises": [
        {
          "name": "string (exercise name)",
          "sets": number,
          "reps": "string (e.g., 10-12 or 30 sec)",
          "type": "strength|yoga|cardio|breathe",
          "tip": "string (one coaching tip)"
        }
      ]
    }
  ],
  "nutritionNote": "string (specific to their goal)",
  "progressionTip": "string (what to do after 2 weeks)"
}
 
Start with { not with any explanation.`;
 
  try {
    console.log('Calling Gemini API...');
    
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{
            role: 'user',
            parts: [{ text: prompt }]
          }],
          generationConfig: {
            temperature: 0.3,  // Lower temp for deterministic JSON
            maxOutputTokens: 2500,
            topP: 0.9,
          }
        })
      }
    );
 
    const data = await response.json();
    console.log('Gemini response:', data);
 
    if (data.error) {
      throw new Error(`Gemini API Error: ${data.error.message}`);
    }
 
    if (!data.candidates || !data.candidates[0]) {
      throw new Error('Invalid response from Gemini API');
    }
 
    const text = data.candidates[0].content.parts[0].text;
    console.log('Raw response (first 200 chars):', text.substring(0, 200));
 
    // Clean up markdown if present
    let cleanedText = text.trim();
    if (cleanedText.startsWith('```json')) {
      cleanedText = cleanedText.substring(7);
    }
    if (cleanedText.startsWith('```')) {
      cleanedText = cleanedText.substring(3);
    }
    if (cleanedText.endsWith('```')) {
      cleanedText = cleanedText.substring(0, cleanedText.length - 3);
    }
    cleanedText = cleanedText.trim();
 
    const plan = JSON.parse(cleanedText);
    console.log('Parsed plan:', plan);
    
    return plan;
  } catch (error) {
    console.error('AI Plan Generation Error:', error);
    throw new Error(`Failed to generate plan: ${error.message}`);
  }
}
 