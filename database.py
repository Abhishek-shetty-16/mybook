from sqlmodel import create_engine, SQLModel
from models import Book, User

sqlite_file_name = "database.db"
engine = create_engine(f"sqlite:///{sqlite_file_name}")

def create_db():
    SQLModel.metadata.create_all(engine)
