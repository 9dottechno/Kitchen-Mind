def is_approved(recipe):
    """Safely check if a recipe (object or dict) is approved."""
    if hasattr(recipe, 'approved'):
        return recipe.approved
    if isinstance(recipe, dict):
        return recipe.get('approved', False)
    return False
