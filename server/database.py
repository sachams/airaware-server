from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app_config import database_username, database_password, database_name

# SQLALCHEMY_DATABASE_URL = f"postgresql://{database_username}:{database_password}@breathe-air-postgres.flycast:5432/{database_name}?sslmode=disable"
SQLALCHEMY_DATABASE_URL = f"postgresql://{database_username}:{database_password}@127.0.0.1:5432/{database_name}?sslmode=disable"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
