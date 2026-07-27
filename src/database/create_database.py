import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


SERVER_URL = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 3306)),
)


engine = create_engine(SERVER_URL)


def create_database():

    database_name = os.getenv("DB_NAME")

    if not database_name:
        raise ValueError("DB_NAME is missing from .env")

    with engine.connect() as connection:

        connection.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{database_name}`"
            )
        )

        connection.commit()

    print(
        f"Database '{database_name}' created successfully."
    )


if __name__ == "__main__":
    create_database()