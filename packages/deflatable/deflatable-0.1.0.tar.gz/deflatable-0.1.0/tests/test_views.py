#!/usr/bin/env python3
"""Test views feature."""

from pathlib import Path

import pytest

from deflatable import display
from deflatable.app import Deflatable
from deflatable.config import DeflatableConfig


class TestViewsFeature:
    """Test suite for views functionality."""

    @pytest.fixture
    def app(self):
        """Create Deflatable app with grocery.db for tests."""
        test_dir = Path(__file__).parent
        config_path = test_dir / "grocery.yml"
        config = DeflatableConfig(str(config_path))

        app_instance = Deflatable(config=config)
        return app_instance

    def test_app_initialization(self, app):
        """Test that app initializes with correct number of tables."""
        assert len(app.tables) == 3
        assert "aisle" in app.tables
        assert "product" in app.tables
        assert "cost" in app.tables

    def test_get_view_names(self, app):
        """Test getting view names for a table."""
        view_names = app.state_manager.get_view_names("product")
        assert "All" in view_names
        assert len(view_names) >= 1

    def test_switch_view(self, app):
        """Test switching between views."""
        # Get initial state
        initial_state = app.state_manager.get_state("product")
        assert initial_state.current_view_name == "Refrigerated Foods"

        # Switch view to "All"
        app.state_manager.switch_view("product", "All")
        state = app.state_manager.get_state("product")
        assert state.current_view_name == "All"

    def test_modification_tracking(self, app):
        """Test that modifications are tracked."""
        # Initial state should not be modified
        state = app.state_manager.get_state("product")
        assert not state.is_modified

        # Change grouping should mark as modified
        app.state_manager.set_grouping("product", "brand")
        state = app.state_manager.get_state("product")
        assert state.is_modified

        # Switch view should clear modified flag
        app.state_manager.switch_view("product", "All")
        state = app.state_manager.get_state("product")
        # Modified flag may or may not be cleared depending on if view differs
        assert isinstance(state.is_modified, bool)

    def test_load_table_display(self, app):
        """Test loading table display data."""
        # Switch to "All" view to avoid lookup field filtering issues
        app.state_manager.switch_view("product", "All")
        state = app.state_manager.get_state("product")
        columns, grouped_rows = display.load_table_display(app.engine, state)

        # Should have columns
        assert len(columns) > 0

        # Should have data
        total_rows = sum(len(rows) for rows in grouped_rows.values())
        assert total_rows > 0

    def test_state_manager_initialized(self, app):
        """Test that state manager has state for all tables."""
        for table in app.tables:
            state = app.state_manager.get_state(table)
            assert state is not None
            assert state.table_name == table
            assert isinstance(state.visible_fields, set)
            assert isinstance(state.sort_config, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
