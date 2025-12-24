---
title: Getting Started
description: Install Deflatable and explore your first database
---

# Getting Started

This tutorial will walk you through installing Deflatable and using it to browse a sample database. By the end, you'll understand the basic interface and core concepts.

## What You'll Learn

- How to install Deflatable
- How to create a configuration file
- How to navigate the interface
- How to browse table data
- How to use basic keyboard shortcuts

## Prerequisites

- Python 3.8 or later
- A terminal emulator
- (Optional) A database to explore, or use our sample database

## Installation

Install Deflatable from source:

```bash
git clone https://github.com/ryanlovett/deflatable.git
cd deflatable
pip install -e .
```

Verify the installation:

```bash
deflatable --help
```

You should see the help output with available commands.

## Create Sample Database

For this tutorial, we'll create a sample grocery store database.

If you cloned the Deflatable repository, you can use the complete test database:

```bash
# From the deflatable repository directory
sqlite3 grocery.db < tests/grocery.sql
```

This creates a database with three tables and sample data:
- **aisle**: Store aisles with properties like length, refrigeration status, and endcaps (8 aisles)
- **product**: Products with names, brands, sizes, and aisle assignments (44 products)
- **cost**: Historical pricing data linked to products (27 price records)

## Create Configuration File

Initialize a Deflatable config for your database:

```bash
deflatable init grocery.yaml sqlite:///grocery.db
```

You should see output like:

```
✓ Created config file: grocery.yaml
  Database: sqlite:///grocery.db
  Tables: aisle, cost, product

Run: deflatable grocery.yaml
```

Let's look at the generated config:

```bash
cat grocery.yaml
```

You'll see a basic YAML structure with your database URL and space for custom views.

## Launch Deflatable

Start the TUI:

```bash
deflatable grocery.yaml
```

## Navigate the Interface

You should see the Deflatable interface with:

- **Header bar** at the top showing the app name and database menu
- **Tab bar** with your tables (Aisle, Cost, Product)
- **Control buttons** for View, Group, Fields, Filter, Sort
- **Data table** showing rows from the first table
- **Footer** showing available keyboard shortcuts

### Basic Navigation

Try these keyboard commands:

- **Arrow keys**: Move between rows
- **Tab**: Switch between tables
- **q**: Quit the application
- **/**: Search within the current table
- **e**: Edit the currently selected row
- **+**: Add a new row

### Explore Tables

1. **Switch to the Product table**: Press `Tab` or click on "Product" in the tab bar
2. **Navigate rows**: Use arrow keys to move up and down through the 44 products
3. **Notice the foreign key**: The "Aisle Id" column shows which aisle each product is in
4. **Check the Cost table**: Press `Tab` again to see historical pricing data

## View Data

The data table shows all columns by default. Notice:

- The 🔑 icon marks primary key columns
- Foreign key columns display the related record's name when available
- Long text is automatically truncated with "..."

## Search for Data

Let's search for a specific product:

1. Press `/` to open the search bar
2. Type "milk" and press Enter
3. The table will highlight rows matching your search
4. Press `n` to jump to the next match
5. Press `Esc` to close search

## What You've Learned

- How to install Deflatable
- How to create a config file from a database
- How to launch the TUI
- How to navigate tables and rows
- How to search within tables

## Next Steps

Now that you understand the basics, try:

- **[Create your first database](first-database.md)**: Learn to add and edit data
- **[Filter and sort data](../how-to/filter-sort.md)**: Narrow down what you see
- **[Use record links](../how-to/record-links.md)**: Display related table data inline

## Troubleshooting

**Problem**: "Error: Cannot connect to database"

Solution: Verify your database URL is correct. For SQLite, ensure the path is absolute or relative to your config file.

**Problem**: "File must be a YAML config file"

Solution: Make sure you're passing the `.yaml` config file, not the `.db` database file directly.

**Problem**: Terminal looks garbled or broken

Solution: Try a different terminal emulator. Deflatable works best with modern terminals that support ANSI escape codes.
