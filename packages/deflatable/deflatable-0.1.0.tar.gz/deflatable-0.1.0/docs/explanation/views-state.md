---
title: Views and State Management
description: Understanding how Deflatable manages table configurations
---

# Views and State Management

This document explains how Deflatable manages table configurations through views and state, and why this design makes working with databases easier.

## The Problem: Database Interfaces Are Stateless

Traditional database tools show you everything, every time:
- All columns, even ones you don't care about
- No saved filters or sorts
- You rebuild the same queries repeatedly

This works for ad-hoc queries but becomes tedious for regular tasks.

## The Solution: Views as Saved Configurations

Deflatable uses **views** - named configurations that remember how you want to see a table.

A view saves:
- Which columns to display
- How to sort the data
- What filters to apply
- How to group rows

Think of views like browser bookmarks, but for database table configurations.

## How Views Work

### The Default "All" View

Every table starts with a default view named "All":
- Shows all columns
- No filters
- No sorting
- No grouping

This is your baseline view.

### Creating Custom Views

When you modify the table display:

1. Add a filter, sort, or change visible fields
2. The view is marked as "modified" (shown with an asterisk)
3. You can:
   - **Save**: Overwrite the current view
   - **Save As**: Create a new view with a different name
   - **Discard**: Switch views without saving

### Switching Between Views

Click the **View** button to see all saved views for the current table. Click any view name to switch to it instantly.

Each table has its own independent views.

## State Management

Deflatable tracks two types of state:

### 1. Persistent State (Config File)

Saved in your YAML config file:
- Database connection
- All saved views
- Which view is active per table

This persists between sessions.

### 2. Runtime State (In-Memory)

Exists only while Deflatable is running:
- Current cursor position
- Search results
- Temporary modifications before saving

This is lost when you quit.

## The Modified Flag

When you make changes to a view, Deflatable marks it as "modified":

- The view button shows: `"View Name *"`
- The asterisk indicates unsaved changes
- You can save, save-as, or discard

### Why This Matters

The modified flag helps you avoid:
- Accidentally losing configuration changes
- Confusion about whether changes were saved
- Overwriting views you didn't mean to change

## State Synchronization

### From Config to Display

When you launch Deflatable:

1. Config file is read
2. Active view for each table is loaded
3. Table displays with that view's configuration

### From Display to Config

When you save a view:

1. Current state (filters, sorts, etc.) is captured
2. Written to the config file
3. Modified flag is cleared

The config file is the source of truth.

## View Independence

Each table's views are completely independent:

```yaml
views:
  product:
    active_view: "Expensive"
    views:
      All: {...}
      Expensive: {...}

  aisle:
    active_view: "All"
    views:
      All: {...}
```

Changing a view on the "product" table doesn't affect the "aisle" table.

## Why This Design?

### Repeatability

Once you save a view, you can return to that exact configuration anytime. No need to rebuild filters or remember sort orders.

### Sharing

Config files can be shared with teammates. Everyone sees the same views and can collaborate on database exploration.

### Context Switching

Different tasks need different views:
- Debugging: All columns, no filters
- Data entry: Only editable fields, grouped by category
- Analysis: Specific columns, complex filters

Switch between contexts instantly.

### Version Control

Config files are plain YAML - you can commit them to git:
- Track when views change
- Review what filters were added
- Revert to previous configurations

## Common Patterns

### The "All" Baseline

Keep the default "All" view unchanged. Create new views for specific tasks. This gives you a reset button.

### Task-Based Views

Create views for specific workflows:
- "Data Entry": Minimal columns, sorted for insertion
- "Review": All columns, sorted chronologically
- "Analysis": Filtered subset, grouped by category

### Temporary Explorations

Make changes without saving to explore data temporarily. Switch back to a saved view to discard changes.

## State Lifecycle Example

Here's a complete flow:

1. **Launch**: Load "Expensive Products" view from config
2. **Modify**: Add a filter `aisle_id = 2`
3. **Mark**: View now shows "Expensive Products *"
4. **Decide**:
   - **Save**: Update "Expensive Products" with the new filter
   - **Save As**: Create "Expensive Dairy" as a new view
   - **Discard**: Switch to "All" view, losing the filter

The choice is yours.

## Technical Details

### State Storage Location

- **Config file**: Views, filters, sorts, grouping
- **Database**: Actual table data (Deflatable never modifies this)
- **Memory**: Current UI state, cursor position, search

### View Activation

When you switch views, Deflatable:

1. Clears current filters/sorts
2. Applies the new view's configuration
3. Re-queries the database
4. Updates the display
5. Marks the new view as active in config

### Save Operations

**Save** overwrites:
```yaml
views:
  product:
    views:
      "Expensive Products":  # ← This gets updated
        filters: [[price, >, 5.00]]
```

**Save As** creates:
```yaml
views:
  product:
    views:
      "Expensive Products":
        filters: [[price, >, 3.00]]
      "Very Expensive":  # ← New view added
        filters: [[price, >, 5.00]]
```

## Best Practices

**Name Views Descriptively**: "High Value Orders" beats "View 1"

**Don't Over-save**: Not every temporary filter needs to be a view

**Use the "All" View for Exploration**: Keep it clean as your starting point

**Save Before Sharing**: Ensure your useful views are in the config file

**Review Periodically**: Delete obsolete views to keep configs manageable

## Conclusion

Views and state management in Deflatable provide:
- Repeatable workflows
- Shareable configurations
- Version-controlled database exploration
- No-code interface with power-user features

Understanding how state flows between the config file, memory, and database helps you work more effectively.
