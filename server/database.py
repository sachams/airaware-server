from app_config import database_host, database_name, database_password, database_username
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{database_username}:{database_password}@{database_host}:"
    f"5432/{database_name}?sslmode=disable"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
