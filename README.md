# College Marketplace

A desktop marketplace exclusively for students to buy and sell items with each other. Built with Python and Tkinter, backed by a local SQLite database, with an optional AI chat assistant (powered by xAI's Grok API) that can answer natural-language questions about the product catalog.

## Features

- Student login/registration (USN + DOB based)
- Buyer view: browse, search, and filter products by category
- Seller view: list new products (with images), manage/mark items as sold
- Wishlist: save products for later
- Smart Chat: ask questions like "which product is cheapest?" or "which category is trending?" and get answers generated from live database queries

## Project Structure

```
├── main.py             # App entry point
├── ui.py                # Tkinter UI (all pages/frames)
├── database.py           # SQLite setup and CRUD helpers
├── chat_assistant.py     # Grok API integration + SQL safety checks
├── theme.py               # UI styling
├── config.py               # App constants and API key loading
├── requirements.txt
└── data/                    # Auto-created: SQLite DB + uploaded images (ignored by git)
```

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/<your-username>/<repo-name>.git
   cd <repo-name>
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   On Linux, you may also need Tkinter itself:
   ```bash
   sudo apt install python3-tk
   ```

3. **(Optional) Set your xAI API key** — only needed for the Smart Chat feature:
   ```bash
   export XAI_API_KEY="your-key-here"      # Mac/Linux
   set XAI_API_KEY=your-key-here           # Windows cmd
   ```
   The app runs fine without this; the chat assistant just won't be able to reach Grok.

4. **Run the app**
   ```bash
   python main.py
   ```

## Notes

- The database (`data/marketplace.db`) and any uploaded product images are created automatically on first run and are not tracked in git.
- `is_safe_select` in `chat_assistant.py` is a heuristic allowlist filter for AI-generated SQL — a reasonable safeguard for this project, but not a substitute for parameterized queries in a production system.

## Tech Stack

- Python 3 / Tkinter
- SQLite
- Pillow (image handling)
- xAI Grok API (optional AI assistant)
