"""Comprehensive tests for state management."""

import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from deflatable.config import DeflatableConfig
from deflatable.state import StateManager, TableState


@pytest.fixture
def temp_db():
    """Create a temporary in-memory database."""
    engine = create_engine("sqlite:///:memory:")

    # Create test tables
    with engine.begin() as conn:
        conn.execute(
            text("""
            CREATE TABLE category (
                id INTEGER PRIMARY KEY,
                name TEXT,
                description TEXT
            )
        """)
        )
        conn.execute(
            text("""
            CREATE TABLE product (
                id INTEGER PRIMARY KEY,
                name TEXT,
                category_id INTEGER,
                price REAL,
                stock INTEGER
            )
        """)
        )

    yield engine
    engine.dispose()


@pytest.fixture
def temp_config():
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write("""database: ":memory:"
views:
  product:
    active_view: All
    views:
      All:
        visible_fields:
        - name
        - price
        - stock
        grouping: []
        sort_config: []
        filters: []
      Expensive:
        visible_fields:
        - name
        - price
        grouping: [category_id]
        sort_config:
        - - Price
          - desc
        filters:
        - - price
          - gt
          - '100'
          - AND
""")
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def grocery_config():
    """Use the existing grocery test config."""
    test_dir = Path(__file__).parent
    config_path = test_dir / "grocery.yml"
    return DeflatableConfig(str(config_path))


@pytest.fixture
def grocery_db():
    """Use the existing grocery test database."""
    test_dir = Path(__file__).parent
    db_path = test_dir / "grocery.db"
    engine = create_engine(f"sqlite:///{db_path}")
    yield engine
    engine.dispose()


class TestTableState:
    """Tests for TableState dataclass."""

    def test_create_table_state_minimal(self):
        """Test creating TableState with minimal parameters."""
        state = TableState(table_name="product")

        assert state.table_name == "product"
        assert state.grouping == []
        assert state.visible_fields == set()
        assert state.sort_config == []
        assert state.filters == []
        assert state.current_view_name == "All"
        assert not state.is_modified

    def test_create_table_state_full(self):
        """Test creating TableState with all parameters."""
        state = TableState(
            table_name="product",
            grouping=["category_id"],
            visible_fields={"name", "price", "stock"},
            sort_config=[("Price", "desc")],
            filters=[("price", "gt", "100", "AND")],
            current_view_name="Expensive",
            is_modified=True,
        )

        assert state.table_name == "product"
        assert state.grouping == ["category_id"]
        assert state.visible_fields == {"name", "price", "stock"}
        assert state.sort_config == [("Price", "desc")]
        assert state.filters == [("price", "gt", "100", "AND")]
        assert state.current_view_name == "Expensive"
        assert state.is_modified

    def test_visible_fields_converts_to_set(self):
        """Test that visible_fields list is converted to set."""
        state = TableState(table_name="product", visible_fields=["name", "price"])

        assert isinstance(state.visible_fields, set)
        assert state.visible_fields == {"name", "price"}


class TestStateManagerInitialization:
    """Tests for StateManager initialization."""

    def test_init_with_empty_config(self, temp_db):
        """Test initialization with empty config creates default states."""
        # Create empty config
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write('database: ":memory:"\n')
            config_path = f.name

        try:
            config = DeflatableConfig(config_path)
            manager = StateManager(temp_db, config)

            # Should have states for both tables
            assert "category" in manager.states
            assert "product" in manager.states

            # States should have defaults
            category_state = manager.get_state("category")
            assert category_state.grouping == []
            assert category_state.current_view_name == "All"
            assert not category_state.is_modified
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_init_with_saved_views(self, temp_db, temp_config):
        """Test initialization loads saved views from config."""
        config = DeflatableConfig(temp_config)
        manager = StateManager(temp_db, config)

        # Should load product state from config
        product_state = manager.get_state("product")
        assert product_state.current_view_name == "All"
        assert product_state.visible_fields == {"name", "price", "stock"}
        assert not product_state.is_modified

    def test_init_normalizes_filters(self, temp_db):
        """Test that 3-element filters are normalized to 4-element."""
        # Create config with old 3-element filter format
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("""database: ":memory:"
views:
  product:
    active_view: Filtered
    views:
      Filtered:
        visible_fields:
        - name
        grouping: []
        sort_config: []
        filters:
        - - price
          - gt
          - '50'
""")
            config_path = f.name

        try:
            config = DeflatableConfig(config_path)
            manager = StateManager(temp_db, config)

            state = manager.get_state("product")
            # Should normalize 3-element to 4-element with "AND"
            assert len(state.filters) == 1
            assert state.filters[0] == ("price", "gt", "50", "AND")
        finally:
            Path(config_path).unlink(missing_ok=True)


class TestStateManagerGetters:
    """Tests for StateManager getter methods."""

    def test_get_state_existing(self, temp_db, temp_config):
        """Test getting state for existing table."""
        config = DeflatableConfig(temp_config)
        manager = StateManager(temp_db, config)

        state = manager.get_state("product")
        assert isinstance(state, TableState)
        assert state.table_name == "product"

    def test_get_state_creates_default_if_missing(self, temp_db, temp_config):
        """Test that get_state creates default state for unknown table."""
        config = DeflatableConfig(temp_config)
        manager = StateManager(temp_db, config)

        # Clear states to simulate missing entry
        if "category" in manager.states:
            del manager.states["category"]

        state = manager.get_state("category")
        assert isinstance(state, TableState)
        assert state.table_name == "category"
        assert state.current_view_name == "All"

    def test_get_tables(self, temp_db, temp_config):
        """Test getting list of table names."""
        config = DeflatableConfig(temp_config)
        manager = StateManager(temp_db, config)

        tables = manager.get_tables()
        assert "product" in tables
        assert "category" in tables

    def test_get_view_names_with_views(self, temp_db, temp_config):
        """Test getting view names for table with saved views."""
        config = DeflatableConfig(temp_config)
        manager = StateManager(temp_db, config)

        views = manager.get_view_names("product")
        assert "All" in views
        assert "Expensive" in views

    def test_get_view_names_without_views(self, temp_db, temp_config):
        """Test getting view names for table without saved views."""
        config = DeflatableConfig(temp_config)
        manager = StateManager(temp_db, config)

        views = manager.get_view_names("category")
        assert views == ["All"]


class TestStateManagerSetters:
    """Tests for StateManager setter methods."""

    def test_set_grouping(self, temp_db, temp_config):
        """Test setting grouping column."""
        config = DeflatableConfig(temp_config)
        manager = StateManager(temp_db, config)

        manager.set_grouping("product", ["category_id"])

        state = manager.get_state("product")
        assert state.grouping == ["category_id"]
        assert state.is_modified

    def test_set_grouping_to_empty(self, temp_db, temp_config):
        """Test clearing grouping."""
        config = DeflatableConfig(temp_config)
        manager = StateManager(temp_db, config)

        manager.set_grouping("product", ["category_id"])
        manager.set_grouping("product", [])

        state = manager.get_state("product")
        assert state.grouping == []

    def test_set_visible_fields(self, temp_db, temp_config):
        """Test setting visible fields."""
        config = DeflatableConfig(temp_config)
        manager = StateManager(temp_db, config)

        new_fields = {"name", "price"}
        manager.set_visible_fields("product", new_fields)

        state = manager.get_state("product")
        assert state.visible_fields == new_fields
        assert state.is_modified

    def test_set_sort_config(self, temp_db, temp_config):
        """Test setting sort configuration."""
        config = DeflatableConfig(temp_config)
        manager = StateManager(temp_db, config)

        sort_config = [("Price", "desc"), ("Name", "asc")]
        manager.set_sort_config("product", sort_config)

        state = manager.get_state("product")
        assert state.sort_config == sort_config
        assert state.is_modified

    def test_set_filters(self, temp_db, temp_config):
        """Test setting filters."""
        config = DeflatableConfig(temp_config)
        manager = StateManager(temp_db, config)

        filters = [("price", "gt", "100", "AND"), ("stock", "lt", "10", "OR")]
        manager.set_filters("product", filters)

        state = manager.get_state("product")
        assert state.filters == filters
        assert state.is_modified


class TestStateManagerViewSwitching:
    """Tests for view switching functionality."""

    def test_switch_view_updates_state(self, temp_db, temp_config):
        """Test switching views updates all state properties."""
        config = DeflatableConfig(temp_config)
        manager = StateManager(temp_db, config)

        # Start with All view
        state = manager.get_state("product")
        assert state.current_view_name == "All"

        # Switch to Expensive view
        manager.switch_view("product", "Expensive")

        state = manager.get_state("product")
        assert state.current_view_name == "Expensive"
        assert state.grouping == ["category_id"]
        assert state.visible_fields == {"name", "price"}
        assert state.sort_config == [["Price", "desc"]]
        assert len(state.filters) == 1
        assert state.filters[0] == ("price", "gt", "100", "AND")
        assert not state.is_modified

    def test_switch_view_updates_config_active_view(self, temp_db, temp_config):
        """Test that switching view updates config's active_view."""
        config = DeflatableConfig(temp_config)
        manager = StateManager(temp_db, config)

        manager.switch_view("product", "Expensive")

        table_views = config.get_table_views("product")
        assert table_views.active_view == "Expensive"

    def test_switch_view_invalid_view_does_nothing(self, temp_db, temp_config):
        """Test switching to non-existent view does nothing."""
        config = DeflatableConfig(temp_config)
        manager = StateManager(temp_db, config)

        original_state = manager.get_state("product")
        original_view = original_state.current_view_name

        manager.switch_view("product", "NonExistentView")

        state = manager.get_state("product")
        assert state.current_view_name == original_view

    def test_switch_view_clears_modified_flag(self, temp_db, temp_config):
        """Test that switching views clears the modified flag."""
        config = DeflatableConfig(temp_config)
        manager = StateManager(temp_db, config)

        # Make a modification
        manager.set_grouping("product", ["category_id"])
        state = manager.get_state("product")
        assert state.is_modified

        # Switch view
        manager.switch_view("product", "All")
        state = manager.get_state("product")
        assert not state.is_modified


class TestStateManagerViewSaving:
    """Tests for saving view state."""

    def test_save_current_view_updates_config(self, temp_db, temp_config):
        """Test saving current view updates the config."""
        config = DeflatableConfig(temp_config)
        manager = StateManager(temp_db, config)

        # Modify state
        manager.set_grouping("product", ["category_id"])
        manager.set_visible_fields("product", {"name", "price"})

        # Save
        result = manager.save_current_view("product")
        assert result

        # Check that view was updated
        table_views = config.get_table_views("product")
        all_view = table_views.views["All"]
        assert all_view.grouping == ["category_id"]
        assert set(all_view.visible_fields) == {"name", "price"}

    def test_save_current_view_clears_modified_flag(self, temp_db, temp_config):
        """Test that saving clears the modified flag."""
        config = DeflatableConfig(temp_config)
        manager = StateManager(temp_db, config)

        manager.set_grouping("product", ["category_id"])
        state = manager.get_state("product")
        assert state.is_modified

        manager.save_current_view("product")
        state = manager.get_state("product")
        assert not state.is_modified

    def test_save_view_alias(self, temp_db, temp_config):
        """Test that save_view is an alias for save_current_view."""
        config = DeflatableConfig(temp_config)
        manager = StateManager(temp_db, config)

        manager.set_grouping("product", "category_id")

        result = manager.save_view("product")
        assert result

        state = manager.get_state("product")
        assert not state.is_modified

    def test_save_view_as_creates_new_view(self, temp_db, temp_config):
        """Test saving as new view creates a new view entry."""
        config = DeflatableConfig(temp_config)
        manager = StateManager(temp_db, config)

        # Set up custom state
        manager.set_grouping("product", "category_id")
        manager.set_visible_fields("product", {"name", "price"})
        manager.set_filters("product", [("price", "lt", "50", "AND")])

        # Save as new view
        result = manager.save_view_as("product", "Cheap")
        assert result

        # Check new view exists
        views = manager.get_view_names("product")
        assert "Cheap" in views

        # Check new view has correct data
        table_views = config.get_table_views("product")
        cheap_view = table_views.views["Cheap"]
        assert cheap_view.grouping == "category_id"
        assert set(cheap_view.visible_fields) == {"name", "price"}
        assert len(cheap_view.filters) == 1

    def test_save_view_as_creates_table_views_if_missing(self, temp_db, temp_config):
        """Test save_view_as creates TableViews if table has no views yet."""
        config = DeflatableConfig(temp_config)
        manager = StateManager(temp_db, config)

        # category has no views in config
        manager.set_visible_fields("category", {"name", "description"})

        result = manager.save_view_as("category", "Custom")
        assert result

        # Check TableViews was created
        table_views = config.get_table_views("category")
        assert table_views is not None
        assert "Custom" in table_views.views

    def test_save_current_view_returns_false_if_no_views(self, temp_db):
        """Test save_current_view returns False if table has no views."""
        # Create empty config
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write('database: ":memory:"\n')
            config_path = f.name

        try:
            config = DeflatableConfig(config_path)
            manager = StateManager(temp_db, config)

            # Clear any auto-created views
            if "product" in config.table_views:
                del config.table_views["product"]

            result = manager.save_current_view("product")
            assert not result
        finally:
            Path(config_path).unlink(missing_ok=True)


class TestFilterNormalization:
    """Tests for filter format normalization."""

    def test_normalize_filter_4_element(self):
        """Test 4-element filter passes through unchanged."""
        filter_list = ["price", "gt", "100", "OR"]
        result = StateManager._normalize_filter(filter_list)

        assert result == ("price", "gt", "100", "OR")

    def test_normalize_filter_3_element_adds_and(self):
        """Test 3-element filter gets AND added."""
        filter_list = ["price", "gt", "100"]
        result = StateManager._normalize_filter(filter_list)

        assert result == ("price", "gt", "100", "AND")

    def test_normalize_filter_invalid_raises_error(self):
        """Test invalid filter format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid filter format"):
            StateManager._normalize_filter(["price", "gt"])

        with pytest.raises(ValueError, match="Invalid filter format"):
            StateManager._normalize_filter(["price"])


class TestStateManagerIntegration:
    """Integration tests with real grocery database."""

    def test_full_workflow_with_grocery_db(self, grocery_db, grocery_config):
        """Test complete workflow with grocery database."""
        manager = StateManager(grocery_db, grocery_config)

        # Get initial state
        state = manager.get_state("product")
        initial_view = state.current_view_name

        # Make modifications
        manager.set_grouping("product", "aisle_id")
        manager.set_visible_fields("product", {"name", "brand"})
        manager.set_sort_config("product", [("Name", "asc")])
        manager.set_filters("product", [("brand", "is", "Organic Valley", "AND")])

        # Verify modifications
        state = manager.get_state("product")
        assert state.grouping == "aisle_id"
        assert state.visible_fields == {"name", "brand"}
        assert state.is_modified

        # Switch to different view (if exists)
        all_views = manager.get_view_names("product")
        if len(all_views) > 1:
            other_view = [v for v in all_views if v != initial_view][0]
            manager.switch_view("product", other_view)

            state = manager.get_state("product")
            assert state.current_view_name == other_view
            assert not state.is_modified

    def test_multiple_tables_independent(self, grocery_db, grocery_config):
        """Test that state for different tables is independent."""
        manager = StateManager(grocery_db, grocery_config)

        # Modify product state
        manager.set_grouping("product", "aisle_id")

        # Get aisle state
        aisle_state = manager.get_state("aisle")

        # aisle should have its own independent state
        assert aisle_state.table_name == "aisle"
        # aisle grouping should be independent of product grouping
        assert aisle_state.grouping != "aisle_id" or not aisle_state.is_modified
