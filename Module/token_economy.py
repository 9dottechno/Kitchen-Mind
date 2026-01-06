"""
Token economy for rewarding contributors.
Implements RMDT token rewards for trainers and validators.
"""

from typing import Dict

# Define a minimal User class for demonstration or import from your models
class User:
    def __init__(self, id: str, role: str = '', total_points: float = 0.0):
        self.id = id
        self.role = role
        self.total_points = total_points


class TokenEconomy:
    """Manages RMDT token rewards and ledger"""
    
    def __init__(self):
        self.ledger: Dict[str, float] = {}

    def reward_trainer_submission(self, trainer: User, amount: float = 1.0):
        """Reward a trainer for submitting a recipe"""
        # PATCH: Increment total_points instead of credit()
        trainer.total_points = (trainer.total_points or 0) + amount
        self.ledger.setdefault(trainer.id, 0.0)
        self.ledger[trainer.id] += amount

    def reward_validator(self, validator: User, amount: float = 0.5):
        """Reward a validator for validating a recipe.
        
        NOTE: AI validators do not receive RMDT rewards.
        """
        # AI validators do not receive RMDT rewards
        if validator.role == 'validator':
            self.ledger.setdefault(validator.id, 0.0)
            return
        
        # Only reward if not a validator (should not occur normally)
        # PATCH: Increment total_points instead of credit()
        validator.total_points = (validator.total_points or 0) + amount
        self.ledger.setdefault(validator.id, 0.0)
        self.ledger[validator.id] += amount

    def reward_user_request(self, user: User, amount: float = 0.25):
        """Reward a user for requesting a recipe synthesis.
        
        Args:
            user (User): User requesting the recipe
            amount (float): Token amount to reward
        """
        if not user:
            raise ValueError("User cannot be None")
        if amount <= 0:
            raise ValueError("Reward amount must be positive")
        
        # PATCH: Increment total_points instead of credit()
        user.total_points = (user.total_points or 0) + amount
        self.ledger.setdefault(user.id, 0.0)
        self.ledger[user.id] += amount

    def reward_user_rating(self, user: User, amount: float = 0.1):
        """Reward a user for rating a recipe.
        
        Args:
            user (User): User rating the recipe
            amount (float): Token amount to reward
        """
        if not user:
            raise ValueError("User cannot be None")
        if amount <= 0:
            raise ValueError("Reward amount must be positive")
        
        # PATCH: Increment total_points instead of credit()
        user.total_points = (user.total_points or 0) + amount
        self.ledger.setdefault(user.id, 0.0)
        self.ledger[user.id] += amount
