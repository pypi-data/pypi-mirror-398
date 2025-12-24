"""Main application module."""

from rich.text import Text
from sqlalchemy import create_engine
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, HorizontalScroll, Vertical
from textual.events import Click
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Input,
    Label,
    Static,
    TabbedContent,
    TabPane,
)

from . import display, schema
from .config import DeflatableConfig
from .screens import (
    AddFieldScreen,
    AddTableScreen,
    DatabaseMenuScreen,
    EditFieldScreen,
    EditRowScreen,
    FieldManagementScreen,
    GroupingScreen,
    RecordFilterScreen,
    RemoveFieldScreen,
    RemoveTableScreen,
    ReverseFKDetailScreen,
    SaveViewScreen,
    SortingScreen,
    ViewSelectorScreen,
)
from .state import StateManager


class DeflatableHeader(Static):
    """Custom header with app title and database menu button."""

    DEFAULT_CSS = """
    DeflatableHeader {
        dock: top;
        width: 100%;
        height: 1;
        background: $boost;
        color: $text;
        padding: 0 1;
    }

    DeflatableHeader Horizontal {
        width: 100%;
        height: 1;
        align: left middle;
    }

    DeflatableHeader .header-title {
        width: auto;
        margin-right: 2;
        color: $accent;
        text-style: bold;
    }

    DeflatableHeader .menu-item {
        width: auto;
        margin-left: 2;
        color: $text;
        text-style: bold;
    }

    DeflatableHeader .menu-item:hover {
        color: $accent;
        text-style: bold reverse;
    }
    """

    def __init__(self, app_title: str = "Deflatable"):
        super().__init__()
        self.app_title = app_title

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(f"⚙ {self.app_title}", classes="header-title")
            yield Label("Database ▾", id="database-menu-button", classes="menu-item")


class Deflatable(App):
    """A generic Textual app to browse any SQLite database."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("/", "start_search", "Search"),
        ("n", "next_match", "Next"),
        ("N,shift+n", "prev_match", "Previous"),
        ("e", "edit_current_row", "Edit Row"),
        ("+", "add_row", "Add Row"),
        Binding("escape", "cancel_search", "", show=False),
    ]

    CSS = """
    Screen {
        background: $surface;
    }

    .tab-container {
        height: 1fr;
    }

    .tab-controls {
        height: auto;
        padding: 1 2;
        background: $boost;
        border-bottom: solid $primary;
    }

    .tab-controls Button {
        margin-right: 2;
        min-width: 12;
    }

    .tab-controls Select {
        width: 30;
        margin-right: 2;
    }

    DataTable {
        height: 1fr;
    }

    .info-label {
        color: $text-muted;
    }

    TabbedContent {
        height: 1fr;
    }

    .group-header {
        background: $boost;
        text-style: bold;
    }

    #search-container {
        dock: bottom;
        height: 3;
        background: $boost;
        display: none;
    }

    #search-input {
        width: 1fr;
    }

    #search-status {
        width: auto;
        padding: 0 2;
        color: $text-muted;
    }
    """

    def __init__(self, config: "DeflatableConfig"):
        """
        Initialize the database browser app.

        Args:
            config: Configuration object with database URL and views (required)
        """
        super().__init__()
        self.engine = create_engine(config.db_url)
        self.config = config
        self.state_manager = StateManager(self.engine, config=config)

        # Get tables in config-specified order
        all_tables = schema.get_tables(self.engine)
        self.tables = config.get_ordered_tables(all_tables)

        # Search state
        self.search_query = ""
        self.search_matches = []  # List of row indices that match
        self.search_match_index = 0  # Current position in matches list
        self.current_table = None  # Track which table we're searching in

        # Double-click tracking
        self._last_click_time = 0.0
        self._last_click_row = None
        self._last_click_table = None

    def compose(self) -> ComposeResult:
        """Create child widgets dynamically based on database schema."""
        yield DeflatableHeader(app_title=self.title)

        # Determine initial tab (first table)
        initial_tab = f"tab-{self.tables[0]}" if self.tables else "tab-default"

        with TabbedContent(initial=initial_tab):
            for table in self.tables:
                table_title = schema.to_title_case(table)
                tab_id = f"tab-{table}"

                with TabPane(table_title, id=tab_id):
                    with Vertical(classes="tab-container"):
                        with HorizontalScroll(
                            classes="tab-controls", id=f"{table}-controls"
                        ):
                            # Get view names for this table
                            view_names = self.state_manager.get_view_names(table)
                            state = self.state_manager.get_state(table)

                            # Add view selector button
                            view_label = state.current_view_name + (
                                " *" if state.is_modified else ""
                            )
                            yield Button(
                                f"View: {view_label}",
                                id=f"{table}-view-button",
                                variant="primary",
                            )

                            # Get grouping options for this table
                            # Pass current state filters so options reflect the filtered dataset
                            state = self.state_manager.get_state(table)
                            grouping_options = schema.get_grouping_options(
                                self.engine, table, state.filters
                            )

                            # Add grouping button (only if grouping options available)
                            if grouping_options:
                                yield Button(
                                    "Group",
                                    id=f"{table}-group-button",
                                    variant="primary",
                                )

                            # Add fields, filter, and sort buttons
                            yield Button(
                                "Fields", id=f"{table}-fields-button", variant="primary"
                            )
                            yield Button(
                                "Filter", id=f"{table}-filter-button", variant="primary"
                            )
                            yield Button(
                                "Sort", id=f"{table}-sort-button", variant="primary"
                            )

                        yield DataTable(id=f"{table}-table")

        # Search container (hidden by default, shown when / is pressed)
        with Horizontal(id="search-container"):
            yield Label("/", id="search-prompt")
            yield Input(placeholder="Search...", id="search-input")
            yield Label("", id="search-status")

        yield Footer()

    def on_mount(self) -> None:
        """Set up the app when it starts."""
        # Load data for all tables
        for table in self.tables:
            self.load_table_display(table)

    def update_view_select_prompt(self, table: str) -> None:
        """Update the view button label to show modified indicator."""
        state = self.state_manager.get_state(table)
        button_id = f"{table}-view-button"

        try:
            view_button = self.query_one(f"#{button_id}", Button)
            view_label = state.current_view_name + (" *" if state.is_modified else "")
            view_button.label = f"View: {view_label}"
        except:
            pass  # Widget might not exist yet

    def load_table_display(self, table: str) -> None:
        """
        Load data for a specific table.

        Args:
            table: Table name
        """
        state = self.state_manager.get_state(table)

        # Get field formats configuration for this table
        table_views = self.config.get_table_views(table)
        field_formats = {}
        record_links = {}
        if table_views:
            # Get field formats
            if table_views.field_formats:
                # Build dict mapping field name to format type
                for (
                    field_name,
                    field_config,
                ) in table_views.field_formats.fields.items():
                    if field_config.format:
                        field_formats[field_name] = field_config.format

            # Get record links
            if table_views.record_links:
                record_links = table_views.record_links

        # Get display data
        columns, grouped_rows = display.load_table_display(
            self.engine,
            state,
            reverse_fk_preview_items=self.config.settings.display.reverse_fk_preview_items,
            cell_truncation_length=self.config.settings.display.cell_truncation_length,
            field_formats=field_formats,
            record_links=record_links,
        )

        # Check if we have grouping enabled
        if state.grouping and len(grouped_rows) > 1:
            # Use Collapsible view for grouped data
            self._load_collapsible_view(table, columns, grouped_rows, state)
        else:
            # Use single DataTable for ungrouped data
            self._load_single_table_view(table, columns, grouped_rows)

    def _load_single_table_view(
        self, table: str, columns: list, grouped_rows: dict
    ) -> None:
        """Load data in a single DataTable (ungrouped view)."""
        table_widget = self.query_one(f"#{table}-table", DataTable)
        table_widget.clear(columns=True)
        table_widget.cursor_type = "cell"
        table_widget.display = True

        # Add columns
        table_widget.add_columns(*columns)

        # Add all rows (ungrouped data will have None as key)
        # Store row metadata in a mapping for cell click handling
        if not hasattr(self, "row_metadata"):
            self.row_metadata = {}

        self.row_metadata[table] = []

        for rows in grouped_rows.values():
            for row_data, row_display in rows:
                # Store row_data for this row
                self.row_metadata[table].append(row_data)
                # Add the display row to the table
                table_widget.add_row(*row_display)

    def _load_collapsible_view(
        self, table: str, columns: list, grouped_rows: dict, state
    ) -> None:
        """Load data in Collapsible sections (grouped view)."""
        # Hide the regular DataTable
        table_widget = self.query_one(f"#{table}-table", DataTable)
        table_widget.display = False

        # TODO: Implement collapsible view with dynamic mounting
        # For now, fall back to the old header-based approach
        table_widget.display = True
        table_widget.clear(columns=True)
        table_widget.cursor_type = "cell"

        # Add columns
        table_widget.add_columns(*columns)

        # Calculate column widths - need to extract display rows only
        display_rows_only = {}
        for group_name, rows in grouped_rows.items():
            display_rows_only[group_name] = [row_display for _, row_display in rows]
        col_widths = display.calculate_column_widths(columns, display_rows_only)

        # Store row metadata
        if not hasattr(self, "row_metadata"):
            self.row_metadata = {}
        self.row_metadata[table] = []

        # Add rows with group headers (enhanced styling)
        for group_name, rows in grouped_rows.items():
            # Add group header if we have grouping
            if group_name is not None:
                # Get group header styles from config
                header_style = self.config.settings.display.group_header_style
                bg_style = self.config.settings.display.group_header_bg_style

                # Create header row with styled text spanning all columns
                # Use calculated column widths to fill cells properly
                header_row = [Text(group_name, style=header_style)]
                for i in range(1, len(columns)):
                    # Fill each cell with spaces based on column width
                    width = col_widths[i] if i < len(col_widths) else 20
                    header_row.append(Text(" " * width, style=bg_style))
                table_widget.add_row(*header_row)
                # Add empty metadata for header row
                self.row_metadata[table].append({})

            # Add data rows
            for row_data, row_display in rows:
                # Store row_data for this row
                self.row_metadata[table].append(row_data)
                table_widget.add_row(*row_display)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id or ""

        # Handle database menu button
        if button_id == "database-menu-button":
            self.handle_database_menu()
            return

        # Extract table name from button ID
        if button_id.endswith("-view-button"):
            table = button_id[: -len("-view-button")]
            self.handle_view_button(table)

        elif button_id.endswith("-fields-button"):
            table = button_id[: -len("-fields-button")]
            self.handle_fields_button(table)

        elif button_id.endswith("-group-button"):
            table = button_id[: -len("-group-button")]
            self.handle_group_button(table)

        elif button_id.endswith("-filter-button"):
            table = button_id[: -len("-filter-button")]
            self.handle_filter_button(table)

        elif button_id.endswith("-sort-button"):
            table = button_id[: -len("-sort-button")]
            self.handle_sort_button(table)

    def on_click(self, event: Click) -> None:
        """Handle clicks on widgets (for header menu items)."""
        # Check if we clicked on the database menu label
        widget = self.app.get_widget_at(event.screen_x, event.screen_y)[0]
        if hasattr(widget, "id") and widget.id == "database-menu-button":
            self.handle_database_menu()
            event.stop()

    def handle_database_menu(self):
        """Handle database menu button press - show database operations modal."""
        screen = DatabaseMenuScreen()

        def handle_result(result):
            if result is None:
                return

            action = result.get("action")

            if action == "add_table":
                self.handle_add_table()
            elif action == "remove_table":
                self.handle_remove_table()

        self.push_screen(screen, handle_result)

    def handle_view_button(self, table: str):
        """
        Handle view button press - show view selector modal.

        Args:
            table: Table name
        """
        state = self.state_manager.get_state(table)
        view_names = self.state_manager.get_view_names(table)

        screen = ViewSelectorScreen(table, view_names, state.current_view_name)

        def handle_result(selected_option):
            if not selected_option:
                return

            # Handle special actions
            if selected_option == "__save__":
                self.handle_save_current_view(table)
            elif selected_option == "__save_as__":
                self.handle_save_as_new_view(table)
            else:
                # Normal view switch
                self.state_manager.switch_view(table, selected_option)
                self.update_view_select_prompt(table)
                self.load_table_display(table)

        self.push_screen(screen, handle_result)

    def handle_fields_button(self, table: str):
        """
        Handle fields button press for a table.

        Args:
            table: Table name
        """
        state = self.state_manager.get_state(table)

        # Get record links configuration
        table_views = self.config.get_table_views(table)
        record_links = table_views.record_links if table_views else {}

        # Build field list including lookup fields from record links
        fields = display.get_all_available_fields(self.engine, table, record_links)

        table_title = schema.to_title_case(table)
        screen = FieldManagementScreen(table_title, fields, state.visible_fields)

        def handle_result(result):
            if result is None:
                return

            action = result.get("action")

            if action == "apply":
                # Update visible fields
                new_visible_fields = result.get("visible_fields", set())
                self.state_manager.set_visible_fields(table, new_visible_fields)
                self.update_view_select_prompt(table)
                self.load_table_display(table)

            elif action == "add_field":
                self.handle_add_field(table)

            elif action == "edit_field":
                self.handle_edit_field(table)

            elif action == "remove_field":
                self.handle_remove_field(table)

        self.push_screen(screen, handle_result)

    def handle_add_field(self, table: str):
        """
        Handle adding a new field to a table.

        Args:
            table: Table name
        """
        table_title = schema.to_title_case(table)
        screen = AddFieldScreen(table_title)

        def handle_result(result):
            if result is None:
                # User cancelled - return to field management screen
                self.handle_fields_button(table)
                return

            try:
                # Add the column to the database
                schema.add_column(
                    self.engine,
                    table,
                    result["name"],
                    result["type"],
                    result.get("default"),
                )

                # Show success notification
                self.notify(
                    f"Added field '{result['name']}' to {table_title}",
                    severity="information",
                    timeout=2,
                )

                # Return to field management screen so user can continue managing fields
                self.handle_fields_button(table)

            except Exception as e:
                # Show error notification
                self.notify(
                    f"Error adding field: {str(e)}", severity="error", timeout=5
                )
                # Return to field management screen
                self.handle_fields_button(table)

        self.push_screen(screen, handle_result)

    def handle_edit_field(self, table: str):
        """
        Handle editing (renaming) a field in a table.

        Args:
            table: Table name
        """
        columns = schema.get_columns(self.engine, table)
        # Build field list (exclude PKs)
        fields = [
            (col["name"], col["display_name"]) for col in columns if not col["pk"]
        ]

        table_title = schema.to_title_case(table)
        screen = EditFieldScreen(table_title, fields)

        def handle_result(result):
            if result is None:
                # User cancelled - return to field management screen
                self.handle_fields_button(table)
                return

            try:
                # Rename the column in the database
                schema.rename_column(
                    self.engine, table, result["old_name"], result["new_name"]
                )

                # Show success notification
                self.notify(
                    f"Renamed field '{result['old_name']}' to '{result['new_name']}' in {table_title}",
                    severity="information",
                    timeout=2,
                )

                # Return to field management screen so user can continue managing fields
                self.handle_fields_button(table)

            except Exception as e:
                # Show error notification
                self.notify(
                    f"Error renaming field: {str(e)}", severity="error", timeout=5
                )
                # Return to field management screen
                self.handle_fields_button(table)

        self.push_screen(screen, handle_result)

    def handle_remove_field(self, table: str):
        """
        Handle removing a field from a table.

        Args:
            table: Table name
        """
        columns = schema.get_columns(self.engine, table)

        # Build field list (exclude PKs since they can't be removed)
        fields = [
            (col["name"], col["display_name"]) for col in columns if not col["pk"]
        ]

        if not fields:
            self.notify("No fields available to remove", severity="warning", timeout=3)
            # Return to field management screen
            self.handle_fields_button(table)
            return

        table_title = schema.to_title_case(table)
        screen = RemoveFieldScreen(table_title, fields)

        def handle_result(result):
            if result is None:
                # User cancelled - return to field management screen
                self.handle_fields_button(table)
                return

            try:
                # Remove the column from the database
                schema.remove_column(self.engine, table, result)

                # Update state to remove from visible fields if present
                state = self.state_manager.get_state(table)
                if result in state.visible_fields:
                    state.visible_fields.remove(result)

                # Show success notification
                self.notify(
                    f"Removed field '{result}' from {table_title}",
                    severity="information",
                    timeout=2,
                )

                # Return to field management screen so user can continue managing fields
                self.handle_fields_button(table)

            except Exception as e:
                # Show error notification
                self.notify(
                    f"Error removing field: {str(e)}", severity="error", timeout=5
                )
                # Return to field management screen
                self.handle_fields_button(table)

        self.push_screen(screen, handle_result)

    def handle_add_table(self):
        """Handle adding a new table to the database."""
        screen = AddTableScreen()

        def handle_result(result):
            if result is None:
                return

            try:
                table_name = result["table_name"]
                columns = result["columns"]

                # Create the table
                schema.create_table(self.engine, table_name, columns)

                # Refresh table list
                self.tables = schema.get_tables(self.engine)

                # Create default view in config
                visible_fields = schema.get_default_visible_fields(
                    self.engine, table_name
                )
                self.config.create_default_view(table_name, list(visible_fields))

                # Initialize state (this will use the default view we just created)
                state = self.state_manager.get_state(table_name)

                # Add new tab to TabbedContent
                tabs = self.query_one(TabbedContent)
                tab_id = f"tab-{table_name}"

                # Create new tab pane and add it to TabbedContent first
                new_tab = TabPane(schema.to_title_case(table_name), id=tab_id)
                tabs.add_pane(new_tab)

                # Now mount the container structure into the tab
                tab_container = Vertical(classes="tab-container")
                new_tab.mount(tab_container)

                # Mount controls container into tab_container
                controls_container = HorizontalScroll(
                    classes="tab-controls", id=f"{table_name}-controls"
                )
                tab_container.mount(controls_container)

                # Now we can mount buttons into controls_container
                view_label = state.current_view_name + (
                    " *" if state.is_modified else ""
                )
                controls_container.mount(
                    Button(
                        f"View: {view_label}",
                        id=f"{table_name}-view-button",
                        variant="primary",
                    )
                )

                # Check if there are grouping options
                grouping_options = schema.get_grouping_options(
                    self.engine, table_name, state.filters
                )
                if grouping_options:
                    controls_container.mount(
                        Button(
                            "Group", id=f"{table_name}-group-button", variant="primary"
                        )
                    )

                # Add fields, filter, and sort buttons
                controls_container.mount(
                    Button(
                        "Fields", id=f"{table_name}-fields-button", variant="primary"
                    )
                )
                controls_container.mount(
                    Button(
                        "Filter", id=f"{table_name}-filter-button", variant="primary"
                    )
                )
                controls_container.mount(
                    Button("Sort", id=f"{table_name}-sort-button", variant="primary")
                )

                # Add data table to tab_container
                data_table = DataTable(id=f"{table_name}-table")
                tab_container.mount(data_table)

                # Switch to the new tab
                tabs.active = tab_id

                # Load the display for the new table
                self.load_table_display(table_name)

                # Show success notification
                self.notify(
                    f"Created table '{table_name}'", severity="information", timeout=2
                )

            except Exception as e:
                # Show error notification with longer timeout and log the full error
                import traceback

                error_msg = f"Error creating table: {str(e)}"
                self.log.error(error_msg)
                self.log.error(traceback.format_exc())
                self.notify(error_msg, severity="error", timeout=30)

        self.push_screen(screen, handle_result)

    def handle_remove_table(self):
        """Handle removing a table from the database."""
        # Don't allow removing the last table
        if len(self.tables) <= 1:
            self.notify(
                "Cannot remove the last table in the database",
                severity="warning",
                timeout=3,
            )
            return

        screen = RemoveTableScreen(self.tables)

        def handle_result(result):
            if result is None:
                return

            try:
                table_name = result["table_name"]

                # Remove the table from the database
                schema.drop_table(self.engine, table_name)

                # Remove state for the table from the states dict
                if table_name in self.state_manager.states:
                    del self.state_manager.states[table_name]

                # Refresh table list
                self.tables = schema.get_tables(self.engine)

                # Remove tab from TabbedContent
                tabs = self.query_one(TabbedContent)
                tab_id = f"tab-{table_name}"

                # Switch to first available tab before removing current one
                if tabs.active == tab_id:
                    # Find first tab that's not the one being removed
                    for tab in tabs.query(TabPane):
                        if tab.id and tab.id != tab_id:
                            tabs.active = tab.id
                            break

                # Find and remove the tab
                for tab in tabs.query(TabPane):
                    if tab.id == tab_id:
                        tab.remove()
                        break

                # Show success notification
                self.notify(
                    f"Removed table '{table_name}'", severity="information", timeout=2
                )

            except Exception as e:
                # Show error notification
                self.notify(
                    f"Error removing table: {str(e)}", severity="error", timeout=5
                )

        self.push_screen(screen, handle_result)

    def handle_group_button(self, table: str):
        """
        Handle grouping button press for a table.

        Args:
            table: Table name
        """
        state = self.state_manager.get_state(table)

        # Get grouping thresholds from config
        rec = self.config.settings.grouping.recommendations

        # Get record links configuration
        table_views = self.config.get_table_views(table)
        record_links = table_views.record_links if table_views else {}

        # Get available grouping columns with metadata
        grouping_options = schema.get_grouping_options_with_metadata(
            self.engine,
            table,
            state.filters,
            max_distinct=rec.max_distinct_values,
            max_ratio=rec.max_cardinality_ratio,
            min_distinct=rec.min_distinct_values,
            excluded_types=rec.excluded_types,
            record_links=record_links,
        )

        screen = GroupingScreen(grouping_options, state.grouping)

        def handle_result(result):
            if result is not None:
                self.state_manager.set_grouping(table, result)
                self.update_view_select_prompt(table)
                self.load_table_display(table)

        self.push_screen(screen, handle_result)

    def handle_filter_button(self, table: str):
        """
        Handle filter button press for a table.

        Args:
            table: Table name
        """
        state = self.state_manager.get_state(table)

        # Get record links configuration
        table_views = self.config.get_table_views(table)
        record_links = table_views.record_links if table_views else {}

        # Build field list including lookup fields from record links
        fields = display.get_all_available_fields(self.engine, table, record_links)

        table_title = schema.to_title_case(table)
        screen = RecordFilterScreen(table_title, fields, state.filters)

        def handle_result(result):
            if result is not None:
                self.state_manager.set_filters(table, result)
                self.update_view_select_prompt(table)
                self.load_table_display(table)

        self.push_screen(screen, handle_result)

    def handle_sort_button(self, table: str):
        """
        Handle sort button press for a table.

        Args:
            table: Table name
        """
        state = self.state_manager.get_state(table)

        # Get record links configuration
        table_views = self.config.get_table_views(table)
        record_links = table_views.record_links if table_views else {}

        # Build comprehensive list of available columns for sorting
        # Include all non-PK columns (not just visible ones), lookup fields, and reverse FKs
        fields = display.get_all_available_fields(self.engine, table, record_links)
        available_columns = [display_name for field_id, display_name in fields]

        screen = SortingScreen(available_columns, state.sort_config)

        def handle_result(result):
            if result is not None:
                self.state_manager.set_sort_config(table, result)
                self.update_view_select_prompt(table)
                self.load_table_display(table)

        self.push_screen(screen, handle_result)

    def handle_add_row(self, table: str):
        """
        Handle add row button press for a table.

        Args:
            table: Table name
        """
        # Get column and FK information
        columns = schema.get_columns(self.engine, table)
        foreign_keys = schema.get_all_foreign_keys(self.engine, table)

        table_title = schema.to_title_case(table)
        screen = EditRowScreen(table_title, columns, foreign_keys, existing_row=None)

        def handle_result(result):
            if result is None:
                return

            try:
                mode = result.get("mode")
                data = result.get("data", {})

                if mode == "add":
                    # Insert new row
                    new_row_id = schema.insert_row(self.engine, table, data)

                    # Reload table display
                    self.load_table_display(table)

                    # Show success notification
                    self.notify(
                        f"Added new row to {table_title} (ID: {new_row_id})",
                        severity="information",
                        timeout=2,
                    )

            except Exception as e:
                # Show error notification
                self.notify(f"Error adding row: {str(e)}", severity="error", timeout=5)

        self.push_screen(screen, handle_result)

    def handle_edit_row(self, table: str, row_data: dict):
        """
        Handle edit row action for a table.

        Args:
            table: Table name
            row_data: Existing row data as dict
        """
        # Get column and FK information
        columns = schema.get_columns(self.engine, table)
        foreign_keys = schema.get_all_foreign_keys(self.engine, table)

        table_title = schema.to_title_case(table)
        screen = EditRowScreen(
            table_title, columns, foreign_keys, existing_row=row_data
        )

        def handle_result(result):
            if result is None:
                return

            try:
                mode = result.get("mode")
                data = result.get("data", {})

                if mode == "edit":
                    # Find PK column
                    pk_col = next((c["name"] for c in columns if c["pk"]), "id")
                    pk_value = data.get(pk_col)

                    if pk_value is None:
                        raise ValueError("Primary key value not found")

                    # Update existing row
                    schema.update_row(self.engine, table, pk_col, pk_value, data)

                    # Reload table display
                    self.load_table_display(table)

                    # Show success notification
                    self.notify(
                        f"Updated row in {table_title}",
                        severity="information",
                        timeout=2,
                    )

            except Exception as e:
                # Show error notification
                self.notify(
                    f"Error updating row: {str(e)}", severity="error", timeout=5
                )

        self.push_screen(screen, handle_result)

    def handle_save_current_view(self, table: str):
        """
        Save the current view state (update existing view).

        Args:
            table: Table name
        """
        state = self.state_manager.get_state(table)

        # Save the current state to the config
        self.state_manager.save_view(table)
        self.config.save()

        # Clear the modified indicator
        self.update_view_select_prompt(table)

        # Show notification
        self.notify(
            f"Saved view '{state.current_view_name}'", severity="information", timeout=2
        )

    def handle_save_as_new_view(self, table: str):
        """
        Save current state as a new view with a custom name.

        Args:
            table: Table name
        """
        state = self.state_manager.get_state(table)

        # Show dialog to get view name
        screen = SaveViewScreen("Save As New View", default_name="")

        def handle_result(view_name):
            if view_name:
                # Check if view already exists
                existing_views = self.state_manager.get_view_names(table)
                if view_name in existing_views:
                    self.notify(
                        f"View '{view_name}' already exists",
                        severity="warning",
                        timeout=3,
                    )
                    return

                # Create new view with current state
                self.state_manager.save_view_as(table, view_name)
                self.config.save()

                # Switch to the new view
                self.state_manager.switch_view(table, view_name)
                self.update_view_select_prompt(table)

                # Show notification - now the view will appear immediately!
                self.notify(
                    f"Created new view '{view_name}'", severity="information", timeout=2
                )

        self.push_screen(screen, handle_result)

    def action_switch_tab(self, tab_id: str) -> None:
        """
        Switch to a specific tab.

        Args:
            tab_id: Tab identifier (e.g., "tab-systems")
        """
        tabbed_content = self.query_one(TabbedContent)
        tabbed_content.active = tab_id

    def action_start_search(self) -> None:
        """Start search mode - show search input."""
        search_container = self.query_one("#search-container")
        search_input = self.query_one("#search-input", Input)

        # Show search container and focus input
        search_container.display = True
        search_input.value = ""
        search_input.focus()

        # Track current table
        tabbed_content = self.query_one(TabbedContent)
        active_tab = tabbed_content.active
        if active_tab and active_tab.startswith("tab-"):
            self.current_table = active_tab[4:]  # Remove "tab-" prefix

    def action_cancel_search(self) -> None:
        """Cancel search mode - hide search input."""
        search_container = self.query_one("#search-container")
        search_container.display = False

        # Clear search state
        self.search_query = ""
        self.search_matches = []
        self.search_match_index = 0

        # Return focus to current table
        if self.current_table:
            try:
                table_widget = self.query_one(f"#{self.current_table}-table", DataTable)
                table_widget.focus()
            except:
                pass

    def action_next_match(self) -> None:
        """Navigate to next search match."""
        if not self.search_matches:
            return

        # Increment match index (wrap around)
        self.search_match_index = (self.search_match_index + 1) % len(
            self.search_matches
        )
        self._jump_to_current_match()

    def action_prev_match(self) -> None:
        """Navigate to previous search match."""
        if not self.search_matches:
            return

        # Decrement match index (wrap around)
        self.search_match_index = (self.search_match_index - 1) % len(
            self.search_matches
        )
        self._jump_to_current_match()

    def action_edit_current_row(self) -> None:
        """Edit the currently selected row."""
        # Get current table
        tabbed_content = self.query_one(TabbedContent)
        active_tab = tabbed_content.active
        if not active_tab or not active_tab.startswith("tab-"):
            return

        table_name = active_tab[4:]  # Remove "tab-" prefix

        try:
            # Get the table widget
            table_widget = self.query_one(f"#{table_name}-table", DataTable)

            # Get current cursor position
            if not hasattr(table_widget, "cursor_coordinate"):
                return

            cursor = table_widget.cursor_coordinate
            if cursor is None:
                return

            row_idx = cursor.row

            # Get row data from metadata
            if not hasattr(self, "row_metadata") or table_name not in self.row_metadata:
                return

            if row_idx >= len(self.row_metadata[table_name]):
                return

            row_data = self.row_metadata[table_name][row_idx]

            # Empty row data means it's a group header
            if not row_data:
                return

            # Open edit screen
            self.handle_edit_row(table_name, row_data)

        except Exception as e:
            # If anything fails, just silently return
            pass

    def action_add_row(self) -> None:
        """Add a new row to the current table."""
        # Get current table
        tabbed_content = self.query_one(TabbedContent)
        active_tab = tabbed_content.active
        if not active_tab or not active_tab.startswith("tab-"):
            return

        table_name = active_tab[4:]  # Remove "tab-" prefix
        self.handle_add_row(table_name)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search input submission (Enter key)."""
        if event.input.id == "search-input":
            self.search_query = event.value.lower().strip()

            if not self.search_query:
                return

            # Perform search on current table
            self._perform_search()

            # Hide search container after search
            search_container = self.query_one("#search-container")
            search_container.display = False

            # Return focus to table
            if self.current_table:
                try:
                    table_widget = self.query_one(
                        f"#{self.current_table}-table", DataTable
                    )
                    table_widget.focus()
                except:
                    pass

            # Jump to first match
            if self.search_matches:
                self.search_match_index = 0
                self._jump_to_current_match()
            else:
                # No matches found - show notification
                self.notify("No matches found", severity="warning", timeout=2)

    def _perform_search(self) -> None:
        """Search through current table data for matches."""
        if not self.current_table or not self.search_query:
            return

        self.search_matches = []

        try:
            table_widget = self.query_one(f"#{self.current_table}-table", DataTable)

            # Search through all rows
            for row_idx in range(table_widget.row_count):
                row = table_widget.get_row_at(row_idx)

                # Check if any cell contains the search query (case-insensitive)
                for cell in row:
                    cell_str = str(cell).lower()
                    if self.search_query in cell_str:
                        self.search_matches.append(row_idx)
                        break  # Found match in this row, move to next row

            # Update status
            status_label = self.query_one("#search-status", Label)
            if self.search_matches:
                status_label.update(f"1/{len(self.search_matches)}")
            else:
                status_label.update("No matches")

        except Exception:
            # Handle any errors silently
            pass

    def _jump_to_current_match(self) -> None:
        """Move cursor to current match and update status."""
        if not self.search_matches or not self.current_table:
            return

        try:
            table_widget = self.query_one(f"#{self.current_table}-table", DataTable)
            row_idx = self.search_matches[self.search_match_index]

            # Move cursor to matched row
            table_widget.move_cursor(row=row_idx)

            # Update status
            status_label = self.query_one("#search-status", Label)
            status_label.update(
                f"{self.search_match_index + 1}/{len(self.search_matches)}"
            )

        except Exception:
            # Handle any errors silently
            pass

    def _handle_reverse_fk_cell(
        self, table_name: str, row_idx: int, col_idx: int
    ) -> None:
        """
        Handle clicking/selecting a reverse FK cell - show detail modal.

        Args:
            table_name: Name of the table
            row_idx: Row index in the table
            col_idx: Column index in the table
        """
        # Don't open another modal if one is already open
        if any(isinstance(s, ReverseFKDetailScreen) for s in self.screen_stack):
            return

        # Check if we have metadata for this table
        if not hasattr(self, "row_metadata") or table_name not in self.row_metadata:
            return

        if row_idx >= len(self.row_metadata[table_name]):
            return

        # Get row data
        row_data = self.row_metadata[table_name][row_idx]
        if not row_data:  # Empty dict for group headers
            return

        # Get column metadata
        state = self.state_manager.get_state(table_name)
        table_views = self.config.get_table_views(table_name)
        record_links = (
            table_views.record_links if table_views and table_views.record_links else {}
        )
        columns = display.build_column_list(self.engine, state, record_links)

        # Get clicked column name
        if col_idx >= len(columns):
            return
        clicked_col = columns[col_idx]

        # Check if this is a reverse FK column
        reverse_fks = schema.get_reverse_foreign_keys(self.engine, table_name)
        for rfk in reverse_fks:
            rfk_col_name = schema.to_title_case(rfk["from_table"])
            if clicked_col == rfk_col_name:
                # This is a reverse FK column! Get the row's PK value
                all_columns = schema.get_columns(self.engine, table_name)
                pk_cols = [c["name"] for c in all_columns if c["pk"]]
                if not pk_cols:
                    return

                pk_col = pk_cols[0]
                pk_value = row_data.get(pk_col)
                if pk_value is None:
                    return

                # Fetch all items
                items = display.fetch_all_reverse_fk_items(self.engine, rfk, pk_value)

                # Get parent record name for title
                name_col = schema.get_name_column(self.engine, table_name)
                parent_name = str(row_data.get(name_col, "record"))

                # Build title
                from_table_title = schema.to_title_case(rfk["from_table"])
                parent_table_singular = table_name.rstrip("s")  # Simple pluralization
                title = (
                    f"{from_table_title} for {parent_table_singular} '{parent_name}'"
                )

                # Show modal
                self.push_screen(ReverseFKDetailScreen(title, items))
                break

    def on_data_table_cell_highlighted(self, event: DataTable.CellHighlighted) -> None:
        """Handle cell highlight (mouse click) - show detail modal for reverse FK cells or edit on double-click."""
        import time

        # Determine which table this is
        table_id = event.data_table.id or ""
        if not table_id.endswith("-table"):
            return

        table_name = table_id[: -len("-table")]
        row_idx = event.coordinate.row

        # Check for double-click (within 500ms on the same row)
        current_time = time.time()
        time_since_last_click = current_time - self._last_click_time
        is_double_click = (
            time_since_last_click < 0.5
            and self._last_click_row == row_idx
            and self._last_click_table == table_name
        )

        # Update click tracking
        self._last_click_time = current_time
        self._last_click_row = row_idx
        self._last_click_table = table_name

        if is_double_click:
            # Double-click detected - open edit modal
            try:
                # Get row data from metadata
                if (
                    not hasattr(self, "row_metadata")
                    or table_name not in self.row_metadata
                ):
                    return

                if row_idx >= len(self.row_metadata[table_name]):
                    return

                row_data = self.row_metadata[table_name][row_idx]

                # Empty row data means it's a group header
                if not row_data:
                    return

                # Open edit screen
                self.handle_edit_row(table_name, row_data)
                return
            except Exception:
                pass

        # Single click - handle reverse FK cell interaction
        self._handle_reverse_fk_cell(table_name, row_idx, event.coordinate.column)

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Handle cell selection (Enter key) - show detail modal for reverse FK cells."""
        # Determine which table this is
        table_id = event.data_table.id or ""
        if not table_id.endswith("-table"):
            return

        table_name = table_id[: -len("-table")]

        # Handle reverse FK cell interaction
        self._handle_reverse_fk_cell(
            table_name, event.coordinate.row, event.coordinate.column
        )
