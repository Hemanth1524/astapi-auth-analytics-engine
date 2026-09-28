import os

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-development-key-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./engine.db")
