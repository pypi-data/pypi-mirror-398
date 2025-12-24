"""Generic table display logic."""

import re
from typing import Any

from sqlalchemy import Engine, text

from . import schema
from .state import TableState


def _coerce_comparison_value(value: str) -> tuple[str, Any]:
    """
    Coerce a string value for comparison operations.

    Tries to parse as a number (stripping currency symbols).
    If that fails, treats it as a string (for dates, etc.).

    Args:
        value: String value from filter input

    Returns:
        Tuple of (cast_type, coerced_value) where:
        - cast_type is "REAL" for numbers or "TEXT" for strings
        - coerced_value is the value to use in the SQL parameter
    """
    # Strip currency symbols, commas, and whitespace for numeric parsing
    cleaned = re.sub(r"[$€£¥,\s]", "", value)

    # Try to convert to float
    try:
        return "REAL", float(cleaned)
    except ValueError:
        # Not a number - treat as text (works for ISO dates like "2024-12-01")
        return "TEXT", value


def build_where_clause(
    filters: list[tuple[str, str, str, str]],
    table_name: str,
    lookup_map: dict[str, tuple[str, str]] | None = None,
) -> tuple[str, dict[str, Any]]:
    """
    Build WHERE clause and parameters from filters.

    Args:
        filters: List of (field, operator, value, boolean_op) tuples
                 boolean_op is "AND" or "OR" and represents the connector AFTER this condition
        table_name: Name of the table (for qualified column names)
        lookup_map: Optional dict mapping lookup field IDs to (alias, field_name) tuples

    Returns:
        Tuple of (where_clause, parameters) where where_clause is SQL string
        and parameters is dict of named parameters for SQLAlchemy
    """
    if not filters:
        return "", {}

    if lookup_map is None:
        lookup_map = {}

    conditions = []
    params = {}

    for idx, (field, op, value, bool_op) in enumerate(filters):
        # Check if this is a lookup field
        if field in lookup_map:
            alias, field_name = lookup_map[field]
            qualified_field = f'"{alias}"."{field_name}"'
        else:
            # Regular column - quote identifiers to handle reserved keywords and special characters
            qualified_field = f'"{table_name}"."{field}"'
        param_name = f"filter_{idx}"

        if op == "is":
            conditions.append(f"{qualified_field} = :{param_name}")
            params[param_name] = value
        elif op == "is_not":
            conditions.append(f"{qualified_field} != :{param_name}")
            params[param_name] = value
        elif op == "contains":
            conditions.append(f"{qualified_field} LIKE :{param_name}")
            params[param_name] = f"%{value}%"
        elif op == "starts_with":
            conditions.append(f"{qualified_field} LIKE :{param_name}")
            params[param_name] = f"{value}%"
        elif op == "ends_with":
            conditions.append(f"{qualified_field} LIKE :{param_name}")
            params[param_name] = f"%{value}"
        elif op in ("gt", "gte", "lt", "lte"):
            # Comparison operators: coerce value to number or keep as text (for dates)
            cast_type, coerced_value = _coerce_comparison_value(value)

            # Map operator to SQL
            sql_op = {"gt": ">", "gte": ">=", "lt": "<", "lte": "<="}[op]

            # Use CAST to handle type-appropriate comparison in SQL
            conditions.append(f"CAST({qualified_field} AS {cast_type}) {sql_op} :{param_name}")
            params[param_name] = coerced_value

    # Build WHERE clause with dynamic boolean operators
    if not conditions:
        return "", {}

    # Join conditions using the boolean operator from each filter
    # The last filter's boolean_op is ignored since there's nothing after it
    where_parts = []
    for i, condition in enumerate(conditions):
        where_parts.append(condition)
        # Add boolean operator after all conditions except the last
        if i < len(conditions) - 1:
            bool_op = filters[i][3]  # Get boolean_op from the tuple
            where_parts.append(bool_op)

    where_clause = " ".join(where_parts)
    return f" WHERE {where_clause}" if where_clause else "", params


def fetch_reverse_fk_preview(
    engine: Engine, reverse_fk: dict[str, str], pk_value: Any, max_items: int = 2
) -> str:
    """
    Fetch preview of related records for a reverse FK.

    Args:
        engine: Database engine
        reverse_fk: Dict from get_reverse_foreign_keys()
        pk_value: Primary key value of the parent record
        max_items: How many unique names to show before "..."

    Returns:
        String like "CPU-oz-1, CPU-oz-2, ... (25 total)" or "id (x15), ... (100 total)"
    """
    from_table = reverse_fk["from_table"]
    from_column = reverse_fk["from_column"]
    name_column = reverse_fk["name_column"]

    with engine.connect() as conn:
        # Get total count
        result = conn.execute(
            text(f'SELECT COUNT(*) FROM "{from_table}" WHERE "{from_column}" = :pk_value'),
            {"pk_value": pk_value},
        )
        row = result.fetchone()
        total = row[0] if row else 0

        if total == 0:
            return ""

        # Get all names and count occurrences
        result = conn.execute(
            text(
                f'SELECT "{name_column}", COUNT(*) as count FROM "{from_table}" WHERE "{from_column}" = :pk_value GROUP BY "{name_column}" ORDER BY count DESC, "{name_column}"'
            ),
            {"pk_value": pk_value},
        )
        name_counts = [(str(row[0]), row[1]) for row in result.fetchall()]

        # Format names with counts (only show count if > 1)
        formatted_names = []
        for name, count in name_counts[:max_items]:
            if count > 1:
                formatted_names.append(f"{name} (x{count})")
            else:
                formatted_names.append(name)

        unique_count = len(name_counts)
        if unique_count <= max_items:
            return ", ".join(formatted_names)
        else:
            return f"{', '.join(formatted_names)}, ... ({total} total)"


def fetch_all_reverse_fk_items(
    engine: Engine, reverse_fk: dict[str, str], pk_value: Any
) -> list[str]:
    """
    Fetch all related records for a reverse FK.

    Args:
        engine: Database engine
        reverse_fk: Dict from get_reverse_foreign_keys()
        pk_value: Primary key value of the parent record

    Returns:
        List of all item names with counts (e.g., ["id (x15)", "other_id (x3)", "unique_id"])
    """
    from_table = reverse_fk["from_table"]
    from_column = reverse_fk["from_column"]
    name_column = reverse_fk["name_column"]

    with engine.connect() as conn:
        result = conn.execute(
            text(
                f'SELECT "{name_column}", COUNT(*) as count FROM "{from_table}" WHERE "{from_column}" = :pk_value GROUP BY "{name_column}" ORDER BY count DESC, "{name_column}"'
            ),
            {"pk_value": pk_value},
        )

        # Format names with counts (only show count if > 1)
        items = []
        for row in result.fetchall():
            name, count = str(row[0]), row[1]
            if count > 1:
                items.append(f"{name} (x{count})")
            else:
                items.append(name)

        return items


def get_all_available_fields(
    engine: Engine, table_name: str, record_links: dict[str, Any] | None = None
) -> list[tuple[str, str]]:
    """
    Get all available fields for a table, including lookup fields from record links.

    This is used for building field selection lists in UI screens (Fields, Filter, Sort).

    Args:
        engine: SQLAlchemy database engine
        table_name: Name of the table
        record_links: Optional dict of RecordLink configurations from config

    Returns:
        List of (field_id, display_name) tuples, where field_id can be:
        - Regular column name (e.g., "aisle_id")
        - Lookup field ID (e.g., "aisle_id__aisle_number")
    """
    columns = schema.get_columns(engine, table_name)
    fields = []

    # Add regular columns (exclude PKs)
    for col in columns:
        if not col["pk"]:
            fields.append((col["name"], col["display_name"]))

    # Add lookup fields from record links
    if record_links:
        for fk_column, record_link in record_links.items():
            if record_link.lookup_fields:
                for lookup_field in record_link.lookup_fields:
                    lookup_id = schema.get_lookup_field_name(fk_column, lookup_field.field)
                    display_name = schema.get_lookup_field_display_name(
                        engine,
                        table_name,
                        fk_column,
                        lookup_field.field,
                        lookup_field.display_name,
                    )
                    fields.append((lookup_id, display_name))

    # Add reverse FK columns
    reverse_fks = schema.get_reverse_foreign_keys(engine, table_name)
    for rfk in reverse_fks:
        col_name = rfk["from_table"]
        col_display_name = schema.to_title_case(col_name)
        fields.append((col_name, col_display_name))

    return fields


def build_column_list(
    engine: Engine, state: TableState, record_links: dict[str, Any] | None = None
) -> list[str]:
    """
    Build list of column display names based on state.

    Columns are shown in database order (as defined in CREATE TABLE).

    Args:
        engine: SQLAlchemy database engine
        state: Table state
        record_links: Optional dict of RecordLink configurations from config

    Returns:
        List of column display names
    """
    columns = schema.get_columns(engine, state.table_name)

    # Add visible fields in database order (skip grouping fields)
    result = []
    for col in columns:
        if state.grouping and col["name"] in state.grouping:
            continue
        if col["name"] in state.visible_fields:
            # Add PK marker to primary key columns
            display_name = col["display_name"]
            if col["pk"]:
                display_name = f"🔑 {display_name}"
            result.append(display_name)

    # Add lookup fields from record links (if configured)
    if record_links:
        for fk_column, record_link in record_links.items():
            if record_link.lookup_fields:
                for lookup_field in record_link.lookup_fields:
                    # Generate lookup field identifier
                    lookup_id = schema.get_lookup_field_name(fk_column, lookup_field.field)
                    # Skip if used for grouping
                    if state.grouping and lookup_id in state.grouping:
                        continue
                    # Only include if it's in visible_fields
                    if lookup_id in state.visible_fields:
                        display_name = schema.get_lookup_field_display_name(
                            engine,
                            state.table_name,
                            fk_column,
                            lookup_field.field,
                            lookup_field.display_name,
                        )
                        result.append(display_name)

    # Add reverse FK preview columns at the end (only if visible)
    reverse_fks = schema.get_reverse_foreign_keys(engine, state.table_name)
    for rfk in reverse_fks:
        col_name = rfk["from_table"]
        # Only include if it's in visible_fields
        if col_name in state.visible_fields:
            col_display_name = schema.to_title_case(col_name)
            result.append(col_display_name)

    return result


def fetch_grouped_data(
    engine: Engine,
    state: TableState,
    reverse_fk_preview_items: int = 2,
    cell_truncation_length: int = 80,
    field_formats: dict[str, str] | None = None,
    record_links: dict[str, Any] | None = None,
) -> dict[str | None, list[tuple[dict[str, Any], list[str]]]]:
    """
    Fetch data grouped according to state.

    Args:
        engine: SQLAlchemy database engine
        state: Table state
        reverse_fk_preview_items: Max items to show in reverse FK previews (default: 2)
        cell_truncation_length: Max characters in cells before truncation (default: 80)
        field_formats: Dict mapping field names to format types (e.g., 'currency')
        record_links: Optional dict of RecordLink configurations from config

    Returns:
        Dict mapping group names to list of (row_data_dict, row_display_list) tuples
    """
    if field_formats is None:
        field_formats = {}
    if record_links is None:
        record_links = {}

    columns = schema.get_columns(engine, state.table_name)
    name_col = schema.get_name_column(engine, state.table_name)
    fks = schema.get_all_foreign_keys(engine, state.table_name)
    reverse_fks = schema.get_reverse_foreign_keys(engine, state.table_name)

    # Get primary key column for reverse FK lookups
    pk_cols = [c["name"] for c in columns if c["pk"]]
    pk_column = pk_cols[0] if pk_cols else None

    # Build column list for display
    display_columns = build_column_list(engine, state, record_links)

    # Build SELECT clause
    col_names = [col["name"] for col in columns]

    # Build FROM clause with JOINs for FKs and lookup fields
    from_clause = f'"{state.table_name}"'
    fk_map = {}  # Map FK column to alias
    lookup_map = {}  # Map lookup field id to (alias, field_name)
    has_joins = False

    for fk in fks:
        alias = f"{fk['ref_table']}_ref"
        need_join = False

        # Check if we need a JOIN for the FK name column
        ref_name_col = schema.get_name_column(engine, fk["ref_table"])
        if ref_name_col:
            fk_map[fk["column"]] = (alias, ref_name_col)
            need_join = True

        # Check if we need a JOIN for lookup fields
        if fk["column"] in record_links:
            record_link = record_links[fk["column"]]
            if record_link.lookup_fields:
                # We need the JOIN for lookup fields
                need_join = True
                for lookup_field in record_link.lookup_fields:
                    lookup_id = schema.get_lookup_field_name(fk["column"], lookup_field.field)
                    lookup_map[lookup_id] = (alias, lookup_field.field)

        # Create the JOIN if needed
        if need_join:
            from_clause += f' LEFT JOIN "{fk["ref_table"]}" AS "{alias}" ON "{state.table_name}"."{fk["column"]}" = "{alias}"."{fk["ref_column"]}"'
            has_joins = True

    # Qualify column names with table name if we have JOINs to avoid ambiguity
    if has_joins:
        qualified_col_names = [f'"{state.table_name}"."{col}"' for col in col_names]
        select_clause = ", ".join(qualified_col_names)
    else:
        select_clause = ", ".join([f'"{col}"' for col in col_names])

    # Add FK name columns to SELECT
    for fk_col, (alias, ref_name_col) in fk_map.items():
        select_clause += f', "{alias}"."{ref_name_col}" AS "{fk_col}_name"'

    # Add lookup fields to SELECT
    for lookup_id, (alias, field_name) in lookup_map.items():
        select_clause += f', "{alias}"."{field_name}" AS "{lookup_id}"'

    # Build WHERE clause from filters
    where_clause, where_params = build_where_clause(state.filters, state.table_name, lookup_map)

    grouped_rows = {}

    with engine.connect() as conn:
        if not state.grouping:
            # No grouping - fetch all rows
            query = f"SELECT {select_clause} FROM {from_clause}{where_clause}"
            result = conn.execute(text(query), where_params)

            rows = []
            for row in result.fetchall():
                row_data = dict(
                    zip(
                        col_names
                        + [f"{fk}_name" for fk in fk_map.keys()]
                        + list(lookup_map.keys()),
                        row,
                        strict=False,
                    )
                )

                # Add reverse FK preview data
                if pk_column and reverse_fks:
                    pk_value = row_data.get(pk_column)
                    if pk_value is not None:
                        for rfk in reverse_fks:
                            preview = fetch_reverse_fk_preview(
                                engine,
                                rfk,
                                pk_value,
                                max_items=reverse_fk_preview_items,
                            )
                            # Store with display name as key
                            rfk_display_name = schema.to_title_case(rfk["from_table"])
                            row_data[f"_rfk_{rfk_display_name}"] = preview

                row_display = build_row(
                    display_columns,
                    columns,
                    row_data,
                    fk_map,
                    reverse_fks,
                    cell_truncation_length=cell_truncation_length,
                    field_formats=field_formats,
                    lookup_map=lookup_map,
                    engine=engine,
                    table_name=state.table_name,
                    record_links=record_links,
                )
                rows.append((row_data, row_display))

            grouped_rows[None] = rows

        else:
            # Multi-level grouping enabled - use single query with ORDER BY
            group_cols = state.grouping

            # Build WHERE clause to exclude NULL/empty values for all group columns
            non_null_conditions = []
            for col in group_cols:
                # Check if this is a lookup field
                if col in lookup_map:
                    alias, field_name = lookup_map[col]
                    non_null_conditions.append(
                        f'"{alias}"."{field_name}" IS NOT NULL AND "{alias}"."{field_name}" != \'\''
                    )
                else:
                    non_null_conditions.append(
                        f'"{state.table_name}"."{col}" IS NOT NULL AND "{state.table_name}"."{col}" != \'\''
                    )
            non_null_clause = " AND ".join(non_null_conditions)

            # Combine filter WHERE with non-null conditions
            if where_clause:
                full_where = f"{where_clause} AND {non_null_clause}"
                combined_params = where_params
            else:
                full_where = f" WHERE {non_null_clause}"
                combined_params = {}

            # Build ORDER BY clause - order by grouping columns, then any sorting
            order_by_parts = []
            for col in group_cols:
                # Check if this is a lookup field
                if col in lookup_map:
                    alias, field_name = lookup_map[col]
                    order_by_parts.append(f'"{alias}"."{field_name}"')
                elif has_joins:
                    order_by_parts.append(f'"{state.table_name}"."{col}"')
                else:
                    order_by_parts.append(f'"{col}"')

            order_by_clause = f' ORDER BY {", ".join(order_by_parts)}'

            # Execute single query to fetch all rows, ordered by grouping columns
            query = f"SELECT {select_clause} FROM {from_clause}{full_where}{order_by_clause}"
            result = conn.execute(text(query), combined_params)

            # Group rows in Python as we iterate
            current_group_vals = None
            current_group_rows = []

            for row in result.fetchall():
                row_data = dict(
                    zip(
                        col_names
                        + [f"{fk}_name" for fk in fk_map.keys()]
                        + list(lookup_map.keys()),
                        row,
                        strict=False,
                    )
                )

                # Extract grouping column values for this row
                group_vals = tuple(row_data.get(col) for col in group_cols)

                # Check if we've moved to a new group
                if current_group_vals is not None and group_vals != current_group_vals:
                    # Save the previous group
                    if current_group_rows:
                        # Build combined header from all grouping levels
                        header_parts = []
                        assert current_group_vals is not None  # Type checker hint
                        for col_name, group_val in zip(
                            group_cols, current_group_vals, strict=False
                        ):
                            # Check if this is a lookup field
                            if col_name in lookup_map:
                                # Parse the lookup field name
                                parsed = schema.parse_lookup_field_name(col_name)
                                if parsed:
                                    fk_col, field_name = parsed
                                    # Get the display name for the lookup field
                                    display_name = schema.get_lookup_field_display_name(
                                        engine,
                                        state.table_name,
                                        fk_col,
                                        field_name,
                                        None,  # Let it auto-generate from field name
                                    )
                                    header_parts.append(f"{display_name}: {group_val}")
                                else:
                                    header_parts.append(str(group_val))
                            else:
                                group_col = next(
                                    (c for c in columns if c["name"] == col_name), None
                                )
                                if group_col:
                                    # Check if this is an FK - use the referenced name if available
                                    if col_name in fk_map:
                                        # Look up the name from the first row
                                        group_display = current_group_rows[0][0].get(
                                            f"{col_name}_name", group_val
                                        )
                                    else:
                                        group_display = group_val

                                    header_parts.append(
                                        f"{group_col['display_name']}: {group_display}"
                                    )
                                else:
                                    header_parts.append(str(group_val))

                        # Combine all parts with " | " separator
                        group_header = " | ".join(header_parts)
                        grouped_rows[group_header] = current_group_rows

                    # Start new group
                    current_group_vals = group_vals
                    current_group_rows = []

                # First row or continuing current group
                if current_group_vals is None:
                    current_group_vals = group_vals

                # Add reverse FK preview data
                if pk_column and reverse_fks:
                    pk_value = row_data.get(pk_column)
                    if pk_value is not None:
                        for rfk in reverse_fks:
                            preview = fetch_reverse_fk_preview(
                                engine,
                                rfk,
                                pk_value,
                                max_items=reverse_fk_preview_items,
                            )
                            # Store with display name as key
                            rfk_display_name = schema.to_title_case(rfk["from_table"])
                            row_data[f"_rfk_{rfk_display_name}"] = preview

                row_display = build_row(
                    display_columns,
                    columns,
                    row_data,
                    fk_map,
                    reverse_fks,
                    cell_truncation_length=cell_truncation_length,
                    field_formats=field_formats,
                    lookup_map=lookup_map,
                    engine=engine,
                    table_name=state.table_name,
                    record_links=record_links,
                )
                current_group_rows.append((row_data, row_display))

            # Don't forget the last group
            if current_group_rows and current_group_vals is not None:
                header_parts = []
                for col_name, group_val in zip(group_cols, current_group_vals, strict=False):
                    # Check if this is a lookup field
                    if col_name in lookup_map:
                        # Parse the lookup field name
                        parsed = schema.parse_lookup_field_name(col_name)
                        if parsed:
                            fk_col, field_name = parsed
                            # Get the display name for the lookup field
                            display_name = schema.get_lookup_field_display_name(
                                engine,
                                state.table_name,
                                fk_col,
                                field_name,
                                None,  # Let it auto-generate from field name
                            )
                            header_parts.append(f"{display_name}: {group_val}")
                        else:
                            header_parts.append(str(group_val))
                    else:
                        group_col = next((c for c in columns if c["name"] == col_name), None)
                        if group_col:
                            # Check if this is an FK - use the referenced name if available
                            if col_name in fk_map:
                                # Look up the name from the first row
                                group_display = current_group_rows[0][0].get(
                                    f"{col_name}_name", group_val
                                )
                            else:
                                group_display = group_val

                            header_parts.append(f"{group_col['display_name']}: {group_display}")
                        else:
                            header_parts.append(str(group_val))

                # Combine all parts with " | " separator
                group_header = " | ".join(header_parts)
                grouped_rows[group_header] = current_group_rows

    return grouped_rows


def build_row(
    display_columns: list[str],
    all_columns: list[dict[str, Any]],
    row_data: dict[str, Any],
    fk_map: dict[str, tuple[str, str]],
    reverse_fks: list[dict[str, str]] | None = None,
    cell_truncation_length: int = 80,
    field_formats: dict[str, str] | None = None,
    lookup_map: dict[str, tuple[str, str]] | None = None,
    engine: Any = None,
    table_name: str | None = None,
    record_links: dict[str, Any] | None = None,
) -> list[str]:
    """
    Build a display row from raw data.

    Args:
        display_columns: List of column display names to show
        all_columns: List of all column metadata dicts
        row_data: Dict mapping column names to values
        fk_map: Dict mapping FK column names to (alias, ref_col_name) tuples
        reverse_fks: List of reverse FK metadata dicts
        cell_truncation_length: Max characters before truncation (default: 80)
        field_formats: Dict mapping field names to format types (e.g., 'currency')
        lookup_map: Dict mapping lookup field IDs to (alias, field_name) tuples
        engine: SQLAlchemy engine (needed for lookup field display names)
        table_name: Table name (needed for lookup field display names)
        record_links: Dict of RecordLink configurations

    Returns:
        List of display values
    """
    if reverse_fks is None:
        reverse_fks = []
    if field_formats is None:
        field_formats = {}
    if lookup_map is None:
        lookup_map = {}
    if record_links is None:
        record_links = {}

    # Create lookup dict from display name to column metadata
    col_lookup = {col["display_name"]: col for col in all_columns}

    # Also add PK columns with the icon prefix to the lookup
    for col in all_columns:
        if col["pk"]:
            col_lookup[f"🔑 {col['display_name']}"] = col

    # Build reverse mapping from display names to lookup IDs
    # This requires regenerating display names the same way build_column_list does
    lookup_display_to_id = {}
    if engine and table_name and record_links:
        for fk_column, record_link in record_links.items():
            if record_link.lookup_fields:
                for lookup_field in record_link.lookup_fields:
                    lookup_id = schema.get_lookup_field_name(fk_column, lookup_field.field)
                    display_name = schema.get_lookup_field_display_name(
                        engine,
                        table_name,
                        fk_column,
                        lookup_field.field,
                        lookup_field.display_name,
                    )
                    lookup_display_to_id[display_name] = lookup_id

    row = []
    for disp_col in display_columns:
        col_meta = col_lookup.get(disp_col)

        # Check if this is a reverse FK column
        is_reverse_fk = False
        for rfk in reverse_fks:
            if schema.to_title_case(rfk["from_table"]) == disp_col:
                # This is a reverse FK preview column
                preview_key = f"_rfk_{disp_col}"
                row.append(row_data.get(preview_key, ""))
                is_reverse_fk = True
                break

        if is_reverse_fk:
            continue

        # Check if this is a lookup field by display name
        if disp_col in lookup_display_to_id:
            lookup_id = lookup_display_to_id[disp_col]
            value = row_data.get(lookup_id)
            if value is None or value == "":
                row.append("")
            else:
                # Truncate if too long
                value_str = str(value)
                if len(value_str) > cell_truncation_length:
                    row.append(value_str[:cell_truncation_length] + "...")
                else:
                    row.append(value_str)
            continue

        if not col_meta:
            row.append("")
            continue

        col_name = col_meta["name"]
        value = row_data.get(col_name)

        # Check if this is an FK with a display name
        if col_name in fk_map and f"{col_name}_name" in row_data:
            display_value = row_data.get(f"{col_name}_name")
            if display_value:
                row.append(str(display_value))
                continue

        # Format value based on type and configuration
        if value is None or value == "":
            row.append("")
        elif col_meta["type"] in ("INTEGER", "REAL", "NUMERIC"):
            # Check if this field has a format configuration
            field_format = field_formats.get(col_name)
            if field_format == "currency":
                try:
                    row.append(f"${float(value):,.2f}")
                except:
                    row.append(str(value))
            else:
                # Plain number formatting
                row.append(str(value))
        else:
            # Text - truncate if too long
            value_str = str(value)
            if len(value_str) > cell_truncation_length:
                row.append(value_str[:cell_truncation_length] + "...")
            else:
                row.append(value_str)

    return row


def sort_rows(
    rows: list[tuple[dict[str, Any], list[str]]],
    display_columns: list[str],
    sort_config: list[tuple[str, str]],
) -> list[tuple[dict[str, Any], list[str]]]:
    """
    Sort rows according to sort configuration.

    Args:
        rows: List of (row_data_dict, row_display_list) tuples
        display_columns: List of column display names
        sort_config: List of (column_display_name, direction) tuples

    Returns:
        Sorted list of rows
    """
    if not sort_config:
        return rows

    def sort_key(row_tuple):
        row_data, row_display = row_tuple
        key = []

        for col_name, direction in sort_config:
            # Find column index
            try:
                col_idx = display_columns.index(col_name)
                value = row_display[col_idx]

                # Handle None/empty
                if value is None or value == "":
                    value = ""

                # Normalize for case-insensitive sorting
                if isinstance(value, str):
                    # Try to parse as number first
                    if (
                        value.replace(".", "")
                        .replace(",", "")
                        .replace("$", "")
                        .replace("-", "")
                        .isdigit()
                    ):
                        try:
                            value = float(value.replace("$", "").replace(",", ""))
                        except:
                            value = value.lower()
                    else:
                        value = value.lower()

                # Always append value as-is for key generation
                # Direction will be handled by reversing the final sorted list
                key.append(value)
            except (ValueError, IndexError):
                key.append("")

        return key

    sorted_rows = sorted(rows, key=sort_key)

    # Handle descending for string columns (reverse the order)
    # This is a simplified approach - a full implementation would need
    # to handle mixed asc/desc properly
    has_desc = any(direction == "desc" for _, direction in sort_config)
    if has_desc and len(sort_config) == 1 and sort_config[0][1] == "desc":
        sorted_rows = list(reversed(sorted_rows))

    return sorted_rows


def load_table_display(
    engine: Engine,
    state: TableState,
    reverse_fk_preview_items: int = 2,
    cell_truncation_length: int = 80,
    field_formats: dict[str, str] | None = None,
    record_links: dict[str, Any] | None = None,
) -> tuple[list[str], dict[str | None, list[tuple[dict[str, Any], list[str]]]]]:
    """
    Load complete table display data.

    Args:
        engine: SQLAlchemy database engine
        state: Table state
        reverse_fk_preview_items: Max items to show in reverse FK previews (default: 2)
        cell_truncation_length: Max characters in cells before truncation (default: 80)
        field_formats: Dict mapping field names to format types (e.g., 'currency')
        record_links: Optional dict of RecordLink configurations from config

    Returns:
        Tuple of (column_names, grouped_rows_dict) where grouped_rows_dict maps
        group headers (or None) to lists of (row_data, row_display) tuples
    """
    if field_formats is None:
        field_formats = {}
    if record_links is None:
        record_links = {}

    # Get column list
    columns = build_column_list(engine, state, record_links)

    # Fetch grouped data
    grouped_data = fetch_grouped_data(
        engine,
        state,
        reverse_fk_preview_items=reverse_fk_preview_items,
        cell_truncation_length=cell_truncation_length,
        field_formats=field_formats,
        record_links=record_links,
    )

    # Sort within each group (keep both row_data and row_display)
    result = {}
    for group_name, rows in grouped_data.items():
        sorted_rows = sort_rows(rows, columns, state.sort_config)
        result[group_name] = sorted_rows

    return columns, result


def calculate_column_widths(
    columns: list[str], grouped_rows: dict[str | None, list[list[str]]]
) -> list[int]:
    """
    Calculate maximum column widths across all groups.

    Args:
        columns: List of column names
        grouped_rows: Dict mapping group names to row lists

    Returns:
        List of column widths
    """
    col_widths = [len(col) for col in columns]

    # Check all rows in all groups
    for rows in grouped_rows.values():
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))

    return col_widths
