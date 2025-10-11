# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# import os

# # via environment variable or default to a local PostgreSQL database
# SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/mydatabase")

# engine = create_engine(SQLALCHEMY_DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# # Dependency to get a DB session
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# -------------------------------------------------------------
# CRITICAL FIX: Load DATABASE_URL from environment
# This variable is already defined in your web service's Docker Compose environment.
# -------------------------------------------------------------

# Prioritize reading the full connection URL from the environment
SQLALCHEMY_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    # Fallback/Default using the exact values from your docker compose config
    "postgresql://user:password@db:5432/db_name"
)

# Setup the database engine and session
# The 'pool_pre_ping=True' setting helps manage connection health in a pool
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
