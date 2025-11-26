from controller import KitchenMind
import pprint
from dataclasses import asdict

def example_run():
    km = KitchenMind()
    t = km.create_user('alice_trainer', role='trainer')
    v = km.create_user('bob_validator', role='validator')
    u = km.create_user('charlie_user', role='user')

    r1 = km.submit_recipe(
        t,
        title='Idli – Traditional South Indian Steamed Rice Cakes',
        ingredients=[
            {'name': 'Rice', 'quantity': 300, 'unit': 'g'},
            {'name': 'Urad Dal', 'quantity': 100, 'unit': 'g'},
            {'name': 'Water', 'quantity': 350, 'unit': 'ml'},
            {'name': 'Salt', 'quantity': 5, 'unit': 'g'},
        ],
        steps=[
            'Soak rice and urad dal separately for 4 hours.',
            'Grind both into a smooth batter.',
            'Let the batter ferment overnight.',
            'Add salt and steam for 12 minutes.'
        ],
        servings=4
    )

    r2 = km.submit_recipe(
        t,
        title='Rava Idli – Quick Version',
        ingredients=[
            {'name': 'Semolina', 'quantity': 200, 'unit': 'g'},
            {'name': 'Yogurt', 'quantity': 150, 'unit': 'g'},
            {'name': 'Water', 'quantity': 120, 'unit': 'ml'},
            {'name': 'Eno', 'quantity': 3, 'unit': 'g'},
        ],
        steps=[
            'Mix semolina and yogurt to make a batter.',
            'Add water gradually.',
            'Add Eno and steam the batter.'
        ],
        servings=3
    )

    km.validate_recipe(v, r1.id, approved=True, feedback='Looks authentic', confidence=0.9)
    km.validate_recipe(v, r2.id, approved=True, feedback='Quick version ok', confidence=0.8)

    try:
        synthesized = km.request_recipe(u, 'Khaman', servings=5)
        print('\n--- Synthesized Recipe (for 5) ---')
        pprint.pprint(asdict(synthesized))
    except Exception as e:
        print("Synthesis failed:", str(e))
        synthesized = None

    try:
        if synthesized:
            km.rate_recipe(u, synthesized.id, 4.5)
    except Exception:
        pass

    plan = km.event_plan('Birthday Party', guest_count=20, budget_per_person=5.0)
    print('\n--- Event Plan ---')
    pprint.pprint(plan)

    print('\n--- User Balances (RMDT) ---')
    for usr in (t,v,u):
        print(f"{usr.username} ({usr.role}): {usr.rmdt_balance} RMDT")

if __name__ == '__main__':
    example_run()
