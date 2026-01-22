import os
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

with engine.begin() as conn:
    result = conn.execute(
        text("UPDATE \"user\" SET dietary_preference = 'VEG' WHERE email = 'test_admin@example.com';")
    )
    print(f"Rows updated: {result.rowcount}")

    # Optional: verify
    verify = conn.execute(
        text("SELECT user_id, email, dietary_preference FROM \"user\" WHERE email = 'test_admin@example.com';")
    )
    for row in verify:
        print(dict(row._mapping))
