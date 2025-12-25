"""Tests for base model classes."""

import pytest
from sqlalchemy import Column, String

from sonnerrise_core.config import DatabaseConfig
from sonnerrise_core.database import get_database
from sonnerrise_core.models import BaseModel


class TestBaseModel:
    """Tests for BaseModel class."""

    def test_model_creation(self):
        """Test creating a model that inherits from BaseModel."""

        class TestEntity(BaseModel):
            __tablename__ = "test_entities"
            name = Column(String(100), nullable=False)

        # Verify model has expected columns
        columns = {c.name for c in TestEntity.__table__.columns}
        assert "id" in columns
        assert "name" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

    def test_model_persistence(self):
        """Test persisting a model to database."""

        class Person(BaseModel):
            __tablename__ = "persons"
            name = Column(String(100), nullable=False)

        config = DatabaseConfig(plugin="sqlite", database=":memory:")
        db = get_database(config)
        db.create_tables()

        # Create and save
        with db.session() as session:
            person = Person(name="Alice")
            session.add(person)
            session.commit()
            person_id = person.id

        # Verify persistence
        with db.session() as session:
            loaded = session.query(Person).get(person_id)
            assert loaded is not None
            assert loaded.name == "Alice"
            assert loaded.created_at is not None
            assert loaded.updated_at is not None

    def test_to_dict(self):
        """Test converting model to dictionary."""

        class Item(BaseModel):
            __tablename__ = "items"
            name = Column(String(100), nullable=False)

        config = DatabaseConfig(plugin="sqlite", database=":memory:")
        db = get_database(config)
        db.create_tables()

        with db.session() as session:
            item = Item(name="Widget")
            session.add(item)
            session.commit()

            data = item.to_dict()
            assert data["id"] == item.id
            assert data["name"] == "Widget"
            assert "created_at" in data
            assert "updated_at" in data

    def test_repr(self):
        """Test string representation."""

        class Widget(BaseModel):
            __tablename__ = "widgets"
            name = Column(String(100))

        widget = Widget(name="Test")
        widget.id = 42
        assert "Widget" in repr(widget)
        assert "42" in repr(widget)
