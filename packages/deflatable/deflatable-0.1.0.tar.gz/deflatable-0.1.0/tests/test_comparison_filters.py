#!/usr/bin/env python3
"""Test comparison filter operators (gt, gte, lt, lte)."""

from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from deflatable.display import _coerce_comparison_value, build_where_clause


class TestComparisonFilters:
    """Test suite for comparison filter operators."""

    def test_coerce_numeric_with_currency(self):
        """Test coercing numeric values with currency symbols."""
        assert _coerce_comparison_value("5.99") == ("REAL", 5.99)
        assert _coerce_comparison_value("$5.99") == ("REAL", 5.99)
        assert _coerce_comparison_value("€10.50") == ("REAL", 10.5)
        assert _coerce_comparison_value("£1,234.56") == ("REAL", 1234.56)
        assert _coerce_comparison_value("¥1000") == ("REAL", 1000.0)

    def test_coerce_date_values(self):
        """Test that date strings are treated as text."""
        assert _coerce_comparison_value("2024-12-01") == ("TEXT", "2024-12-01")
        assert _coerce_comparison_value("2024-01-15") == ("TEXT", "2024-01-15")

    def test_greater_than_filter(self):
        """Test greater than filter SQL generation."""
        filters = [("price", "gt", "5.00", "AND")]
        where_clause, params = build_where_clause(filters, "cost")

        assert 'CAST("cost"."price" AS REAL) >' in where_clause
        assert params == {"filter_0": 5.0}

    def test_less_than_or_equal_filter(self):
        """Test less than or equal filter SQL generation."""
        filters = [("price", "lte", "$10.00", "AND")]
        where_clause, params = build_where_clause(filters, "cost")

        assert 'CAST("cost"."price" AS REAL) <=' in where_clause
        assert params == {"filter_0": 10.0}

    def test_date_range_filter(self):
        """Test date range with gte and lte."""
        filters = [
            ("date", "gte", "2024-01-01", "AND"),
            ("date", "lte", "2024-12-31", "AND"),
        ]
        where_clause, params = build_where_clause(filters, "cost")

        assert 'CAST("cost"."date" AS TEXT) >=' in where_clause
        assert 'CAST("cost"."date" AS TEXT) <=' in where_clause
        assert params == {"filter_0": "2024-01-01", "filter_1": "2024-12-31"}

    def test_price_range_query(self):
        """Test actual query with price range on grocery.db."""
        test_dir = Path(__file__).parent
        db_path = test_dir / "grocery.db"
        engine = create_engine(f"sqlite:///{db_path}")

        # Find products with price between $3 and $5
        filters = [("price", "gte", "3.00", "AND"), ("price", "lte", "5.00", "AND")]
        where_clause, params = build_where_clause(filters, "cost")
        query = f'SELECT COUNT(*) FROM "cost"{where_clause}'

        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            count = result.fetchone()[0]

        # Should have some results in this range
        assert count > 0

        engine.dispose()

    def test_date_comparison_query(self):
        """Test actual query with date comparison on grocery.db."""
        test_dir = Path(__file__).parent
        db_path = test_dir / "grocery.db"
        engine = create_engine(f"sqlite:///{db_path}")

        # Find prices recorded in 2024
        filters = [
            ("date", "gte", "2024-01-01", "AND"),
            ("date", "lt", "2025-01-01", "AND"),
        ]
        where_clause, params = build_where_clause(filters, "cost")
        query = f'SELECT COUNT(*) FROM "cost"{where_clause}'

        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            count = result.fetchone()[0]

        # Should have results in 2024
        assert count > 0

        engine.dispose()

    def test_combined_filters(self):
        """Test combining comparison and equality filters."""
        filters = [("product_id", "is", "1", "AND"), ("price", "gt", "4.00", "AND")]
        where_clause, params = build_where_clause(filters, "cost")

        assert '"cost"."product_id" = :filter_0' in where_clause
        assert 'CAST("cost"."price" AS REAL) > :filter_1' in where_clause
        assert params == {"filter_0": "1", "filter_1": 4.0}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
