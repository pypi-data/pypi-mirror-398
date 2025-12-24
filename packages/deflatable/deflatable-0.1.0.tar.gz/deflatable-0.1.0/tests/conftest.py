"""Pytest configuration and fixtures for Deflatable tests."""

import sqlite3
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_grocery_db():
    """
    Automatically rebuild grocery.db from grocery.sql before test session.

    This ensures:
    - Tests always use a fresh, clean database
    - grocery.db doesn't need to be committed to git
    - Test data is version-controlled as readable SQL
    """
    tests_dir = Path(__file__).parent
    sql_file = tests_dir / "grocery.sql"
    db_file = tests_dir / "grocery.db"

    # Remove existing db if present
    if db_file.exists():
        db_file.unlink()

    # Rebuild from SQL
    if sql_file.exists():
        conn = sqlite3.connect(str(db_file))
        with open(sql_file) as f:
            sql_script = f.read()
        conn.executescript(sql_script)
        conn.close()
        print(f"\n✓ Built {db_file} from {sql_file}")
    else:
        raise FileNotFoundError(
            f"Test database SQL script not found: {sql_file}\n"
            f"Cannot run tests without test data."
        )

    yield

    # Optional: Clean up after all tests
    # if db_file.exists():
    #     db_file.unlink()
