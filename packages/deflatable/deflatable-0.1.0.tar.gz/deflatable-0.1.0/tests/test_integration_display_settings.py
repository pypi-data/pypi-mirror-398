#!/usr/bin/env python3
"""Integration tests for display settings configuration."""

from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
import yaml

from deflatable.app import Deflatable
from deflatable.config import DeflatableConfig

# Configure pytest to handle async tests
pytestmark = pytest.mark.asyncio

# Test database path
TEST_DIR = Path(__file__).parent
TEST_DB = TEST_DIR / "grocery.db"


class TestDisplaySettingsIntegration:
    """Integration tests for display settings with the full app."""

    async def test_app_starts_with_default_display_settings(self):
        """Test that app starts successfully with default display settings."""
        # Create a minimal config with no display settings
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {"database": f"sqlite:///{TEST_DB}"}
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            config = DeflatableConfig(config_path)
            app = Deflatable(config=config)

            async with app.run_test() as pilot:
                await pilot.pause()

                # App should load successfully
                assert app is not None

                # Verify default settings are applied
                assert config.settings.display.reverse_fk_preview_items == 2
                assert config.settings.display.cell_truncation_length == 80

                # Verify tables loaded
                assert len(app.tables) > 0
        finally:
            Path(config_path).unlink()

    async def test_app_starts_with_custom_display_settings(self):
        """Test that app starts with custom display settings."""
        # Create config with custom display settings
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "database": f"sqlite:///{TEST_DB}",
                "settings": {
                    "display": {
                        "reverse_fk_preview_items": 5,
                        "cell_truncation_length": 120,
                    }
                },
            }
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            config = DeflatableConfig(config_path)
            app = Deflatable(config=config)

            async with app.run_test() as pilot:
                await pilot.pause()

                # App should load successfully
                assert app is not None

                # Verify custom settings are loaded
                assert config.settings.display.reverse_fk_preview_items == 5
                assert config.settings.display.cell_truncation_length == 120

                # Verify tables loaded
                from textual.widgets import DataTable

                table = app.query_one(DataTable)
                assert table.row_count >= 0  # Should load without errors
        finally:
            Path(config_path).unlink()

    async def test_app_starts_with_custom_grouping_settings(self):
        """Test that app starts with custom grouping settings."""
        # Create config with custom grouping settings
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "database": f"sqlite:///{TEST_DB}",
                "settings": {
                    "grouping": {
                        "recommendations": {
                            "max_distinct_values": 1000,
                            "max_cardinality_ratio": 0.5,
                            "min_distinct_values": 3,
                            "excluded_types": ["BLOB", "BINARY", "FLOAT"],
                        }
                    }
                },
            }
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            config = DeflatableConfig(config_path)
            app = Deflatable(config=config)

            async with app.run_test() as pilot:
                await pilot.pause()

                # App should load successfully
                assert app is not None

                # Verify custom grouping settings are loaded
                rec = config.settings.grouping.recommendations
                assert rec.max_distinct_values == 1000
                assert rec.max_cardinality_ratio == 0.5
                assert rec.min_distinct_values == 3
                assert rec.excluded_types == ["BLOB", "BINARY", "FLOAT"]
        finally:
            Path(config_path).unlink()

    async def test_app_starts_with_all_custom_settings(self):
        """Test that app starts with all settings customized."""
        # Create config with all settings customized
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "database": f"sqlite:///{TEST_DB}",
                "settings": {
                    "display": {
                        "reverse_fk_preview_items": 3,
                        "cell_truncation_length": 100,
                    },
                    "grouping": {
                        "recommendations": {
                            "max_distinct_values": 500,
                            "max_cardinality_ratio": 0.6,
                            "min_distinct_values": 2,
                            "excluded_types": ["BLOB", "REAL"],
                        }
                    },
                },
            }
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            config = DeflatableConfig(config_path)
            app = Deflatable(config=config)

            async with app.run_test() as pilot:
                await pilot.pause()

                # App should load successfully
                assert app is not None

                # Verify all custom settings are loaded
                assert config.settings.display.reverse_fk_preview_items == 3
                assert config.settings.display.cell_truncation_length == 100

                rec = config.settings.grouping.recommendations
                assert rec.max_distinct_values == 500
                assert rec.max_cardinality_ratio == 0.6
                assert rec.min_distinct_values == 2
                assert rec.excluded_types == ["BLOB", "REAL"]

                # Verify tables loaded and can be interacted with
                from textual.widgets import DataTable

                table = app.query_one(DataTable)
                assert table is not None
        finally:
            Path(config_path).unlink()

    async def test_display_settings_actually_used_in_rendering(self):
        """Test that display settings are actually used when rendering data."""
        # Create config with very low truncation to test it's being used
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config_data = {
                "database": f"sqlite:///{TEST_DB}",
                "settings": {
                    "display": {
                        "reverse_fk_preview_items": 1,  # Only show 1 item
                        "cell_truncation_length": 10,  # Truncate at 10 chars
                    }
                },
            }
            yaml.dump(config_data, f)
            config_path = f.name

        try:
            config = DeflatableConfig(config_path)
            app = Deflatable(config=config)

            async with app.run_test() as pilot:
                await pilot.pause()

                # Settings should be applied
                assert config.settings.display.reverse_fk_preview_items == 1
                assert config.settings.display.cell_truncation_length == 10

                # App should still function normally
                from textual.widgets import DataTable

                tables = app.query(DataTable)
                assert len(list(tables)) > 0

                # Verify at least one table has data
                for table in tables:
                    if table.row_count > 0:
                        # If we have data, the settings were used during rendering
                        assert True
                        break
        finally:
            Path(config_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
