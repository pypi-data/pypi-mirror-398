#!/usr/bin/env python3
"""Test state manager view synchronization."""

from pathlib import Path

import pytest
from sqlalchemy import create_engine

from deflatable.config import DeflatableConfig
from deflatable.state import StateManager


class TestGroupingSync:
    """Test suite for state manager view synchronization."""

    @pytest.fixture
    def state_manager(self):
        """Create a state manager for tests using grocery.db."""
        test_dir = Path(__file__).parent
        config_path = test_dir / "grocery.yml"
        config = DeflatableConfig(str(config_path))

        db_path = test_dir / "grocery.db"
        engine = create_engine(f"sqlite:///{db_path}")

        manager = StateManager(engine, config=config)
        yield manager
        engine.dispose()

    def test_initial_state(self, state_manager):
        """Test initial state for product table."""
        state = state_manager.get_state("product")
        assert state.current_view_name == "Refrigerated Foods"
        # grouping is now a list (empty by default)
        assert isinstance(state.grouping, list)

    def test_set_grouping(self, state_manager):
        """Test setting grouping updates state."""
        initial_grouping = state_manager.get_state("product").grouping

        # Set grouping to a different value (as list)
        new_grouping = ["aisle_id"] if initial_grouping != ["aisle_id"] else ["brand"]
        state_manager.set_grouping("product", new_grouping)

        state = state_manager.get_state("product")
        assert state.grouping == new_grouping
        assert state.is_modified

    def test_clear_grouping(self, state_manager):
        """Test clearing grouping."""
        # First set grouping
        state_manager.set_grouping("product", ["brand"])
        state = state_manager.get_state("product")
        assert state.grouping == ["brand"]

        # Clear it
        state_manager.set_grouping("product", [])
        state = state_manager.get_state("product")
        assert state.grouping == []

    def test_grouping_marks_modified(self, state_manager):
        """Test that changing grouping marks state as modified."""
        # Change grouping
        state_manager.set_grouping("product", ["brand"])
        state = state_manager.get_state("product")
        assert state.is_modified


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
