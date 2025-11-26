from typing import Dict
from models import User

class TokenEconomy:
    def __init__(self):
        self.ledger: Dict[str, float] = {}

    def reward_trainer_submission(self, trainer: User, amount: float = 1.0):
        trainer.credit(amount)
        self.ledger.setdefault(trainer.id, 0.0)
        self.ledger[trainer.id] += amount

    def reward_validator(self, validator: User, amount: float = 0.5):
        validator.credit(amount)
        self.ledger.setdefault(validator.id, 0.0)
        self.ledger[validator.id] += amount
