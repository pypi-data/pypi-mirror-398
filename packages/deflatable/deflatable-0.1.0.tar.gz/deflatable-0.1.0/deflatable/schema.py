"""Database schema introspection using SQLAlchemy Core."""

from typing import Any

from sqlalchemy import Engine, inspect, text


def to_title_case(snake_case: str) -> str:
    """Convert snake_case to Title Case."""
    return " ".join(word.capitalize() for word in snake_case.replace("_", " ").split())


def get_tables(engine: Engine) -> list[str]:
    """
    Get list of table names from the database.

    Args:
        engine: SQLAlchemy database engine

    Returns:
        List of table names sorted alphabetically
    """
    inspector = inspect(engine)
    return sorted(inspector.get_table_names())


def get_columns(engine: Engine, table: str) -> list[dict[str, Any]]:
    """
    Get column information for a table.

    Args:
        engine: SQLAlchemy database engine
        table: Table name

    Returns:
        List of dicts with keys: name, type, pk (bool), notnull (bool), display_name
    """
    inspector = inspect(engine)
    columns = []

    # Get column info
    for col in inspector.get_columns(table):
        columns.append(
            {
                "name": col["name"],
                "type": str(col["type"]).upper(),
                "pk": col.get("primary_key", False),
                "notnull": not col["nullable"],
                "display_name": to_title_case(col["name"]),
            }
        )

    return columns


def get_foreign_keys(engine: Engine, table: str) -> list[dict[str, str]]:
    """
    Get foreign key relationships for a table.

    Args:
        engine: SQLAlchemy database engine
        table: Table name

    Returns:
        List of dicts with keys: column, ref_table, ref_column
    """
    inspector = inspect(engine)
    fks = []

    for fk in inspector.get_foreign_keys(table):
        # SQLAlchemy returns FK info as a dict with:
        # - constrained_columns: list of columns in this table
        # - referred_table: name of referenced table
        # - referred_columns: list of columns in referenced table

        # Handle composite FKs (though rare in practice)
        for i, column in enumerate(fk["constrained_columns"]):
            ref_column = (
                fk["referred_columns"][i]
                if i < len(fk["referred_columns"])
                else fk["referred_columns"][0]
            )
            fks.append(
                {
                    "column": column,
                    "ref_table": fk["referred_table"],
                    "ref_column": ref_column,
                }
            )

    return fks


def detect_foreign_keys_from_names(
    engine: Engine, table: str, columns: list[dict]
) -> list[dict[str, str]]:
    """
    Detect likely foreign key relationships from column naming conventions.

    Looks for columns ending in '_id' or matching table names.

    Args:
        engine: SQLAlchemy database engine
        table: Table name
        columns: List of column dicts from get_columns()

    Returns:
        List of dicts with keys: column, ref_table, ref_column
    """
    tables = get_tables(engine)
    fks = []

    for col in columns:
        col_name = col["name"]

        # Check if column ends with _id
        if col_name.endswith("_id"):
            # Try to find matching table
            potential_table = col_name[:-3]  # Remove '_id'

            # Try exact match
            if potential_table in tables and potential_table != table:  # Skip self-references
                fks.append(
                    {
                        "column": col_name,
                        "ref_table": potential_table,
                        "ref_column": f"{potential_table}_id",  # Assume same naming convention
                    }
                )
                continue

            # Try singular -> plural (e.g., system -> systems)
            plural = potential_table + "s"
            if plural in tables and plural != table:  # Skip self-references
                # Find the PK of the referenced table
                ref_cols = get_columns(engine, plural)
                pk_cols = [c for c in ref_cols if c["pk"]]
                if pk_cols:
                    fks.append(
                        {
                            "column": col_name,
                            "ref_table": plural,
                            "ref_column": pk_cols[0]["name"],
                        }
                    )
                    continue

            # Try plural -> singular (e.g., systems -> system)
            if potential_table.endswith("s"):
                singular = potential_table[:-1]
                if singular in tables and singular != table:  # Skip self-references
                    ref_cols = get_columns(engine, singular)
                    pk_cols = [c for c in ref_cols if c["pk"]]
                    if pk_cols:
                        fks.append(
                            {
                                "column": col_name,
                                "ref_table": singular,
                                "ref_column": pk_cols[0]["name"],
                            }
                        )
                        continue

        # Check if column name matches a table name exactly
        if col_name in tables and col_name != table:  # Skip self-references
            # Find primary key of referenced table
            ref_cols = get_columns(engine, col_name)
            pk_cols = [c for c in ref_cols if c["pk"]]
            if pk_cols:
                fks.append(
                    {
                        "column": col_name,
                        "ref_table": col_name,
                        "ref_column": pk_cols[0]["name"],
                    }
                )

    return fks


def get_all_foreign_keys(engine: Engine, table: str) -> list[dict[str, str]]:
    """
    Get all foreign keys, combining explicit FKs and naming conventions.

    Args:
        engine: SQLAlchemy database engine
        table: Table name

    Returns:
        List of dicts with keys: column, ref_table, ref_column
    """
    columns = get_columns(engine, table)

    # Get explicit FKs from database schema
    explicit_fks = get_foreign_keys(engine, table)

    # Get inferred FKs from naming
    inferred_fks = detect_foreign_keys_from_names(engine, table, columns)

    # Combine, preferring explicit FKs
    fk_columns = {fk["column"] for fk in explicit_fks}
    all_fks = explicit_fks.copy()

    for fk in inferred_fks:
        if fk["column"] not in fk_columns:
            all_fks.append(fk)

    return all_fks


def get_reverse_foreign_keys(engine: Engine, table: str) -> list[dict[str, str]]:
    """
    Get reverse foreign key relationships - tables that reference this table.

    For example, if components.system_id references systems.system_id,
    then calling this on 'systems' would return info about the components relationship.

    Args:
        engine: SQLAlchemy database engine
        table: Table name to find reverse relationships for

    Returns:
        List of dicts with keys: from_table, from_column, to_column, name_column
    """
    all_tables = get_tables(engine)
    reverse_fks = []

    # Get primary key of this table
    columns = get_columns(engine, table)
    pk_cols = [c["name"] for c in columns if c["pk"]]
    if not pk_cols:
        return []

    pk_col = pk_cols[0]

    # Check each other table for FKs pointing to this table
    for other_table in all_tables:
        if other_table == table:
            continue

        fks = get_all_foreign_keys(engine, other_table)
        for fk in fks:
            if fk["ref_table"] == table and fk["ref_column"] == pk_col:
                # Found a reverse FK!
                # Get name column from the referencing table
                name_col = get_name_column(engine, other_table)

                reverse_fks.append(
                    {
                        "from_table": other_table,
                        "from_column": fk["column"],
                        "to_column": pk_col,
                        "name_column": name_col or "id",
                    }
                )

    return reverse_fks


def get_grouping_options_with_metadata(
    engine: Engine,
    table: str,
    filters=None,
    max_distinct: int = 200,
    max_ratio: float = 0.7,
    min_distinct: int = 2,
    excluded_types: list[str] | None = None,
    record_links: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Get all possible grouping options with cardinality metadata.

    Returns all non-PK columns with information about their suitability for grouping.

    Args:
        engine: SQLAlchemy database engine
        table: Table name
        filters: Optional list of (field, operator, value, boolean_op) tuples to apply when checking cardinality
        max_distinct: Maximum distinct values to recommend a column (default: 200)
        max_ratio: Maximum cardinality ratio (distinct/total) to recommend (default: 0.7)
        min_distinct: Minimum distinct values to recommend a column (default: 2)
        excluded_types: List of column type prefixes to exclude from grouping (default: BLOBs, dates, floats, etc.)
        record_links: Optional dict of RecordLink configurations from config

    Returns:
        List of dicts with keys:
            - column_name: Column name (or lookup field ID for lookup fields)
            - display_name: Display name for UI
            - distinct_count: Number of distinct values (None if couldn't be computed)
            - total_count: Total non-null values (None if couldn't be computed)
            - is_fk: Whether this is a foreign key
            - recommended: Whether this column is recommended for grouping
    """
    # Use default excluded types if not provided
    if excluded_types is None:
        excluded_types = [
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

    columns = get_columns(engine, table)
    fks = get_all_foreign_keys(engine, table)
    fk_columns = {fk["column"]: fk["ref_table"] for fk in fks}

    options = []

    for col in columns:
        # Skip primary keys
        if col["pk"]:
            continue

        # Skip denormalized FK name columns
        if "_from_" in col["name"] or col["name"].startswith("name_from"):
            continue

        # Skip column types that definitely won't work for grouping
        col_type_upper = col["type"].upper()
        if any(col_type_upper.startswith(t) for t in excluded_types):
            continue

        is_fk = col["name"] in fk_columns

        # Try to compute cardinality
        distinct_count = None
        total_count = None

        try:
            # Build WHERE clause for filters
            where_parts = []
            params = {}
            param_count = 0

            # Always exclude NULL values from the column being checked
            where_parts.append(f'"{col["name"]}" IS NOT NULL')

            # Add filter conditions if provided
            if filters:
                for field, op, value, bool_op in filters:
                    qualified_field = f'"{table}"."{field}"'
                    param_name = f"param_{param_count}"
                    param_count += 1

                    if op == "is":
                        where_parts.append(f"{qualified_field} = :{param_name}")
                        params[param_name] = value
                    elif op == "is_not":
                        where_parts.append(f"{qualified_field} != :{param_name}")
                        params[param_name] = value
                    elif op == "contains":
                        where_parts.append(f"{qualified_field} LIKE :{param_name}")
                        params[param_name] = f"%{value}%"
                    elif op == "starts_with":
                        where_parts.append(f"{qualified_field} LIKE :{param_name}")
                        params[param_name] = f"{value}%"
                    elif op == "ends_with":
                        where_parts.append(f"{qualified_field} LIKE :{param_name}")
                        params[param_name] = f"%{value}"

            where_clause = " AND ".join(where_parts)
            query = text(
                f'SELECT COUNT(DISTINCT "{col["name"]}") as distinct_count, COUNT(*) as total FROM "{table}" WHERE {where_clause}'
            )

            with engine.connect() as conn:
                result = conn.execute(query, params)
                row = result.fetchone()
                if row:
                    distinct_count, total_count = row[0], row[1]
        except Exception:
            # Couldn't compute cardinality
            pass

        # Determine if recommended based on cardinality or FK status
        recommended = False
        if is_fk:
            # All FKs are recommended
            recommended = True
        elif distinct_count is not None and total_count is not None and total_count > 0:
            # Recommended if low cardinality using provided thresholds
            ratio = distinct_count / total_count
            if min_distinct <= distinct_count <= max_distinct and ratio < max_ratio:
                recommended = True

        # Build display name
        if is_fk:
            ref_table = fk_columns[col["name"]]
            display_name = f"Group by {to_title_case(ref_table)}"
        else:
            display_name = f"Group by {col['display_name']}"

        options.append(
            {
                "column_name": col["name"],
                "display_name": display_name,
                "distinct_count": distinct_count,
                "total_count": total_count,
                "is_fk": is_fk,
                "recommended": recommended,
            }
        )

    # Add lookup fields from record links
    if record_links:
        for fk_column, record_link in record_links.items():
            if record_link.lookup_fields:
                for lookup_field in record_link.lookup_fields:
                    # Get the referenced table name for display
                    ref_table = None
                    for fk in fks:
                        if fk["column"] == fk_column:
                            ref_table = fk["ref_table"]
                            break

                    if not ref_table:
                        continue  # Skip if FK not found

                    # Generate lookup field identifier
                    lookup_id = get_lookup_field_name(fk_column, lookup_field.field)

                    # Build display name
                    field_display = lookup_field.display_name or to_title_case(lookup_field.field)
                    display_name = f"Group by {field_display} (from {to_title_case(ref_table)})"

                    # Try to compute cardinality for the lookup field
                    distinct_count = None
                    total_count = None

                    try:
                        # Build JOIN for the FK relationship
                        pk_cols = [c["name"] for c in columns if c["pk"]]
                        pk_column = pk_cols[0] if pk_cols else None

                        if pk_column:
                            # Get FK details
                            fk_details = None
                            for fk in fks:
                                if fk["column"] == fk_column:
                                    fk_details = fk
                                    break

                            if fk_details:
                                alias = f"{ref_table}_ref"

                                # Build WHERE clause
                                where_parts = []
                                params = {}
                                param_count = 0

                                # Exclude NULL values from the lookup field
                                where_parts.append(f'"{alias}"."{lookup_field.field}" IS NOT NULL')

                                # Add filter conditions if provided (need to handle lookup fields in filters too)
                                if filters:
                                    for field, op, value, bool_op in filters:
                                        qualified_field = f'"{table}"."{field}"'
                                        param_name = f"param_{param_count}"
                                        param_count += 1

                                        if op == "is":
                                            where_parts.append(f"{qualified_field} = :{param_name}")
                                            params[param_name] = value
                                        elif op == "is_not":
                                            where_parts.append(
                                                f"{qualified_field} != :{param_name}"
                                            )
                                            params[param_name] = value
                                        elif op == "contains":
                                            where_parts.append(
                                                f"{qualified_field} LIKE :{param_name}"
                                            )
                                            params[param_name] = f"%{value}%"
                                        elif op == "starts_with":
                                            where_parts.append(
                                                f"{qualified_field} LIKE :{param_name}"
                                            )
                                            params[param_name] = f"{value}%"
                                        elif op == "ends_with":
                                            where_parts.append(
                                                f"{qualified_field} LIKE :{param_name}"
                                            )
                                            params[param_name] = f"%{value}"

                                where_clause = " AND ".join(where_parts)
                                query = text(
                                    f"""SELECT COUNT(DISTINCT "{alias}"."{lookup_field.field}") as distinct_count, COUNT(*) as total
                                    FROM "{table}"
                                    LEFT JOIN "{ref_table}" AS "{alias}" ON "{table}"."{fk_column}" = "{alias}"."{fk_details['ref_column']}"
                                    WHERE {where_clause}"""
                                )

                                with engine.connect() as conn:
                                    result = conn.execute(query, params)
                                    row = result.fetchone()
                                    if row:
                                        distinct_count, total_count = row[0], row[1]
                    except Exception:
                        # Couldn't compute cardinality
                        pass

                    # Determine if recommended based on cardinality
                    recommended = False
                    if distinct_count is not None and total_count is not None and total_count > 0:
                        ratio = distinct_count / total_count
                        if min_distinct <= distinct_count <= max_distinct and ratio < max_ratio:
                            recommended = True

                    options.append(
                        {
                            "column_name": lookup_id,
                            "display_name": display_name,
                            "distinct_count": distinct_count,
                            "total_count": total_count,
                            "is_fk": False,  # It's a lookup field, not directly a FK
                            "recommended": recommended,
                        }
                    )

    return options


def get_grouping_options(engine: Engine, table: str, filters=None) -> list[tuple[str, str]]:
    """
    Get suggested grouping options for a table.

    Returns foreign key relationships and low-cardinality columns suitable for grouping.

    Args:
        engine: SQLAlchemy database engine
        table: Table name
        filters: Optional list of (field, operator, value, boolean_op) tuples to apply when checking cardinality

    Returns:
        List of tuples: (display_name, column_name)
    """
    # Use the new metadata function and filter to recommended only
    all_options = get_grouping_options_with_metadata(engine, table, filters)
    return [(opt["display_name"], opt["column_name"]) for opt in all_options if opt["recommended"]]


def get_default_visible_fields(engine: Engine, table: str) -> set:
    """
    Get a reasonable default set of visible fields for a table.

    Shows all columns by default (up to 8 to avoid overwhelming the UI).
    Also includes reverse FK columns by default.
    Users can hide columns they don't want via the Fields button.

    Args:
        engine: SQLAlchemy database engine
        table: Table name

    Returns:
        Set of column names to show by default (includes reverse FK column names)
    """
    columns = get_columns(engine, table)

    # Show all columns (up to first 8 to avoid overwhelming UI)
    visible = {col["name"] for col in columns[:8]}

    # Add reverse FK columns by default
    reverse_fks = get_reverse_foreign_keys(engine, table)
    for rfk in reverse_fks:
        visible.add(rfk["from_table"])

    return visible


def get_name_column(engine: Engine, table: str) -> str | None:
    """
    Try to identify the "name" column for a table.

    Looks for columns named 'name', 'title', or containing 'name'.

    Args:
        engine: SQLAlchemy database engine
        table: Table name

    Returns:
        Column name or None
    """
    columns = get_columns(engine, table)

    # Exact matches first
    for col in columns:
        if col["name"].lower() in ("name", "title"):
            return col["name"]

    # Partial matches
    for col in columns:
        if "name" in col["name"].lower() or "title" in col["name"].lower():
            return col["name"]

    # Return first non-PK text column
    for col in columns:
        if not col["pk"] and col["type"] in ("TEXT", "VARCHAR", "CHAR"):
            return col["name"]

    return None


def get_column_display_name(engine: Engine, table: str, column: str) -> str:
    """
    Get the display name for a column.

    Args:
        engine: SQLAlchemy database engine
        table: Table name
        column: Column name

    Returns:
        Display name
    """
    columns = get_columns(engine, table)
    for col in columns:
        if col["name"] == column:
            return col["display_name"]

    return to_title_case(column)


def add_column(
    engine: Engine,
    table: str,
    column_name: str,
    column_type: str,
    default_value: str | None = None,
) -> None:
    """
    Add a new column to a table.

    Args:
        engine: SQLAlchemy database engine
        table: Table name
        column_name: Name of the new column
        column_type: SQL data type (e.g., 'TEXT', 'INTEGER', 'REAL')
        default_value: Optional default value for the column

    Raises:
        ValueError: If column already exists or invalid inputs
        Exception: If SQL execution fails
    """
    # Validate column doesn't already exist
    existing_columns = get_columns(engine, table)
    if any(col["name"] == column_name for col in existing_columns):
        raise ValueError(f"Column '{column_name}' already exists in table '{table}'")

    # Build ALTER TABLE statement
    sql = f'ALTER TABLE "{table}" ADD COLUMN "{column_name}" {column_type}'

    if default_value is not None:
        # SQLite requires a default value when adding NOT NULL columns to existing tables
        sql += f" DEFAULT '{default_value}'"

    # Execute the ALTER TABLE
    with engine.begin() as conn:
        conn.execute(text(sql))


def remove_column(engine: Engine, table: str, column_name: str) -> None:
    """
    Remove a column from a table.

    Note: In SQLite, removing a column requires recreating the table.
    This is a destructive operation and cannot be undone.

    Args:
        engine: SQLAlchemy database engine
        table: Table name
        column_name: Name of the column to remove

    Raises:
        ValueError: If column doesn't exist or is a primary key
        Exception: If SQL execution fails
    """
    # Validate column exists and is not a primary key
    existing_columns = get_columns(engine, table)
    column_to_remove = None
    for col in existing_columns:
        if col["name"] == column_name:
            column_to_remove = col
            break

    if not column_to_remove:
        raise ValueError(f"Column '{column_name}' does not exist in table '{table}'")

    if column_to_remove["pk"]:
        raise ValueError(f"Cannot remove primary key column '{column_name}'")

    # For SQLite 3.35.0+, we can use ALTER TABLE DROP COLUMN
    # For older versions, we'd need to recreate the table
    # Let's try the simple approach first
    try:
        sql = f'ALTER TABLE "{table}" DROP COLUMN "{column_name}"'
        with engine.begin() as conn:
            conn.execute(text(sql))
    except Exception as e:
        # If DROP COLUMN is not supported, we need to recreate the table
        # This is more complex and risky, so we'll raise an error for now
        raise Exception(
            f"Failed to drop column. Your SQLite version may not support DROP COLUMN. "
            f"Error: {str(e)}"
        ) from e


def rename_column(engine: Engine, table: str, old_name: str, new_name: str) -> None:
    """
    Rename a column in a table.

    Note: Requires SQLite 3.25.0+ (2018).

    Args:
        engine: SQLAlchemy database engine
        table: Table name
        old_name: Current column name
        new_name: New column name

    Raises:
        ValueError: If column doesn't exist or new name already exists
        Exception: If SQL execution fails
    """
    # Validate old column exists
    existing_columns = get_columns(engine, table)
    column_names = [col["name"] for col in existing_columns]

    if old_name not in column_names:
        raise ValueError(f"Column '{old_name}' does not exist in table '{table}'")

    if new_name in column_names:
        raise ValueError(f"Column '{new_name}' already exists in table '{table}'")

    # Execute the RENAME COLUMN
    sql = f'ALTER TABLE "{table}" RENAME COLUMN "{old_name}" TO "{new_name}"'
    with engine.begin() as conn:
        conn.execute(text(sql))


def create_table(engine: Engine, table_name: str, columns: list[dict[str, Any]]) -> None:
    """
    Create a new table in the database.

    Args:
        engine: SQLAlchemy database engine
        table_name: Name of the table to create
        columns: List of column definitions, each dict with keys:
            - name: Column name (required)
            - type: SQL data type like 'TEXT', 'INTEGER', 'REAL' (required)
            - nullable: Whether column can be NULL (default: True)
            - default: Optional default value
            - primary_key: Whether this column is the primary key (default: False)

    Raises:
        ValueError: If table already exists or invalid inputs
        Exception: If SQL execution fails

    Example:
        create_table(engine, 'users', [
            {'name': 'username', 'type': 'TEXT', 'nullable': False, 'primary_key': True},
            {'name': 'email', 'type': 'TEXT'},
            {'name': 'age', 'type': 'INTEGER', 'default': 0}
        ])
    """
    # Validate table doesn't already exist
    existing_tables = get_tables(engine)
    if table_name in existing_tables:
        raise ValueError(f"Table '{table_name}' already exists")

    # Validate we have at least one column
    if not columns:
        raise ValueError("At least one column must be specified")

    # Validate column names are unique
    column_names = [col["name"] for col in columns]
    if len(column_names) != len(set(column_names)):
        raise ValueError("Column names must be unique")

    # Check for multiple primary keys
    pk_columns = [col["name"] for col in columns if col.get("primary_key", False)]
    if len(pk_columns) > 1:
        raise ValueError(
            f"Only one column can be marked as primary key, found: {', '.join(pk_columns)}"
        )

    # Build CREATE TABLE statement
    column_defs = []
    for col in columns:
        col_name = col["name"]
        col_type = col["type"].upper()

        # Build column definition
        col_def = f'"{col_name}" {col_type}'

        # Add NOT NULL if specified
        if not col.get("nullable", True):
            col_def += " NOT NULL"

        # Add DEFAULT if specified
        if "default" in col and col["default"] is not None:
            default_val = col["default"]
            # Quote string defaults
            if col_type in ("TEXT", "VARCHAR", "CHAR"):
                col_def += f" DEFAULT '{default_val}'"
            else:
                col_def += f" DEFAULT {default_val}"

        # Add PRIMARY KEY if specified
        if col.get("primary_key", False):
            col_def += " PRIMARY KEY"
            # Add AUTOINCREMENT for INTEGER primary keys
            if col_type == "INTEGER":
                col_def += " AUTOINCREMENT"

        column_defs.append(col_def)

    sql = f'CREATE TABLE "{table_name}" ({", ".join(column_defs)})'

    # Execute the CREATE TABLE
    with engine.begin() as conn:
        conn.execute(text(sql))


def drop_table(engine: Engine, table_name: str) -> None:
    """
    Drop (delete) a table from the database.

    Warning: This is a destructive operation that cannot be undone.
    All data in the table will be permanently lost.

    Args:
        engine: SQLAlchemy database engine
        table_name: Name of the table to drop

    Raises:
        ValueError: If table doesn't exist
        Exception: If SQL execution fails (e.g., foreign key constraints)
    """
    # Validate table exists
    existing_tables = get_tables(engine)
    if table_name not in existing_tables:
        raise ValueError(f"Table '{table_name}' does not exist")

    # Execute the DROP TABLE
    sql = f'DROP TABLE "{table_name}"'
    with engine.begin() as conn:
        conn.execute(text(sql))


def get_lookup_field_name(fk_column: str, lookup_field: str) -> str:
    """
    Generate a unique name for a lookup field.

    Args:
        fk_column: The FK column name (e.g., 'aisle_id')
        lookup_field: The field being looked up (e.g., 'aisle_number')

    Returns:
        Unique lookup field name (e.g., 'aisle_id__aisle_number')
    """
    return f"{fk_column}__{lookup_field}"


def parse_lookup_field_name(lookup_field_name: str) -> tuple[str, str] | None:
    """
    Parse a lookup field name back into FK column and field.

    Args:
        lookup_field_name: Name like 'aisle_id__aisle_number'

    Returns:
        Tuple of (fk_column, field) or None if not a lookup field
    """
    if "__" in lookup_field_name:
        parts = lookup_field_name.split("__", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
    return None


def get_lookup_field_display_name(
    engine: Engine,
    table: str,
    fk_column: str,
    lookup_field: str,
    custom_name: str | None = None,
) -> str:
    """
    Get display name for a lookup field.

    Args:
        engine: SQLAlchemy database engine
        table: Table name containing the FK
        fk_column: FK column name
        lookup_field: Field being looked up from related table
        custom_name: Optional custom display name from config

    Returns:
        Display name like "Aisle Number (from Aisle)"
    """
    if custom_name:
        return custom_name

    # Get the referenced table
    fks = get_all_foreign_keys(engine, table)
    ref_table = None
    for fk in fks:
        if fk["column"] == fk_column:
            ref_table = fk["ref_table"]
            break

    if not ref_table:
        # Fallback if FK not found
        return to_title_case(lookup_field)

    # Get the lookup field's display name
    lookup_display = get_column_display_name(engine, ref_table, lookup_field)

    # Get the FK link display name
    link_display = to_title_case(ref_table)

    return f"{lookup_display} (from {link_display})"


def insert_row(engine: Engine, table: str, data: dict[str, Any]) -> int:
    """
    Insert a new row into a table.

    Args:
        engine: SQLAlchemy database engine
        table: Table name
        data: Dict mapping column names to values (excludes PK for auto-increment)

    Returns:
        The ID of the newly inserted row

    Raises:
        ValueError: If data contains invalid columns
        Exception: If SQL execution fails
    """
    if not data:
        raise ValueError("Cannot insert empty row")

    # Validate columns exist
    existing_columns = {col["name"] for col in get_columns(engine, table)}
    for col_name in data.keys():
        if col_name not in existing_columns:
            raise ValueError(f"Column '{col_name}' does not exist in table '{table}'")

    # Build INSERT statement
    columns = list(data.keys())
    placeholders = ", ".join([f":{col}" for col in columns])
    column_list = ", ".join([f'"{col}"' for col in columns])

    sql = f'INSERT INTO "{table}" ({column_list}) VALUES ({placeholders})'

    # Execute the INSERT
    with engine.begin() as conn:
        result = conn.execute(text(sql), data)
        # Get the last inserted row id
        return result.lastrowid or 0


def update_row(
    engine: Engine, table: str, pk_column: str, pk_value: Any, data: dict[str, Any]
) -> None:
    """
    Update an existing row in a table.

    Args:
        engine: SQLAlchemy database engine
        table: Table name
        pk_column: Name of the primary key column
        pk_value: Value of the primary key to identify the row
        data: Dict mapping column names to new values (can include or exclude PK)

    Raises:
        ValueError: If data contains invalid columns or no data provided
        Exception: If SQL execution fails
    """
    if not data:
        raise ValueError("Cannot update with empty data")

    # Remove PK from data if present (we don't update the PK itself)
    update_data = {k: v for k, v in data.items() if k != pk_column}

    if not update_data:
        raise ValueError("No fields to update (only PK provided)")

    # Validate columns exist
    existing_columns = {col["name"] for col in get_columns(engine, table)}
    for col_name in update_data.keys():
        if col_name not in existing_columns:
            raise ValueError(f"Column '{col_name}' does not exist in table '{table}'")

    # Build UPDATE statement
    set_clauses = ", ".join([f'"{col}" = :{col}' for col in update_data.keys()])
    sql = f'UPDATE "{table}" SET {set_clauses} WHERE "{pk_column}" = :__pk_value__'

    # Add PK to parameters
    params = {**update_data, "__pk_value__": pk_value}

    # Execute the UPDATE
    with engine.begin() as conn:
        conn.execute(text(sql), params)
