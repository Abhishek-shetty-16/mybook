from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password: str = Field(max_length=255)  # Increased length to avoid hash truncation

class Book(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    title: str
    author: str
    isbn: str
    description: str = ""
    owner: str  # This links the book to the username of the user
