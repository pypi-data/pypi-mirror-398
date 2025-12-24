"""Configuration validation for Deflatable."""

import json
import os
from dataclasses import dataclass
from typing import Any

import yaml
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from deflatable import schema


@dataclass
class ValidationError:
    """A validation error found in the config."""

    severity: str  # 'error' or 'warning'
    location: str  # Path to the problematic config element
    message: str

    def __str__(self) -> str:
        """Format error for display."""
        symbol = "✗" if self.severity == "error" else "⚠"
        return f"{symbol} {self.severity.upper()}: {self.location}\n  {self.message}"

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for JSON serialization."""
        return {
            "severity": self.severity,
            "location": self.location,
            "message": self.message,
        }


@dataclass
class ValidationResult:
    """Result of config validation."""

    errors: list[ValidationError]
    warnings: list[ValidationError]

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    def add_error(self, location: str, message: str):
        """Add an error."""
        self.errors.append(ValidationError("error", location, message))

    def add_warning(self, location: str, message: str):
        """Add a warning."""
        self.warnings.append(ValidationError("warning", location, message))

    def format(self) -> str:
        """Format validation result for human-readable display."""
        lines = []

        if self.errors:
            for error in self.errors:
                lines.append(str(error))

        if self.warnings:
            if lines:
                lines.append("")  # Blank line between errors and warnings
            for warning in self.warnings:
                lines.append(str(warning))

        return "\n".join(lines)

    def to_json(self) -> str:
        """Format validation result as JSON."""
        return json.dumps(
            {
                "valid": self.is_valid,
                "error_count": len(self.errors),
                "warning_count": len(self.warnings),
                "errors": [e.to_dict() for e in self.errors],
                "warnings": [w.to_dict() for w in self.warnings],
            },
            indent=2,
        )


def validate_config(config_path: str) -> ValidationResult:
    """
    Validate a Deflatable config file.

    Performs both linting (syntax/structure) and semantic validation
    (checking database references).

    Args:
        config_path: Path to YAML config file

    Returns:
        ValidationResult with errors and warnings
    """
    result = ValidationResult(errors=[], warnings=[])

    # Check file exists
    if not os.path.exists(config_path):
        result.add_error("config_file", f"File not found: {config_path}")
        return result

    # Load and parse YAML
    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        result.add_error("yaml_syntax", f"Invalid YAML syntax: {e}")
        return result
    except Exception as e:
        result.add_error("file_read", f"Failed to read file: {e}")
        return result

    if data is None:
        result.add_error("yaml_content", "Config file is empty")
        return result

    if not isinstance(data, dict):
        result.add_error("yaml_structure", "Config must be a YAML dictionary")
        return result

    # Validate database connection
    db_url = data.get("database")
    if not db_url:
        result.add_error("database", "Missing required 'database' key")
        return result

    if not isinstance(db_url, str):
        result.add_error("database", "Database must be a string (SQLAlchemy URL)")
        return result

    # Resolve relative SQLite paths
    resolved_db_url = db_url
    if db_url.startswith("sqlite:///") and not db_url.startswith("sqlite:////"):
        rel_path = db_url[10:]
        config_dir = os.path.dirname(os.path.abspath(config_path))
        abs_path = os.path.abspath(os.path.join(config_dir, rel_path))
        resolved_db_url = f"sqlite:///{abs_path}"

        # Check if database file exists
        if not os.path.exists(abs_path):
            result.add_error("database", f"Database file not found: {abs_path}")
            return result

    # Try to connect to database
    try:
        engine = create_engine(resolved_db_url)
        tables = schema.get_tables(engine)
    except SQLAlchemyError as e:
        result.add_error("database", f"Cannot connect to database: {e}")
        return result
    except Exception as e:
        result.add_error("database", f"Database error: {e}")
        return result

    if not tables:
        result.add_warning("database", "Database contains no tables")

    # Validate table_order if present
    table_order = data.get("table_order")
    if table_order is not None:
        if not isinstance(table_order, list):
            result.add_error("table_order", "Must be a list of table names")
        else:
            for i, table_name in enumerate(table_order):
                if not isinstance(table_name, str):
                    result.add_error(f"table_order[{i}]", "Table name must be a string")
                elif table_name not in tables:
                    result.add_error(
                        f"table_order[{i}]",
                        f"Table '{table_name}' does not exist in database",
                    )

    # Validate settings if present
    settings = data.get("settings")
    if settings is not None:
        if not isinstance(settings, dict):
            result.add_error("settings", "Must be a dictionary")
        else:
            _validate_settings(settings, result)

    # Validate views
    views = data.get("views")
    if views is not None:
        if not isinstance(views, dict):
            result.add_error("views", "Must be a dictionary of table configurations")
        else:
            _validate_views(views, tables, engine, result)

    # Clean up
    engine.dispose()

    return result


def _validate_settings(settings: dict[str, Any], result: ValidationResult):
    """Validate settings section."""
    # Validate grouping settings
    grouping = settings.get("grouping")
    if grouping is not None:
        if not isinstance(grouping, dict):
            result.add_error("settings.grouping", "Must be a dictionary")
        else:
            recommendations = grouping.get("recommendations")
            if recommendations is not None:
                if not isinstance(recommendations, dict):
                    result.add_error("settings.grouping.recommendations", "Must be a dictionary")
                else:
                    # Validate recommendation parameters
                    max_distinct = recommendations.get("max_distinct_values")
                    if max_distinct is not None and not isinstance(max_distinct, int):
                        result.add_error(
                            "settings.grouping.recommendations.max_distinct_values",
                            "Must be an integer",
                        )

                    max_ratio = recommendations.get("max_cardinality_ratio")
                    if max_ratio is not None and not isinstance(max_ratio | (int, float)):
                        result.add_error(
                            "settings.grouping.recommendations.max_cardinality_ratio",
                            "Must be a number",
                        )

                    min_distinct = recommendations.get("min_distinct_values")
                    if min_distinct is not None and not isinstance(min_distinct, int):
                        result.add_error(
                            "settings.grouping.recommendations.min_distinct_values",
                            "Must be an integer",
                        )

                    excluded_types = recommendations.get("excluded_types")
                    if excluded_types is not None:
                        if not isinstance(excluded_types, list):
                            result.add_error(
                                "settings.grouping.recommendations.excluded_types",
                                "Must be a list of strings",
                            )
                        else:
                            for i, t in enumerate(excluded_types):
                                if not isinstance(t, str):
                                    result.add_error(
                                        f"settings.grouping.recommendations.excluded_types[{i}]",
                                        "Must be a string",
                                    )

    # Validate display settings
    display = settings.get("display")
    if display is not None:
        if not isinstance(display, dict):
            result.add_error("settings.display", "Must be a dictionary")
        else:
            reverse_fk = display.get("reverse_fk_preview_items")
            if reverse_fk is not None and not isinstance(reverse_fk, int):
                result.add_error("settings.display.reverse_fk_preview_items", "Must be an integer")

            cell_trunc = display.get("cell_truncation_length")
            if cell_trunc is not None and not isinstance(cell_trunc, int):
                result.add_error("settings.display.cell_truncation_length", "Must be an integer")

            header_style = display.get("group_header_style")
            if header_style is not None and not isinstance(header_style, str):
                result.add_error("settings.display.group_header_style", "Must be a string")

            bg_style = display.get("group_header_bg_style")
            if bg_style is not None and not isinstance(bg_style, str):
                result.add_error("settings.display.group_header_bg_style", "Must be a string")


def _validate_views(views: dict[str, Any], tables: list[str], engine, result: ValidationResult):
    """Validate views section."""
    for table_name, table_config in views.items():
        location = f"views.{table_name}"

        # Check if table exists
        if table_name not in tables:
            result.add_error(location, f"Table '{table_name}' does not exist in database")
            continue  # Skip further validation for non-existent table

        if not isinstance(table_config, dict):
            result.add_error(location, "Must be a dictionary")
            continue

        # Validate active_view
        active_view = table_config.get("active_view")
        if not active_view:
            result.add_error(f"{location}.active_view", "Missing required 'active_view' key")
        elif not isinstance(active_view, str):
            result.add_error(f"{location}.active_view", "Must be a string")

        # Validate views dictionary
        views_dict = table_config.get("views")
        if not views_dict:
            result.add_error(f"{location}.views", "Missing required 'views' dictionary")
            continue

        if not isinstance(views_dict, dict):
            result.add_error(f"{location}.views", "Must be a dictionary")
            continue

        # Check that active_view exists in views
        if active_view and active_view not in views_dict:
            result.add_error(
                f"{location}.active_view",
                f"Active view '{active_view}' not found in views",
            )

        # Get table columns for validation
        try:
            columns = schema.get_columns(engine, table_name)
            column_names = {col["name"] for col in columns}
        except Exception as e:
            result.add_error(location, f"Failed to get columns: {e}")
            continue

        # Validate each view
        for view_name, view_config in views_dict.items():
            view_location = f"{location}.views.{view_name}"

            if not isinstance(view_config, dict):
                result.add_error(view_location, "Must be a dictionary")
                continue

            # Validate visible_fields
            visible_fields = view_config.get("visible_fields")
            if visible_fields is None:
                result.add_error(
                    f"{view_location}.visible_fields",
                    "Missing required 'visible_fields' key",
                )
            elif not isinstance(visible_fields, list):
                result.add_error(
                    f"{view_location}.visible_fields", "Must be a list of column names"
                )
            else:
                for i, field in enumerate(visible_fields):
                    if not isinstance(field, str):
                        result.add_error(f"{view_location}.visible_fields[{i}]", "Must be a string")
                    elif field not in column_names:
                        result.add_error(
                            f"{view_location}.visible_fields[{i}]",
                            f"Column '{field}' does not exist in table '{table_name}'",
                        )

            # Validate grouping
            grouping = view_config.get("grouping")
            if grouping is not None:
                if isinstance(grouping, str):
                    # Single column grouping
                    if grouping not in column_names:
                        result.add_error(
                            f"{view_location}.grouping",
                            f"Column '{grouping}' does not exist in table '{table_name}'",
                        )
                elif isinstance(grouping, list):
                    # Multi-column grouping
                    for i, col in enumerate(grouping):
                        if not isinstance(col, str):
                            result.add_error(f"{view_location}.grouping[{i}]", "Must be a string")
                        elif col not in column_names:
                            result.add_error(
                                f"{view_location}.grouping[{i}]",
                                f"Column '{col}' does not exist in table '{table_name}'",
                            )
                else:
                    result.add_error(
                        f"{view_location}.grouping",
                        "Must be a string, list of strings, or null",
                    )

            # Validate sort_config
            sort_config = view_config.get("sort_config")
            if sort_config is None:
                result.add_error(
                    f"{view_location}.sort_config", "Missing required 'sort_config' key"
                )
            elif not isinstance(sort_config, list):
                result.add_error(f"{view_location}.sort_config", "Must be a list")
            else:
                for i, sort_item in enumerate(sort_config):
                    if not isinstance(sort_item, list):
                        result.add_error(
                            f"{view_location}.sort_config[{i}]",
                            "Must be a list [column_name, direction]",
                        )
                    elif len(sort_item) != 2:
                        result.add_error(
                            f"{view_location}.sort_config[{i}]",
                            "Must be [column_name, direction]",
                        )
                    else:
                        col_name, direction = sort_item
                        if not isinstance(col_name, str):
                            result.add_error(
                                f"{view_location}.sort_config[{i}][0]",
                                "Column name must be a string",
                            )
                        elif col_name not in column_names:
                            # Check if it's a display name that needs conversion
                            display_names = {col["display_name"]: col["name"] for col in columns}
                            if col_name not in display_names:
                                result.add_error(
                                    f"{view_location}.sort_config[{i}][0]",
                                    f"Column '{col_name}' does not exist in table '{table_name}'",
                                )

                        if not isinstance(direction, str):
                            result.add_error(
                                f"{view_location}.sort_config[{i}][1]",
                                "Direction must be a string",
                            )
                        elif direction.lower() not in ["asc", "desc"]:
                            result.add_error(
                                f"{view_location}.sort_config[{i}][1]",
                                f"Direction must be 'asc' or 'desc', got '{direction}'",
                            )

            # Validate filters
            filters = view_config.get("filters")
            if filters is not None:
                if not isinstance(filters, list):
                    result.add_error(f"{view_location}.filters", "Must be a list")
                else:
                    valid_operators = [
                        "is",
                        "is_not",
                        "contains",
                        "starts_with",
                        "ends_with",
                        "gt",
                        "gte",
                        "lt",
                        "lte",
                    ]
                    valid_boolean_ops = ["AND", "OR"]

                    for i, filter_item in enumerate(filters):
                        if not isinstance(filter_item, list):
                            result.add_error(
                                f"{view_location}.filters[{i}]",
                                "Must be a list [field, operator, value] or [field, operator, value, boolean_op]",
                            )
                        elif len(filter_item) < 3:
                            result.add_error(
                                f"{view_location}.filters[{i}]",
                                "Must have at least [field, operator, value]",
                            )
                        elif len(filter_item) > 4:
                            result.add_error(
                                f"{view_location}.filters[{i}]",
                                "Must be [field, operator, value] or [field, operator, value, boolean_op]",
                            )
                        else:
                            field, operator = filter_item[0], filter_item[1]
                            boolean_op = filter_item[3] if len(filter_item) == 4 else None

                            if not isinstance(field, str):
                                result.add_error(
                                    f"{view_location}.filters[{i}][0]",
                                    "Field name must be a string",
                                )
                            elif field not in column_names:
                                result.add_error(
                                    f"{view_location}.filters[{i}][0]",
                                    f"Column '{field}' does not exist in table '{table_name}'",
                                )

                            if not isinstance(operator, str):
                                result.add_error(
                                    f"{view_location}.filters[{i}][1]",
                                    "Operator must be a string",
                                )
                            elif operator not in valid_operators:
                                result.add_error(
                                    f"{view_location}.filters[{i}][1]",
                                    f"Operator must be one of {valid_operators}, got '{operator}'",
                                )

                            if boolean_op is not None:
                                if not isinstance(boolean_op, str):
                                    result.add_error(
                                        f"{view_location}.filters[{i}][3]",
                                        "Boolean operator must be a string",
                                    )
                                elif boolean_op not in valid_boolean_ops:
                                    result.add_error(
                                        f"{view_location}.filters[{i}][3]",
                                        f"Boolean operator must be one of {valid_boolean_ops}, got '{boolean_op}'",
                                    )

            # Validate field_formats
            field_formats = table_config.get("field_formats")
            if field_formats is not None:
                if not isinstance(field_formats, dict):
                    result.add_error(f"{location}.field_formats", "Must be a dictionary")
                else:
                    fields_dict = field_formats.get("fields")
                    if fields_dict is not None:
                        if not isinstance(fields_dict, dict):
                            result.add_error(
                                f"{location}.field_formats.fields",
                                "Must be a dictionary",
                            )
                        else:
                            for field_name, field_config in fields_dict.items():
                                if field_name not in column_names:
                                    result.add_warning(
                                        f"{location}.field_formats.fields.{field_name}",
                                        f"Column '{field_name}' does not exist in table '{table_name}'",
                                    )

                                if not isinstance(field_config, dict):
                                    result.add_error(
                                        f"{location}.field_formats.fields.{field_name}",
                                        "Must be a dictionary",
                                    )
                                else:
                                    format_type = field_config.get("format")
                                    if format_type is not None and not isinstance(format_type, str):
                                        result.add_error(
                                            f"{location}.field_formats.fields.{field_name}.format",
                                            "Must be a string",
                                        )
