"""
Test script for KitchenMind API
Tests all major endpoints without pytest
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_test(name: str):
    """Print test name."""
    print(f"\n{BLUE}→ Testing: {name}{RESET}")


def print_success(msg: str):
    """Print success message."""
    print(f"  {GREEN}✓ {msg}{RESET}")


def print_error(msg: str):
    """Print error message."""
    print(f"  {RED}✗ {msg}{RESET}")


def test_health_check():
    """Test health check endpoint."""
    print_test("Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print_success("API is healthy")
            return True
        else:
            print_error(f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Connection error: {e}")
        return False


def test_create_user() -> Dict[str, Any]:
    """Test user creation."""
    print_test("Create User")
    try:
        user_data = {
            "username": "test_trainer",
            "role": "trainer"
        }
        response = requests.post(f"{BASE_URL}/users", json=user_data)
        if response.status_code == 200:
            user = response.json()
            print_success(f"User created: {user['username']}")
            return user
        else:
            print_error(f"Status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None


def test_submit_recipe(trainer: Dict[str, Any]) -> Dict[str, Any]:
    """Test recipe submission."""
    print_test("Submit Recipe")
    if not trainer:
        print_error("No trainer provided")
        return None
    
    try:
        recipe_data = {
            "title": "Test Idli Recipe",
            "servings": 4,
            "ingredients": [
                {"name": "Rice", "quantity": 300, "unit": "g"},
                {"name": "Urad Dal", "quantity": 100, "unit": "g"},
                {"name": "Water", "quantity": 350, "unit": "ml"},
                {"name": "Salt", "quantity": 5, "unit": "g"}
            ],
            "steps": [
                "Soak rice and urad dal for 4 hours",
                "Grind into smooth batter",
                "Ferment overnight",
                "Steam for 12 minutes"
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/recipes",
            json=recipe_data,
            params={"trainer_id": trainer["id"]}
        )
        
        if response.status_code == 200:
            recipe = response.json()
            print_success(f"Recipe created: {recipe['title']}")
            return recipe
        else:
            print_error(f"Status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None


def test_get_recipes() -> list:
    """Test recipe listing."""
    print_test("Get Recipes")
    try:
        response = requests.get(f"{BASE_URL}/recipes", params={"approved_only": False})
        if response.status_code == 200:
            recipes = response.json()
            print_success(f"Retrieved {len(recipes)} recipes")
            return recipes
        else:
            print_error(f"Status code: {response.status_code}")
            return []
    except Exception as e:
        print_error(f"Error: {e}")
        return []


def test_get_recipe(recipe: Dict[str, Any]):
    """Test get single recipe."""
    print_test("Get Single Recipe")
    if not recipe:
        print_error("No recipe provided")
        return False
    
    try:
        response = requests.get(f"{BASE_URL}/recipes/{recipe['id']}")
        if response.status_code == 200:
            retrieved = response.json()
            print_success(f"Retrieved recipe: {retrieved['title']}")
            return True
        else:
            print_error(f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_create_validator() -> Dict[str, Any]:
    """Test validator user creation."""
    print_test("Create Validator User")
    try:
        user_data = {
            "username": "test_validator",
            "role": "validator"
        }
        response = requests.post(f"{BASE_URL}/users", json=user_data)
        if response.status_code == 200:
            user = response.json()
            print_success(f"Validator created: {user['username']}")
            return user
        else:
            print_error(f"Status code: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None


def test_validate_recipe(validator: Dict[str, Any], recipe: Dict[str, Any]):
    """Test recipe validation."""
    print_test("Validate Recipe")
    if not validator or not recipe:
        print_error("Missing validator or recipe")
        return False
    
    try:
        validation_data = {
            "approved": True,
            "feedback": "Well-structured recipe",
            "confidence": 0.85
        }
        
        response = requests.post(
            f"{BASE_URL}/recipes/{recipe['id']}/validate",
            json=validation_data,
            params={"validator_id": validator["id"]}
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Recipe validated: {result['message']}")
            return True
        else:
            print_error(f"Status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_rate_recipe(user: Dict[str, Any], recipe: Dict[str, Any]):
    """Test recipe rating."""
    print_test("Rate Recipe")
    if not user or not recipe:
        print_error("Missing user or recipe")
        return False
    
    try:
        response = requests.post(
            f"{BASE_URL}/recipes/{recipe['id']}/rate",
            params={"user_id": user["id"], "rating": 4.5}
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Recipe rated: {result['rating']}/5")
            return True
        else:
            print_error(f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_synthesize_recipe(user: Dict[str, Any]):
    """Test recipe synthesis."""
    print_test("Synthesize Recipe")
    if not user:
        print_error("No user provided")
        return False
    
    try:
        synthesis_data = {
            "dish_name": "Idli",
            "servings": 5,
            "top_k": 5,
            "reorder": True
        }
        
        response = requests.post(
            f"{BASE_URL}/recipes/synthesize",
            json=synthesis_data,
            params={"user_id": user["id"]}
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Recipe synthesized: {result['title']}")
            return True
        else:
            print_error(f"Status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_plan_event():
    """Test event planning."""
    print_test("Plan Event")
    try:
        event_data = {
            "event_name": "Test Party",
            "guest_count": 20,
            "budget_per_person": 5.0,
            "dietary": None
        }
        
        response = requests.post(f"{BASE_URL}/events/plan", json=event_data)
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Event planned: {result['event']}")
            return True
        else:
            print_error(f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print(f"\n{BLUE}{'='*50}")
    print("KitchenMind API Test Suite")
    print(f"{'='*50}{RESET}")
    
    results = {
        "health_check": test_health_check(),
    }
    
    # Create users
    trainer = test_create_user()
    results["create_user"] = trainer is not None
    
    validator = test_create_validator()
    results["create_validator"] = validator is not None
    
    # Regular user
    user_response = requests.post(
        f"{BASE_URL}/users",
        json={"username": "test_user", "role": "user"}
    )
    regular_user = user_response.json() if user_response.status_code == 200 else None
    
    # Submit recipe
    recipe = test_submit_recipe(trainer)
    results["submit_recipe"] = recipe is not None
    
    # Get recipes
    recipes = test_get_recipes()
    results["get_recipes"] = len(recipes) > 0
    
    # Get single recipe
    if recipe:
        results["get_single_recipe"] = test_get_recipe(recipe)
    
    # Validate recipe
    if recipe and validator:
        results["validate_recipe"] = test_validate_recipe(validator, recipe)
    
    # Rate recipe
    if recipe and regular_user:
        results["rate_recipe"] = test_rate_recipe(regular_user, recipe)
    
    # Synthesize recipe
    if regular_user:
        results["synthesize_recipe"] = test_synthesize_recipe(regular_user)
    
    # Plan event
    results["plan_event"] = test_plan_event()
    
    # Summary
    print(f"\n{BLUE}{'='*50}")
    print("Test Summary")
    print(f"{'='*50}{RESET}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{GREEN}✓ PASS{RESET}" if result else f"{RED}✗ FAIL{RESET}"
        print(f"  {test_name}: {status}")
    
    print(f"\n{BLUE}Total: {passed}/{total} tests passed{RESET}\n")


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print(f"\n{RED}Tests interrupted{RESET}")
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")
