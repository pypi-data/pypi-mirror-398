---
title: Configuration File Format
description: YAML configuration file reference
---

# Configuration File Format

Deflatable uses a YAML configuration file to specify database connections and view configurations.

## File Structure

```yaml
database: <sqlalchemy-url>
table_order:
  - <table-name>
  - <table-name>

settings:
  display:
    reverse_fk_preview_items: <number>
    cell_truncation_length: <number>
  grouping:
    recommendations:
      max_distinct_values: <number>
      max_cardinality_ratio: <ratio>

views:
  <table-name>:
    active_view: <view-name>
    record_links:
      <fk-column>:
        display_name: <custom-name>
        lookup_fields:
          - <field-name>
    views:
      <view-name>:
        visible_fields: [<column>, ...]
        grouping: <column>
        sort_config: [[<column>, <direction>], ...]
        filters: [[<column>, <operator>, <value>, <logic>], ...]
```

## Required Fields

### `database`

**Type**: String
**Required**: Yes
**Description**: SQLAlchemy database URL

**Examples**:
```yaml
# SQLite (relative path)
database: sqlite:///database.db

# SQLite (absolute path)
database: sqlite:////absolute/path/to/database.db

# PostgreSQL
database: postgresql://user:password@localhost:5432/dbname

# MySQL
database: mysql://user:password@localhost/dbname

# DuckDB
database: duckdb:///data.duckdb
```

## Optional Fields

### `table_order`

**Type**: Array of strings
**Required**: No
**Description**: Specifies the order tables appear in tabs

By default, tables are displayed in alphabetical order. Use `table_order` to customize this.

**Example**:
```yaml
table_order:
  - product
  - order
  - customer
```

Tables not listed in `table_order` will appear after the specified tables in alphabetical order.

### `settings`

**Type**: Object
**Required**: No
**Description**: Global application settings for display and grouping behavior

The `settings` section contains configuration for how Deflatable displays data and recommends grouping options.

#### `settings.display`

**Type**: Object
**Description**: Controls display behavior for table cells and related records

**Available options**:

- `reverse_fk_preview_items` (default: `2`)
  Maximum number of items to show when previewing reverse foreign key relationships

- `cell_truncation_length` (default: `80`)
  Maximum characters to display in table cells before truncating

- `group_header_style` (default: `"bold white on dark_green"`)
  Rich style string for group header text (uses [Rich markup](https://rich.readthedocs.io/en/stable/style.html))

- `group_header_bg_style` (default: `"on dark_green"`)
  Rich style string for group header background cells

**Example**:
```yaml
settings:
  display:
    reverse_fk_preview_items: 3
    cell_truncation_length: 100
    group_header_style: "bold cyan"
    group_header_bg_style: "on blue"
```

#### `settings.grouping`

**Type**: Object
**Description**: Controls how Deflatable recommends columns for grouping

When you create or edit a view, Deflatable suggests which columns are suitable for grouping based on these criteria.

##### `settings.grouping.recommendations`

**Available options**:

- `max_distinct_values` (default: `200`)
  Columns with more unique values than this won't be recommended for grouping

- `max_cardinality_ratio` (default: `0.7`)
  Maximum ratio of unique values to total rows (0.0-1.0). Columns with higher ratios won't be recommended

- `min_distinct_values` (default: `2`)
  Columns with fewer unique values than this won't be recommended for grouping

- `excluded_types` (default: `["BLOB", "BINARY", "VARBINARY", "FLOAT", "REAL", "DOUBLE", "DATE", "TIME", "DATETIME", "TIMESTAMP"]`)
  List of column types to exclude from grouping recommendations

**Example**:
```yaml
settings:
  grouping:
    recommendations:
      max_distinct_values: 100  # Stricter - only recommend low-cardinality columns
      max_cardinality_ratio: 0.5  # Only recommend if < 50% unique values
      min_distinct_values: 3  # Require at least 3 distinct values
      excluded_types:
        - BLOB
        - BINARY
        - FLOAT
```

**Complete settings example**:
```yaml
database: sqlite:///mydb.db

settings:
  display:
    reverse_fk_preview_items: 3
    cell_truncation_length: 120
  grouping:
    recommendations:
      max_distinct_values: 150
      max_cardinality_ratio: 0.6

views:
  # ... table views ...
```

### `views`

**Type**: Object
**Required**: No
**Description**: Named view configurations per table

Each table can have multiple saved views.

## View Configuration

### `views.<table-name>`

Each table can have:

#### `active_view`

**Type**: String
**Default**: `"All"`
**Description**: Name of the currently active view for this table

#### `record_links`

**Type**: Object
**Optional**: Yes
**Description**: Configuration for foreign key relationships to display related table data

Record links allow you to show fields from related tables inline, without writing joins.

**Format**:
```yaml
record_links:
  <fk_column>:
    display_name: <custom-name>  # Optional
    lookup_fields:
      - field: <field-name>
        display_name: <custom-name>  # Optional
      - <field-name>  # Shorthand form
```

**Example**:
```yaml
product:
  record_links:
    aisle_id:
      display_name: "Aisle"
      lookup_fields:
        - field: "refrigerated"
          display_name: "Is Refrigerated"
        - "length_feet"  # Uses default display name
```

This creates virtual columns in the product table:
- `aisle_id__refrigerated` - Shows the refrigerated value from the linked aisle
- `aisle_id__length_feet` - Shows the length_feet value from the linked aisle

These lookup columns can be used in:
- `visible_fields` - Display them in the table
- `filters` - Filter by related table values
- `sort_config` - Sort by related table values
- `grouping` - Group by related table values

#### `views.<view-name>`

Each view object can contain:

#### `visible_fields`

**Type**: Array of strings
**Description**: List of column names to display
**Default**: All columns

```yaml
visible_fields: [id, name, price]
```

#### `grouping`

**Type**: String
**Description**: Column name to group rows by
**Default**: `null` (no grouping)

```yaml
grouping: aisle_id
```

#### `sort_config`

**Type**: Array of [column, direction] tuples
**Description**: Sort order specification
**Default**: `[]` (no sorting)

Direction values: `"asc"` or `"desc"`

```yaml
sort_config:
  - [price, desc]
  - [name, asc]
```

#### `filters`

**Type**: Array of [column, operator, value, logic] tuples
**Description**: Filter conditions
**Default**: `[]` (no filters)

**Format**: `[column, operator, value, logic]`

**Operators**:
- `=` - Equals
- `!=` - Not equals
- `>` - Greater than
- `>=` - Greater than or equal
- `<` - Less than
- `<=` - Less than or equal
- `contains` - Text contains
- `starts_with` - Text starts with
- `ends_with` - Text ends with

**Logic** (for multiple filters):
- `and` - Both conditions must be true
- `or` - Either condition must be true

```yaml
filters:
  - [price, ">", "3.00", "and"]
  - [aisle_id, "=", "2", "and"]
```

## Complete Example

```yaml
database: sqlite:///grocery.db
table_order:
  - product
  - aisle

settings:
  display:
    reverse_fk_preview_items: 2
    cell_truncation_length: 80
  grouping:
    recommendations:
      max_distinct_values: 200
      max_cardinality_ratio: 0.7
      min_distinct_values: 2

views:
  product:
    active_view: Expensive Products
    record_links:
      aisle_id:
        display_name: "Aisle"
        lookup_fields:
          - field: "refrigerated"
            display_name: "Is Refrigerated"
          - "length_feet"
    views:
      All:
        visible_fields: [id, name, aisle_id, aisle_id__refrigerated, price]
        sort_config: []
        filters: []

      "Expensive Products":
        visible_fields: [name, price, aisle_id, aisle_id__refrigerated]
        grouping: null
        sort_config:
          - [price, desc]
        filters:
          - [price, ">", "3.00", "and"]

      "Dairy Products":
        visible_fields: [id, name, price]
        filters:
          - [aisle_id, "=", "2", "and"]
        sort_config:
          - [name, asc]

  aisle:
    active_view: All
    views:
      All:
        visible_fields: [id, length_feet, refrigerated, has_endcaps]
```

## File Location

Config files can be placed anywhere. Specify the path when running:

```bash
deflatable /path/to/config.yaml
```

## Creating Config Files

Use the init command:

```bash
deflatable init <config-file> <database-url>
```

Example:
```bash
deflatable init mydb.yaml sqlite:///mydb.db
```

## Modifying Configuration

### Manual Editing

Edit the YAML file directly with any text editor.

### From Within Deflatable

1. Make changes (filters, sorts, etc.)
2. Click **View** → **Save** to update the current view
3. Or click **View** → **Save As** to create a new view

Changes are written back to the config file.

## Validation

Validate your config file:

```bash
deflatable validate config.yaml
```

Output formats:
- `--format human` (default): Human-readable
- `--format json`: Machine-readable JSON

Quiet mode (exit code only):
```bash
deflatable validate config.yaml --quiet
```

## Path Handling

### Relative Paths (SQLite)

Relative to the config file's directory:

```yaml
# config.yaml in /home/user/project/
database: sqlite:///data/db.sqlite

# Resolves to: /home/user/project/data/db.sqlite
```

### Absolute Paths

Use absolute paths for databases outside the project:

```yaml
database: sqlite:////var/data/production.db
```

### Remote Databases

PostgreSQL, MySQL, and other network databases use full URLs:

```yaml
database: postgresql://user:pass@db.example.com:5432/production
```

## Schema Changes

When your database schema changes (new tables, columns, etc.):

1. Deflatable automatically detects new tables
2. New columns appear in existing tables
3. Views referencing deleted columns/tables will show errors
4. Update or remove outdated view configurations manually

## Security

**Do Not Commit Credentials**: For production databases with passwords, use environment variables:

```yaml
database: postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}/${DB_NAME}
```

Then set environment variables before running:
```bash
export DB_USER=myuser
export DB_PASS=mypassword
export DB_HOST=localhost
export DB_NAME=mydb
deflatable config.yaml
```

## Troubleshooting

**"Cannot connect to database"**
- Check the database URL format
- Verify the database file exists (for file-based DBs)
- Check network connectivity (for remote databases)
- Ensure credentials are correct

**"Table not found in views"**
- Table was renamed or deleted
- Remove the view configuration for that table

**"Column not found"**
- Column was renamed or deleted in the database
- Update or remove the view referencing that column
