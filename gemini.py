
import json
import logging
import os
import base64
import re
from typing import Dict, Any

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logging.warning("Google GenerativeAI not available. Using mock responses.")

from pydantic import BaseModel

class WorkoutPlan(BaseModel):
    plan_name: str
    duration_weeks: int
    workouts: list

class FoodAnalysis(BaseModel):
    food_items: list
    total_calories: int
    nutritional_info: dict

# Initialize Gemini AI client
if GENAI_AVAILABLE:
    try:
        # Use the provided API key directly
        api_key = "AIzaSyAGDJZktWCgc-78xHrCp7g4a-nFLyPW6Bw"
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        GEMINI_CONFIGURED = True
        logging.info("Gemini AI configured successfully with API key")
    except Exception as e:
        GEMINI_CONFIGURED = False
        logging.error(f"Failed to configure Gemini AI: {e}")
else:
    GEMINI_CONFIGURED = False

def generate_workout_plan(fitness_level: str, goals: str, equipment: str = "none") -> Dict[str, Any]:
    """Generate a personalized workout plan using Gemini AI"""
    try:
        if GEMINI_CONFIGURED:
            prompt = f"""
            Create a personalized workout plan for someone with:
            - Fitness Level: {fitness_level}
            - Goals: {goals}
            - Available Equipment: {equipment}

            Generate a detailed 4-week workout plan including:
            - Weekly workout schedule (3-5 days per week)
            - Specific exercises with sets/reps
            - Progressive difficulty increase each week
            - Rest days and recovery advice

            Format the response as a structured workout plan with clear sections for each week.
            Make it practical and achievable for the specified fitness level.
            """

            response = model.generate_content(prompt)
            return {"success": True, "plan": response.text}
        else:
            # Mock response when Gemini is not configured
            mock_plan = f"""
# {fitness_level.title()} Workout Plan - {goals}

## Equipment: {equipment.title()}

### Week 1-2: Foundation Building
**Monday - Full Body Strength**
- Warm-up: 5-10 minutes light cardio
- Push-ups: 3 sets of 8-12 reps
- Squats: 3 sets of 12-15 reps
- Plank: 3 sets of 30-45 seconds
- Mountain climbers: 3 sets of 20 reps
- Cool-down: 5 minutes stretching

**Wednesday - Cardio & Core**
- Jumping jacks: 3 sets of 30 seconds
- Burpees: 3 sets of 5-8 reps
- Bicycle crunches: 3 sets of 20 reps
- High knees: 3 sets of 30 seconds
- Russian twists: 3 sets of 15 reps each side

**Friday - Upper Body Focus**
- Push-ups: 3 sets of 8-12 reps
- Pike push-ups: 3 sets of 6-10 reps
- Tricep dips: 3 sets of 8-12 reps
- Arm circles: 2 sets of 15 each direction
- Wall sits: 3 sets of 30-45 seconds

### Week 3-4: Progression
- Increase reps by 2-3 per exercise
- Add 15-30 seconds to hold exercises
- Include additional sets if comfortable
- Focus on form and control

### Rest & Recovery
- Take rest days between workout days
- Stay hydrated and get adequate sleep
- Listen to your body and adjust intensity as needed
"""
            return {"success": True, "plan": mock_plan}

    except Exception as e:
        logging.error(f"Failed to generate workout plan: {e}")
        return {"success": False, "error": str(e)}

def analyze_food_image(image_data: bytes) -> Dict[str, Any]:
    """Analyze food image for nutritional information using Gemini AI"""
    try:
        if GEMINI_CONFIGURED:
            # Convert image data to base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')

            prompt = """
            Analyze this food image and provide:
            1. List of food items you can identify
            2. Estimated total calories for the portion shown
            3. Approximate nutritional breakdown (protein, carbs, fats)
            4. Serving size estimation

            Be specific about portions and provide realistic calorie estimates.
            If you cannot clearly identify the food, say so.

            Format your response clearly with sections for each part.
            """

            # Create the image part for Gemini using the correct format
            image_part = {
                "mime_type": "image/jpeg",
                "data": image_b64
            }

            # Use the correct API call for the current version
            try:
                response = model.generate_content([prompt, image_part])
                if response and hasattr(response, 'text'):
                    return {"success": True, "analysis": response.text}
                else:
                    logging.error("Invalid response format from Gemini API")
                    return {"success": False, "error": "Invalid response from AI model"}
            except Exception as api_error:
                logging.error(f"Gemini API error: {api_error}")
                return {"success": False, "error": f"AI analysis failed: {str(api_error)}"}
        else:
            # Mock response when Gemini is not configured
            mock_analysis = """
**Food Analysis Results:**

**Identified Items:**
- Mixed salad with lettuce, tomatoes, and cucumbers
- Grilled chicken breast (approximately 4 oz)
- Olive oil dressing (1-2 tablespoons)

**Nutritional Estimates:**
- **Total Calories:** 350-400 calories
- **Protein:** 35-40g (from chicken)
- **Carbohydrates:** 8-12g (from vegetables)
- **Fat:** 15-20g (from dressing and chicken)

**Serving Size:** 1 medium meal portion

**Notes:** This appears to be a healthy, balanced meal with lean protein and fresh vegetables. The calorie estimate assumes a moderate amount of dressing.
"""
            return {"success": True, "analysis": mock_analysis}

    except Exception as e:
        logging.error(f"Failed to analyze food image: {e}")
        return {"success": False, "error": str(e)}

def get_workout_plan(user_context: str) -> str:
    """Get personalized workout plan using Gemini AI"""
    # Extract information from user context
    fitness_level = re.search(r'Fitness level: (\w+)', user_context).group(1)
    equipment = re.search(r'Equipment: (\w+)', user_context).group(1)
    goals = re.search(r'Goals: (.+)$', user_context).group(1)

    # Generate the workout plan
    result = generate_workout_plan(fitness_level, goals, equipment)
    return result['plan'] if result['success'] else 'Failed to generate workout plan. Please try again.'

def get_fitness_advice(question: str, user_context: str = "") -> str:
    """Get fitness advice using Gemini AI"""
    try:
        if GEMINI_CONFIGURED:
            prompt = f"""
            You are a knowledgeable fitness coach. Answer this fitness question:

            Question: {question}

            User Context: {user_context}

            Provide helpful, accurate, and practical advice. Keep the response concise but informative.
            If the question is not fitness-related, politely redirect to fitness topics.
            """

            response = model.generate_content(prompt)
            return response.text
        else:
            # Mock response when Gemini is not configured
            return f"""
Based on your question about "{question}", here are some general fitness tips:

• **Consistency is key** - Regular exercise, even in small amounts, is better than sporadic intense sessions
• **Progressive overload** - Gradually increase intensity, duration, or resistance over time
• **Recovery matters** - Allow adequate rest between workouts for muscle repair and growth
• **Nutrition support** - Proper nutrition fuels your workouts and aids recovery
• **Listen to your body** - Adjust intensity based on how you feel

For personalized advice, consider consulting with a certified fitness trainer or healthcare provider.

*Note: AI fitness advice is currently in demo mode. For full AI-powered responses, configure your Gemini API key.*
"""

    except Exception as e:
        logging.error(f"Failed to get fitness advice: {e}")
        return "I'm sorry, I'm having trouble processing your request right now. Please try again later."
