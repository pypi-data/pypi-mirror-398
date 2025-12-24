---
title: Keybindings
description: Complete reference for keyboard shortcuts
---

# Keybindings

Deflatable is designed to be keyboard-driven. This page lists all available keyboard shortcuts.

## Global Shortcuts

These shortcuts work anywhere in the application:

| Key | Action | Description |
|-----|--------|-------------|
| `q` | Quit | Exit Deflatable |
| `Ctrl+p` | Command palette | Open the command palette |
| `Esc` | Cancel | Close modal or cancel current action |

## Navigation

| Key | Action | Description |
|-----|--------|-------------|
| `↑` / `↓` | Move cursor | Navigate up/down in the table |
| `←` / `→` | Scroll | Scroll table horizontally |
| `Tab` | Next table | Switch to the next table tab |
| `Shift+Tab` | Previous table | Switch to the previous table tab |
| `Home` | First row | Jump to the first row |
| `End` | Last row | Jump to the last row |
| `Page Up` / `Page Down` | Scroll page | Move one page up/down |

## Data Operations

| Key | Action | Description |
|-----|--------|-------------|
| `+` | Add row | Open modal to add a new row |
| `e` | Edit row | Edit the currently selected row |
| **Double-click** | Edit row | Alternative way to edit a row |
| `Enter` | Select cell | Activate special cells (reverse FK) |

## Search

| Key | Action | Description |
|-----|--------|-------------|
| `/` | Start search | Open search bar |
| `n` | Next match | Jump to next search result |
| `N` / `Shift+n` | Previous match | Jump to previous search result |
| `Esc` | Close search | Exit search mode |

## View Controls

These operations use button clicks in the control bar:

| Button | Description |
|--------|-------------|
| **View** | Switch between saved views or create new ones |
| **Group** | Group table rows by a column |
| **Fields** | Show/hide columns, reorder fields |
| **Filter** | Add filters to narrow down data |
| **Sort** | Sort by one or more columns |

## Modal Windows

When a modal is open (e.g., Edit Row, Filters, etc.):

| Key | Action | Description |
|-----|--------|-------------|
| `Esc` | Cancel | Close the modal without saving |
| `Enter` | Submit | Save changes (when focused on button) |
| `Tab` | Next field | Move to the next input field |
| `Shift+Tab` | Previous field | Move to the previous input field |

## Form Navigation

In edit/add row forms:

| Key | Action | Description |
|-----|--------|-------------|
| `Tab` | Next field | Move to next input |
| `Shift+Tab` | Previous field | Move to previous input |
| `Enter` | Next/Submit | Move to next field or submit if on button |
| `Space` | Toggle/Open | Activate checkboxes or open dropdowns |

## Tips

**Keyboard-first**: While mouse clicking is supported, keyboard navigation is generally faster.

**Context-sensitive**: Some keys have different meanings depending on where you are in the interface.

**Discoverable**: The footer bar always shows the most relevant shortcuts for your current context.

**Command palette**: Press `Ctrl+p` to see all available actions in context.

## Customization

Currently, keybindings are not customizable. If you need different bindings, please open an issue on GitHub to discuss your use case.
