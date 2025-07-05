from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    password: str = Field(max_length=255, nullable=False)

class Book(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    title: str = Field(nullable=False)
    author: str = Field(nullable=False)
    isbn: str = Field(nullable=False)
    description: str = Field(default="", nullable=False)
    owner: str = Field(nullable=False)  # ideally this should be a ForeignKey to User.id
