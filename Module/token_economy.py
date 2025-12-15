"""
Token economy for rewarding contributors.
Implements RMDT token rewards for trainers and validators.
"""

from typing import Dict
from .models import User


class TokenEconomy:
    """Manages RMDT token rewards and ledger"""
    
    def __init__(self):
        self.ledger: Dict[str, float] = {}

    def reward_trainer_submission(self, trainer: User, amount: float = 1.0):
        """Reward a trainer for submitting a recipe"""
        trainer.credit(amount)
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
        validator.credit(amount)
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
        
        user.credit(amount)
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
        
        user.credit(amount)
        self.ledger.setdefault(user.id, 0.0)
        self.ledger[user.id] += amount
