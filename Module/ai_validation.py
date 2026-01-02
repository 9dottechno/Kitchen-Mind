import os
import openai

# Utility to call OpenAI for recipe validation

def ai_validate_recipe(recipe_title, ingredients, steps, api_key=None):
    """
    Use OpenAI GPT to validate a recipe. Returns (approved: bool, feedback: str, confidence: float)
    """
    if api_key is None:
        api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not set in environment or provided.")
    openai.api_key = api_key

    prompt = f"""
You are a professional chef and food safety expert. Review the following recipe for completeness, clarity, and safety. 
If the recipe is clear, complete, and safe, approve it. Otherwise, reject and provide feedback.

Recipe Title: {recipe_title}
Ingredients: {ingredients}
Steps: {steps}

Respond in JSON with keys: approved (true/false), feedback (string), confidence (0.0-1.0).
"""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are a recipe validation assistant."},
                  {"role": "user", "content": prompt}],
        max_tokens=256,
        temperature=0.2,
    )
    import json
    try:
        content = response["choices"][0]["message"]["content"]
        result = json.loads(content)
        accuracy = float(result.get("accuracy", 0.0))
        feedback = str(result.get("feedback", "No feedback provided."))
        approved = accuracy > 0.9
        if approved:
            feedback = feedback + "\nRecipe approved: accuracy greater than 90%."
        else:
            feedback = feedback + "\nRecipe rejected: accuracy 90% or less. Please address the feedback above."
        return approved, feedback, accuracy
    except Exception as e:
        return False, f"AI validation failed: {e}", 0.0
