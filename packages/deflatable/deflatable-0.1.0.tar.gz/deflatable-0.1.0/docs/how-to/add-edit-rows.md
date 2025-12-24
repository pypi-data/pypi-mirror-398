---
title: Add and Edit Rows
description: How to add new records and edit existing data
---

# Add and Edit Rows

This guide shows you how to add new records and edit existing data in your database tables.

## Add a New Row

To add a new row to the current table:

1. Press `+` (plus key)
2. Fill in the form fields
3. Click "Add Row" or press Enter

### Required vs Optional Fields

- **Required fields**: Must have a value (cannot be empty)
- **Optional fields**: Show "(optional)" placeholder text

If you try to submit without filling required fields, you'll get an error message.

### Primary Key Fields

When adding rows, primary key field behavior depends on the database:
- **Auto-increment fields** (like SQLite's INTEGER PRIMARY KEY): Show "(auto)" and are automatically generated
- **Manually-set primary keys** (UUIDs, composite keys, etc.): Must be provided by you

When editing rows, primary key fields are displayed but not editable. This prevents accidental changes that could break foreign key relationships.

## Edit an Existing Row

To edit a row:

**Method 1: Keyboard**
1. Navigate to the row using arrow keys
2. Press `e`

**Method 2: Mouse**
1. Double-click on the row

### Edit Form Behavior

- Primary key field is displayed but read-only
- All other fields are pre-filled with current values
- Button says "Save Changes"

Make your changes and click "Save Changes" or press Enter.

## Working with Foreign Keys

When a field references another table (foreign key), you'll see a dropdown instead of a text field.

### Foreign Key Dropdowns

The dropdown shows:
- `(none)` - for NULL/no relationship
- List of records from the related table

Example: If a table has a foreign key to a "categories" table, the dropdown might show:
- `(none)`
- `Category A`
- `Category B`
- etc.

The dropdown displays human-readable names, not just IDs.

### Setting a Foreign Key to NULL

To remove a relationship, select `(none)` from the dropdown.

## Cancel Changes

To close the form without saving:

- Press `Esc`
- Click "Cancel" button

No changes will be made to the database.

## Keyboard Navigation in Forms

| Key | Action |
|-----|--------|
| `Tab` | Move to next field |
| `Shift+Tab` | Move to previous field |
| `Enter` | Submit form (when on button) |
| `Space` | Open dropdown / toggle checkbox |
| `Esc` | Cancel and close form |

## Common Issues

### "Missing required field" Error

**Problem**: You tried to submit without filling a required field.

**Solution**: Fill in all fields that don't show "(optional)".

### "Invalid value" Error

**Problem**: You entered the wrong data type (e.g., text in a number field).

**Solution**: Check the field type and enter appropriate data:
- Numbers: Just digits and optionally a decimal point
- Text: Any characters
- Integers: Whole numbers only

### Foreign Key Dropdown is Empty

**Problem**: The dropdown only shows "(none)" with no other options.

**Solution**: The related table is empty. Add records to that table first.

### Can't Edit Primary Key

**Problem**: The ID field is grayed out when editing.

**Explanation**: Deflatable prevents editing primary keys to avoid breaking foreign key relationships. If you need to change a primary key, delete the row and create a new one.

## Tips

**Use Tab for Navigation**: Press Tab to move between fields quickly instead of clicking.

**Foreign Keys Save Time**: Let Deflatable handle foreign keys instead of remembering IDs manually.

**Double-click to Edit**: Faster than navigating and pressing `e`.

**Check Before Submitting**: Review your changes before clicking "Add Row" or "Save Changes".
