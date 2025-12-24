"""Modal screen components for filtering and sorting."""

from typing import Any, Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Input,
    Label,
    OptionList,
    RadioButton,
    RadioSet,
    Select,
    SelectionList,
    Static,
)
from textual.widgets.option_list import Option, Separator
from textual.widgets.selection_list import Selection


class FilterFieldsScreen(ModalScreen):
    """Modal screen for selecting which fields to display."""

    DEFAULT_CSS = """
    FilterFieldsScreen {
        align: center middle;
    }

    #filter-dialog {
        width: 50;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #filter-dialog-title {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        text-style: bold;
    }

    #filter-checkboxes {
        height: auto;
        max-height: 20;
        padding: 1 0;
    }

    #field-selection-list {
        height: auto;
        max-height: 20;
    }

    #filter-buttons {
        dock: bottom;
        height: auto;
        align: right middle;
        padding: 1 0;
    }

    #filter-buttons Button {
        margin-left: 2;
    }
    """

    def __init__(self, table_name: str, fields: list[tuple[str, str]], visible_fields: set[str]):
        """
        Initialize filter fields screen.

        Args:
            table_name: Name of the table being filtered
            fields: List of (field_name, display_label) tuples
            visible_fields: Set of currently visible field names
        """
        super().__init__()
        self.table_name = table_name
        self.fields = fields
        self.visible_fields = visible_fields.copy()

    def compose(self) -> ComposeResult:
        with Container(id="filter-dialog"):
            yield Label(f"Filter {self.table_name} Fields", id="filter-dialog-title")
            with Vertical(id="filter-checkboxes"):
                # Create SelectionList with all fields
                selections = [
                    Selection(
                        field_label,
                        field_name,
                        initial_state=(field_name in self.visible_fields),
                    )
                    for field_name, field_label in self.fields
                ]
                yield SelectionList(*selections, id="field-selection-list")
            with Horizontal(id="filter-buttons"):
                yield Button("Cancel", id="cancel-button", variant="default")
                yield Button("Apply", id="apply-button", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-button":
            event.stop()
            self.dismiss(None)
        elif event.button.id == "apply-button":
            event.stop()
            # Get selected fields from SelectionList
            selection_list = self.query_one("#field-selection-list", SelectionList)
            new_visible_fields = set(selection_list.selected)
            self.dismiss(new_visible_fields)


class SortingScreen(ModalScreen):
    """Modal screen for configuring multi-column sorting."""

    DEFAULT_CSS = """
    SortingScreen {
        align: center middle;
    }

    #sort-dialog {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #sort-dialog-title {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        text-style: bold;
    }

    #sort-options {
        height: auto;
        padding: 1 0;
    }

    .sort-row {
        height: auto;
        padding: 0 0 1 0;
    }

    .sort-row Select {
        width: 30;
        margin-right: 2;
    }

    .sort-row RadioSet {
        height: 3;
        width: auto;
    }

    #sort-buttons {
        dock: bottom;
        height: auto;
        align: right middle;
        padding: 1 0;
    }

    #sort-buttons Button {
        margin-left: 2;
    }

    #add-sort-button {
        margin-top: 1;
        margin-bottom: 1;
    }
    """

    def __init__(self, available_columns: list[str], current_sort: list[tuple[str, str]]):
        """
        Initialize sorting screen.

        Args:
            available_columns: List of column names available for sorting
            current_sort: Current sort configuration as list of (column, direction) tuples
        """
        super().__init__()
        self.available_columns = available_columns
        self.sort_config = current_sort.copy() if current_sort else []

    def compose(self) -> ComposeResult:
        with Container(id="sort-dialog"):
            yield Label("Configure Sorting", id="sort-dialog-title")
            with Vertical(id="sort-options"):
                # Add existing sort rows
                for idx, (col, direction) in enumerate(self.sort_config):
                    yield from self._create_sort_row(idx, col, direction)

                # Add one empty row if no sorts exist
                if not self.sort_config:
                    yield from self._create_sort_row(0, None, "asc")

                yield Button("+ Add Sort Column", id="add-sort-button", variant="default")

            with Horizontal(id="sort-buttons"):
                yield Button("Clear All", id="clear-button", variant="default")
                yield Button("Cancel", id="cancel-button", variant="default")
                yield Button("Apply", id="apply-button", variant="primary")

    def _create_sort_row(self, idx: int, selected_col=None, direction="asc"):
        """Create a row with column selector and asc/desc radio buttons."""
        with Horizontal(classes="sort-row", id=f"sort-row-{idx}"):
            # Column selector
            options = [("(none)", "")] + [(col, col) for col in self.available_columns]
            yield Select(
                options,
                value=selected_col or "",
                id=f"sort-col-{idx}",
                allow_blank=False,
            )

            # Direction radio buttons
            with RadioSet(id=f"sort-dir-{idx}"):
                yield RadioButton("Ascending", value=(direction == "asc"), id=f"sort-asc-{idx}")
                yield RadioButton("Descending", value=(direction == "desc"), id=f"sort-desc-{idx}")

            # Remove button
            yield Button("✕", id=f"remove-{idx}", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""

        if button_id == "cancel-button":
            event.stop()
            self.dismiss(None)
        elif button_id == "apply-button":
            event.stop()
            # Collect sort configuration
            sort_config = []
            idx = 0
            while True:
                try:
                    col_select = self.query_one(f"#sort-col-{idx}", Select)
                    if col_select.value and col_select.value != "":
                        # Check which radio button is selected
                        radio_set = self.query_one(f"#sort-dir-{idx}", RadioSet)
                        direction = "desc" if radio_set.pressed_index == 1 else "asc"
                        sort_config.append((col_select.value, direction))
                    idx += 1
                except:
                    break
            self.dismiss(sort_config)
        elif button_id == "clear-button":
            event.stop()
            self.dismiss([])
        elif button_id == "add-sort-button":
            event.stop()
            # Add a new sort row
            idx = 0
            while True:
                try:
                    self.query_one(f"#sort-row-{idx}")
                    idx += 1
                except:
                    break

            container = self.query_one("#sort-options", Vertical)
            # Mount the new row before the "Add Sort Column" button
            add_button = self.query_one("#add-sort-button")
            # Use mount and then reorder if needed, or just append
            for widget in self._create_sort_row(idx, None, "asc"):
                container.mount(widget, before=add_button)
        elif button_id.startswith("remove-"):
            event.stop()
            # Remove the specific row
            row_id = button_id.replace("remove-", "sort-row-")
            row = self.query_one(f"#{row_id}")
            row.remove()


class GroupingScreen(ModalScreen):
    """Modal screen for configuring multi-level grouping."""

    DEFAULT_CSS = """
    GroupingScreen {
        align: center middle;
    }

    #group-dialog {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #group-dialog-title {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        text-style: bold;
    }

    #group-options {
        height: auto;
        padding: 1 0;
    }

    .group-row {
        height: auto;
        padding: 0 0 1 0;
    }

    .group-row Select {
        width: 40;
        margin-right: 2;
    }

    #group-buttons {
        dock: bottom;
        height: auto;
        align: right middle;
        padding: 1 0;
    }

    #group-buttons Button {
        margin-left: 2;
    }

    #add-group-button {
        margin-top: 1;
        margin-bottom: 1;
    }
    """

    def __init__(self, available_columns: list[dict[str, Any]], current_grouping: list[str]):
        """
        Initialize grouping screen.

        Args:
            available_columns: List of dicts with column metadata (from get_grouping_options_with_metadata)
            current_grouping: Current grouping configuration as list of column names
        """
        super().__init__()
        self.available_columns = available_columns
        self.grouping_config = current_grouping.copy() if current_grouping else []

    def compose(self) -> ComposeResult:
        with Container(id="group-dialog"):
            yield Label("Configure Grouping", id="group-dialog-title")
            with Vertical(id="group-options"):
                # Add existing grouping rows
                for idx, col in enumerate(self.grouping_config):
                    yield from self._create_group_row(idx, col)

                # Add one empty row if no groupings exist
                if not self.grouping_config:
                    yield from self._create_group_row(0, None)

                yield Button("+ Add Grouping Level", id="add-group-button", variant="default")

            with Horizontal(id="group-buttons"):
                yield Button("Clear All", id="clear-button", variant="default")
                yield Button("Cancel", id="cancel-button", variant="default")
                yield Button("Apply", id="apply-button", variant="primary")

    def on_mount(self) -> None:
        """Update button state after initial mount."""
        self._update_add_button_state()

    def _create_group_row(self, idx: int, selected_col=None):
        """Create a row with column selector."""
        with Horizontal(classes="group-row", id=f"group-row-{idx}"):
            # Column selector - filter out already selected columns
            options = self._get_available_options(idx, selected_col)
            yield Select(
                options,
                value=selected_col or "",
                id=f"group-col-{idx}",
                allow_blank=False,
            )

            # Remove button
            yield Button("✕", id=f"remove-{idx}", variant="error")

    def _get_available_options(self, current_idx: int, current_selection=None):
        """Get options for a select dropdown, excluding already-selected columns."""
        # Get currently selected columns from other rows
        selected_columns = set()
        idx = 0
        while True:
            try:
                if idx != current_idx:  # Don't exclude our own selection
                    select = self.query_one(f"#group-col-{idx}", Select)
                    if select.value and select.value != "":
                        selected_columns.add(select.value)
                idx += 1
            except:
                break

        # Build options with cardinality annotations
        # Sort: recommended first, then by display name
        recommended = []
        other = []

        for col_meta in self.available_columns:
            col_name = col_meta["column_name"]

            # Skip if already selected (unless it's the current selection)
            if col_name in selected_columns and col_name != current_selection:
                continue

            # Build display text with cardinality info
            display = col_meta["display_name"]

            # Add cardinality annotation if available
            if col_meta["distinct_count"] is not None:
                distinct = col_meta["distinct_count"]
                if distinct <= 50:
                    # Show exact count for small numbers
                    display = f"{display} ({distinct} groups)"
                else:
                    # Show rounded for larger numbers
                    display = f"{display} (~{distinct} groups)"

            option = (display, col_name)

            if col_meta["recommended"]:
                recommended.append(option)
            else:
                other.append(option)

        # Sort each group by display name
        recommended.sort(key=lambda x: x[0])
        other.sort(key=lambda x: x[0])

        # Combine: none option, recommended, separator, other
        options = [("(none)", "")]
        options.extend(recommended)

        if other:
            # Add a visual separator
            options.append(("— Other columns —", ""))
            options.extend(other)

        return options

    def _create_group_row_dynamic(self, idx: int, selected_col=None):
        """Create a row for dynamic mounting (non-compose context)."""
        # Create the container
        row = Horizontal(classes="group-row", id=f"group-row-{idx}")

        # For new rows, get available options excluding already selected columns
        # Since we're in a dynamic context, we can query existing selects
        options = self._get_available_options(idx, selected_col)

        select = Select(options, value=selected_col or "", id=f"group-col-{idx}", allow_blank=False)
        remove_btn = Button("✕", id=f"remove-{idx}", variant="error")

        # Mount children to the row
        # Note: This needs to happen after the row itself is mounted to the DOM
        # We'll return both the row and its children
        return row, [select, remove_btn]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""

        if button_id == "cancel-button":
            event.stop()
            self.dismiss(None)
        elif button_id == "apply-button":
            event.stop()
            # Collect grouping configuration
            grouping_config = []
            idx = 0
            while True:
                try:
                    col_select = self.query_one(f"#group-col-{idx}", Select)
                    if col_select.value and col_select.value != "":
                        grouping_config.append(col_select.value)
                    idx += 1
                except:
                    break
            self.dismiss(grouping_config)
        elif button_id == "clear-button":
            event.stop()
            self.dismiss([])
        elif button_id == "add-group-button":
            event.stop()
            # Add a new grouping row
            idx = 0
            while True:
                try:
                    self.query_one(f"#group-row-{idx}")
                    idx += 1
                except:
                    break

            container = self.query_one("#group-options", Vertical)
            # Mount the new row before the "Add Grouping Level" button
            add_button = self.query_one("#add-group-button")
            new_row, children = self._create_group_row_dynamic(idx, None)
            container.mount(new_row, before=add_button)

            # Schedule mounting children after the row is in the DOM, then update button state
            def mount_and_update():
                new_row.mount(*children)
                self._update_add_button_state()

            self.call_after_refresh(mount_and_update)
        elif button_id.startswith("remove-"):
            event.stop()
            # Remove the specific row
            row_id = button_id.replace("remove-", "group-row-")
            row = self.query_one(f"#{row_id}")
            row.remove()
            # Update button state after removal
            self.call_after_refresh(self._update_add_button_state)

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select changes - update Add button state."""
        event.stop()
        self._update_add_button_state()

    def _update_add_button_state(self) -> None:
        """Enable/disable the Add Grouping Level button based on whether all rows have selections."""
        try:
            add_button = self.query_one("#add-group-button", Button)

            # Check if all existing rows have non-empty selections
            idx = 0
            all_selected = True
            while True:
                try:
                    select = self.query_one(f"#group-col-{idx}", Select)
                    if not select.value or select.value == "":
                        all_selected = False
                        break
                    idx += 1
                except:
                    break

            # Disable button if any row has no selection
            add_button.disabled = not all_selected
        except:
            # Button might not be mounted yet
            pass


class ReverseFKDetailScreen(ModalScreen):
    """Modal screen showing all items in a reverse FK relationship."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
    ]

    DEFAULT_CSS = """
    ReverseFKDetailScreen {
        align: center middle;
    }

    #detail-dialog {
        width: 60;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #detail-dialog-title {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        text-style: bold;
    }

    #detail-list {
        height: auto;
        min-height: 5;
        max-height: 30;
        padding: 1 0;
    }

    #detail-buttons {
        dock: bottom;
        height: 3;
        align: center middle;
        padding: 0;
    }

    #detail-buttons Button {
        margin: 0 2;
    }
    """

    def __init__(self, title: str, items: list[str]):
        """
        Initialize reverse FK detail screen.

        Args:
            title: Title for the dialog (e.g., "Components for system 'oz'")
            items: List of item names to display
        """
        super().__init__()
        self.title_text = title
        self.items = items

    def compose(self) -> ComposeResult:
        with Container(id="detail-dialog"):
            yield Label(self.title_text, id="detail-dialog-title")
            with VerticalScroll(id="detail-list"):
                if self.items:
                    for item in self.items:
                        yield Static(f"• {item}")
                else:
                    yield Static("(no items)")
            with Horizontal(id="detail-buttons"):
                yield Button("Close", id="close-button", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-button":
            event.stop()
            self.dismiss()


class SaveViewScreen(ModalScreen[str]):
    """Modal screen for saving a view with a name."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    SaveViewScreen {
        align: center middle;
    }

    #save-view-dialog {
        width: 50;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #save-view-title {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        text-style: bold;
    }

    #save-view-content {
        height: auto;
        padding: 2 0;
    }

    #save-view-label {
        height: 1;
        margin-bottom: 1;
    }

    #save-view-input {
        width: 100%;
        margin-bottom: 1;
    }

    #save-view-buttons {
        dock: bottom;
        height: 3;
        align: center middle;
        padding: 0;
    }

    #save-view-buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self, title: str, default_name: str = ""):
        """
        Initialize save view screen.

        Args:
            title: Title for the dialog (e.g., "Save View" or "Save As New View")
            default_name: Default name to pre-fill in the input
        """
        super().__init__()
        self.dialog_title = title
        self.default_name = default_name

    def compose(self) -> ComposeResult:
        with Container(id="save-view-dialog"):
            yield Label(self.dialog_title, id="save-view-title")
            with Vertical(id="save-view-content"):
                yield Label("View name:", id="save-view-label")
                yield Input(
                    placeholder="Enter view name",
                    id="save-view-input",
                    value=self.default_name,
                )
            with Horizontal(id="save-view-buttons"):
                yield Button("Cancel", id="cancel-button", variant="default")
                yield Button("Save", id="save-button", variant="primary")

    def on_mount(self) -> None:
        """Focus the input when mounted."""
        input_widget = self.query_one("#save-view-input", Input)
        input_widget.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-button":
            event.stop()
            input_widget = self.query_one("#save-view-input", Input)
            view_name = input_widget.value.strip()
            if view_name:
                self.dismiss(view_name)
            else:
                # Could show an error message here
                pass
        elif event.button.id == "cancel-button":
            event.stop()
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input field."""
        view_name = event.value.strip()
        if view_name:
            self.dismiss(view_name)

    def action_cancel(self) -> None:
        """Handle cancel action (Escape key)."""
        self.dismiss(None)


class ViewSelectorScreen(ModalScreen[str]):
    """Modal screen for selecting a view with dynamic options."""

    BINDINGS = [
        ("escape", "dismiss_none", "Close"),
    ]

    DEFAULT_CSS = """
    ViewSelectorScreen {
        align: center middle;
    }

    #view-selector-dialog {
        width: 40;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #view-selector-title {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        text-style: bold;
    }

    #view-selector-list {
        height: auto;
        min-height: 5;
        max-height: 20;
        padding: 1 0;
        border: solid $primary;
    }
    """

    def __init__(self, table_name: str, view_names: list[str], current_view: str):
        """
        Initialize view selector screen.

        Args:
            table_name: Name of the table (for display)
            view_names: List of available view names
            current_view: Currently active view name
        """
        super().__init__()
        self.table_name = table_name
        self.view_names = view_names
        self.current_view = current_view

    def compose(self) -> ComposeResult:
        with Container(id="view-selector-dialog"):
            yield Label("Select View", id="view-selector-title")

            # Create OptionList with views
            option_list = OptionList(id="view-selector-list")
            yield option_list

    def on_mount(self) -> None:
        """Populate the option list when mounted."""
        option_list = self.query_one("#view-selector-list", OptionList)

        # Add view options
        for view_name in self.view_names:
            # Highlight the current view
            if view_name == self.current_view:
                option_list.add_option(Option(f"● {view_name}", id=view_name))
            else:
                option_list.add_option(Option(f"  {view_name}", id=view_name))

        # Add separator
        option_list.add_option(Separator())

        # Add special actions
        option_list.add_option(Option("💾 Save current view", id="__save__"))
        option_list.add_option(Option("➕ Save as new view...", id="__save_as__"))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle option selection."""
        option_id = event.option_id
        if option_id:
            self.dismiss(option_id)

    def action_dismiss_none(self) -> None:
        """Dismiss with None (cancel)."""
        self.dismiss(None)


class AddTableScreen(ModalScreen):
    """Modal screen for creating a new table."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    AddTableScreen {
        align: center middle;
    }

    #add-table-dialog {
        width: 70;
        height: auto;
        max-height: 90%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #add-table-title {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        text-style: bold;
    }

    #add-table-content {
        height: auto;
        padding: 2 0;
    }

    .section-title {
        height: 2;
        text-style: bold;
        margin-top: 1;
    }

    .field-label {
        height: 1;
        margin-bottom: 1;
    }

    .field-input {
        width: 100%;
        margin-bottom: 1;
    }

    #column-list {
        height: auto;
        max-height: 20;
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
    }

    .column-item {
        height: 1;
        margin-bottom: 0;
    }

    #add-table-buttons {
        dock: bottom;
        height: 3;
        align: center middle;
        padding: 0;
    }

    #add-table-buttons Button {
        margin: 0 1;
    }

    #column-buttons {
        height: 3;
        align: left middle;
        margin-bottom: 1;
    }

    #column-buttons Button {
        margin-right: 1;
    }
    """

    def __init__(self):
        """Initialize add table screen."""
        super().__init__()
        self.columns = []  # List of {"name": str, "type": str, "nullable": bool, "default": Optional[str], "primary_key": bool}

        # Common SQLite data types
        self.data_types = [
            ("TEXT", "TEXT"),
            ("INTEGER", "INTEGER"),
            ("REAL", "REAL"),
            ("BLOB", "BLOB"),
            ("NUMERIC", "NUMERIC"),
        ]

    def compose(self) -> ComposeResult:
        from textual.widgets import Static

        with Container(id="add-table-dialog"):
            yield Label("Create New Table", id="add-table-title")
            with Vertical(id="add-table-content"):
                # Table name input
                yield Label("Table name:", classes="field-label")
                yield Input(
                    placeholder="table_name",
                    id="table-name-input",
                    classes="field-input",
                )

                # Column management section
                yield Label("Columns:", classes="section-title")
                yield Static("No columns added yet.", id="column-list")

                with Horizontal(id="column-buttons"):
                    yield Button("+ Add Column", id="add-column-button", variant="primary")

            with Horizontal(id="add-table-buttons"):
                yield Button("Cancel", id="cancel-button", variant="default")
                yield Button("Create Table", id="create-button", variant="success")

    def on_mount(self) -> None:
        """Focus the input when mounted."""
        input_widget = self.query_one("#table-name-input", Input)
        input_widget.focus()

    def update_column_list(self) -> None:
        """Update the column list display."""
        from textual.widgets import Static

        column_list = self.query_one("#column-list", Static)

        if not self.columns:
            column_list.update("No columns added yet.")
        else:
            lines = []
            for i, col in enumerate(self.columns):
                nullable = "NULL" if col.get("nullable", True) else "NOT NULL"
                default = f" DEFAULT '{col['default']}'" if col.get("default") else ""
                pk = " [PK]" if col.get("primary_key", False) else ""
                lines.append(f"{i+1}. {col['name']} ({col['type']}, {nullable}{default}){pk}")
            column_list.update("\n".join(lines))

        # Force a refresh to ensure the display updates
        column_list.refresh()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add-column-button":
            event.stop()
            # Determine if this should be marked as PK (first column by default)
            is_first_column = len(self.columns) == 0

            # Define callback for when screen is dismissed
            def handle_column_result(result):
                if result:
                    # If this column is marked as PK, unmark any existing PKs
                    if result.get("primary_key", False):
                        for col in self.columns:
                            col["primary_key"] = False

                    self.columns.append(result)
                    self.update_column_list()

            # Show column definition screen with callback
            self.app.push_screen(
                AddColumnDefScreen(default_primary_key=is_first_column),
                handle_column_result,
            )

        elif event.button.id == "create-button":
            event.stop()
            name_input = self.query_one("#table-name-input", Input)
            table_name = name_input.value.strip()

            if table_name:
                self.dismiss({"table_name": table_name, "columns": self.columns})
            else:
                # Could show an error message here
                pass
        elif event.button.id == "cancel-button":
            event.stop()
            self.dismiss(None)

    def action_cancel(self) -> None:
        """Handle cancel action (Escape key)."""
        self.dismiss(None)


class AddColumnDefScreen(ModalScreen):
    """Modal screen for defining a column to add to a new table."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    AddColumnDefScreen {
        align: center middle;
    }

    #add-column-dialog {
        width: 50;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #add-column-title {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        text-style: bold;
    }

    #add-column-content {
        height: auto;
        padding: 2 0;
    }

    .field-label {
        height: 1;
        margin-bottom: 1;
    }

    .field-input {
        width: 100%;
        margin-bottom: 1;
    }

    .field-select {
        width: 100%;
        margin-bottom: 1;
    }

    .field-switch {
        margin-bottom: 1;
    }

    #add-column-buttons {
        dock: bottom;
        height: 3;
        align: center middle;
        padding: 0;
    }

    #add-column-buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self, default_primary_key: bool = False):
        """Initialize add column definition screen.

        Args:
            default_primary_key: Whether to default the primary key checkbox to checked
        """
        super().__init__()
        self.default_primary_key = default_primary_key

        # Common SQLite data types
        self.data_types = [
            ("TEXT", "TEXT"),
            ("INTEGER", "INTEGER"),
            ("REAL", "REAL"),
            ("BLOB", "BLOB"),
            ("NUMERIC", "NUMERIC"),
        ]

    def compose(self) -> ComposeResult:
        from textual.widgets import Switch

        with Container(id="add-column-dialog"):
            yield Label("Define Column", id="add-column-title")
            with Vertical(id="add-column-content"):
                # Column name input
                yield Label("Column name:", classes="field-label")
                yield Input(
                    placeholder="column_name",
                    id="column-name-input",
                    classes="field-input",
                )

                # Column type selector
                yield Label("Column type:", classes="field-label")
                yield Select(
                    self.data_types,
                    value="TEXT",
                    id="column-type-select",
                    allow_blank=False,
                    classes="field-select",
                )

                # Nullable switch
                yield Label("Allow NULL values:", classes="field-label")
                yield Switch(value=False, id="nullable-switch", classes="field-switch")

                # Primary key switch
                yield Label("Primary key:", classes="field-label")
                yield Switch(
                    value=self.default_primary_key,
                    id="primary-key-switch",
                    classes="field-switch",
                )

                # Default value input (optional)
                yield Label("Default value (optional):", classes="field-label")
                yield Input(placeholder="", id="column-default-input", classes="field-input")

            with Horizontal(id="add-column-buttons"):
                yield Button("Cancel", id="cancel-button", variant="default")
                yield Button("Add Column", id="add-button", variant="primary")

    def on_mount(self) -> None:
        """Focus the input when mounted."""
        input_widget = self.query_one("#column-name-input", Input)
        input_widget.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        from textual.widgets import Switch

        if event.button.id == "add-button":
            event.stop()
            name_input = self.query_one("#column-name-input", Input)
            type_select = self.query_one("#column-type-select", Select)
            nullable_switch = self.query_one("#nullable-switch", Switch)
            pk_switch = self.query_one("#primary-key-switch", Switch)
            default_input = self.query_one("#column-default-input", Input)

            column_name = name_input.value.strip()
            column_type = type_select.value
            nullable = nullable_switch.value
            primary_key = pk_switch.value
            default_value = default_input.value.strip() or None

            if column_name:
                result = {
                    "name": column_name,
                    "type": column_type,
                    "nullable": nullable,
                    "primary_key": primary_key,
                }
                if default_value:
                    result["default"] = default_value

                self.dismiss(result)
            else:
                # Could show an error message here
                pass
        elif event.button.id == "cancel-button":
            event.stop()
            self.dismiss(None)

    def action_cancel(self) -> None:
        """Handle cancel action (Escape key)."""
        self.dismiss(None)


class RemoveTableScreen(ModalScreen):
    """Modal screen for removing a table from the database."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    RemoveTableScreen {
        align: center middle;
    }

    #remove-table-dialog {
        width: 50;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #remove-table-title {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        text-style: bold;
    }

    #remove-table-content {
        height: auto;
        padding: 2 0;
    }

    .field-label {
        height: 1;
        margin-bottom: 1;
    }

    .field-select {
        width: 100%;
        margin-bottom: 1;
    }

    #remove-table-buttons {
        dock: bottom;
        height: 3;
        align: center middle;
        padding: 0;
    }

    #remove-table-buttons Button {
        margin: 0 1;
    }

    #warning-label {
        color: $warning;
        text-style: bold;
        margin-top: 1;
    }
    """

    def __init__(self, tables: list[str]):
        """
        Initialize remove table screen.

        Args:
            tables: List of table names in the database
        """
        super().__init__()
        self.tables = tables

    def compose(self) -> ComposeResult:
        with Container(id="remove-table-dialog"):
            yield Label("Remove Table", id="remove-table-title")
            with Vertical(id="remove-table-content"):
                # Table selector
                yield Label("Select table to remove:", classes="field-label")
                table_options = [("(select table)", "")] + [(name, name) for name in self.tables]
                yield Select(
                    table_options,
                    value="",
                    id="table-select",
                    allow_blank=False,
                    classes="field-select",
                )

                # Warning
                yield Label(
                    "⚠ Warning: This will permanently delete the table and ALL its data!",
                    id="warning-label",
                )

            with Horizontal(id="remove-table-buttons"):
                yield Button("Cancel", id="cancel-button", variant="default")
                yield Button("Remove Table", id="remove-button", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "remove-button":
            event.stop()
            table_select = self.query_one("#table-select", Select)
            table_name = table_select.value

            if table_name:
                self.dismiss({"table_name": table_name})
            else:
                # Could show an error message here
                pass
        elif event.button.id == "cancel-button":
            event.stop()
            self.dismiss(None)

    def action_cancel(self) -> None:
        """Handle cancel action (Escape key)."""
        self.dismiss(None)

    def refresh_options(self, view_names: list[str], current_view: str) -> None:
        """
        Refresh the list of views dynamically.

        Args:
            view_names: Updated list of view names
            current_view: Currently active view
        """
        self.view_names = view_names
        self.current_view = current_view

        option_list = self.query_one("#view-selector-list", OptionList)
        option_list.clear_options()

        # Re-add all options
        for view_name in self.view_names:
            if view_name == self.current_view:
                option_list.add_option(Option(f"● {view_name}", id=view_name))
            else:
                option_list.add_option(Option(f"  {view_name}", id=view_name))

        option_list.add_option(Separator())
        option_list.add_option(Option("💾 Save current view", id="__save__"))
        option_list.add_option(Option("➕ Save as new view...", id="__save_as__"))


class FieldManagementScreen(ModalScreen):
    """Modal screen for managing fields - filter visibility, add new, or remove existing."""

    BINDINGS = [
        ("escape", "dismiss_none", "Close"),
    ]

    DEFAULT_CSS = """
    FieldManagementScreen {
        align: center middle;
    }

    #field-mgmt-dialog {
        width: 60;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #field-mgmt-title {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        text-style: bold;
    }

    #field-mgmt-content {
        height: auto;
        padding: 1 0;
    }

    #field-selection-list {
        height: auto;
        max-height: 20;
        margin-bottom: 1;
    }

    #field-mgmt-actions {
        height: auto;
        padding: 1 0;
    }

    #field-mgmt-actions Button {
        margin-right: 2;
    }

    #field-mgmt-buttons {
        dock: bottom;
        height: 3;
        align: right middle;
        padding: 0;
    }

    #field-mgmt-buttons Button {
        margin-left: 2;
    }
    """

    def __init__(self, table_name: str, fields: list[tuple[str, str]], visible_fields: set[str]):
        """
        Initialize field management screen.

        Args:
            table_name: Name of the table
            fields: List of (field_name, display_label) tuples
            visible_fields: Set of currently visible field names
        """
        super().__init__()
        self.table_name = table_name
        self.fields = fields
        self.visible_fields = visible_fields.copy()

    def compose(self) -> ComposeResult:
        with Container(id="field-mgmt-dialog"):
            yield Label(f"Manage {self.table_name} Fields", id="field-mgmt-title")

            with Vertical(id="field-mgmt-content"):
                # Field visibility selection
                yield Label("Select fields to display:", classes="field-label")
                selections = [
                    Selection(
                        field_label,
                        field_name,
                        initial_state=(field_name in self.visible_fields),
                    )
                    for field_name, field_label in self.fields
                ]
                yield SelectionList(*selections, id="field-selection-list")

                # Management actions
                with Horizontal(id="field-mgmt-actions"):
                    yield Button("+ Add New Field", id="add-field-button", variant="primary")
                    yield Button("✎ Rename Field", id="edit-field-button", variant="default")
                    yield Button("- Remove Field", id="remove-field-button", variant="default")

            with Horizontal(id="field-mgmt-buttons"):
                yield Button("Cancel", id="cancel-button", variant="default")
                yield Button("Apply", id="apply-button", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id or ""

        if button_id == "cancel-button":
            event.stop()
            self.dismiss(None)
        elif button_id == "apply-button":
            event.stop()
            # Get selected fields from SelectionList
            selection_list = self.query_one("#field-selection-list", SelectionList)
            new_visible_fields = set(selection_list.selected)
            self.dismiss({"action": "apply", "visible_fields": new_visible_fields})
        elif button_id == "add-field-button":
            event.stop()
            self.dismiss({"action": "add_field"})
        elif button_id == "edit-field-button":
            event.stop()
            self.dismiss({"action": "edit_field"})
        elif button_id == "remove-field-button":
            event.stop()
            self.dismiss({"action": "remove_field"})

    def action_dismiss_none(self) -> None:
        """Dismiss with None (cancel)."""
        self.dismiss(None)


class AddFieldScreen(ModalScreen):
    """Modal screen for adding a new field to a table."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    AddFieldScreen {
        align: center middle;
    }

    #add-field-dialog {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #add-field-title {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        text-style: bold;
    }

    #add-field-content {
        height: auto;
        padding: 2 0;
    }

    .field-input-row {
        height: auto;
        padding: 0 0 1 0;
    }

    .field-label {
        height: 1;
        margin-bottom: 1;
    }

    .field-input {
        width: 100%;
        margin-bottom: 1;
    }

    .field-select {
        width: 100%;
        margin-bottom: 1;
    }

    #add-field-buttons {
        dock: bottom;
        height: 3;
        align: center middle;
        padding: 0;
    }

    #add-field-buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self, table_name: str):
        """
        Initialize add field screen.

        Args:
            table_name: Name of the table to add field to
        """
        super().__init__()
        self.table_name = table_name

        # Common SQLite data types
        self.data_types = [
            ("TEXT", "TEXT"),
            ("INTEGER", "INTEGER"),
            ("REAL", "REAL"),
            ("BLOB", "BLOB"),
            ("NUMERIC", "NUMERIC"),
        ]

    def compose(self) -> ComposeResult:
        with Container(id="add-field-dialog"):
            yield Label(f"Add Field to {self.table_name}", id="add-field-title")
            with Vertical(id="add-field-content"):
                # Field name input
                yield Label("Field name:", classes="field-label")
                yield Input(
                    placeholder="field_name",
                    id="field-name-input",
                    classes="field-input",
                )

                # Field type selector
                yield Label("Field type:", classes="field-label")
                yield Select(
                    self.data_types,
                    value="TEXT",
                    id="field-type-select",
                    allow_blank=False,
                    classes="field-select",
                )

                # Default value input (optional)
                yield Label("Default value (optional):", classes="field-label")
                yield Input(placeholder="", id="field-default-input", classes="field-input")

            with Horizontal(id="add-field-buttons"):
                yield Button("Cancel", id="cancel-button", variant="default")
                yield Button("Add Field", id="add-button", variant="primary")

    def on_mount(self) -> None:
        """Focus the input when mounted."""
        input_widget = self.query_one("#field-name-input", Input)
        input_widget.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add-button":
            event.stop()
            name_input = self.query_one("#field-name-input", Input)
            type_select = self.query_one("#field-type-select", Select)
            default_input = self.query_one("#field-default-input", Input)

            field_name = name_input.value.strip()
            field_type = type_select.value
            default_value = default_input.value.strip() or None

            if field_name:
                self.dismiss({"name": field_name, "type": field_type, "default": default_value})
            else:
                # Could show an error message here
                pass
        elif event.button.id == "cancel-button":
            event.stop()
            self.dismiss(None)

    def action_cancel(self) -> None:
        """Handle cancel action (Escape key)."""
        self.dismiss(None)


class RemoveFieldScreen(ModalScreen):
    """Modal screen for removing a field from a table."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    RemoveFieldScreen {
        align: center middle;
    }

    #remove-field-dialog {
        width: 50;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #remove-field-title {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        text-style: bold;
    }

    #remove-field-content {
        height: auto;
        padding: 2 0;
    }

    .field-label {
        height: 1;
        margin-bottom: 1;
    }

    .field-select {
        width: 100%;
        margin-bottom: 1;
    }

    #remove-field-buttons {
        dock: bottom;
        height: 3;
        align: center middle;
        padding: 0;
    }

    #remove-field-buttons Button {
        margin: 0 1;
    }

    #warning-label {
        color: $warning;
        text-style: bold;
        margin-top: 1;
    }
    """

    def __init__(self, table_name: str, fields: list[tuple[str, str]]):
        """
        Initialize remove field screen.

        Args:
            table_name: Name of the table
            fields: List of (field_name, display_label) tuples
        """
        super().__init__()
        self.table_name = table_name
        self.fields = fields

    def compose(self) -> ComposeResult:
        with Container(id="remove-field-dialog"):
            yield Label(f"Remove Field from {self.table_name}", id="remove-field-title")
            with Vertical(id="remove-field-content"):
                # Field selector
                yield Label("Select field to remove:", classes="field-label")
                field_options = [("(select field)", "")] + [
                    (display_label, field_name) for field_name, display_label in self.fields
                ]
                yield Select(
                    field_options,
                    value="",
                    id="field-select",
                    allow_blank=False,
                    classes="field-select",
                )

                # Warning
                yield Label(
                    "⚠ Warning: This will permanently delete the field and all its data!",
                    id="warning-label",
                )

            with Horizontal(id="remove-field-buttons"):
                yield Button("Cancel", id="cancel-button", variant="default")
                yield Button("Remove Field", id="remove-button", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "remove-button":
            event.stop()
            field_select = self.query_one("#field-select", Select)
            field_name = field_select.value

            if field_name and field_name != "":
                self.dismiss(field_name)
            else:
                # Could show an error message here
                pass
        elif event.button.id == "cancel-button":
            event.stop()
            self.dismiss(None)

    def action_cancel(self) -> None:
        """Handle cancel action (Escape key)."""
        self.dismiss(None)


class EditFieldScreen(ModalScreen):
    """Modal screen for editing (renaming) a field in a table."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    EditFieldScreen {
        align: center middle;
    }

    #edit-field-dialog {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #edit-field-title {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        text-style: bold;
    }

    #edit-field-content {
        height: auto;
        padding: 2 0;
    }

    .field-label {
        height: 1;
        margin-bottom: 1;
    }

    .field-select {
        width: 100%;
        margin-bottom: 1;
    }

    .field-input {
        width: 100%;
        margin-bottom: 1;
    }

    #edit-field-buttons {
        dock: bottom;
        height: 3;
        align: center middle;
        padding: 0;
    }

    #edit-field-buttons Button {
        margin: 0 1;
    }
    """

    def __init__(self, table_name: str, fields: list[tuple[str, str]]):
        """
        Initialize edit field screen.

        Args:
            table_name: Name of the table
            fields: List of (field_name, display_label) tuples
        """
        super().__init__()
        self.table_name = table_name
        self.fields = fields

    def compose(self) -> ComposeResult:
        with Container(id="edit-field-dialog"):
            yield Label(f"Rename Field in {self.table_name}", id="edit-field-title")
            with Vertical(id="edit-field-content"):
                # Field selector
                yield Label("Select field to rename:", classes="field-label")
                field_options = [("(select field)", "")] + [
                    (display_label, field_name) for field_name, display_label in self.fields
                ]
                yield Select(
                    field_options,
                    value="",
                    id="field-select",
                    allow_blank=False,
                    classes="field-select",
                )

                # New name input
                yield Label("New field name:", classes="field-label")
                yield Input(
                    placeholder="new_field_name",
                    id="new-name-input",
                    classes="field-input",
                )

            with Horizontal(id="edit-field-buttons"):
                yield Button("Cancel", id="cancel-button", variant="default")
                yield Button("Rename Field", id="rename-button", variant="primary")

    def on_select_changed(self, event: Select.Changed) -> None:
        """When field is selected, focus the input."""
        if event.value:
            input_widget = self.query_one("#new-name-input", Input)
            input_widget.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "rename-button":
            event.stop()
            field_select = self.query_one("#field-select", Select)
            name_input = self.query_one("#new-name-input", Input)

            old_name = field_select.value
            new_name = name_input.value.strip()

            if old_name and new_name:
                self.dismiss({"old_name": old_name, "new_name": new_name})
            else:
                # Could show an error message here
                pass
        elif event.button.id == "cancel-button":
            event.stop()
            self.dismiss(None)

    def action_cancel(self) -> None:
        """Handle cancel action (Escape key)."""
        self.dismiss(None)


class RecordFilterScreen(ModalScreen[Optional[list[tuple[str, str, str, str]]]]):
    """Modal screen for filtering records with WHERE conditions."""

    BINDINGS = [
        ("escape", "dismiss_none", "Close"),
    ]

    DEFAULT_CSS = """
    RecordFilterScreen {
        align: center middle;
    }

    #record-filter-dialog {
        width: 90%;
        max-width: 100;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #record-filter-title {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        text-style: bold;
    }

    #filter-header {
        height: auto;
        padding: 1 0;
        color: $text-muted;
    }

    #filter-list {
        height: auto;
        max-height: 20;
        padding: 1 0;
        overflow-x: auto;
    }

    .filter-row {
        height: auto;
        padding: 0 0 1 0;
        min-width: 70;
    }

    .filter-row Label {
        width: 5;
        padding: 0 1;
    }

    .filter-bool-placeholder {
        width: 1;
        min-width: 1;
    }

    .filter-bool-select {
        width: 5;
        min-width: 5;
        margin-right: 1;
    }

    .filter-row Select {
        width: 18;
        margin-right: 1;
    }

    .filter-row Input {
        width: 18;
        margin-right: 1;
    }

    .filter-row Button {
        width: 3;
    }

    #add-filter-button {
        margin-top: 1;
        margin-bottom: 1;
    }

    #filter-buttons {
        dock: bottom;
        height: 3;
        align: right middle;
        padding: 0;
    }

    #filter-buttons Button {
        margin-left: 2;
    }
    """

    def __init__(
        self,
        table_name: str,
        fields: list[tuple[str, str]],
        current_filters: list[tuple[str, str, str, str]],
    ):
        """
        Initialize record filter screen.

        Args:
            table_name: Display name of the table
            fields: List of (field_name, display_label) tuples
            current_filters: Current filter configuration as list of (field, operator, value, boolean_op) tuples
        """
        super().__init__()
        self.table_name = table_name
        self.fields = fields
        self.current_filters = current_filters.copy() if current_filters else []

        # Operator options
        self.operators = [
            ("is", "is"),
            ("is not", "is_not"),
            ("contains", "contains"),
            ("starts with", "starts_with"),
            ("ends with", "ends_with"),
            ("greater than", "gt"),
            ("greater than or equal", "gte"),
            ("less than", "lt"),
            ("less than or equal", "lte"),
        ]

        # Boolean operator options
        self.boolean_operators = [
            ("and", "AND"),
            ("or", "OR"),
        ]

    def compose(self) -> ComposeResult:
        with Container(id="record-filter-dialog"):
            yield Label(f"Filter {self.table_name}", id="record-filter-title")
            yield Label("In this view, show records where:", id="filter-header")

            with Vertical(id="filter-list"):
                # Add existing filter rows
                for idx, filter_tuple in enumerate(self.current_filters):
                    # Handle both old (3-tuple) and new (4-tuple) formats
                    if len(filter_tuple) == 4:
                        field, op, value, bool_op = filter_tuple
                    elif len(filter_tuple) == 3:
                        field, op, value = (
                            filter_tuple[0],
                            filter_tuple[1],
                            filter_tuple[2],
                        )
                        bool_op = "AND"  # Default for old format
                    else:
                        field, op, value, bool_op = None, "is", "", "AND"

                    yield from self._create_filter_row(idx, field, op, value, bool_op)

                # Add one empty row if no filters exist
                if not self.current_filters:
                    yield from self._create_filter_row(0, None, "is", "", "AND")

                yield Button("+ Add Filter", id="add-filter-button", variant="default")

            with Horizontal(id="filter-buttons"):
                yield Button("Clear All", id="clear-button", variant="default")
                yield Button("Cancel", id="cancel-button", variant="default")
                yield Button("Apply", id="apply-button", variant="primary")

    def _create_filter_row(
        self, idx: int, selected_field=None, selected_op="is", value="", bool_op="AND"
    ):
        """Create a row with field selector, operator selector, value input, and remove button."""
        with Horizontal(classes="filter-row", id=f"filter-row-{idx}"):
            # Boolean operator dropdown for rows after the first
            if idx > 0:
                yield Select(
                    self.boolean_operators,
                    value=bool_op,
                    id=f"filter-bool-{idx}",
                    allow_blank=False,
                    classes="filter-bool-select",
                )
            else:
                # Empty placeholder for first row to maintain alignment
                yield Label("", classes="filter-bool-placeholder")

            # Field selector
            field_options = [("(select field)", "")] + [
                (display_label, field_name) for field_name, display_label in self.fields
            ]
            yield Select(
                field_options,
                value=selected_field or "",
                id=f"filter-field-{idx}",
                allow_blank=False,
            )

            # Operator selector
            yield Select(
                self.operators,
                value=selected_op,
                id=f"filter-op-{idx}",
                allow_blank=False,
            )

            # Value input
            yield Input(placeholder="value", value=value, id=f"filter-value-{idx}")

            # Remove button
            yield Button("✕", id=f"remove-filter-{idx}", variant="error")

    def _create_filter_row_widget(
        self, idx: int, selected_field=None, selected_op="is", value="", bool_op="AND"
    ):
        """Create a complete filter row widget for dynamic mounting."""
        # Create the container with all children
        row = Horizontal(classes="filter-row", id=f"filter-row-{idx}")

        # Create child widgets
        if idx > 0:
            bool_select = Select(
                self.boolean_operators,
                value=bool_op,
                id=f"filter-bool-{idx}",
                allow_blank=False,
                classes="filter-bool-select",
            )
        else:
            bool_select = Label("", classes="filter-bool-placeholder")  # Empty placeholder

        # Field selector
        field_options = [("(select field)", "")] + [
            (display_label, field_name) for field_name, display_label in self.fields
        ]
        field_select = Select(
            field_options,
            value=selected_field or "",
            id=f"filter-field-{idx}",
            allow_blank=False,
        )

        # Operator selector
        op_select = Select(
            self.operators, value=selected_op, id=f"filter-op-{idx}", allow_blank=False
        )

        # Value input
        value_input = Input(placeholder="value", value=value, id=f"filter-value-{idx}")

        # Remove button
        remove_button = Button("✕", id=f"remove-filter-{idx}", variant="error")

        # Compose all children into the row
        row._add_children(bool_select, field_select, op_select, value_input, remove_button)

        return row

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        event.stop()  # Prevent event from bubbling to parent handlers

        if button_id == "cancel-button":
            self.dismiss(None)
        elif button_id == "apply-button":
            # Collect filter configuration
            filters = []
            idx = 0
            while True:
                try:
                    field_select = self.query_one(f"#filter-field-{idx}", Select)
                    op_select = self.query_one(f"#filter-op-{idx}", Select)
                    value_input = self.query_one(f"#filter-value-{idx}", Input)

                    field = field_select.value
                    op = op_select.value
                    value = value_input.value.strip()

                    # Get boolean operator for rows after the first
                    if idx > 0:
                        try:
                            bool_select = self.query_one(f"#filter-bool-{idx}", Select)
                            bool_op = bool_select.value
                        except:
                            bool_op = "AND"  # Default if not found
                    else:
                        bool_op = "AND"  # First row always uses AND (though it's ignored)

                    # Only include filters with a field and value
                    if field and field != "" and value:
                        filters.append((field, op, value, bool_op))

                    idx += 1
                except:
                    break

            self.dismiss(filters)
        elif button_id == "clear-button":
            self.dismiss([])
        elif button_id == "add-filter-button":
            # Add a new filter row
            idx = 0
            while True:
                try:
                    self.query_one(f"#filter-row-{idx}")
                    idx += 1
                except:
                    break

            container = self.query_one("#filter-list", Vertical)
            add_button = self.query_one("#add-filter-button")

            # Create new row widget with default AND operator
            new_row = self._create_filter_row_widget(idx, None, "is", "", "AND")
            container.mount(new_row, before=add_button)
        elif button_id.startswith("remove-filter-"):
            # Remove the specific row
            row_id = button_id.replace("remove-filter-", "filter-row-")
            row = self.query_one(f"#{row_id}")
            row.remove()

    def action_dismiss_none(self) -> None:
        """Dismiss with None (cancel)."""
        self.dismiss(None)


class DatabaseMenuScreen(ModalScreen):
    """Modal screen for database operations menu."""

    BINDINGS = [
        ("escape", "dismiss_none", "Close"),
    ]

    DEFAULT_CSS = """
    DatabaseMenuScreen {
        align: center middle;
    }

    #db-menu-dialog {
        width: 50;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #db-menu-title {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        text-style: bold;
    }

    #db-menu-content {
        height: auto;
        padding: 2 0;
    }

    #db-menu-content Button {
        width: 100%;
        margin-bottom: 1;
    }

    #db-menu-buttons {
        dock: bottom;
        height: 3;
        align: center middle;
        padding: 0;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="db-menu-dialog"):
            yield Label("Database Operations", id="db-menu-title")
            with Vertical(id="db-menu-content"):
                yield Button("+ Add New Table", id="add-table-button", variant="primary")
                yield Button("- Remove Table", id="remove-table-button", variant="default")
            with Horizontal(id="db-menu-buttons"):
                yield Button("Close", id="close-button", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""

        if button_id == "add-table-button":
            event.stop()
            self.dismiss({"action": "add_table"})
        elif button_id == "remove-table-button":
            event.stop()
            self.dismiss({"action": "remove_table"})
        elif button_id == "close-button":
            event.stop()
            self.dismiss(None)

    def action_dismiss_none(self) -> None:
        """Dismiss with None (cancel)."""
        self.dismiss(None)


class EditRowScreen(ModalScreen):
    """Modal screen for adding or editing a row in a table."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    EditRowScreen {
        align: center middle;
    }

    #edit-row-dialog {
        width: 70;
        height: auto;
        max-height: 90%;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    #edit-row-title {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        text-style: bold;
    }

    #edit-row-content {
        height: auto;
        max-height: 30;
        padding: 2 0;
    }

    .field-row {
        height: auto;
        padding: 0 0 1 0;
    }

    .field-label {
        height: 1;
        width: 20;
        margin-right: 2;
    }

    .field-input {
        width: 1fr;
    }

    .field-select {
        width: 1fr;
    }

    .pk-value {
        width: 1fr;
        color: $text-muted;
    }

    #edit-row-buttons {
        dock: bottom;
        height: 3;
        align: center middle;
        padding: 0;
    }

    #edit-row-buttons Button {
        margin: 0 1;
    }
    """

    def __init__(
        self,
        table_name: str,
        columns: list[dict],
        foreign_keys: list[dict],
        existing_row: dict | None = None,
    ):
        """
        Initialize edit row screen.

        Args:
            table_name: Name of the table
            columns: List of column dicts from schema.get_columns()
            foreign_keys: List of FK dicts from schema.get_all_foreign_keys()
            existing_row: Optional dict of existing row data for edit mode (None for add mode)
        """
        super().__init__()
        self.table_name = table_name
        self.columns = columns
        self.foreign_keys = foreign_keys
        self.existing_row = existing_row
        self.is_edit_mode = existing_row is not None

        # Build FK lookup dict for quick access
        self.fk_map = {fk["column"]: fk for fk in foreign_keys}

    def compose(self) -> ComposeResult:
        title = (
            f"Edit Row in {self.table_name}"
            if self.is_edit_mode
            else f"Add Row to {self.table_name}"
        )
        button_label = "Save Changes" if self.is_edit_mode else "Add Row"

        with Container(id="edit-row-dialog"):
            yield Label(title, id="edit-row-title")
            with VerticalScroll(id="edit-row-content"):
                # Create input for each column
                for col in self.columns:
                    col_name = col["name"]
                    display_name = col["display_name"]

                    with Horizontal(classes="field-row"):
                        yield Label(f"{display_name}:", classes="field-label")

                        # Primary key: show as read-only in edit mode, hide in add mode
                        if col["pk"]:
                            if self.is_edit_mode and self.existing_row:
                                pk_value = str(self.existing_row.get(col_name, ""))
                                yield Static(pk_value, classes="pk-value")
                            else:
                                # In add mode, skip PK (auto-increment)
                                yield Static("(auto)", classes="pk-value")
                            continue

                        # Check if this is a foreign key
                        if col_name in self.fk_map:
                            # Create a Select widget with options from referenced table
                            # Placeholder - will be populated in on_mount
                            initial_value = Select.BLANK
                            if self.is_edit_mode and self.existing_row:
                                val = self.existing_row.get(col_name)
                                initial_value = str(val) if val is not None else Select.BLANK

                            yield Select(
                                [("Loading...", Select.BLANK)],  # Placeholder option
                                value=initial_value,
                                id=f"input-{col_name}",
                                allow_blank=True,
                                classes="field-select",
                            )
                        else:
                            # Regular input field
                            placeholder = ""
                            if not col["notnull"]:
                                placeholder = "(optional)"

                            initial_value = ""
                            if self.is_edit_mode and self.existing_row:
                                val = self.existing_row.get(col_name)
                                initial_value = str(val) if val is not None else ""

                            yield Input(
                                value=initial_value,
                                placeholder=placeholder,
                                id=f"input-{col_name}",
                                classes="field-input",
                            )

            with Horizontal(id="edit-row-buttons"):
                yield Button("Cancel", id="cancel-button", variant="default")
                yield Button(button_label, id="save-button", variant="primary")

    def on_mount(self) -> None:
        """Populate FK dropdowns after mount."""
        # Import here to avoid circular dependency
        from sqlalchemy import text

        from . import schema
        from .app import Deflatable

        # Get the app instance to access the engine
        app = self.app
        if not isinstance(app, Deflatable):
            return

        engine = app.engine

        # Populate FK select widgets
        for col_name, fk in self.fk_map.items():
            try:
                select_widget = self.query_one(f"#input-{col_name}", Select)

                # Get records from referenced table
                ref_table = fk["ref_table"]
                ref_columns = schema.get_columns(engine, ref_table)

                # Find PK and name column
                pk_col = next((c["name"] for c in ref_columns if c["pk"]), "id")
                name_col = schema.get_name_column(engine, ref_table)

                # Fetch records
                with engine.connect() as conn:
                    result = conn.execute(
                        text(
                            f'SELECT "{pk_col}", "{name_col}" FROM "{ref_table}" ORDER BY "{name_col}"'
                        )
                    )
                    records = result.fetchall()

                # Build options - use Select.BLANK for the empty option
                from typing import Any

                options: list[tuple[str, Any]] = [("(none)", Select.BLANK)]
                for record in records:
                    pk_value = record[0]
                    name_value = record[1] if record[1] is not None else f"(ID: {pk_value})"
                    options.append((str(name_value), str(pk_value)))

                # Get current value to preserve selection in edit mode
                current_value = select_widget.value

                # Determine the value to set
                if current_value and current_value != Select.BLANK:
                    # Check if current value exists in options
                    if any(opt[1] == current_value for opt in options):
                        new_value = current_value
                    else:
                        new_value = Select.BLANK
                else:
                    new_value = Select.BLANK

                # Use set_options to update the select widget in place
                select_widget.set_options(options)
                select_widget.value = new_value

            except Exception as e:
                # If FK population fails, log error and leave placeholder select
                if hasattr(app, "log"):
                    app.log.error(f"Failed to populate FK dropdown for {col_name}: {e}")
                    import traceback

                    app.log.error(traceback.format_exc())
                pass

        # Focus first editable input
        try:
            for col in self.columns:
                if not col["pk"]:
                    first_input = self.query_one(f"#input-{col['name']}")
                    first_input.focus()
                    break
        except:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-button":
            event.stop()

            # Collect values from all inputs
            row_data = {}

            # Include PK if in edit mode
            if self.is_edit_mode and self.existing_row:
                for col in self.columns:
                    if col["pk"]:
                        row_data[col["name"]] = self.existing_row.get(col["name"])

            # Collect other fields
            for col in self.columns:
                if col["pk"]:
                    continue

                col_name = col["name"]
                try:
                    widget = self.query_one(f"#input-{col_name}")

                    if isinstance(widget, Select):
                        # Foreign key select - check for BLANK sentinel
                        value = widget.value if widget.value != Select.BLANK else None
                    elif isinstance(widget, Input):
                        # Regular input
                        value = widget.value.strip() if widget.value else None

                        # Convert empty strings to None
                        if value == "":
                            value = None
                    else:
                        continue

                    row_data[col_name] = value

                except Exception:
                    # If widget not found, skip
                    pass

            # Validate required fields
            validation_errors = []
            for col in self.columns:
                if col["pk"]:
                    continue

                col_name = col["name"]
                if col["notnull"] and (col_name not in row_data or row_data[col_name] is None):
                    validation_errors.append(f"{col['display_name']} is required")

            if validation_errors:
                # Show error notification
                app = self.app
                if hasattr(app, "notify"):
                    app.notify("\n".join(validation_errors), severity="error", timeout=5)
                self.dismiss(None)
                return

            # Return result with mode indicator
            result = {"mode": "edit" if self.is_edit_mode else "add", "data": row_data}
            self.dismiss(result)

        elif event.button.id == "cancel-button":
            event.stop()
            self.dismiss(None)

    def action_cancel(self) -> None:
        """Handle cancel action (Escape key)."""
        self.dismiss(None)
