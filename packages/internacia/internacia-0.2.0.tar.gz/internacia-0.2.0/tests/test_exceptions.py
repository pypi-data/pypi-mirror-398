"""Tests for custom exceptions."""

from internacia.exceptions import (
    InternaciaError,
    DatabaseError,
    NotFoundError,
    ValidationError,
)


def test_internacia_error():
    """Test base exception."""
    error = InternaciaError("Test error")
    assert str(error) == "Test error"
    assert isinstance(error, Exception)


def test_database_error():
    """Test database error."""
    error = DatabaseError("Database connection failed")
    assert str(error) == "Database connection failed"
    assert isinstance(error, InternaciaError)


def test_not_found_error():
    """Test not found error."""
    error = NotFoundError("Country not found")
    assert str(error) == "Country not found"
    assert isinstance(error, InternaciaError)


def test_validation_error():
    """Test validation error."""
    error = ValidationError("Invalid input")
    assert str(error) == "Invalid input"
    assert isinstance(error, InternaciaError)
