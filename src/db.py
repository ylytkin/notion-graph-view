from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import db_url
from src.models import BaseModel

__all__ = [
    'engine',
    'session',
    'create_db',
]

engine = create_engine(db_url)

Session = sessionmaker(bind=engine)
session = Session()


def create_db():
    BaseModel.metadata.create_all(engine)
