print("[DEBUG] test_api.py loaded")
"""
Test script for KitchenMind API
Tests all endpoints of KitchenMind API (new schema)
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



def test_create_role() -> Dict[str, Any]:
    """Test role creation."""
    print_test("Create Role")
    try:
        role_data = {
            "role_id": "trainer",
            "role_name": "TRAINER",
            "description": "Trainer role"
        }
        response = requests.post(f"{BASE_URL}/roles", json=role_data)
        if response.status_code in (200, 201):
            role = response.json()
            print_success(f"Role created: {role['role_name']}")
            return role
        elif response.status_code == 409:
            # Fetch existing role if duplicate
            get_resp = requests.get(f"{BASE_URL}/roles/{role_data['role_id']}")
            if get_resp.status_code == 200:
                role = get_resp.json()
                print_success(f"Role exists: {role['role_name']}")
                return role
            print_error(f"Status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
        else:
            print_error(f"Status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None

def test_create_user() -> Dict[str, Any]:
    """Test user creation."""
    print_test("Create User")
    try:
        user_data = {
            "name": "Test Trainer",
            "email": "test_trainer@example.com",
            "login_identifier": "test_trainer",
            "password_hash": "hashedpassword",
            "auth_type": "password",
            "role_id": "trainer",
            "dietary_preference": "VEG"
        }
        response = requests.post(f"{BASE_URL}/users", json=user_data)
        if response.status_code in (200, 201):
            user = response.json()
            print_success(f"User created: {user['name']}")
            return user
        elif response.status_code == 409:
            # Fetch existing user if duplicate
            get_resp = requests.get(f"{BASE_URL}/users/by_email/{user_data['email']}")
            if get_resp.status_code == 200:
                user = get_resp.json()
                print_success(f"User exists: {user['name']}")
                return user
            print_error(f"Status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
        else:
            print_error(f"Status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None
def test_create_admin_profile(user: Dict[str, Any]) -> Dict[str, Any]:
    """Test admin profile creation."""
    print_test("Create Admin Profile")
    if not user:
        print_error("No user provided")
        return None
    try:
        admin_data = {
            "user_id": user["user_id"],
            "created_by": "system",
            "is_super_admin": True
        }
        response = requests.post(f"{BASE_URL}/admin_profiles", json=admin_data)
        if response.status_code in (200, 201):
            admin = response.json()
            print_success(f"Admin profile created: {admin['admin_id']}")
            return admin
        else:
            print_error(f"Status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None
def test_create_session(user: Dict[str, Any]) -> Dict[str, Any]:
    """Test session creation."""
    print_test("Create Session")
    if not user:
        print_error("No user provided")
        return None
    try:
        session_data = {
            "user_id": user["user_id"]
        }
        response = requests.post(f"{BASE_URL}/sessions", json=session_data)
        if response.status_code in (200, 201):
            session = response.json()
            print_success(f"Session created: {session['session_id']}")
            return session
        else:
            print_error(f"Status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None
def test_create_admin_action(admin: Dict[str, Any]) -> Dict[str, Any]:
    """Test admin action log creation."""
    print_test("Create Admin Action Log")
    if not admin:
        print_error("No admin provided")
        return None
    try:
        action_data = {
            "admin_id": admin["admin_id"],
            "action_type": "MANUAL_ADJUSTMENT",
            "target_type": "USER",
            "target_id": admin["user_id"],
            "description": "Manual adjustment for test"
        }
        response = requests.post(f"{BASE_URL}/admin_actions", json=action_data)
        if response.status_code in (200, 201):
            action = response.json()
            print_success(f"Admin action logged: {action['action_id']}")
            return action
        else:
            print_error(f"Status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None


def test_submit_recipe(trainer: Dict[str, Any]) -> Dict[str, Any]:
    """Test recipe submission."""
    print("[DEBUG] test_submit_recipe called")
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
        # Ensure validator role exists
        role_data = {
            "role_id": "validator",
            "role_name": "VALIDATOR",
            "description": "Validator role"
        }
        role_resp = requests.post(f"{BASE_URL}/roles", json=role_data)
        if role_resp.status_code not in (200, 201, 409):
            print_error(f"Failed to ensure validator role: {role_resp.text}")
            return None

        user_data = {
            "name": "Test Validator",
            "email": "test_validator@example.com",
            "login_identifier": "test_validator",
            "password_hash": "hashedpassword",
            "auth_type": "password",
            "role_id": "validator",
            "dietary_preference": "VEG"
        }
        response = requests.post(f"{BASE_URL}/users", json=user_data)
        if response.status_code in (200, 201):
            user = response.json()
            print_success(f"Validator created: {user['name']}")
            return user
        elif response.status_code == 409:
            # Fetch existing user if duplicate
            get_resp = requests.get(f"{BASE_URL}/users/by_email/{user_data['email']}")
            if get_resp.status_code == 200:
                user = get_resp.json()
                print_success(f"Validator exists: {user['name']}")
                return user
            print_error(f"Status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
        else:
            print_error(f"Status code: {response.status_code}")
            print_error(f"Response: {response.text}")
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
    """Run all tests for all endpoints."""
    print(f"\n{BLUE}{'='*50}")
    print("KitchenMind API Test Suite (Full Endpoints)")
    print(f"{'='*50}{RESET}")

    results = {
        "health_check": test_health_check(),
    }

    # Create role
    role = test_create_role()
    results["create_role"] = role is not None

    # Create user
    user = test_create_user()
    results["create_user"] = user is not None

    # Create admin profile
    admin_profile = test_create_admin_profile(user)
    results["create_admin_profile"] = admin_profile is not None

    # Create session
    session = test_create_session(user)
    results["create_session"] = session is not None

    # Create admin action log
    admin_action = test_create_admin_action(admin_profile)
    results["create_admin_action"] = admin_action is not None

    # Submit recipe (reuse test_submit_recipe)
    recipe = test_submit_recipe(user)
    results["submit_recipe"] = recipe is not None

    # Get recipes
    recipes = test_get_recipes()
    results["get_recipes"] = len(recipes) > 0

    # Get single recipe
    if recipe:
        results["get_single_recipe"] = test_get_recipe(recipe)

    # Validate recipe (reuse test_create_validator and test_validate_recipe)
    validator = test_create_validator()
    results["create_validator"] = validator is not None
    if recipe and validator:
        results["validate_recipe"] = test_validate_recipe(validator, recipe)

    # Rate recipe
    if recipe and user:
        results["rate_recipe"] = test_rate_recipe(user, recipe)

    # Synthesize recipe
    if user:
        results["synthesize_recipe"] = test_synthesize_recipe(user)

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
