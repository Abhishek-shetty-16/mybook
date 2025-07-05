# main.py
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Session, create_engine, select
from models import User, Book
from passlib.hash import bcrypt
from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_303_SEE_OTHER

app = FastAPI()

# Use a strong secret key in production
app.add_middleware(SessionMiddleware, secret_key="a_super_secure_and_long_secret_key")

# PostgreSQL Database setup
DATABASE_URL = "postgresql://postgres:1234@localhost:5432/mydatabase"

engine = create_engine(DATABASE_URL, echo=True)

def create_db():
    SQLModel.metadata.create_all(engine)

create_db()

# Static and template directories
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Dependency
def get_session():
    with Session(engine) as session:
        yield session

# Home redirects to login
@app.get("/", response_class=RedirectResponse)
def home():
    return RedirectResponse("/login", status_code=HTTP_303_SEE_OTHER)

# Signup
@app.get("/signup", response_class=HTMLResponse)
def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
def signup(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    existing_user = session.exec(select(User).where(User.username == username)).first()
    if existing_user:
        return templates.TemplateResponse("signup.html", {"request": request, "message": "Username already exists!"})

    hashed_password = bcrypt.hash(password)
    user = User(username=username, password=hashed_password)
    session.add(user)
    session.commit()
    return RedirectResponse("/login", status_code=HTTP_303_SEE_OTHER)

# Login
@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not bcrypt.verify(password, user.password):
        return templates.TemplateResponse("login.html", {"request": request, "message": "Invalid credentials!"})

    request.session['user'] = username
    return RedirectResponse("/dashboard", status_code=HTTP_303_SEE_OTHER)

# Logout
@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=HTTP_303_SEE_OTHER)

# Dashboard
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, session: Session = Depends(get_session)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", status_code=HTTP_303_SEE_OTHER)
    books = session.exec(select(Book).where(Book.owner == user)).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "books": books, "user": {"username": user}})

# Add Book
@app.post("/add")
def add_book(
    request: Request,
    title: str = Form(...),
    author: str = Form(...),
    isbn: str = Form(...),
    description: str = Form(""),
    session: Session = Depends(get_session)
):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", status_code=HTTP_303_SEE_OTHER)

    book = Book(title=title, author=author, isbn=isbn, description=description, owner=user)
    session.add(book)
    session.commit()
    return RedirectResponse("/dashboard", status_code=HTTP_303_SEE_OTHER)

# Delete Book
@app.get("/delete/{book_id}")
def delete_book(book_id: int, request: Request, session: Session = Depends(get_session)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", status_code=HTTP_303_SEE_OTHER)

    book = session.get(Book, book_id)
    if book and book.owner == user:
        session.delete(book)
        session.commit()
    return RedirectResponse("/dashboard", status_code=HTTP_303_SEE_OTHER)

# Update Book
@app.get("/update/{book_id}", response_class=HTMLResponse)
def update_form(book_id: int, request: Request, session: Session = Depends(get_session)):
    user = request.session.get("user")
    book = session.get(Book, book_id)
    if not book or book.owner != user:
        return RedirectResponse("/dashboard", status_code=HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("update.html", {"request": request, "book": book})

@app.post("/update/{book_id}")
def update_book(
    book_id: int,
    request: Request,
    title: str = Form(...),
    author: str = Form(...),
    isbn: str = Form(...),
    description: str = Form(""),
    session: Session = Depends(get_session)
):
    user = request.session.get("user")
    book = session.get(Book, book_id)
    if not book or book.owner != user:
        return RedirectResponse("/dashboard", status_code=HTTP_303_SEE_OTHER)

    book.title = title
    book.author = author
    book.isbn = isbn
    book.description = description
    session.add(book)
    session.commit()
    return RedirectResponse("/dashboard", status_code=HTTP_303_SEE_OTHER)
