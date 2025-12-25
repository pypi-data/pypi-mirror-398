"""Tests for the sample module."""

import pytest

from nv_pylib_template.sample import greet


def test_greet_basic() -> None:
    """Test basic greeting."""
    assert greet("World") == "Hello, World!"


def test_greet_enthusiastic() -> None:
    """Test enthusiastic greeting."""
    assert greet("Python", enthusiastic=True) == "Hello, Python!!!"


def test_greet_empty_name() -> None:
    """Test greeting with empty name."""
    assert greet("") == "Hello, !"


@pytest.mark.parametrize(
    "name,enthusiastic,expected",
    [
        ("Alice", False, "Hello, Alice!"),
        ("Bob", True, "Hello, Bob!!!"),
        ("", False, "Hello, !"),
    ],
)
def test_greet_parametrized(name: str, enthusiastic: bool, expected: str) -> None:
    """Test greet with multiple parameter combinations."""
    assert greet(name, enthusiastic=enthusiastic) == expected
