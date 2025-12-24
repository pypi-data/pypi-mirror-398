"""Tests for display logic functions."""

from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from deflatable.config import LookupField, RecordLink
from deflatable.display import (
    _coerce_comparison_value,
    build_column_list,
    build_row,
    build_where_clause,
    fetch_all_reverse_fk_items,
    fetch_grouped_data,
    fetch_reverse_fk_preview,
    load_table_display,
    sort_rows,
)
from deflatable.state import TableState


def execute_sql(engine, *sql_statements):
    """Execute SQL statements on an engine."""
    with engine.begin() as conn:
        for sql in sql_statements:
            conn.execute(text(sql))


@pytest.fixture
def grocery_db():
    """Provide engine for test database."""
    test_dir = Path(__file__).parent
    db_path = test_dir / "grocery.db"
    engine = create_engine(f"sqlite:///{db_path}")
    yield engine
    engine.dispose()


@pytest.fixture
def temp_db():
    """Create a temporary in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    yield engine
    engine.dispose()


class TestWhereClauseBuilding:
    """Tests for building WHERE clauses from filters."""

    def test_empty_filters(self):
        """Test that empty filter list returns empty WHERE clause."""
        where, params = build_where_clause([], "product")
        assert where == ""
        assert params == {}

    def test_single_equality_filter(self):
        """Test single 'is' filter."""
        filters = [("brand", "is", "Organic Valley", "AND")]
        where, params = build_where_clause(filters, "product")

        assert '"product"."brand" = :filter_0' in where
        assert params == {"filter_0": "Organic Valley"}

    def test_single_inequality_filter(self):
        """Test 'is_not' operator."""
        filters = [("brand", "is_not", "Generic", "AND")]
        where, params = build_where_clause(filters, "product")

        assert '"product"."brand" != :filter_0' in where
        assert params == {"filter_0": "Generic"}

    def test_contains_filter(self):
        """Test LIKE pattern for 'contains'."""
        filters = [("name", "contains", "Milk", "AND")]
        where, params = build_where_clause(filters, "product")

        assert '"product"."name" LIKE :filter_0' in where
        assert params == {"filter_0": "%Milk%"}

    def test_starts_with_filter(self):
        """Test LIKE pattern for 'starts_with'."""
        filters = [("name", "starts_with", "Organic", "AND")]
        where, params = build_where_clause(filters, "product")

        assert '"product"."name" LIKE :filter_0' in where
        assert params == {"filter_0": "Organic%"}

    def test_ends_with_filter(self):
        """Test LIKE pattern for 'ends_with'."""
        filters = [("name", "ends_with", "Cheese", "AND")]
        where, params = build_where_clause(filters, "product")

        assert '"product"."name" LIKE :filter_0' in where
        assert params == {"filter_0": "%Cheese"}

    def test_greater_than_numeric(self):
        """Test gt operator with numeric value."""
        filters = [("price", "gt", "5.99", "AND")]
        where, params = build_where_clause(filters, "cost")

        assert 'CAST("cost"."price" AS REAL) > :filter_0' in where
        assert params == {"filter_0": 5.99}

    def test_greater_than_or_equal_date(self):
        """Test gte operator with date value."""
        filters = [("date", "gte", "2024-01-01", "AND")]
        where, params = build_where_clause(filters, "cost")

        assert 'CAST("cost"."date" AS TEXT) >= :filter_0' in where
        assert params == {"filter_0": "2024-01-01"}

    def test_less_than_currency(self):
        """Test lt operator with currency symbol."""
        filters = [("price", "lt", "$10.00", "AND")]
        where, params = build_where_clause(filters, "cost")

        assert 'CAST("cost"."price" AS REAL) < :filter_0' in where
        assert params == {"filter_0": 10.00}

    def test_less_than_or_equal(self):
        """Test lte operator."""
        filters = [("price", "lte", "15.50", "AND")]
        where, params = build_where_clause(filters, "cost")

        assert 'CAST("cost"."price" AS REAL) <= :filter_0' in where
        assert params == {"filter_0": 15.50}

    def test_multiple_filters_with_and(self):
        """Test multiple filters combined with AND."""
        filters = [
            ("brand", "is", "Organic Valley", "AND"),
            ("price", "gt", "5.00", "AND"),
        ]
        where, params = build_where_clause(filters, "product")

        assert '"product"."brand" = :filter_0' in where
        assert 'CAST("product"."price" AS REAL) > :filter_1' in where
        assert " AND " in where
        assert params == {"filter_0": "Organic Valley", "filter_1": 5.00}

    def test_multiple_filters_with_or(self):
        """Test multiple filters combined with OR."""
        filters = [
            ("brand", "is", "Organic Valley", "OR"),
            ("brand", "is", "Horizon", "AND"),
        ]
        where, params = build_where_clause(filters, "product")

        assert " OR " in where
        assert params == {"filter_0": "Organic Valley", "filter_1": "Horizon"}

    def test_mixed_and_or_operators(self):
        """Test mix of AND and OR boolean operators."""
        filters = [
            ("brand", "is", "Organic Valley", "OR"),
            ("brand", "is", "Horizon", "AND"),
            ("price", "lt", "10.00", "AND"),
        ]
        where, params = build_where_clause(filters, "product")

        assert " OR " in where
        assert " AND " in where
        assert len(params) == 3


class TestComparisonValueCoercion:
    """Tests for _coerce_comparison_value helper."""

    def test_coerce_plain_number(self):
        """Test coercing plain numeric string."""
        cast_type, value = _coerce_comparison_value("123.45")
        assert cast_type == "REAL"
        assert value == 123.45

    def test_coerce_currency_dollar(self):
        """Test stripping dollar sign."""
        cast_type, value = _coerce_comparison_value("$99.99")
        assert cast_type == "REAL"
        assert value == 99.99

    def test_coerce_currency_euro(self):
        """Test stripping euro symbol."""
        cast_type, value = _coerce_comparison_value("€50.00")
        assert cast_type == "REAL"
        assert value == 50.00

    def test_coerce_with_commas(self):
        """Test stripping comma thousands separators."""
        cast_type, value = _coerce_comparison_value("$1,234.56")
        assert cast_type == "REAL"
        assert value == 1234.56

    def test_coerce_date_string(self):
        """Test date remains as TEXT."""
        cast_type, value = _coerce_comparison_value("2024-12-01")
        assert cast_type == "TEXT"
        assert value == "2024-12-01"

    def test_coerce_text_string(self):
        """Test arbitrary text remains as TEXT."""
        cast_type, value = _coerce_comparison_value("hello world")
        assert cast_type == "TEXT"
        assert value == "hello world"


class TestReverseForeignKeyFetching:
    """Tests for reverse FK preview and fetching."""

    def test_fetch_reverse_fk_preview_with_items(self, grocery_db):
        """Test fetching preview of related items."""
        # Get an aisle with products
        with grocery_db.connect() as conn:
            result = conn.execute(text("SELECT id FROM aisle LIMIT 1"))
            aisle_id = result.fetchone()[0]

            # Get product count for this aisle
            result = conn.execute(
                text("SELECT COUNT(*) FROM product WHERE aisle_id = :aisle_id"),
                {"aisle_id": aisle_id},
            )
            product_count = result.fetchone()[0]

        if product_count == 0:
            pytest.skip("No products in first aisle")

        reverse_fk = {
            "from_table": "product",
            "from_column": "aisle_id",
            "to_column": "id",
            "name_column": "name",
        }

        preview = fetch_reverse_fk_preview(grocery_db, reverse_fk, aisle_id, max_items=2)

        # Should have content
        assert preview != ""

        # If more than 2 products, should show "... (N total)"
        if product_count > 2:
            assert "total)" in preview

    def test_fetch_reverse_fk_preview_empty(self, temp_db):
        """Test preview returns empty string when no related items."""
        execute_sql(
            temp_db,
            "CREATE TABLE parent (id INTEGER PRIMARY KEY, name TEXT)",
            "CREATE TABLE child (id INTEGER PRIMARY KEY, parent_id INTEGER, name TEXT)",
            "INSERT INTO parent VALUES (1, 'Parent1')",
        )

        reverse_fk = {
            "from_table": "child",
            "from_column": "parent_id",
            "to_column": "id",
            "name_column": "name",
        }

        preview = fetch_reverse_fk_preview(temp_db, reverse_fk, 1)
        assert preview == ""

    def test_fetch_reverse_fk_preview_few_items(self, temp_db):
        """Test preview shows all items when count <= max_items."""
        execute_sql(
            temp_db,
            "CREATE TABLE parent (id INTEGER PRIMARY KEY, name TEXT)",
            "CREATE TABLE child (id INTEGER PRIMARY KEY, parent_id INTEGER, name TEXT)",
            "INSERT INTO parent VALUES (1, 'Parent1')",
            "INSERT INTO child VALUES (1, 1, 'Child1')",
            "INSERT INTO child VALUES (2, 1, 'Child2')",
        )

        reverse_fk = {
            "from_table": "child",
            "from_column": "parent_id",
            "to_column": "id",
            "name_column": "name",
        }

        preview = fetch_reverse_fk_preview(temp_db, reverse_fk, 1, max_items=2)
        assert "Child1" in preview
        assert "Child2" in preview
        assert "total)" not in preview

    def test_fetch_all_reverse_fk_items(self, temp_db):
        """Test fetching all related items."""
        execute_sql(
            temp_db,
            "CREATE TABLE parent (id INTEGER PRIMARY KEY, name TEXT)",
            "CREATE TABLE child (id INTEGER PRIMARY KEY, parent_id INTEGER, name TEXT)",
            "INSERT INTO parent VALUES (1, 'Parent1')",
            "INSERT INTO child VALUES (1, 1, 'Child3')",
            "INSERT INTO child VALUES (2, 1, 'Child1')",
            "INSERT INTO child VALUES (3, 1, 'Child2')",
        )

        reverse_fk = {
            "from_table": "child",
            "from_column": "parent_id",
            "to_column": "id",
            "name_column": "name",
        }

        items = fetch_all_reverse_fk_items(temp_db, reverse_fk, 1)

        # Should be sorted by name
        assert items == ["Child1", "Child2", "Child3"]


class TestColumnListBuilding:
    """Tests for building display column lists."""

    def test_build_column_list_no_grouping(self, grocery_db):
        """Test building column list without grouping."""
        state = TableState(table_name="product", visible_fields={"name", "brand", "size"})

        columns = build_column_list(grocery_db, state)

        # Should include name first (it's the name column)
        assert "Name" in columns
        assert columns[0] == "Name"

        # Should include visible fields
        assert "Brand" in columns
        assert "Size" in columns

    def test_build_column_list_excludes_grouping_field(self, grocery_db):
        """Test that grouping column is excluded from display."""
        state = TableState(
            table_name="product",
            grouping=["aisle_id"],
            visible_fields={"name", "brand", "aisle_id"},
        )

        columns = build_column_list(grocery_db, state)

        # Should NOT include grouping column
        assert "Aisle Id" not in columns

        # Should still include other visible fields
        assert "Name" in columns
        assert "Brand" in columns

    def test_build_column_list_includes_reverse_fks(self, grocery_db):
        """Test that reverse FK columns are added when in visible_fields."""
        state = TableState(
            table_name="aisle", visible_fields={"aisle_number", "length_feet", "product"}
        )

        columns = build_column_list(grocery_db, state)

        # aisle has reverse FK from product.aisle_id
        # Should add "Product" column when it's in visible_fields
        assert "Product" in columns

    def test_build_column_list_excludes_reverse_fks_when_not_visible(self, grocery_db):
        """Test that reverse FK columns are excluded when not in visible_fields."""
        state = TableState(table_name="aisle", visible_fields={"aisle_number", "length_feet"})

        columns = build_column_list(grocery_db, state)

        # aisle has reverse FK from product.aisle_id
        # Should NOT add "Product" column when it's not in visible_fields
        assert "Product" not in columns

    def test_build_column_list_adds_pk_marker(self, grocery_db):
        """Test that PK columns get a key icon marker."""
        state = TableState(table_name="aisle", visible_fields={"id", "length_feet"})

        columns = build_column_list(grocery_db, state)

        # id is the PK, should have key icon
        assert "🔑 Id" in columns
        # length_feet is not PK, should not have key icon
        assert "Length Feet" in columns
        assert "🔑 Length Feet" not in columns


class TestRowBuilding:
    """Tests for building display rows from raw data."""

    def test_build_row_basic_data(self):
        """Test building row with basic column data."""
        display_columns = ["Name", "Amount"]
        all_columns = [
            {"name": "name", "type": "TEXT", "pk": False, "display_name": "Name"},
            {"name": "amount", "type": "REAL", "pk": False, "display_name": "Amount"},
        ]
        row_data = {"name": "Test Product", "amount": 9.99}

        row = build_row(display_columns, all_columns, row_data, {})

        # amount doesn't contain 'price' or 'cost', so no formatting
        assert row == ["Test Product", "9.99"]

    def test_build_row_formats_money(self):
        """Test that price/cost columns are formatted as currency when configured."""
        display_columns = ["Name", "Price"]
        all_columns = [
            {"name": "name", "type": "TEXT", "pk": False, "display_name": "Name"},
            {"name": "price", "type": "REAL", "pk": False, "display_name": "Price"},
        ]
        row_data = {"name": "Test", "price": 1234.56}
        field_formats = {"price": "currency"}

        row = build_row(display_columns, all_columns, row_data, {}, None, 80, field_formats)

        assert row[1] == "$1,234.56"

    def test_build_row_with_fk_display_name(self):
        """Test that FK columns show referenced table's name value."""
        display_columns = ["Product", "Aisle"]
        all_columns = [
            {"name": "name", "type": "TEXT", "pk": False, "display_name": "Product"},
            {
                "name": "aisle_id",
                "type": "INTEGER",
                "pk": False,
                "display_name": "Aisle",
            },
        ]
        row_data = {
            "name": "Milk",
            "aisle_id": 1,
            "aisle_id_name": "Dairy",  # FK display value
        }
        fk_map = {"aisle_id": ("aisle_ref", "name")}

        row = build_row(display_columns, all_columns, row_data, fk_map)

        assert row == ["Milk", "Dairy"]

    def test_build_row_truncates_long_text(self):
        """Test that long text is truncated with ellipsis."""
        display_columns = ["Description"]
        all_columns = [
            {
                "name": "description",
                "type": "TEXT",
                "pk": False,
                "display_name": "Description",
            }
        ]
        long_text = "x" * 100
        row_data = {"description": long_text}

        row = build_row(display_columns, all_columns, row_data, {})

        assert len(row[0]) == 83  # 80 chars + "..."
        assert row[0].endswith("...")

    def test_build_row_handles_null_values(self):
        """Test that NULL/empty values display as empty string."""
        display_columns = ["Name", "Price"]
        all_columns = [
            {"name": "name", "type": "TEXT", "pk": False, "display_name": "Name"},
            {"name": "price", "type": "REAL", "pk": False, "display_name": "Price"},
        ]
        row_data = {"name": None, "price": ""}

        row = build_row(display_columns, all_columns, row_data, {})

        assert row == ["", ""]

    def test_build_row_with_reverse_fk(self):
        """Test that reverse FK preview data is included."""
        display_columns = ["Name", "Product"]
        all_columns = [{"name": "name", "type": "TEXT", "pk": False, "display_name": "Name"}]
        row_data = {"name": "Dairy", "_rfk_Product": "Milk, Cheese, ... (10 total)"}
        reverse_fks = [
            {
                "from_table": "product",
                "from_column": "aisle_id",
                "to_column": "id",
                "name_column": "name",
            }
        ]

        row = build_row(display_columns, all_columns, row_data, {}, reverse_fks)

        assert row == ["Dairy", "Milk, Cheese, ... (10 total)"]


class TestSorting:
    """Tests for row sorting."""

    def test_sort_single_column_ascending(self):
        """Test sorting by single column ascending."""
        rows = [
            ({"name": "Banana"}, ["Banana", "1.99"]),
            ({"name": "Apple"}, ["Apple", "2.49"]),
            ({"name": "Cherry"}, ["Cherry", "3.99"]),
        ]
        display_columns = ["Name", "Price"]
        sort_config = [("Name", "asc")]

        sorted_rows = sort_rows(rows, display_columns, sort_config)

        assert sorted_rows[0][0]["name"] == "Apple"
        assert sorted_rows[1][0]["name"] == "Banana"
        assert sorted_rows[2][0]["name"] == "Cherry"

    def test_sort_single_column_descending(self):
        """Test sorting by single column descending."""
        # Test with string column
        string_rows = [({}, ["Banana"]), ({}, ["Apple"]), ({}, ["Cherry"])]
        display_columns = ["Name"]
        sort_config = [("Name", "desc")]

        sorted_rows = sort_rows(string_rows, display_columns, sort_config)

        # String descending works: Cherry, Banana, Apple
        assert sorted_rows[0][1][0] == "Cherry"
        assert sorted_rows[2][1][0] == "Apple"

        # Test with numeric column
        numeric_rows = [
            ({}, ["Apple", "1.99"]),
            ({}, ["Cherry", "3.99"]),
            ({}, ["Banana", "2.49"]),
        ]
        display_columns_num = ["Name", "Price"]
        sort_config_num = [("Price", "desc")]

        sorted_numeric = sort_rows(numeric_rows, display_columns_num, sort_config_num)

        # Numeric descending: 3.99, 2.49, 1.99 (highest first)
        assert sorted_numeric[0][1][1] == "3.99"
        assert sorted_numeric[1][1][1] == "2.49"
        assert sorted_numeric[2][1][1] == "1.99"

    def test_sort_case_insensitive(self):
        """Test that sorting is case-insensitive."""
        rows = [({}, ["zebra"]), ({}, ["Apple"]), ({}, ["Banana"])]
        display_columns = ["Name"]
        sort_config = [("Name", "asc")]

        sorted_rows = sort_rows(rows, display_columns, sort_config)

        assert sorted_rows[0][1][0] == "Apple"
        assert sorted_rows[1][1][0] == "Banana"
        assert sorted_rows[2][1][0] == "zebra"

    def test_sort_handles_nulls(self):
        """Test that NULL/empty values are sorted."""
        rows = [({}, ["Cherry"]), ({}, [""]), ({}, ["Apple"])]
        display_columns = ["Name"]
        sort_config = [("Name", "asc")]

        sorted_rows = sort_rows(rows, display_columns, sort_config)

        # Empty should come first
        assert sorted_rows[0][1][0] == ""

    def test_sort_numeric_values(self):
        """Test sorting numeric values correctly."""
        rows = [
            ({}, ["Product", "$10.00"]),
            ({}, ["Product", "$2.50"]),
            ({}, ["Product", "$100.00"]),
        ]
        display_columns = ["Name", "Price"]
        sort_config = [("Price", "asc")]

        sorted_rows = sort_rows(rows, display_columns, sort_config)

        # Should sort numerically, not alphabetically
        assert sorted_rows[0][1][1] == "$2.50"
        assert sorted_rows[1][1][1] == "$10.00"
        assert sorted_rows[2][1][1] == "$100.00"

    def test_sort_no_config_returns_unchanged(self):
        """Test that empty sort config returns rows unchanged."""
        rows = [({"name": "B"}, ["B"]), ({"name": "A"}, ["A"])]
        display_columns = ["Name"]

        sorted_rows = sort_rows(rows, display_columns, [])

        # Should maintain original order
        assert sorted_rows[0][0]["name"] == "B"
        assert sorted_rows[1][0]["name"] == "A"


class TestFetchGroupedData:
    """Tests for fetching grouped data."""

    def test_fetch_ungrouped_data(self, grocery_db):
        """Test fetching without grouping."""
        state = TableState(
            table_name="aisle",
            grouping=[],
            visible_fields={"aisle_number", "length_feet"},
        )

        grouped_data = fetch_grouped_data(grocery_db, state)

        # Should have one group with None as key
        assert None in grouped_data
        assert len(grouped_data) == 1

        # Should have multiple rows
        rows = grouped_data[None]
        assert len(rows) > 0

        # Each row should be (row_data, row_display) tuple
        assert isinstance(rows[0], tuple)
        assert len(rows[0]) == 2

    def test_fetch_grouped_by_fk(self, grocery_db):
        """Test grouping by foreign key column."""
        state = TableState(
            table_name="product",
            grouping=["aisle_id"],
            visible_fields={"name", "brand"},
        )

        grouped_data = fetch_grouped_data(grocery_db, state)

        # Should have multiple groups (one per aisle)
        assert len(grouped_data) > 1

        # Group names should include aisle display value
        group_names = list(grouped_data.keys())
        assert any("Aisle" in str(name) for name in group_names if name)

    def test_fetch_grouped_by_integer_column(self, grocery_db):
        """Test grouping by INTEGER column (new feature!)."""
        state = TableState(
            table_name="aisle",
            grouping=["refrigerated"],
            visible_fields={"aisle_number", "length_feet"},
        )

        grouped_data = fetch_grouped_data(grocery_db, state)

        # Should have groups for refrigerated values (0 and 1)
        assert len(grouped_data) >= 1

        # Check that we have actual data
        total_rows = sum(len(rows) for rows in grouped_data.values())
        assert total_rows > 0

    def test_fetch_with_filters(self, grocery_db):
        """Test that filters reduce result set."""
        # First get count without filters
        state_no_filter = TableState(table_name="product", visible_fields={"name"})
        data_no_filter = fetch_grouped_data(grocery_db, state_no_filter)
        count_no_filter = len(data_no_filter[None])

        # Now with filter
        state_with_filter = TableState(
            table_name="product",
            visible_fields={"name"},
            filters=[("brand", "is", "Organic Valley", "AND")],
        )
        data_with_filter = fetch_grouped_data(grocery_db, state_with_filter)
        count_with_filter = len(data_with_filter[None])

        # Filtered count should be less than unfiltered
        assert count_with_filter < count_no_filter

    def test_fetch_empty_results(self, grocery_db):
        """Test filters that match nothing return empty dict."""
        state = TableState(
            table_name="product",
            visible_fields={"name"},
            filters=[("name", "is", "NonexistentProduct12345", "AND")],
        )

        grouped_data = fetch_grouped_data(grocery_db, state)

        # Should have None key but empty list
        assert None in grouped_data
        assert len(grouped_data[None]) == 0

    def test_fetch_grouped_by_lookup_field(self, grocery_db):
        """Test grouping by lookup field produces consistent headers."""
        # Create record links configuration
        record_links = {
            "aisle_id": RecordLink(
                fk_column="aisle_id",
                display_name="Aisle",
                lookup_fields=[LookupField(field="refrigerated", display_name="Refrigerated")],
            )
        }

        state = TableState(
            table_name="product",
            grouping=["aisle_id__refrigerated"],
            visible_fields={"name", "brand"},
        )

        grouped_data = fetch_grouped_data(grocery_db, state, record_links=record_links)

        # Should have groups for refrigerated values (0 and 1)
        assert len(grouped_data) == 2

        # ALL group headers should have the lookup field display name format
        group_headers = list(grouped_data.keys())
        for header in group_headers:
            # Header should not be None and should contain the prefix
            assert header is not None
            assert (
                "Refrigerated (from Aisle):" in header
            ), f"Group header '{header}' should contain 'Refrigerated (from Aisle):' prefix"

        # Verify both expected headers exist
        expected_headers = {
            "Refrigerated (from Aisle): 0",
            "Refrigerated (from Aisle): 1",
        }
        actual_headers = set(group_headers)
        assert actual_headers == expected_headers


class TestLoadTableDisplay:
    """Tests for complete table display loading."""

    def test_load_table_display_ungrouped(self, grocery_db):
        """Test loading complete display data without grouping."""
        state = TableState(table_name="aisle", visible_fields={"aisle_number", "length_feet"})

        columns, grouped_rows = load_table_display(grocery_db, state)

        # Should return column names
        assert len(columns) > 0
        assert isinstance(columns[0], str)

        # Should return grouped data
        assert None in grouped_rows
        assert len(grouped_rows[None]) > 0

    def test_load_table_display_with_sorting(self, grocery_db):
        """Test that sorting is applied."""
        state = TableState(
            table_name="aisle",
            visible_fields={"aisle_number", "length_feet"},
            sort_config=[("Aisle Number", "asc")],
        )

        columns, grouped_rows = load_table_display(grocery_db, state)

        # Get the column index for aisle_number
        try:
            aisle_num_idx = columns.index("Aisle Number")

            # Check that rows are sorted
            rows = grouped_rows[None]
            values = [row[1][aisle_num_idx] for row in rows]

            # Convert to ints and check sorted
            int_values = [int(v) for v in values if v]
            assert int_values == sorted(int_values)
        except (ValueError, IndexError):
            # Skip if column not found
            pass

    def test_load_table_display_with_grouping(self, grocery_db):
        """Test loading with grouping enabled."""
        state = TableState(
            table_name="product",
            grouping=["aisle_id"],
            visible_fields={"name", "brand"},
            sort_config=[("Name", "asc")],
        )

        columns, grouped_rows = load_table_display(grocery_db, state)

        # Should have multiple groups
        assert len(grouped_rows) > 1

        # Each group should have sorted rows
        for group_name, rows in grouped_rows.items():
            if len(rows) > 1 and "Name" in columns:
                name_idx = columns.index("Name")
                names = [row[1][name_idx].lower() for row in rows]
                # Should be sorted alphabetically
                assert names == sorted(names)
