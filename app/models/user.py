from sqlalchemy.orm import Mapped, mapped_column, validates, relationship
from flask import flash
from typing import Optional, TYPE_CHECKING, List
from sqlalchemy import Integer, String, ForeignKey
from db.base import db
import re

# Prevent circular import
if TYPE_CHECKING:
    # from .bookarchive import BookArchive
    # from .book import Book
    from .userbook import UserBook

class User(db.Model):
    """Create a model class"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(30), unique=False, nullable=False)
    email: Mapped[str] = mapped_column(db.String(50), unique=True, nullable=True)
    username: Mapped[str] = mapped_column(db.String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(db.String(50), unique=False, nullable=False)
    # is_active: Mapped[bool] = mapped_column(db.Bool, unique=False, nullable=False, default=False)
    
    # Relationship to UserBook (each user has more user_books)
    user_books: Mapped[List["UserBook"]] = relationship("UserBook", back_populates="user")

    @validates('name')
    def validate_name(self, key, name):
        if len(name) > 30 or not (isinstance(name, str)) or re.match(r"\d", name):
            raise ValueError("Invalid user name!")
        return name
    
    @validates('email')
    def validate_email(self, key, email):
        if (not re.match(r"[^@]+@[^@]+\.[^@]+", email)) or len(email) > 50:
            raise ValueError("Invalid email!")
        return email
    
    @validates('username')
    def validate_username(self, key, username):
        if len(username) > 50 or not (isinstance(username, str)) or re.match(r"\d", username):
            raise ValueError("Invalid username!")
        return username
    
    @validates('password')
    def validate_password(self, key, password):
        if len(password) < 8:
            raise ValueError("Invalid password (Password length must more than or equal 8 letters and does not contain special symbol)")
        return password
    # добавлять книги в каталог,
    # редактировать сведения,
    # удалять записи,
    # отмечать статус чтения (не начата / читаю / прочитана),
    # просматривать каталог.

    def modify_infor(self, name, email):
        self.name = name
        self.email = email
        db.session.commit()

    def add_to_archive(self, book_id):
        from .book import Book
        from .userbook import UserBook

        if UserBook.query.filter((UserBook.user_id == self.id), (UserBook.book_id == book_id)).first() is not None:
            flash("This book is already in your archive!", "warning")
            return

        if Book.query.get(book_id) is None:
            raise ValueError("Book id is not invalid")
        
        new_user_book = UserBook(user_id = self.id, book_id = book_id)
        db.session.add(new_user_book)
        db.session.commit()

    def remove_from_archive(self, book_id):
        from .userbook import UserBook
        # userbook = db.session.execute(db.select(UserBook).filter(UserBook.id == userbook_id)).scalar()
        userbook = UserBook.query.filter((UserBook.user_id == self.id), (UserBook.book_id == book_id)).first()
        if userbook:
            db.session.delete(userbook)
            db.session.commit()
        else:
            raise ValueError("Book was not finded!")

    def remove_all_from_archive(self):
        for userbook in self.user_books:
            db.session.delete(userbook)
            # db.session.flush()
        db.session.commit()

    def update_reading_status(self, book_id):
        from .userbook import UserBook

        statuses = {"unread": "reading", "reading": "completed", "completed": "unread"}
        user_book = UserBook.query.filter_by(user_id = self.id, book_id = book_id).first()

        user_book.reading_status = statuses[user_book.reading_status]
        db.session.commit()

        


