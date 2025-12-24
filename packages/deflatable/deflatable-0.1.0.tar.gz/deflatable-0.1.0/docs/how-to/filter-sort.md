---
title: Filter and Sort Data
description: How to find and organize specific records
---

# Filter and Sort Data

This guide shows you how to filter tables to show only specific records and sort data in custom orders.

## Quick Search

The fastest way to find data:

1. Press `/` to open search
2. Type your search term
3. Press `Enter`

Matching rows are highlighted. Press `n` for next match, `N` for previous.

Press `Esc` to close search.

## Add Filters

To show only rows matching specific criteria:

1. Click the **Filter** button
2. Click "Add Filter"
3. Configure your filter:
   - **Column**: Which field to filter on
   - **Operator**: How to compare (equals, contains, greater than, etc.)
   - **Value**: What to compare against
4. Click "Apply"

### Filter Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equals exactly | `price = 2.99` |
| `!=` | Not equal to | `aisle_id != 1` |
| `>` | Greater than | `price > 3.00` |
| `>=` | Greater than or equal | `length_feet >= 50` |
| `<` | Less than | `price < 5.00` |
| `<=` | Less than or equal | `length_feet <= 45` |
| `contains` | Text contains substring | `name contains milk` |
| `starts with` | Text starts with | `name starts with A` |
| `ends with` | Text ends with | `name ends with s` |

### Multiple Filters

You can add multiple filters:

1. Click "Add Filter" again
2. Choose the logic connector:
   - **AND**: Row must match all filters
   - **OR**: Row must match any filter
3. Configure and apply

Example: Show products where `price > 3.00 AND aisle_id = 2`

## Remove Filters

To remove a specific filter:

1. Open the Filter modal
2. Click the × next to the filter
3. Click "Apply"

To remove all filters:

1. Click "Filter"
2. Click "Clear All"

## Sort Data

To sort by a column:

1. Click the **Sort** button
2. Click "Add Sort"
3. Select:
   - **Column**: Field to sort by
   - **Direction**: Ascending (A-Z, 0-9) or Descending (Z-A, 9-0)
4. Click "Apply"

### Multi-Column Sorting

You can sort by multiple columns:

1. Add a second sort
2. The first sort is primary, second is used for ties

Example:
1. Sort by `aisle_id` ascending
2. Then by `name` ascending

This groups products by aisle, with names alphabetically within each aisle.

## Save Your Configuration

After setting up filters and sorts:

1. Click **View**
2. Click "Save As"
3. Enter a name like "Expensive Products"
4. Click "Save"

Now you can switch back to this configuration anytime!

## Combine Filters, Sorts, and Grouping

You can use all three together:

1. **Filter** to narrow down rows
2. **Sort** to order them
3. **Group** to organize by categories

Example workflow:
1. Filter: `price > 3.00`
2. Sort: `price` descending
3. Group: `aisle_id`

Result: Expensive products organized by aisle, most expensive first within each aisle.

## Clear All Configuration

To reset to default view:

1. Click **View**
2. Select "All" (the default view)

This removes all filters, sorts, and grouping.

## Tips

**Use Comparison Filters for Numbers**: Greater than/less than work well for prices, dates, quantities.

**Use Text Filters for Names**: `contains`, `starts with`, and `ends with` are useful for finding text.

**Save Complex Views**: If you use the same filters repeatedly, save them as a view.

**Combine AND/OR**: Complex logic is possible - e.g., `(price < 2.00 OR price > 10.00) AND refrigerated = 1`

**Sort Determines Display Order**: Even within groups, sort order matters.
