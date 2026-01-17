from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from typing import Optional, TYPE_CHECKING
from db.base import db

if TYPE_CHECKING:
    from .user import User
    from .book import Book

class UserBook(db.Model):
    __tablename__ = "user_books"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    
    # user personal information with these columns
    reading_status: Mapped[str] = mapped_column(db.String(20), default="unread", nullable=False)
    rating: Mapped[Optional[int]] = mapped_column(db.Integer, default=0, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_books")
    book: Mapped["Book"] = relationship("Book", back_populates="user_books")
    
    # each couple (user_id, book_id) is unique
    # __table_args__ = (
    #     db.UniqueConstraint('user_id', 'book_id', name='uq_user_book'),
    # )