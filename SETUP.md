# Advanced Web Browser

A modern web browser with tabs, bookmarks, history, and embedded web view support.

## Features

- Tabbed browsing
- Navigation controls (Back, Forward, Refresh, Home)
- Address bar with URL auto-completion
- Bookmark system with folders, search, and import/export
- History management
- Smart page rendering (embedded view for simple sites, text mode for JavaScript-heavy sites)
- Download tracking

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the browser:
   ```bash
   python3 main.py
   ```

## Usage

- Enter URLs or search terms in the address bar
- Use navigation buttons to browse
- Add bookmarks with the "Add Bookmark" button
- Manage bookmarks with the "Bookmarks" button
- View browsing history with the "History" button

## Data Files

- Bookmarks: `~/.browser_bookmarks.json`
- History: `~/.browser_history.json`