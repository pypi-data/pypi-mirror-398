"""Table state management."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from sqlalchemy import Engine

from . import schema

if TYPE_CHECKING:
    from .config import DeflatableConfig


@dataclass
class TableState:
    """State for a single table view."""

    table_name: str
    grouping: list[str] = field(default_factory=list)  # List of column names to group by (in order)
    visible_fields: set[str] = field(default_factory=set)
    sort_config: list[tuple[str, str]] = field(default_factory=list)  # [(column, direction), ...]
    filters: list[tuple[str, str, str, str]] = field(
        default_factory=list
    )  # [(field, operator, value, boolean_op), ...]
    # boolean_op is "AND" or "OR" and represents the connector AFTER this condition (ignored for last filter)

    # View management
    current_view_name: str = "All"
    is_modified: bool = False  # True if current state differs from saved view

    def __post_init__(self):
        """Ensure visible_fields is a set."""
        if not isinstance(self.visible_fields, set):
            self.visible_fields = set(self.visible_fields)


class StateManager:
    """Manages state for all tables in the database."""

    @staticmethod
    def _normalize_filter(f: list) -> tuple[str, str, str, str]:
        """
        Convert filter from config format to state format.
        Handles backward compatibility for 3-element filters (old format).

        Args:
            f: Filter as list, either [field, op, value] or [field, op, value, bool_op]

        Returns:
            Tuple of (field, op, value, bool_op) with "AND" as default bool_op
        """
        if len(f) == 4:
            return tuple(f)
        elif len(f) == 3:
            # Old format - add "AND" as default
            return (f[0], f[1], f[2], "AND")
        else:
            raise ValueError(f"Invalid filter format: {f}")

    def __init__(self, engine: Engine, config: "DeflatableConfig"):
        """
        Initialize state manager.

        Args:
            engine: SQLAlchemy database engine
            config: Configuration with views (required)
        """
        self.engine = engine
        self.config = config
        self.states: dict[str, TableState] = {}

        # Initialize state for all tables
        self._initialize_states()

    def _initialize_states(self):
        """Initialize state for all tables with sensible defaults or from config."""
        tables = schema.get_tables(self.engine)

        for table in tables:
            # Check if we have a saved view config for this table
            table_views = self.config.get_table_views(table)
            if table_views:
                # Load from saved active view
                active_view = table_views.get_active_view()
                self.states[table] = TableState(
                    table_name=table,
                    grouping=active_view.grouping or [],
                    visible_fields=set(active_view.visible_fields),
                    sort_config=active_view.sort_config.copy(),
                    filters=[self._normalize_filter(f) for f in active_view.filters]
                    if active_view.filters
                    else [],
                    current_view_name=table_views.active_view,
                    is_modified=False,
                )
                continue

            # No views for this table - use defaults and create a default view
            visible_fields = schema.get_default_visible_fields(self.engine, table)
            self.config.create_default_view(table, list(visible_fields))

            self.states[table] = TableState(
                table_name=table,
                grouping=[],
                visible_fields=visible_fields,
                sort_config=[],
                current_view_name="All",
                is_modified=False,
            )

    def get_state(self, table: str) -> TableState:
        """
        Get state for a table.

        Args:
            table: Table name

        Returns:
            TableState object
        """
        if table not in self.states:
            # Create default state if not found
            visible_fields = schema.get_default_visible_fields(self.engine, table)
            self.states[table] = TableState(table_name=table, visible_fields=visible_fields)

        return self.states[table]

    def set_grouping(self, table: str, columns: list[str]):
        """
        Set grouping columns for a table.

        Args:
            table: Table name
            columns: List of column names to group by (in order), or empty list for no grouping
        """
        state = self.get_state(table)
        state.grouping = columns
        state.is_modified = True

    def set_visible_fields(self, table: str, fields: set[str]):
        """
        Set visible fields for a table.

        Args:
            table: Table name
            fields: Set of column names to show
        """
        state = self.get_state(table)
        state.visible_fields = fields
        state.is_modified = True

    def set_sort_config(self, table: str, sort_config: list[tuple[str, str]]):
        """
        Set sort configuration for a table.

        Args:
            table: Table name
            sort_config: List of (column, direction) tuples
        """
        state = self.get_state(table)
        state.sort_config = sort_config
        state.is_modified = True

    def set_filters(self, table: str, filters: list[tuple[str, str, str, str]]):
        """
        Set filter configuration for a table.

        Args:
            table: Table name
            filters: List of (field, operator, value, boolean_op) tuples
        """
        state = self.get_state(table)
        state.filters = filters
        state.is_modified = True

    def get_tables(self) -> list[str]:
        """Get list of all table names."""
        return list(self.states.keys())

    def get_view_names(self, table: str) -> list[str]:
        """Get list of view names for a table."""
        table_views = self.config.get_table_views(table)
        if not table_views:
            return ["All"]

        return list(table_views.views.keys())

    def switch_view(self, table: str, view_name: str):
        """
        Switch to a different view for a table.

        Args:
            table: Table name
            view_name: Name of view to switch to
        """
        table_views = self.config.get_table_views(table)
        if not table_views or view_name not in table_views.views:
            return

        view_config = table_views.views[view_name]
        state = self.get_state(table)

        # Update state from view
        state.visible_fields = set(view_config.visible_fields)
        state.grouping = view_config.grouping
        state.sort_config = view_config.sort_config.copy()
        state.filters = (
            [self._normalize_filter(f) for f in view_config.filters] if view_config.filters else []
        )
        state.current_view_name = view_name
        state.is_modified = False

        # Update active view in config
        table_views.active_view = view_name

    def save_current_view(self, table: str):
        """Save current state to the current view."""
        state = self.get_state(table)
        table_views = self.config.get_table_views(table)

        if not table_views:
            return False

        view = table_views.views.get(state.current_view_name)
        if not view:
            return False

        # Update view with current state
        view.visible_fields = list(state.visible_fields)
        view.grouping = state.grouping
        # Convert tuples to lists for YAML serialization
        view.sort_config = [[col, direction] for col, direction in state.sort_config]
        view.filters = [[field, op, value, bool_op] for field, op, value, bool_op in state.filters]

        state.is_modified = False

        # Save config to file
        self.config.save()
        return True

    def save_view(self, table: str):
        """Alias for save_current_view for consistency."""
        return self.save_current_view(table)

    def save_view_as(self, table: str, new_view_name: str):
        """
        Save current state as a new view.

        Args:
            table: Table name
            new_view_name: Name for the new view
        """
        state = self.get_state(table)

        # Get or create table views config
        table_views = self.config.get_table_views(table)
        if not table_views:
            # Create table views if it doesn't exist
            from .config import TableViews, ViewConfig

            table_views = TableViews(table_name=table, active_view="All", views={})
            self.config.table_views[table] = table_views

        # Create new view from current state
        from .config import ViewConfig

        new_view = ViewConfig(
            name=new_view_name,
            visible_fields=list(state.visible_fields),
            grouping=state.grouping,
            # Convert tuples to lists for YAML serialization
            sort_config=[[col, direction] for col, direction in state.sort_config],
            filters=[[field, op, value, bool_op] for field, op, value, bool_op in state.filters],
        )

        # Add to table views
        table_views.views[new_view_name] = new_view

        # Don't automatically switch to it or mark as unmodified
        # The caller will handle that

        return True
