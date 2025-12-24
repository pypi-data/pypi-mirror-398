#!/usr/bin/env python3
"""Tests for the Deflatable database browser application."""

from pathlib import Path

import pytest

from deflatable.app import Deflatable
from deflatable.config import DeflatableConfig

# Configure pytest to handle async tests
pytestmark = pytest.mark.asyncio

# Test database path - use grocery fixtures in tests directory
TEST_DIR = Path(__file__).parent
TEST_DB = TEST_DIR / "grocery.db"
TEST_CONFIG_PATH = TEST_DIR / "grocery.yml"


def _get_config():
    """Helper to create config for tests."""
    return DeflatableConfig(str(TEST_CONFIG_PATH))


class TestDeflatable:
    """Test suite for the Deflatable App."""

    async def test_app_loads(self):
        """Test that the app loads successfully."""
        config = _get_config()
        app = Deflatable(config=config)
        async with app.run_test():
            # App should load without errors
            assert app is not None

    async def test_first_tab_default(self):
        """Test that first table tab is the default tab."""
        config = _get_config()
        app = Deflatable(config=config)
        async with app.run_test() as pilot:
            # Wait for app to mount
            await pilot.pause()

            # Check that we're on the first tab (should be aisle, cost, or product)
            from textual.widgets import TabbedContent

            tabbed_content = app.query_one(TabbedContent)
            # Just verify a tab is active - grocery.db has aisle, cost, product tables
            assert tabbed_content.active.startswith("tab-")

    async def test_switch_to_components_tab(self):
        """Test switching to product tab programmatically."""
        config = _get_config()
        app = Deflatable(config=config)
        async with app.run_test() as pilot:
            await pilot.pause()

            # Switch tabs programmatically to product table
            from textual.widgets import TabbedContent

            tabbed_content = app.query_one(TabbedContent)
            tabbed_content.active = "tab-product"
            await pilot.pause()

            assert tabbed_content.active == "tab-product"

    async def test_components_table_loads(self):
        """Test that product table loads with data."""
        config = _get_config()
        app = Deflatable(config=config)
        async with app.run_test() as pilot:
            await pilot.pause()

            # Get the product table
            from textual.widgets import DataTable

            table = app.query_one("#product-table", DataTable)

            # Should have columns
            assert len(table.columns) > 0

            # Should have rows (product data)
            assert table.row_count > 0

    async def test_grouping_select(self):
        """Test grouping button exists."""
        config = _get_config()
        app = Deflatable(config=config)
        async with app.run_test() as pilot:
            await pilot.pause()

            # Switch to product tab
            await pilot.press("2")
            await pilot.pause()

            # Find the grouping button
            from textual.widgets import Button

            group_button = app.query_one("#product-group-button", Button)
            assert group_button is not None
            assert str(group_button.label) == "Group"

    async def test_filter_button_exists(self):
        """Test that filter button exists for all tables."""
        config = _get_config()
        app = Deflatable(config=config)
        async with app.run_test() as pilot:
            await pilot.pause()

            from textual.widgets import Button

            # Check each table has a filter button
            for table in app.tables:
                filter_button = app.query_one(f"#{table}-filter-button", Button)
                assert filter_button is not None

    async def test_sort_button_exists(self):
        """Test that sort button exists for all tables."""
        config = _get_config()
        app = Deflatable(config=config)
        async with app.run_test() as pilot:
            await pilot.pause()

            from textual.widgets import Button

            # Check each table has a sort button
            for table in app.tables:
                sort_button = app.query_one(f"#{table}-sort-button", Button)
                assert sort_button is not None

    async def test_all_tables_have_tabs(self):
        """Test that all database tables have corresponding tabs."""
        config = _get_config()
        app = Deflatable(config=config)
        async with app.run_test() as pilot:
            await pilot.pause()

            # Should have 3 tables in grocery.db
            assert len(app.tables) == 3
            assert "aisle" in app.tables
            assert "cost" in app.tables
            assert "product" in app.tables

    async def test_state_manager_initialized(self):
        """Test that state manager is properly initialized."""
        config = _get_config()
        app = Deflatable(config=config)
        async with app.run_test() as pilot:
            await pilot.pause()

            # State manager should have state for each table
            for table in app.tables:
                state = app.state_manager.get_state(table)
                assert state is not None
                assert state.table_name == table
                assert isinstance(state.visible_fields, set)
                assert isinstance(state.sort_config, list)


class TestSchemaIntrospection:
    """Test schema introspection functionality."""

    def test_get_tables(self):
        """Test getting list of tables."""
        from sqlalchemy import create_engine

        from deflatable import schema

        engine = create_engine(f"sqlite:///{TEST_DB}")
        tables = schema.get_tables(engine)

        assert len(tables) > 0
        assert "aisle" in tables or "product" in tables
        engine.dispose()

    def test_get_columns(self):
        """Test getting columns for a table."""
        from sqlalchemy import create_engine

        from deflatable import schema

        engine = create_engine(f"sqlite:///{TEST_DB}")
        columns = schema.get_columns(engine, "product")

        assert len(columns) > 0
        assert all("name" in col for col in columns)
        assert all("type" in col for col in columns)
        engine.dispose()

    def test_to_title_case(self):
        """Test snake_case to Title Case conversion."""
        from deflatable import schema

        assert schema.to_title_case("system_id") == "System Id"
        assert schema.to_title_case("purchase_order") == "Purchase Order"
        assert schema.to_title_case("name") == "Name"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
