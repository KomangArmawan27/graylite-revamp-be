import sys
from sqlalchemy import create_engine
from app.core.config import settings, get_sqlalchemy_database_url

def check_db():
    print("Checking database connectivity...")
    if not settings.DB_HOST or not settings.DB_NAME:
        print("Error: DB_HOST or DB_NAME not set in .env")
        sys.exit(1)

    url = get_sqlalchemy_database_url(settings, settings.DB_USER, settings.DB_PASSWORD)
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            res = conn.exec_driver_sql("SELECT @@VERSION").scalar()
            print("Successfully connected to SQL Server!")
            print(f"Server version: {res}")
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_db()
