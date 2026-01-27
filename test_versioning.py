#!/usr/bin/env python
"""Test script to verify recipe versioning is working correctly."""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
USER_ID = "0f5aee3b-a301-47f8-9b60-f7c256aa8f23"

def test_synthesize(dish_name, servings):
    """Synthesize a recipe and return the response."""
    url = f"{BASE_URL}/api/recipe/synthesize?user_id={USER_ID}"
    body = {
        "dish_name": dish_name,
        "servings": servings
    }
    print(f"\n[TEST] Synthesizing {dish_name} with {servings} servings...")
    try:
        response = requests.post(url, json=body, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Success")
            print(f"  Recipe ID: {result['recipe_id']}")
            print(f"  Version ID: {result['version_id']}")
            print(f"  Servings: {result['servings']}")
            return result
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"  {response.text}")
            return None
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return None

def main():
    print("=" * 70)
    print("Testing Recipe Versioning")
    print("=" * 70)
    
    time.sleep(2)  # Wait for requests to be ready
    
    # Test 1: First synthesis
    result1 = test_synthesize("Pancakes", 2)
    if not result1:
        print("\n[ERROR] Could not run Test 1")
        return
    
    recipe_id_1 = result1['recipe_id']
    version_id_1 = result1['version_id']
    
    time.sleep(2)
    
    # Test 2: Same dish, different servings (should add version, not create new recipe)
    result2 = test_synthesize("Pancakes", 3)
    if not result2:
        print("\n[ERROR] Could not run Test 2")
        return
    
    recipe_id_2 = result2['recipe_id']
    version_id_2 = result2['version_id']
    
    print("\n" + "=" * 70)
    print("VERSIONING RESULTS:")
    print("=" * 70)
    print(f"Test 1 (2 servings): recipe_id={recipe_id_1}, version_id={version_id_1}")
    print(f"Test 2 (3 servings): recipe_id={recipe_id_2}, version_id={version_id_2}")
    
    if recipe_id_1 == recipe_id_2:
        if version_id_1 != version_id_2:
            print("\n✓ SUCCESS: Same recipe_id, different version_ids (VERSIONING WORKS!)")
        else:
            print("\n✗ FAIL: Same recipe_id but same version_id (deduplication triggered incorrectly)")
    else:
        print("\n✗ FAIL: Different recipe_ids (versioning not working)")
    
    time.sleep(2)
    
    # Test 3: Duplicate (same dish, same servings - should return existing)
    result3 = test_synthesize("Pancakes", 2)
    if not result3:
        print("\n[ERROR] Could not run Test 3")
        return
    
    recipe_id_3 = result3['recipe_id']
    version_id_3 = result3['version_id']
    
    print(f"\nTest 3 (2 servings again): recipe_id={recipe_id_3}, version_id={version_id_3}")
    if recipe_id_3 == recipe_id_1 and version_id_3 == version_id_1:
        print("✓ SUCCESS: Duplicate detected and returned existing version")
    else:
        print("✗ FAIL: Duplicate created new version instead of returning existing")

if __name__ == "__main__":
    main()
