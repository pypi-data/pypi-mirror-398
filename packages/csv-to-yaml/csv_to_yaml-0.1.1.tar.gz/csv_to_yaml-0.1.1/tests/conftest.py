"""Pytest configuration and fixtures."""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def english_csv() -> Path:
    """Return path to English CSV fixture."""
    return FIXTURES_DIR / "english.csv"


@pytest.fixture
def korean_csv() -> Path:
    """Return path to Korean CSV fixture."""
    return FIXTURES_DIR / "korean.csv"


@pytest.fixture
def mixed_csv() -> Path:
    """Return path to mixed Korean/English CSV fixture."""
    return FIXTURES_DIR / "mixed.csv"


@pytest.fixture
def special_chars_csv() -> Path:
    """Return path to CSV with special characters fixture."""
    return FIXTURES_DIR / "special_chars.csv"


@pytest.fixture
def empty_csv() -> Path:
    """Return path to empty CSV fixture."""
    return FIXTURES_DIR / "empty.csv"


@pytest.fixture
def english_yaml() -> Path:
    """Return path to English YAML fixture."""
    return FIXTURES_DIR / "english.yaml"


@pytest.fixture
def korean_yaml() -> Path:
    """Return path to Korean YAML fixture."""
    return FIXTURES_DIR / "korean.yaml"


@pytest.fixture
def mixed_yaml() -> Path:
    """Return path to mixed Korean/English YAML fixture."""
    return FIXTURES_DIR / "mixed.yaml"


@pytest.fixture
def single_object_yaml() -> Path:
    """Return path to single object YAML fixture."""
    return FIXTURES_DIR / "single_object.yaml"


@pytest.fixture
def multiline_yaml() -> Path:
    """Return path to multiline YAML fixture."""
    return FIXTURES_DIR / "multiline.yaml"
