#!/usr/bin/env python3
"""Tests for configuration file management."""

import tempfile
from pathlib import Path

import pytest
import yaml

from deflatable.config import DeflatableConfig, TableViews, ViewConfig


class TestViewConfig:
    """Test ViewConfig dataclass."""

    def test_create_view_config(self):
        """Test creating a basic ViewConfig."""
        view = ViewConfig(
            name="Test View",
            visible_fields=["field1", "field2"],
            grouping="field3",
            sort_config=[["field1", "asc"]],
        )

        assert view.name == "Test View"
        assert view.visible_fields == ["field1", "field2"]
        assert view.grouping == "field3"
        assert view.sort_config == [["field1", "asc"]]
        assert view.filters == []

    def test_view_config_with_filters(self):
        """Test ViewConfig with filters."""
        view = ViewConfig(
            name="Filtered View",
            visible_fields=["price", "name"],
            grouping=None,
            sort_config=[],
            filters=[["price", "gt", "5.00", "AND"]],
        )

        assert len(view.filters) == 1
        assert view.filters[0] == ["price", "gt", "5.00", "AND"]

    def test_view_config_to_dict(self):
        """Test converting ViewConfig to dictionary."""
        view = ViewConfig(
            name="Test",
            visible_fields=["a", "b"],
            grouping="c",
            sort_config=[["a", "desc"]],
            filters=[["a", "is", "test", "AND"]],
        )

        result = view.to_dict()
        assert result["visible_fields"] == ["a", "b"]
        assert result["grouping"] == "c"
        assert result["sort_config"] == [["a", "desc"]]
        assert result["filters"] == [["a", "is", "test", "AND"]]

    def test_view_config_to_dict_without_filters(self):
        """Test to_dict excludes empty filters."""
        view = ViewConfig(name="Test", visible_fields=["a"], grouping=None, sort_config=[])

        result = view.to_dict()
        assert "filters" not in result

    def test_view_config_from_dict(self):
        """Test creating ViewConfig from dictionary."""
        data = {
            "visible_fields": ["x", "y"],
            "grouping": "z",
            "sort_config": [["x", "asc"]],
            "filters": [["x", "contains", "test", "OR"]],
        }

        view = ViewConfig.from_dict("MyView", data)
        assert view.name == "MyView"
        assert view.visible_fields == ["x", "y"]
        assert view.grouping == ["z"]  # Backward compatibility: string converted to list
        assert view.sort_config == [["x", "asc"]]
        assert view.filters == [["x", "contains", "test", "OR"]]

    def test_view_config_from_dict_with_defaults(self):
        """Test from_dict uses defaults for missing fields."""
        data = {"visible_fields": ["a"]}

        view = ViewConfig.from_dict("Minimal", data)
        assert view.name == "Minimal"
        assert view.visible_fields == ["a"]
        assert view.grouping is None
        assert view.sort_config == []
        assert view.filters == []


class TestTableViews:
    """Test TableViews dataclass."""

    def test_create_table_views(self):
        """Test creating TableViews."""
        view1 = ViewConfig("All", ["a", "b"], None, [])
        view2 = ViewConfig("Grouped", ["a"], "b", [])

        table_views = TableViews(
            table_name="products",
            active_view="All",
            views={"All": view1, "Grouped": view2},
        )

        assert table_views.table_name == "products"
        assert table_views.active_view == "All"
        assert len(table_views.views) == 2

    def test_get_active_view(self):
        """Test getting the active view."""
        view1 = ViewConfig("All", ["a"], None, [])
        view2 = ViewConfig("Other", ["b"], None, [])

        table_views = TableViews(
            table_name="test", active_view="Other", views={"All": view1, "Other": view2}
        )

        active = table_views.get_active_view()
        assert active.name == "Other"
        assert active.visible_fields == ["b"]

    def test_table_views_to_dict(self):
        """Test converting TableViews to dictionary."""
        view = ViewConfig("All", ["x", "y"], "z", [["x", "asc"]])
        table_views = TableViews("test", "All", {"All": view})

        result = table_views.to_dict()
        assert result["active_view"] == "All"
        assert "All" in result["views"]
        assert result["views"]["All"]["visible_fields"] == ["x", "y"]

    def test_table_views_from_dict(self):
        """Test creating TableViews from dictionary."""
        data = {
            "active_view": "Custom",
            "views": {
                "All": {
                    "visible_fields": ["a", "b"],
                    "grouping": None,
                    "sort_config": [],
                },
                "Custom": {
                    "visible_fields": ["a"],
                    "grouping": "b",
                    "sort_config": [["a", "desc"]],
                },
            },
        }

        table_views = TableViews.from_dict("products", data)
        assert table_views.table_name == "products"
        assert table_views.active_view == "Custom"
        assert len(table_views.views) == 2
        assert table_views.views["Custom"].grouping == ["b"]  # Backward compatibility


class TestDeflatableConfig:
    """Test DeflatableConfig class."""

    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        # Create temporary config file
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yml"
            db_path = Path(tmpdir) / "test.db"

            # Create database file
            db_path.touch()

            # Write config
            config_data = {
                "database": f"sqlite:///{db_path}",
                "views": {
                    "products": {
                        "active_view": "All",
                        "views": {
                            "All": {
                                "visible_fields": ["name", "price"],
                                "grouping": None,
                                "sort_config": [],
                            }
                        },
                    }
                },
            }

            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            # Load config
            config = DeflatableConfig(str(config_path))

            assert config.db_url == f"sqlite:///{db_path}"
            assert "products" in config.table_views
            assert config.table_views["products"].active_view == "All"

    def test_load_config_missing_file(self):
        """Test loading non-existent config file raises error."""
        with pytest.raises(FileNotFoundError):
            DeflatableConfig("/nonexistent/config.yml")

    def test_load_config_missing_database_key(self):
        """Test config without 'database' key raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "bad.yml"

            # Config without database key
            with open(config_path, "w") as f:
                yaml.dump({"views": {}}, f)

            with pytest.raises(ValueError, match="must specify 'database'"):
                DeflatableConfig(str(config_path))

    def test_load_config_relative_database_path(self):
        """Test SQLAlchemy URL is loaded as-is."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            config_dir.mkdir()
            config_path = config_dir / "test.yml"

            db_dir = Path(tmpdir) / "data"
            db_dir.mkdir()
            db_path = db_dir / "test.db"
            db_path.touch()

            # Use SQLAlchemy URL in config
            db_url = f"sqlite:///{db_path}"

            with open(config_path, "w") as f:
                yaml.dump({"database": db_url}, f)

            config = DeflatableConfig(str(config_path))
            assert config.db_url == db_url

    def test_load_config_absolute_database_path(self):
        """Test SQLAlchemy URL with absolute path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yml"
            db_path = Path(tmpdir) / "test.db"
            db_path.touch()

            # Use SQLAlchemy URL with absolute path
            db_url = f"sqlite:///{db_path}"
            with open(config_path, "w") as f:
                yaml.dump({"database": db_url}, f)

            config = DeflatableConfig(str(config_path))
            assert config.db_url == db_url

    def test_load_empty_config_file(self):
        """Test loading empty YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "empty.yml"
            config_path.touch()  # Empty file

            with pytest.raises(ValueError, match="must specify 'database'"):
                DeflatableConfig(str(config_path))

    def test_get_table_views(self):
        """Test getting views for a table."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yml"
            db_path = Path(tmpdir) / "test.db"
            db_path.touch()

            config_data = {
                "database": "test.db",
                "views": {
                    "products": {
                        "active_view": "All",
                        "views": {
                            "All": {
                                "visible_fields": ["name"],
                                "grouping": None,
                                "sort_config": [],
                            }
                        },
                    }
                },
            }

            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            config = DeflatableConfig(str(config_path))

            # Table exists
            views = config.get_table_views("products")
            assert views is not None
            assert views.table_name == "products"

            # Table doesn't exist
            views = config.get_table_views("nonexistent")
            assert views is None

    def test_save_config(self):
        """Test saving configuration back to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yml"
            db_path = Path(tmpdir) / "test.db"
            db_path.touch()

            # Create initial config
            initial_data = {
                "database": "test.db",
                "views": {
                    "products": {
                        "active_view": "All",
                        "views": {
                            "All": {
                                "visible_fields": ["name"],
                                "grouping": None,
                                "sort_config": [],
                            }
                        },
                    }
                },
            }

            with open(config_path, "w") as f:
                yaml.dump(initial_data, f)

            # Load and modify
            config = DeflatableConfig(str(config_path))

            # Add a new view
            new_view = ViewConfig(
                name="Grouped",
                visible_fields=["name", "category"],
                grouping=["category"],
                sort_config=[["name", "asc"]],
            )
            config.table_views["products"].views["Grouped"] = new_view

            # Save
            config.save()

            # Reload and verify
            config2 = DeflatableConfig(str(config_path))
            assert "Grouped" in config2.table_views["products"].views
            grouped = config2.table_views["products"].views["Grouped"]
            assert grouped.grouping == ["category"]

    def test_save_preserves_relative_paths(self):
        """Test that save() preserves SQLAlchemy URLs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yml"
            db_path = Path(tmpdir) / "test.db"
            db_path.touch()

            # Create with absolute SQLAlchemy URL
            db_url = f"sqlite:///{db_path}"
            with open(config_path, "w") as f:
                yaml.dump({"database": db_url}, f)

            config = DeflatableConfig(str(config_path))
            config.save()

            # Check saved file preserves the URL
            with open(config_path) as f:
                saved_data = yaml.safe_load(f)

            assert saved_data["database"] == db_url

    def test_get_ordered_tables_default(self):
        """Test get_ordered_tables with no table_order specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yml"
            db_path = Path(tmpdir) / "test.db"
            db_path.touch()

            with open(config_path, "w") as f:
                yaml.dump({"database": f"sqlite:///{db_path}"}, f)

            config = DeflatableConfig(str(config_path))

            tables = ["zebra", "apple", "banana"]
            ordered = config.get_ordered_tables(tables)

            # Should return tables as-is (no sorting applied in config)
            assert ordered == tables

    def test_get_ordered_tables_with_config(self):
        """Test get_ordered_tables with table_order in config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yml"
            db_path = Path(tmpdir) / "test.db"
            db_path.touch()

            config_data = {"database": "test.db", "table_order": ["products", "orders"]}

            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            config = DeflatableConfig(str(config_path))

            all_tables = ["customers", "orders", "products", "invoices"]
            ordered = config.get_ordered_tables(all_tables)

            # Should start with configured order, then alphabetical
            assert ordered == ["products", "orders", "customers", "invoices"]

    def test_create_default_view(self):
        """Test creating a default view for a table."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yml"
            db_path = Path(tmpdir) / "test.db"
            db_path.touch()

            with open(config_path, "w") as f:
                yaml.dump({"database": "test.db"}, f)

            config = DeflatableConfig(str(config_path))

            # Create default view
            table_views = config.create_default_view("products", ["name", "price"])

            assert table_views.table_name == "products"
            assert table_views.active_view == "All"
            assert "All" in table_views.views
            assert table_views.views["All"].visible_fields == ["name", "price"]
            assert table_views.views["All"].grouping is None

            # Should be stored in config
            assert config.table_views["products"] == table_views

    def test_load_config_with_filters(self):
        """Test loading config with filter definitions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test.yml"
            db_path = Path(tmpdir) / "test.db"
            db_path.touch()

            config_data = {
                "database": "test.db",
                "views": {
                    "products": {
                        "active_view": "Expensive",
                        "views": {
                            "Expensive": {
                                "visible_fields": ["name", "price"],
                                "grouping": None,
                                "sort_config": [["price", "desc"]],
                                "filters": [
                                    ["price", "gt", "100", "AND"],
                                    ["stock", "gt", "0", "AND"],
                                ],
                            }
                        },
                    }
                },
            }

            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            config = DeflatableConfig(str(config_path))

            expensive_view = config.table_views["products"].views["Expensive"]
            assert len(expensive_view.filters) == 2
            assert expensive_view.filters[0] == ["price", "gt", "100", "AND"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
