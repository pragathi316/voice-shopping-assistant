"""
Database layer: SQLite via SQLAlchemy.

We use SQLite instead of MongoDB/Firebase to keep the free-tier deployment
footprint tiny (no external DB service to provision) while still modeling
the same collections described in the assignment: Users, Products,
ShoppingHistory, ShoppingList.
"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, create_engine, JSON
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = "sqlite:///./shopping_assistant.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    preferences = Column(JSON, default=dict)  # e.g. {"diet": "vegetarian"}

    history = relationship("ShoppingHistory", back_populates="user")
    list_items = relationship("ShoppingListItem", back_populates="user")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    category = Column(String, index=True)
    brand = Column(String)
    price = Column(Float)
    description = Column(String)
    # embedding stored as JSON list of floats (small catalog, fine for SQLite)
    embedding = Column(JSON)


class ShoppingHistory(Base):
    __tablename__ = "shopping_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), index=True)
    product = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="history")


class ShoppingListItem(Base):
    __tablename__ = "shopping_list"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), index=True)
    product = Column(String, index=True)
    quantity = Column(Integer, default=1)
    category = Column(String)

    user = relationship("User", back_populates="list_items")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
