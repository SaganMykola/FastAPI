import psycopg2
import re
from fastapi import FastAPI, HTTPException, Path, Depends
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base
from session import get_session

app = FastAPI()

connection = psycopg2.connect(
    host='localhost',
    port='5432',
    user='root',
    password='',
    database='postgres'
)

Base = declarative_base()

@app.post("/create_table_books")
def create_table_books():
    with connection:
        with connection.cursor() as cursor:
            sql = """
            CREATE TABLE IF NOT EXISTS books (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255)
            )
            """
            cursor.execute(sql)
        connection.commit()

@app.post("/add_author_column")
def add_author_column_to_books():
    with connection:
        with connection.cursor() as cursor:
            sql = """
            ALTER TABLE  books
            ADD COLUMN author INT REFERENCES authors(id) ON DELETE CASCADE
            """
            cursor.execute(sql)
        connection.commit()

@app.post("/create_table_auther")
def create_table_books():
    with connection:
        with connection.cursor() as cursor:
            sql = """
            CREATE TABLE IF NOT EXISTS authors (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255)
            )
            """
            cursor.execute(sql)
        connection.commit()


@app.get("/")
def read_root():
    return {"Hello World"}

@app.get("/home/{text}")
def home(text: str):
    count = 0
    numbers = []

    numbers = re.findall(r'\+38(?: |)0(?: |)(?:95|66|99)(?: |)\d{3}(?: |-|)\d{2}(?: |-|)\d{2}', text)

    count = len(numbers)

    return {
        "numbers": numbers,
        "count": count
    }


class Author(BaseModel):
    name: str

class Book(BaseModel):
    name: str
    author: int

@app.post("/delete_author_from_db")
def delete_author_from_db(id):
    count_books = 0
    with connection:
        with connection.cursor() as cursor:
            sql = "DELETE FROM books WHERE author=%s"
            cursor.execute(sql, id)
            count_books = cursor.rowcount

            sql = "DELETE FROM authors WHERE id=%s"
            cursor.execute(sql, id)
        connection.commit()


    return {
        "result": "ok",
        "message": f"Видалено книг: {count_books} "
    }

@app.get("/get_books_by_author_id")
def get_books_by_author_id(author):
    with connection:
        with connection.cursor() as cursor:
            sql = "SELECT id, name, author FROM books WHERE author = %s"
            cursor.execute(sql, author)
            book_rows = cursor.fetchall()



    books = []
    for row in book_rows:
        book_id = row[0]
        book_name = row[1]
        book_author = row[2]

        books.append({
            "id": book_id,
            "name": book_name,
            "author": book_author
        })

    return books


@app.post("/insert_to_book")
def insert_to_book(item: Book, item2: Author):
    try:
        with connection.cursor() as cursor:
            sql_author = "INSERT INTO authors (name) VALUES (%s) RETURNING id"
            cursor.execute(sql_author, (item2.name,))
            author_id = cursor.fetchone()[0]

        with connection.cursor() as cursor:
            sql_book = "INSERT INTO books (name, author) VALUES (%s, %s) RETURNING id"
            cursor.execute(sql_book, (item.name, author_id))

        connection.commit()

        return {
            "result": "ok",
            "message": f"Автора створено і книгу створено"
        }
    except Exception as e:
        connection.rollback()
        return {
            "result": "error",
            "message": str(e)
        }


@app.put("/update_book/{id}")
def insert_to_book(id: Annotated[int, Path(ge=0)], item: Book):
    try:
        with connection:
            with connection.cursor() as cursor:
                sql = "UPDATE books SET name = %s, author = %s WHERE id = %s"
                cursor.execute(sql, (item.name, item.author, id))
            connection.commit()

        return {
                "result": "ok",
                "message": f"Книгу {id} оновлено."
        }
    except:
        raise HTTPException(status_code=400, detail="Неправильне id")

@app.delete("/delete_book/{id}")
def delete_book(id):
    with connection:
        with connection.cursor() as cursor:
            sql = "DELETE FROM books WHERE id = %s"
            cursor.execute(sql, (id))
        connection.commit()

    return {
            "result": "ok",
            "message": f"Книгу {id} видалено."
    }

@app.post("/insert_to_author")
def insert_to_author(item: Author):
    with connection:
        with connection.cursor() as cursor:
            sql = "INSERT INTO authors (name) VALUES (%s) RETURNING id"
            cursor.execute(sql, (item.name,))
        connection.commit()

    return {
        "result": "ok",
        "message": f"Автора створено"
    }


@app.put("/update_author/{id}")
def insert_to_author(id, item: Author):
    with connection:
        with connection.cursor() as cursor:
            sql = "UPDATE authors SET name = %s WHERE id = %s"
            cursor.execute(sql, (item.name, id))
        connection.commit()

    return {
            "result": "ok",
            "message": f"Автора {id} оновлено."
    }

@app.delete("/delete_author/{id}")
def delete_author(id):
    with connection:
        with connection.cursor() as cursor:
            sql = "DELETE FROM authors WHERE id = %s"
            cursor.execute(sql, (id))
        connection.commit()

    return {
            "result": "ok",
            "message": f"Автора {id} видалено."
    }

class Authors(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(124))
    email = Column(String(124))
    country_id = Column(Integer, ForeignKey("country.id"))

    def __repr__(self):
        return self.__dict__

class Books(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(124))
    author = Column(Integer, ForeignKey("authors.id"))


    def __repr__(self):
        return self.__dict__

class Country(Base):
    __tablename__ = 'country'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(124))


class Book(BaseModel):
    name: str
    author: int

class Author(BaseModel):
    name: str
    emil: str


class CountryModel(BaseModel):
    name: str

@app.post("/create_book_orm")
async def books(book: Book, db=Depends(get_session)):
    db.add(Books(name=book.name, author=book.author))
    db.commit()

    return db.query(Books).all()

@app.post("/create_author_orm")
async def authors(author: Author, db=Depends(get_session)):
    db.add(Authors(name=author.name))
    db.commit()

    return db.query(Authors).all()

@app.get("/by_author_orm/{author}")
async def books_by_author(author: int, db=Depends(get_session)):
    books = db.query(Books).filter_by(author=author).all()
    return books