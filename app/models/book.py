from sqlalchemy.orm import Mapped, mapped_column, validates, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey
from typing import TYPE_CHECKING, List
from db.base import db
from datetime import datetime
import re

# Prevent circular import
if TYPE_CHECKING:
    # from .bookarchive import BookArchive
    from .userbook import UserBook

class Book(db.Model):
    """Create a model class"""
    __tablename__ = "books"
    # Primary Key is a special database constraint that uniquely identifies each row (record) in a table
    # UNIQUE constraint when you want to ensure that all values in a specific column (or a group of columns) are distinct from one another
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True) 
    # isbn: Mapped[str] = mapped_column(db.String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(db.String(500), unique=True, nullable=False)
    author: Mapped[str] = mapped_column(db.String(500), unique=False, nullable=False)
    category: Mapped[str] = mapped_column(db.String(500), unique=False, nullable=False)
    describe: Mapped[str] = mapped_column(db.Text, unique=True, nullable=False)
    # publisher: Mapped[str] = mapped_column(db.String(150), unique=False, nullable=False)
    # publication_date: Mapped[datetime] = mapped_column(db.DateTime, unique=False, nullable=False)
    # publication_date: Mapped[String] = mapped_column(db.String(8), unique=False, nullable=False)
    publication_year: Mapped[int] = mapped_column(db.Integer, unique=False, nullable=False)

    # Each Book has more UserBooks (many owners)
    user_books: Mapped[List["UserBook"]] = relationship("UserBook", back_populates="book")

    # названием,
    # автором,
    # годом издания,
    # жанром,
    # кратким описанием,
    # статусом чтения (не начата / читаю / прочитана).

    @validates("name")
    def validate_name(self, key, name):
        if len(name) > 500 or not isinstance(name, str):
            raise ValueError("Invalid book name")
        return name
    
    @validates("author")
    def validate_author(self, key, author):
        if len(author) > 500 or not isinstance(author, str):
            raise ValueError("Invalid book author")
        return author
    
    # @validates("isbn")
    # def validate_isbn(self, key, isbn):
    #     if len(isbn) > 50 or isinstance(isbn, str):
    #         raise ValueError("Invalid international standard book number")
    #     return isbn
    
    # @validates("publisher")
    # def validate_publisher(self, key, publisher):
    #     if len(publisher) > 120 or isinstance(publisher, str):
    #         raise ValueError("Invalid publisher publisher")
    #     return publisher
    
    # @validates("publication_date")
    # def validate_publication_date(self, key, publication_date):
    #     if re.match(r"\d{2}/\d{2}/\d{4}", publication_date):
    #         raise ValueError("Invalid book publication date")
    #     return publication_date
    
    @validates("publication_year")
    def validate_publication_year(self, key, publication_year):
        if not re.match(r"\d{4}", str(publication_year)):
            raise ValueError("Invalid book publication year")
        return publication_year
    
    @validates("category")
    def validate_category(self, key, category):
        if len(category) > 500 or not isinstance(category, str):
            raise ValueError("Invalid book category")
        return category
    
    @validates("describe")
    def validate_describe(self, key, describe):
        if not isinstance(describe, str):
            raise ValueError("Invalid book describe")
        return describe