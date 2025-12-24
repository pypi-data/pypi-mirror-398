"""Configuration file management for Deflatable."""

import os
from dataclasses import dataclass
from typing import Any

import yaml


@dataclass
class GroupingRecommendations:
    """Configuration for grouping column recommendations."""

    max_distinct_values: int = 200
    max_cardinality_ratio: float = 0.7
    min_distinct_values: int = 2
    excluded_types: list[str] | None = None  # Column types to exclude from grouping

    def __post_init__(self):
        """Set default excluded types if not provided."""
        if self.excluded_types is None:
            self.excluded_types = [
                "BLOB",
                "BINARY",
                "VARBINARY",
                "FLOAT",
                "REAL",
                "DOUBLE",
                "DATE",
                "TIME",
                "DATETIME",
                "TIMESTAMP",
            ]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GroupingRecommendations":
        """Create from dictionary."""
        return cls(
            max_distinct_values=data.get("max_distinct_values", 200),
            max_cardinality_ratio=data.get("max_cardinality_ratio", 0.7),
            min_distinct_values=data.get("min_distinct_values", 2),
            excluded_types=data.get("excluded_types"),  # None means use defaults
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result = {
            "max_distinct_values": self.max_distinct_values,
            "max_cardinality_ratio": self.max_cardinality_ratio,
            "min_distinct_values": self.min_distinct_values,
        }
        # Only include excluded_types if it differs from defaults
        default_types = [
            "BLOB",
            "BINARY",
            "VARBINARY",
            "FLOAT",
            "REAL",
            "DOUBLE",
            "DATE",
            "TIME",
            "DATETIME",
            "TIMESTAMP",
        ]
        if self.excluded_types != default_types:
            result["excluded_types"] = self.excluded_types
        return result


@dataclass
class GroupingSettings:
    """Configuration for grouping behavior."""

    recommendations: GroupingRecommendations

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GroupingSettings":
        """Create from dictionary."""
        recommendations_data = data.get("recommendations", {})
        return cls(recommendations=GroupingRecommendations.from_dict(recommendations_data))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {"recommendations": self.recommendations.to_dict()}


@dataclass
class DisplaySettings:
    """Configuration for display behavior."""

    reverse_fk_preview_items: int = 2  # Max items to show in reverse FK previews
    cell_truncation_length: int = 80  # Max characters in table cells before truncation
    group_header_style: str = "bold white on dark_green"  # Rich style for group header text
    group_header_bg_style: str = "on dark_green"  # Rich style for group header background cells

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DisplaySettings":
        """Create from dictionary."""
        return cls(
            reverse_fk_preview_items=data.get("reverse_fk_preview_items", 2),
            cell_truncation_length=data.get("cell_truncation_length", 80),
            group_header_style=data.get("group_header_style", "bold white on dark_green"),
            group_header_bg_style=data.get("group_header_bg_style", "on dark_green"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result = {
            "reverse_fk_preview_items": self.reverse_fk_preview_items,
            "cell_truncation_length": self.cell_truncation_length,
        }
        # Only include non-default values
        if self.group_header_style != "bold white on dark_green":
            result["group_header_style"] = self.group_header_style
        if self.group_header_bg_style != "on dark_green":
            result["group_header_bg_style"] = self.group_header_bg_style
        return result


@dataclass
class LookupField:
    """Configuration for a lookup field from a linked table."""

    field: str  # Field name in the linked table
    display_name: str | None = None  # Optional custom display name

    @classmethod
    def from_dict(cls, data: dict[str, Any] | str) -> "LookupField":
        """Create from dictionary or string."""
        if isinstance(data, str):
            # Simple form: just the field name
            return cls(field=data)
        # Full form: dict with field and optional display_name
        return cls(field=data["field"], display_name=data.get("display_name"))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result = {"field": self.field}
        if self.display_name:
            result["display_name"] = self.display_name
        return result


@dataclass
class RecordLink:
    """Configuration for a linked record field (FK relationship)."""

    fk_column: str  # The FK column in this table
    display_name: str | None = None  # Optional custom name for the link
    lookup_fields: list[LookupField] | None = None  # Fields to expose from linked table

    def __post_init__(self):
        """Initialize empty list if None."""
        if self.lookup_fields is None:
            self.lookup_fields = []

    @classmethod
    def from_dict(cls, fk_column: str, data: dict[str, Any] | None) -> "RecordLink":
        """Create from dictionary."""
        if data is None:
            return cls(fk_column=fk_column)

        lookup_fields = []
        if "lookup_fields" in data:
            for lookup_data in data["lookup_fields"]:
                lookup_fields.append(LookupField.from_dict(lookup_data))

        return cls(
            fk_column=fk_column,
            display_name=data.get("display_name"),
            lookup_fields=lookup_fields,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result = {}
        if self.display_name:
            result["display_name"] = self.display_name
        if self.lookup_fields:
            result["lookup_fields"] = [lf.to_dict() for lf in self.lookup_fields]
        return result


@dataclass
class FieldConfig:
    """Configuration for a single field."""

    name: str
    format: str | None = None  # e.g., 'currency', 'date', 'percentage', etc.
    # Future attributes could include: width, alignment, color, etc.

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any] | None) -> "FieldConfig":
        """Create from dictionary."""
        if data is None:
            return cls(name=name)
        return cls(name=name, format=data.get("format"))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result = {}
        if self.format:
            result["format"] = self.format
        return result


@dataclass
class TableFieldFormats:
    """Field formatting configuration for a table."""

    fields: dict[str, FieldConfig]  # Map field name to its config

    def __post_init__(self):
        """Initialize empty dict if None."""
        if self.fields is None:
            self.fields = {}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TableFieldFormats":
        """Create from dictionary."""
        fields = {}
        fields_data = data.get("fields", {})
        for field_name, field_config in fields_data.items():
            fields[field_name] = FieldConfig.from_dict(field_name, field_config)
        return cls(fields=fields)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result = {}
        if self.fields:
            result["fields"] = {
                name: config.to_dict()
                for name, config in self.fields.items()
                if config.to_dict()  # Only include fields with non-empty config
            }
        return result

    def get_field_format(self, field_name: str) -> str | None:
        """Get format for a field, returns None if not configured."""
        field_config = self.fields.get(field_name)
        return field_config.format if field_config else None


@dataclass
class AppSettings:
    """Global application settings."""

    grouping: GroupingSettings
    display: DisplaySettings

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppSettings":
        """Create from dictionary."""
        grouping_data = data.get("grouping", {})
        display_data = data.get("display", {})
        return cls(
            grouping=GroupingSettings.from_dict(grouping_data),
            display=DisplaySettings.from_dict(display_data),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {"grouping": self.grouping.to_dict(), "display": self.display.to_dict()}


@dataclass
class ViewConfig:
    """Configuration for a single view."""

    name: str
    visible_fields: list[str]
    grouping: list[str] | None  # List of column names to group by (in order), or None
    sort_config: list[list[str]]  # List of [column_name, direction]
    filters: list[list[str]] | None = (
        None  # List of [field, operator, value, boolean_op] (boolean_op optional for backward compat)
    )

    def __post_init__(self):
        """Initialize filters if None."""
        if self.filters is None:
            self.filters = []

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result = {
            "visible_fields": self.visible_fields,
            "grouping": self.grouping,
            "sort_config": self.sort_config,
        }
        if self.filters:
            result["filters"] = self.filters
        return result

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "ViewConfig":
        """Create ViewConfig from dictionary."""
        # Handle grouping as either None, string (backward compat), or list
        grouping_data = data.get("grouping")
        if grouping_data is None:
            grouping = None
        elif isinstance(grouping_data, str):
            # Backward compatibility: convert single string to list
            grouping = [grouping_data]
        else:
            # Already a list
            grouping = grouping_data

        return cls(
            name=name,
            visible_fields=data.get("visible_fields", []),
            grouping=grouping,
            sort_config=data.get("sort_config", []),
            filters=data.get("filters", []),
        )


@dataclass
class TableViews:
    """Views configuration for a single table."""

    table_name: str
    active_view: str
    views: dict[str, ViewConfig]
    field_formats: TableFieldFormats | None = None  # Field formatting configuration
    record_links: dict[str, RecordLink] | None = None  # Record link configuration

    def __post_init__(self):
        """Initialize empty dict if None."""
        if self.record_links is None:
            self.record_links = {}

    def get_active_view(self) -> ViewConfig:
        """Get the currently active view."""
        return self.views[self.active_view]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        result = {
            "active_view": self.active_view,
            "views": {name: view.to_dict() for name, view in self.views.items()},
        }
        if self.field_formats:
            formats_dict = self.field_formats.to_dict()
            if formats_dict:  # Only add if not empty
                result["field_formats"] = formats_dict
        if self.record_links:
            links_dict = {fk: link.to_dict() for fk, link in self.record_links.items()}
            # Only include if at least one link has configuration
            if any(links_dict.values()):
                result["record_links"] = links_dict
        return result

    @classmethod
    def from_dict(cls, table_name: str, data: dict[str, Any]) -> "TableViews":
        """Create TableViews from dictionary."""
        views = {
            name: ViewConfig.from_dict(name, view_data)
            for name, view_data in data.get("views", {}).items()
        }

        # Load field formats if present
        field_formats = None
        if "field_formats" in data:
            field_formats = TableFieldFormats.from_dict(data["field_formats"])

        # Load record links if present
        record_links = {}
        if "record_links" in data:
            for fk_column, link_data in data["record_links"].items():
                record_links[fk_column] = RecordLink.from_dict(fk_column, link_data)

        return cls(
            table_name=table_name,
            active_view=data.get("active_view", list(views.keys())[0] if views else "Default"),
            views=views,
            field_formats=field_formats,
            record_links=record_links,
        )


class DeflatableConfig:
    """Configuration for Deflatable application."""

    def __init__(self, config_path: str):
        """
        Initialize configuration.

        Args:
            config_path: Path to YAML config file
        """
        self.config_path = config_path
        self.db_url: str  # SQLAlchemy database URI (set in _load())
        self.table_order: list[str] = []  # Optional table ordering
        self.table_views: dict[str, TableViews] = {}
        self.settings: AppSettings = AppSettings.from_dict({})  # Default settings
        self._load()

    def _load(self):
        """Load configuration from YAML file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path) as f:
            data = yaml.safe_load(f) or {}

        # Get database URL (must be a SQLAlchemy URL)
        db_url = data.get("database")
        if not db_url:
            raise ValueError("Config file must specify 'database' as a SQLAlchemy URL")

        # For SQLite relative URLs, resolve path relative to config file
        if db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:////"):
            # It's a relative path (3 slashes, not 4)
            # Extract the relative path part
            rel_path = db_url[10:]  # Remove 'sqlite:///'

            # Resolve relative to config file directory
            config_dir = os.path.dirname(os.path.abspath(self.config_path))
            abs_path = os.path.abspath(os.path.join(config_dir, rel_path))

            # Convert back to absolute SQLite URL
            self.db_url = f"sqlite:///{abs_path}"
        else:
            # Already absolute or non-SQLite URL
            self.db_url = db_url

        # Load table order (optional)
        self.table_order = data.get("table_order", [])

        # Load settings (optional)
        settings_data = data.get("settings", {})
        self.settings = AppSettings.from_dict(settings_data)

        # Load views
        views_data = data.get("views", {})
        for table_name, table_data in views_data.items():
            self.table_views[table_name] = TableViews.from_dict(table_name, table_data)

    def save(self):
        """Save configuration to YAML file."""
        data = {"database": self.db_url}

        # Save settings if not default
        if self.settings:
            data["settings"] = self.settings.to_dict()

        if self.table_views:
            data["views"] = {
                table_name: table_views.to_dict()
                for table_name, table_views in self.table_views.items()
            }

        with open(self.config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def get_table_views(self, table_name: str) -> TableViews | None:
        """Get views configuration for a table."""
        return self.table_views.get(table_name)

    def get_ordered_tables(self, all_tables: list[str]) -> list[str]:
        """
        Get tables in the order specified by config, or default order.

        Args:
            all_tables: List of all tables from database

        Returns:
            Ordered list of tables
        """
        if not self.table_order:
            return all_tables

        # Start with specified order
        ordered = []
        remaining = set(all_tables)

        for table in self.table_order:
            if table in remaining:
                ordered.append(table)
                remaining.remove(table)

        # Append any tables not in the config order
        ordered.extend(sorted(remaining))

        return ordered

    def create_default_view(self, table_name: str, visible_fields: list[str]) -> TableViews:
        """Create a default view for a table."""
        default_view = ViewConfig(
            name="All", visible_fields=visible_fields, grouping=None, sort_config=[]
        )

        table_views = TableViews(
            table_name=table_name, active_view="All", views={"All": default_view}
        )

        self.table_views[table_name] = table_views
        return table_views
