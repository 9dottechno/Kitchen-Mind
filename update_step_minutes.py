import os
import re
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://kitchenmind:password@localhost:5432/kitchenmind"
)

from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Checks connection before use, auto-reconnects
    pool_size=10,            # Number of connections to keep in pool
    max_overflow=20,         # Extra connections allowed above pool_size
    pool_recycle=1800        # Recycle connections every 30 min
)

def extract_minutes(instruction):
    match = re.search(r"(\d+)\s*(minute|min)s?", instruction.lower())
    if match:
        return int(match.group(1))
    return None

with engine.begin() as conn:
    steps = conn.execute(text('SELECT step_id, instruction FROM steps')).fetchall()
    updated = 0
    for row in steps:
        step_id = row.step_id
        instruction = row.instruction
        minutes = extract_minutes(instruction)
        if minutes is not None:
            conn.execute(
                text('UPDATE steps SET minutes = :minutes WHERE step_id = :step_id'),
                {"minutes": minutes, "step_id": step_id}
            )
            print(f"Updated step {step_id} with minutes={minutes}")
            updated += 1
    print(f"Total steps updated: {updated}")
