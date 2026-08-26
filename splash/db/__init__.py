from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker
from splash.env import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME

DATABASE_URL = URL.create(
    'postgresql+psycopg',
    username=DB_USER,
    password=DB_PASS,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)

engine = create_engine(DATABASE_URL, future=True)
Session = sessionmaker(bind=engine, future=True)
