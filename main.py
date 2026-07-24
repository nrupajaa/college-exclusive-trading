"""
Entry point for the NHCE Marketplace app.

Run with:
    python main.py
"""
from database import init_db
from ui import MarketplaceApp


def main():
    # Make sure the DB/tables and image folder exist before the UI starts
    init_db()

    app = MarketplaceApp()
    app.mainloop()


if __name__ == "__main__":
    main()
