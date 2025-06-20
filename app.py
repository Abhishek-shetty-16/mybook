from fastapi import FastAPI,HTTPException,Depends
import uvicorn
from pydantic import BaseModel
from typing import Optional,List
from sqlmodel import Field,SQLModel,Session,create_engine,select
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request


#pydantic model,sql model
class BookBase(SQLModel):
    title:str=Field(index=True)
    author:str
    isbn:str=Field(min_length=4,max_length=5,default="0011")
    description:Optional[str]

class Book(BookBase,table=True):
    id:Optional[int]=Field(default=None,primary_key=True)

class BookUpdate(SQLModel):
    title: Optional[str]
    author: Optional[str]
    isbn: Optional[str]
    description: Optional[str]


#serialzation and validation
#class Book(BaseModel):
 #   author:str
 #   isbn:str
 #   description:str

  #  class Config:
    #    orm_mode=True

#database
#Base=declarative_base()
#class BookModel(Base):
 #   __tablename__="books"
  #  id=sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,index=True)
  #  title=sqlalchemy.Column(sqlalchemy.String,index=True)
  #  author=sqlalchemy.Column(sqlalchemy.String,index=True)
  #  description=sqlalchemy.Column(sqlalchemy.String,index=True)

sqlite_url="sqlite:///books.db"
connect_args={"check_same_thread":False}
engine=create_engine(sqlite_url,echo=True,connect_args=connect_args)

def create_db_and_table():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def on_startup():
    create_db_and_table()

@app.get("/", response_class=HTMLResponse)
def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})



@app.post("/books")
@app.post("/books", response_model=Book)
def create_book(book: Book, session: Session = Depends(get_session)):
    session.add(book)
    session.commit()
    session.refresh(book)
    return book

@app.get("/books",response_model=List[Book])
def read_books():
    with Session(engine) as session:
        books=session.exec(select(Book)).all()
        return books

@app.get("/books/{book_id}",response_model=Book)
def read_book(book_id: int,session:Session=Depends(get_session)):
    #SELECT * FROM table WHERE book.id==?
    book_item=session.get(Book,book_id)
    if not book_item:
        raise HTTPException(status_code=404,detail="Book not found")
    return book_item


@app.patch("/books/{book_id}", response_model=Book)
def update_book(book_id: int, book: BookUpdate, session: Session = Depends(get_session)):

    book_item=session.get(Book,book_id)
    if not book_item:
        raise HTTPException(status_code=404,detail="Book not found")
    book_data=book.dict(exclude_unset=True)
    for key,value in book_data.items():
        setattr(book_item,key,value)
    session.add(book_item)
    session.commit()
    session.refresh(book_item)
    return book_item

@app.delete("/books/{book_id}")
def delete_book(book_id:int,session:Session=Depends(get_session)):
    book_item=session.get(Book,book_id)
    if not book_item:
        raise HTTPException(status_code=404,detail="Book not found")
    session.delete(book_item)
    session.commit()
    return{"ok":True}

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

    