from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from splash.env import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME

DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, future=True)
Session = sessionmaker(bind=engine, future=True)
