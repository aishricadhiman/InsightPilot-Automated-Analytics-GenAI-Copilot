import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 3306)),
    database=os.getenv("DB_NAME"),
)


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


def test_connection():
    """Test whether the application can connect to MySQL."""

    try:
        with engine.connect() as connection:
            print("Successfully connected to MySQL.")

    except Exception as error:
        print(f"Database connection failed: {error}")
        raise


if __name__ == "__main__":
    test_connection()