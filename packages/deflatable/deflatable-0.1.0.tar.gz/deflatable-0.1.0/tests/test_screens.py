"""Tests for modal screen components."""

from deflatable.screens import (
    FilterFieldsScreen,
    RecordFilterScreen,
    ReverseFKDetailScreen,
    SaveViewScreen,
    SortingScreen,
    ViewSelectorScreen,
)

# Note: Textual screen testing is complex and requires the Textual test harness
# These tests focus on initialization and basic logic rather than full UI interaction


class TestFilterFieldsScreen:
    """Tests for field visibility selection screen."""

    def test_init_stores_parameters(self):
        """Test that initialization stores all parameters correctly."""
        fields = [("name", "Name"), ("price", "Price"), ("stock", "Stock")]
        visible = {"name", "price"}

        screen = FilterFieldsScreen(table_name="product", fields=fields, visible_fields=visible)

        assert screen.table_name == "product"
        assert screen.fields == fields
        assert screen.visible_fields == {"name", "price"}
        # Should be a copy, not the same object
        assert screen.visible_fields is not visible

    def test_init_with_empty_visible_fields(self):
        """Test initialization with no visible fields."""
        fields = [("id", "ID"), ("name", "Name")]

        screen = FilterFieldsScreen(table_name="product", fields=fields, visible_fields=set())

        assert screen.visible_fields == set()

    def test_init_with_all_fields_visible(self):
        """Test initialization with all fields visible."""
        fields = [("id", "ID"), ("name", "Name"), ("price", "Price")]
        visible = {"id", "name", "price"}

        screen = FilterFieldsScreen(table_name="product", fields=fields, visible_fields=visible)

        assert screen.visible_fields == visible


class TestRecordFilterScreen:
    """Tests for record filtering screen."""

    def test_init_with_no_filters(self):
        """Test initialization with empty filter list."""
        screen = RecordFilterScreen(
            table_name="product", fields=[("name", "Name")], current_filters=[]
        )

        assert screen.table_name == "product"
        assert len(screen.fields) == 1
        assert screen.current_filters == []

    def test_init_with_existing_filters(self):
        """Test initialization with existing filters."""
        filters = [("price", "gt", "100", "AND"), ("stock", "lt", "10", "OR")]

        screen = RecordFilterScreen(
            table_name="product",
            fields=[("name", "Name"), ("price", "Price"), ("stock", "Stock")],
            current_filters=filters,
        )

        assert len(screen.current_filters) == 2
        assert screen.current_filters[0] == ("price", "gt", "100", "AND")
        assert screen.current_filters[1] == ("stock", "lt", "10", "OR")

    def test_operators_list_available(self):
        """Test that operators list is available and complete."""
        screen = RecordFilterScreen(
            table_name="product", fields=[("name", "Name")], current_filters=[]
        )

        # Check operators list
        operators_dict = {op_id: display for display, op_id in screen.operators}

        # Should include all standard operators
        assert "is" in operators_dict
        assert "is_not" in operators_dict
        assert "contains" in operators_dict
        assert "starts_with" in operators_dict
        assert "ends_with" in operators_dict
        assert "gt" in operators_dict
        assert "gte" in operators_dict
        assert "lt" in operators_dict
        assert "lte" in operators_dict

    def test_boolean_operators_list_available(self):
        """Test that boolean operators list is available."""
        screen = RecordFilterScreen(
            table_name="product", fields=[("price", "Price")], current_filters=[]
        )

        # Check boolean operators
        bool_ops_dict = {op_id: display for display, op_id in screen.boolean_operators}

        assert "AND" in bool_ops_dict
        assert "OR" in bool_ops_dict
        assert len(screen.boolean_operators) == 2

    def test_operator_display_names(self):
        """Test that operators have proper display names."""
        screen = RecordFilterScreen(
            table_name="product", fields=[("price", "Price")], current_filters=[]
        )

        # Check a few key operator display names
        operators_dict = {op_id: display for display, op_id in screen.operators}

        assert operators_dict["is"] == "is"
        assert operators_dict["is_not"] == "is not"
        assert operators_dict["gt"] == "greater than"
        assert operators_dict["gte"] == "greater than or equal"
        assert operators_dict["lt"] == "less than"
        assert operators_dict["lte"] == "less than or equal"

    def test_filter_list_initialization(self):
        """Test that filter list starts with existing filters."""
        filters = [("price", "gt", "100", "AND")]

        screen = RecordFilterScreen(
            table_name="product", fields=[("price", "Price")], current_filters=filters
        )

        # The screen should store existing filters (as a copy)
        assert len(screen.current_filters) == 1
        assert screen.current_filters[0] == ("price", "gt", "100", "AND")
        # Should be a copy, not the same object
        assert screen.current_filters is not filters


class TestBooleanOperators:
    """Tests for boolean operator handling."""

    def test_multiple_filters_with_different_operators(self):
        """Test filters can have different boolean operators."""
        filters = [
            ("price", "gt", "100", "AND"),
            ("stock", "lt", "10", "OR"),
            ("name", "contains", "special", "AND"),
        ]

        screen = RecordFilterScreen(
            table_name="product",
            fields=[("price", "Price"), ("stock", "Stock"), ("name", "Name")],
            current_filters=filters,
        )

        assert screen.current_filters[0][3] == "AND"
        assert screen.current_filters[1][3] == "OR"
        assert screen.current_filters[2][3] == "AND"


class TestOperatorsAvailability:
    """Tests for operator availability in screens."""

    def test_all_standard_operators_available(self):
        """Test all standard operators are available."""
        screen = RecordFilterScreen(
            table_name="product", fields=[("name", "Name")], current_filters=[]
        )

        ops = {op_id for _, op_id in screen.operators}

        # All operators should be available (no type-specific filtering)
        assert "contains" in ops
        assert "starts_with" in ops
        assert "ends_with" in ops
        assert "gt" in ops
        assert "gte" in ops
        assert "lt" in ops
        assert "lte" in ops
        assert "is" in ops
        assert "is_not" in ops

    def test_operators_have_correct_count(self):
        """Test that the expected number of operators is available."""
        screen = RecordFilterScreen(
            table_name="product", fields=[("price", "Price")], current_filters=[]
        )

        # Should have 9 operators based on the implementation
        assert len(screen.operators) == 9

    def test_boolean_operators_count(self):
        """Test that both AND and OR are available."""
        screen = RecordFilterScreen(
            table_name="product", fields=[("qty", "Quantity")], current_filters=[]
        )

        bool_ops = {op_id for _, op_id in screen.boolean_operators}

        assert "AND" in bool_ops
        assert "OR" in bool_ops
        assert len(screen.boolean_operators) == 2


class TestFilterScreenEdgeCases:
    """Tests for edge cases in filter screens."""

    def test_empty_field_list(self):
        """Test handling of empty field list."""
        screen = RecordFilterScreen(table_name="product", fields=[], current_filters=[])

        assert screen.fields == []
        assert screen.table_name == "product"

    def test_single_field(self):
        """Test handling of single field."""
        screen = RecordFilterScreen(
            table_name="product", fields=[("name", "Name")], current_filters=[]
        )

        assert len(screen.fields) == 1
        assert screen.fields[0] == ("name", "Name")

    def test_many_filters(self):
        """Test handling of many filters."""
        filters = [
            ("field1", "is", "val1", "AND"),
            ("field2", "is", "val2", "AND"),
            ("field3", "is", "val3", "AND"),
            ("field4", "is", "val4", "AND"),
            ("field5", "is", "val5", "AND"),
        ]

        screen = RecordFilterScreen(
            table_name="product", fields=[("field1", "Field1")], current_filters=filters
        )

        assert len(screen.current_filters) == 5

    def test_filter_with_special_characters(self):
        """Test filters with special characters in values."""
        filters = [
            ("name", "contains", "O'Reilly", "AND"),
            ("description", "contains", '10" screen', "AND"),
        ]

        screen = RecordFilterScreen(
            table_name="product",
            fields=[("name", "Name"), ("description", "Description")],
            current_filters=filters,
        )

        assert screen.current_filters[0][2] == "O'Reilly"
        assert screen.current_filters[1][2] == '10" screen'


class TestSortingScreen:
    """Tests for multi-column sorting screen."""

    def test_init_with_no_sorts(self):
        """Test initialization with empty sort configuration."""
        screen = SortingScreen(available_columns=["name", "price", "stock"], current_sort=[])

        assert screen.available_columns == ["name", "price", "stock"]
        assert screen.sort_config == []

    def test_init_with_existing_sort(self):
        """Test initialization with existing sort configuration."""
        sort_config = [("price", "desc"), ("name", "asc")]

        screen = SortingScreen(
            available_columns=["name", "price", "stock"], current_sort=sort_config
        )

        assert len(screen.sort_config) == 2
        assert screen.sort_config[0] == ("price", "desc")
        assert screen.sort_config[1] == ("name", "asc")
        # Should be a copy
        assert screen.sort_config is not sort_config

    def test_init_with_single_column_available(self):
        """Test initialization with only one column."""
        screen = SortingScreen(available_columns=["id"], current_sort=[])

        assert screen.available_columns == ["id"]

    def test_init_copies_sort_config(self):
        """Test that sort config is copied, not referenced."""
        original_sort = [("price", "asc")]

        screen = SortingScreen(available_columns=["price"], current_sort=original_sort)

        # Modify the original
        original_sort.append(("name", "desc"))

        # Screen's copy should be unchanged
        assert len(screen.sort_config) == 1


class TestSaveViewScreen:
    """Tests for save view dialog screen."""

    def test_init_with_default_name(self):
        """Test initialization with default name."""
        screen = SaveViewScreen(title="Save View", default_name="my_view")

        assert screen.dialog_title == "Save View"
        assert screen.default_name == "my_view"

    def test_init_without_default_name(self):
        """Test initialization without default name."""
        screen = SaveViewScreen(title="Save As New View", default_name="")

        assert screen.dialog_title == "Save As New View"
        assert screen.default_name == ""

    def test_init_with_save_as_title(self):
        """Test initialization with 'save as' title."""
        screen = SaveViewScreen(title="Save As New View", default_name="copy_of_view")

        assert screen.dialog_title == "Save As New View"
        assert screen.default_name == "copy_of_view"


class TestViewSelectorScreen:
    """Tests for view selection screen."""

    def test_init_with_multiple_views(self):
        """Test initialization with multiple views."""
        screen = ViewSelectorScreen(
            table_name="product",
            view_names=["default", "low_stock", "expensive"],
            current_view="low_stock",
        )

        assert screen.table_name == "product"
        assert len(screen.view_names) == 3
        assert screen.current_view == "low_stock"

    def test_init_with_single_view(self):
        """Test initialization with single view."""
        screen = ViewSelectorScreen(
            table_name="product", view_names=["default"], current_view="default"
        )

        assert len(screen.view_names) == 1
        assert screen.current_view == "default"

    def test_init_stores_parameters(self):
        """Test that all parameters are stored correctly."""
        screen = ViewSelectorScreen(
            table_name="orders",
            view_names=["all", "pending", "completed"],
            current_view="pending",
        )

        assert screen.table_name == "orders"
        assert "all" in screen.view_names
        assert "pending" in screen.view_names
        assert "completed" in screen.view_names
        assert screen.current_view == "pending"


class TestReverseFKDetailScreen:
    """Tests for reverse foreign key detail screen."""

    def test_init_with_items(self):
        """Test initialization with items list."""
        screen = ReverseFKDetailScreen(
            title="Components for system 'oz'", items=["cpu", "ram", "disk"]
        )

        assert screen.title_text == "Components for system 'oz'"
        assert len(screen.items) == 3
        assert "cpu" in screen.items

    def test_init_with_empty_items(self):
        """Test initialization with no items."""
        screen = ReverseFKDetailScreen(title="No components found", items=[])

        assert screen.title_text == "No components found"
        assert screen.items == []

    def test_init_with_many_items(self):
        """Test initialization with many items."""
        items = [f"item_{i}" for i in range(100)]

        screen = ReverseFKDetailScreen(title="Many items", items=items)

        assert len(screen.items) == 100
        assert screen.items[0] == "item_0"
        assert screen.items[99] == "item_99"

    def test_init_with_special_characters_in_title(self):
        """Test initialization with special characters in title."""
        screen = ReverseFKDetailScreen(
            title="Items for 'O\"Reilly & Sons'", items=["item1", "item2"]
        )

        assert screen.title_text == "Items for 'O\"Reilly & Sons'"


class TestScreenParameterValidation:
    """Tests for parameter validation across screens."""

    def test_filter_fields_screen_preserves_field_order(self):
        """Test that field order is preserved."""
        fields = [
            ("z_field", "Z Field"),
            ("a_field", "A Field"),
            ("m_field", "M Field"),
        ]

        screen = FilterFieldsScreen(table_name="test", fields=fields, visible_fields=set())

        # Order should be preserved
        assert screen.fields[0][0] == "z_field"
        assert screen.fields[1][0] == "a_field"
        assert screen.fields[2][0] == "m_field"

    def test_sorting_screen_preserves_column_order(self):
        """Test that column order is preserved."""
        columns = ["zebra", "apple", "mango"]

        screen = SortingScreen(available_columns=columns, current_sort=[])

        assert screen.available_columns[0] == "zebra"
        assert screen.available_columns[1] == "apple"
        assert screen.available_columns[2] == "mango"

    def test_view_selector_preserves_view_order(self):
        """Test that view order is preserved."""
        views = ["view3", "view1", "view2"]

        screen = ViewSelectorScreen(table_name="test", view_names=views, current_view="view1")

        assert screen.view_names[0] == "view3"
        assert screen.view_names[1] == "view1"
        assert screen.view_names[2] == "view2"
