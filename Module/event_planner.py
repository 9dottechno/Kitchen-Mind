"""
Event planning module for creating menus based on recipes.
"""

from typing import Dict, Any, Optional, List


class EventPlanner:
    def __init__(self, recipe_repo):
        self.recipe_repo = recipe_repo

    def plan_event(self, event_name: str, guest_count: int, budget_per_person: float, dietary: Optional[str] = None) -> Dict[str, Any]:
        print(f"[DEBUG] (EventPlanner.plan_event) called with event_name={event_name}, guest_count={guest_count}, budget_per_person={budget_per_person}, dietary={dietary}")
        candidates = self.recipe_repo.approved()
        print(f"[DEBUG] (EventPlanner.plan_event) candidates: {candidates}")
        if dietary:
            candidates = [r for r in candidates if dietary.lower() in r['title'].lower()]
            print(f"[DEBUG] (EventPlanner.plan_event) filtered candidates: {candidates}")
        selected = candidates[:5]
        print(f"[DEBUG] (EventPlanner.plan_event) selected: {selected}")
        menu = [{'title': r['title'], 'serves': r['servings']} for r in selected]
        total_cost_est = guest_count * budget_per_person
        result = {
            'event': event_name,
            'guests': guest_count,
            'budget': total_cost_est,
            'menu': menu,
            'notes': 'This is a sample plan. Replace with price/availability integrations.'
        }
        print(f"[DEBUG] (EventPlanner.plan_event) returning: {result}")
        return result
