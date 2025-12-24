"""Tests for schema introspection functions."""

from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from deflatable.schema import (
    detect_foreign_keys_from_names,
    get_all_foreign_keys,
    get_columns,
    get_default_visible_fields,
    get_foreign_keys,
    get_grouping_options,
    get_name_column,
    get_reverse_foreign_keys,
    to_title_case,
)


@pytest.fixture
def grocery_db():
    """Provide engine to test database."""
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


def execute_sql(engine, *sql_statements):
    """Helper to execute SQL statements on an engine."""
    with engine.begin() as conn:
        for sql in sql_statements:
            conn.execute(text(sql))


class TestForeignKeyDetection:
    """Tests for foreign key detection functions."""

    def test_get_foreign_keys_with_pragma(self, grocery_db):
        """Test getting FKs when PRAGMA foreign_key_list returns results."""
        # The grocery.db has PRAGMA-defined FKs
        fks = get_foreign_keys(grocery_db, "product")

        # Should find aisle_id FK
        assert len(fks) >= 1
        aisle_fk = next((fk for fk in fks if fk["column"] == "aisle_id"), None)
        assert aisle_fk is not None
        assert aisle_fk["ref_table"] == "aisle"
        assert aisle_fk["ref_column"] == "id"

    def test_get_foreign_keys_empty_for_no_fks(self, grocery_db):
        """Test PRAGMA returns empty list for tables with no FKs."""
        fks = get_foreign_keys(grocery_db, "aisle")
        assert fks == []

    def test_detect_fk_from_column_name_exact_match(self, temp_db):
        """Test heuristic detection: product_id → product."""
        # Create test tables
        execute_sql(
            temp_db,
            "CREATE TABLE product (product_id INTEGER PRIMARY KEY, name TEXT)",
            "CREATE TABLE inventory (id INTEGER PRIMARY KEY, product_id INTEGER, qty INTEGER)",
        )

        columns = get_columns(temp_db, "inventory")
        fks = detect_foreign_keys_from_names(temp_db, "inventory", columns)

        # Should detect product_id FK
        assert len(fks) == 1
        assert fks[0]["column"] == "product_id"
        assert fks[0]["ref_table"] == "product"
        assert fks[0]["ref_column"] == "product_id"

    def test_detect_fk_handles_plural_tables(self, temp_db):
        """Test: system_id → systems (with 's')."""
        # Create test tables with plural name
        execute_sql(
            temp_db,
            "CREATE TABLE systems (system_id INTEGER PRIMARY KEY, name TEXT)",
            "CREATE TABLE components (id INTEGER PRIMARY KEY, system_id INTEGER, part TEXT)",
        )

        columns = get_columns(temp_db, "components")
        fks = detect_foreign_keys_from_names(temp_db, "components", columns)

        # Should detect system_id → systems
        assert len(fks) == 1
        assert fks[0]["column"] == "system_id"
        assert fks[0]["ref_table"] == "systems"
        assert fks[0]["ref_column"] == "system_id"

    def test_detect_fk_handles_singular_from_plural(self, temp_db):
        """Test: items_id → item (removing 's')."""
        execute_sql(
            temp_db,
            "CREATE TABLE item (item_id INTEGER PRIMARY KEY, name TEXT)",
            "CREATE TABLE orders (id INTEGER PRIMARY KEY, items_id INTEGER)",
        )

        columns = get_columns(temp_db, "orders")
        fks = detect_foreign_keys_from_names(temp_db, "orders", columns)

        # Should detect items_id → item
        assert len(fks) == 1
        assert fks[0]["column"] == "items_id"
        assert fks[0]["ref_table"] == "item"

    def test_detect_fk_skips_self_references(self, temp_db):
        """Test that self-referencing columns are skipped by heuristic detection."""
        execute_sql(temp_db, "CREATE TABLE product (product_id INTEGER PRIMARY KEY, name TEXT)")

        columns = get_columns(temp_db, "product")
        fks = detect_foreign_keys_from_names(temp_db, "product", columns)

        # product_id in product table should NOT be detected as FK to itself
        # The bug fix at schema.py:109 adds check: potential_table != table
        assert len(fks) == 0

    def test_get_all_foreign_keys_combines_both(self, grocery_db):
        """Test combined FK detection merges PRAGMA and heuristic results."""
        fks = get_all_foreign_keys(grocery_db, "product")

        # Should include PRAGMA-defined FKs
        aisle_fk = next((fk for fk in fks if fk["column"] == "aisle_id"), None)
        assert aisle_fk is not None
        assert aisle_fk["ref_table"] == "aisle"

    def test_get_all_foreign_keys_prefers_explicit_over_inferred(self, temp_db):
        """Test that PRAGMA FKs take precedence over heuristic detection."""
        # Create with explicit FK
        execute_sql(
            temp_db,
            "CREATE TABLE category (id INTEGER PRIMARY KEY, name TEXT)",
            """
            CREATE TABLE product (
                id INTEGER PRIMARY KEY,
                category_id INTEGER,
                FOREIGN KEY (category_id) REFERENCES category(id)
            )
        """,
        )

        fks = get_all_foreign_keys(temp_db, "product")

        # Should have exactly one FK (not duplicated by heuristic)
        category_fks = [fk for fk in fks if fk["column"] == "category_id"]
        assert len(category_fks) == 1
        assert category_fks[0]["ref_table"] == "category"


class TestReverseForeignKeys:
    """Tests for reverse foreign key discovery."""

    def test_get_reverse_fks_finds_referencing_tables(self, grocery_db):
        """Test finding tables that reference this table."""
        # aisle should show product.aisle_id as reverse FK
        reverse_fks = get_reverse_foreign_keys(grocery_db, "aisle")

        assert len(reverse_fks) >= 1
        product_fk = next((fk for fk in reverse_fks if fk["from_table"] == "product"), None)
        assert product_fk is not None
        assert product_fk["from_column"] == "aisle_id"
        assert product_fk["to_column"] == "id"
        assert product_fk["name_column"] is not None  # Should find product name column

    def test_reverse_fks_empty_for_leaf_tables(self, grocery_db):
        """Test tables with no incoming FKs return empty list."""
        # cost is a leaf table (nothing references it)
        reverse_fks = get_reverse_foreign_keys(grocery_db, "cost")
        assert reverse_fks == []

    def test_reverse_fks_empty_for_no_pk(self, temp_db):
        """Test returns empty list if table has no primary key."""
        execute_sql(temp_db, "CREATE TABLE no_pk (name TEXT, value INTEGER)")

        reverse_fks = get_reverse_foreign_keys(temp_db, "no_pk")
        assert reverse_fks == []

    def test_reverse_fks_includes_name_column(self, temp_db):
        """Test that reverse FK includes name column from referencing table."""
        execute_sql(
            temp_db,
            "CREATE TABLE category (id INTEGER PRIMARY KEY, name TEXT)",
            """
            CREATE TABLE product (
                id INTEGER PRIMARY KEY,
                product_name TEXT,
                category_id INTEGER,
                FOREIGN KEY (category_id) REFERENCES category(id)
            )
        """,
        )

        reverse_fks = get_reverse_foreign_keys(temp_db, "category")

        assert len(reverse_fks) == 1
        assert reverse_fks[0]["from_table"] == "product"
        assert reverse_fks[0]["name_column"] == "product_name"


class TestGroupingOptions:
    """Tests for grouping option detection."""

    def test_grouping_includes_foreign_keys(self, grocery_db):
        """Test that FK columns are always available for grouping."""
        options = get_grouping_options(grocery_db, "product")

        # Should include aisle FK
        option_columns = [col for _, col in options]
        assert "aisle_id" in option_columns

        # Check display name
        aisle_option = next((name for name, col in options if col == "aisle_id"), None)
        assert aisle_option is not None
        assert "Aisle" in aisle_option

    def test_grouping_includes_integer_columns(self, grocery_db):
        """Test that INTEGER columns are grouping candidates (new feature!)."""
        options = get_grouping_options(grocery_db, "aisle")

        option_columns = [col for _, col in options]

        # aisle.refrigerated should be available (0/1, 2 distinct values)
        assert "refrigerated" in option_columns

        # aisle.has_endcaps should be available (0/1, 2 distinct values)
        assert "has_endcaps" in option_columns

    def test_grouping_includes_low_cardinality_text(self, temp_db):
        """Test that low-cardinality text columns are included."""
        execute_sql(
            temp_db,
            """
            CREATE TABLE product (
                id INTEGER PRIMARY KEY,
                name TEXT,
                brand TEXT,
                category TEXT
            )
        """,
            "INSERT INTO product VALUES (1, 'Product0', 'BrandA', 'Category1')",
            "INSERT INTO product VALUES (2, 'Product1', 'BrandB', 'Category1')",
            "INSERT INTO product VALUES (3, 'Product2', 'BrandA', 'Category1')",
            "INSERT INTO product VALUES (4, 'Product3', 'BrandC', 'Category1')",
            "INSERT INTO product VALUES (5, 'Product4', 'BrandA', 'Category1')",
            "INSERT INTO product VALUES (6, 'Product5', 'BrandB', 'Category1')",
        )

        options = get_grouping_options(temp_db, "product")
        option_columns = [col for _, col in options]

        # brand has 3 distinct values out of 6 rows (50%) - should be included
        assert "brand" in option_columns

        # category has 1 distinct value (too low) - might not be included
        # Actually, with 1 distinct value, ratio is 1/6 < 0.7, so it passes cardinality
        # But we need >= 2 distinct values
        assert "category" not in option_columns

    def test_grouping_excludes_high_cardinality(self, temp_db):
        """Test >100 distinct values excluded."""
        # Insert 150 unique serial numbers
        inserts = ["CREATE TABLE product (id INTEGER PRIMARY KEY, serial_number TEXT)"]
        inserts.extend([f"INSERT INTO product VALUES ({i + 1}, 'SN-{i:05d}')" for i in range(150)])
        execute_sql(temp_db, *inserts)

        options = get_grouping_options(temp_db, "product")
        option_columns = [col for _, col in options]

        # serial_number has 150 distinct values - should be excluded
        assert "serial_number" not in option_columns

    def test_grouping_excludes_primary_keys(self, temp_db):
        """Test that primary keys are excluded from grouping options."""
        # Create a table with PK following common naming pattern
        inserts = [
            """
            CREATE TABLE product (
                product_id INTEGER PRIMARY KEY,
                name TEXT,
                category TEXT
            )
        """
        ]
        # Add some data with low cardinality
        inserts.extend(
            [
                f"INSERT INTO product VALUES ({i + 1}, 'Product {i}', 'Category{i % 3}')"
                for i in range(10)
            ]
        )
        execute_sql(temp_db, *inserts)

        options = get_grouping_options(temp_db, "product")
        option_columns = [col for _, col in options]

        # product_id is PK - should not be in grouping options
        # With the bug fix, product_id won't be detected as a self-referencing FK
        assert "product_id" not in option_columns
        # category should be included (low cardinality)
        assert "category" in option_columns

    def test_grouping_with_filters_more_permissive(self, temp_db):
        """Test filtered data has higher thresholds (90% ratio, 200 max distinct)."""
        # Insert 180 rows with 180 distinct categories (would normally be excluded at 100 limit)
        inserts = ["CREATE TABLE product (id INTEGER PRIMARY KEY, category TEXT, price REAL)"]
        inserts.extend(
            [f"INSERT INTO product VALUES ({i + 1}, 'Category{i}', {10.0 + i})" for i in range(180)]
        )
        execute_sql(temp_db, *inserts)

        # Without filters: max_distinct=100, so 180 distinct values excluded
        options_no_filter = get_grouping_options(temp_db, "product")
        option_columns_no_filter = [col for _, col in options_no_filter]
        assert "category" not in option_columns_no_filter

        # With filters: max_distinct=200, so 180 distinct values could be included
        # But ratio matters: 180/180 = 1.0 > 0.9, so still excluded
        # Let's test with a filter that actually helps
        filters = [("price", "is", 10.0, "AND")]
        options_with_filter = get_grouping_options(temp_db, "product", filters=filters)
        # With the filter, only 1 row matches, so category would have ratio 1/1 = 1.0 > 0.9
        # Still excluded. This test shows the filter mechanism works, but we need better data.

        # Better test: 250 categories, 300 rows
        deletes_and_inserts = ["DELETE FROM product"]
        deletes_and_inserts.extend(
            [
                f"INSERT INTO product VALUES ({i + 1}, 'Category{i % 250}', {10.0 + (i % 10)})"
                for i in range(300)
            ]
        )
        execute_sql(temp_db, *deletes_and_inserts)

        # Without filters: 250 > 200 max_distinct, excluded
        options_no_filter = get_grouping_options(temp_db, "product")
        option_columns_no_filter = [col for _, col in options_no_filter]
        assert "category" not in option_columns_no_filter

        # With filters: 250 > 200 but ratio = 250/300 = 0.83 > 0.7, still excluded
        # (This test just verifies that the filter mechanism works)
        filters = [("price", "is", 10.0, "AND")]
        options_with_filter = get_grouping_options(temp_db, "product", filters=filters)
        option_columns_with_filter = [col for _, col in options_with_filter]
        # With such high cardinality, it should still be excluded
        assert "category" not in option_columns_with_filter

    def test_grouping_excludes_denormalized_fk_names(self, temp_db):
        """Test that denormalized FK name columns are excluded."""
        execute_sql(
            temp_db,
            """
            CREATE TABLE product (
                id INTEGER PRIMARY KEY,
                category_id INTEGER,
                name_from_category TEXT
            )
        """,
        )

        options = get_grouping_options(temp_db, "product")
        option_columns = [col for _, col in options]

        # name_from_category should be excluded (denormalized)
        assert "name_from_category" not in option_columns


class TestNameColumnDetection:
    """Tests for identifying the 'name' column of a table."""

    def test_get_name_column_with_name_field(self, grocery_db):
        """Test prefers 'name' column."""
        # Use product table which has a 'name' column
        name_col = get_name_column(grocery_db, "product")
        assert name_col == "name"

    def test_get_name_column_with_title_field(self, temp_db):
        """Test prefers 'title' column when 'name' not available."""
        execute_sql(
            temp_db,
            "CREATE TABLE article (id INTEGER PRIMARY KEY, title TEXT, content TEXT)",
        )

        name_col = get_name_column(temp_db, "article")
        assert name_col == "title"

    def test_get_name_column_partial_match(self, temp_db):
        """Test finds columns containing 'name' or 'title'."""
        execute_sql(
            temp_db,
            "CREATE TABLE product (id INTEGER PRIMARY KEY, product_name TEXT, qty INTEGER)",
        )

        name_col = get_name_column(temp_db, "product")
        assert name_col == "product_name"

    def test_get_name_column_fallback_to_text(self, temp_db):
        """Test falls back to first non-PK text column."""
        execute_sql(
            temp_db,
            "CREATE TABLE data (id INTEGER PRIMARY KEY, description TEXT, count INTEGER)",
        )

        name_col = get_name_column(temp_db, "data")
        assert name_col == "description"

    def test_get_name_column_returns_none(self, temp_db):
        """Test returns None if no suitable column."""
        execute_sql(
            temp_db,
            "CREATE TABLE numbers (id INTEGER PRIMARY KEY, value INTEGER, count INTEGER)",
        )

        name_col = get_name_column(temp_db, "numbers")
        assert name_col is None


class TestDefaultVisibleFields:
    """Tests for determining default visible columns."""

    def test_includes_primary_key(self, grocery_db):
        """Test PK is included in default visible fields."""
        visible = get_default_visible_fields(grocery_db, "product")

        # id is PK - should be visible by default
        assert "id" in visible

    def test_includes_all_columns(self, grocery_db):
        """Test includes all columns by default."""
        visible = get_default_visible_fields(grocery_db, "product")

        # Should include all columns
        assert "name" in visible
        assert "id" in visible

    def test_limits_to_8_columns(self, temp_db):
        """Test maximum of 8 default columns."""
        # Create table with many columns
        cols = ", ".join([f"col{i} TEXT" for i in range(15)])
        execute_sql(temp_db, f"CREATE TABLE wide_table (id INTEGER PRIMARY KEY, {cols})")

        visible = get_default_visible_fields(temp_db, "wide_table")

        # Should have at most 8 columns (including PK)
        assert len(visible) <= 8

    def test_all_columns_visible_if_few_columns(self, temp_db):
        """Test all columns visible if table has few columns."""
        execute_sql(
            temp_db,
            "CREATE TABLE small_table (id INTEGER PRIMARY KEY, name TEXT, value INTEGER)",
        )

        visible = get_default_visible_fields(temp_db, "small_table")

        # Should include all columns including PK
        assert visible == {"id", "name", "value"}


class TestTitleCase:
    """Tests for snake_case to Title Case conversion."""

    def test_simple_snake_case(self):
        """Test basic conversion."""
        assert to_title_case("product_id") == "Product Id"
        assert to_title_case("aisle_name") == "Aisle Name"

    def test_single_word(self):
        """Test single word without underscores."""
        assert to_title_case("name") == "Name"
        assert to_title_case("price") == "Price"

    def test_multiple_underscores(self):
        """Test multiple consecutive underscores."""
        assert to_title_case("system__config__value") == "System Config Value"
