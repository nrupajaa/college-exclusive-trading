"""
Theme & styling for the NHCE Marketplace app.
"""
from tkinter import ttk


def apply_theme(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    BG = "#7C9BA3"
    PANEL = "#EDEDED"
    ENTRY_BG = "#F7F7F7"
    BUTTON = "#DADADA"
    BUTTON_HOVER = "#EDEDED"
    TEXT = "#FFFFFF"

    root.configure(bg=BG)
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=PANEL, relief="flat")
    style.configure("TLabel", background=BG, foreground=TEXT, font=("Julius Sans One", 11))
    style.configure("Heading.TLabel", background=BG, foreground=TEXT, font=("Julius Sans One", 22, "bold"))
    style.configure("Small.TLabel", background=BG, foreground=TEXT, font=("Julius Sans One", 10))
    style.configure("TEntry", fieldbackground=ENTRY_BG, background=ENTRY_BG, relief="flat", padding=6)
    style.configure("TCombobox", fieldbackground=ENTRY_BG, background=ENTRY_BG)
    style.configure("TButton",
                    background=BUTTON,
                    foreground="black",
                    font=("Segoe UI", 10, "bold"),
                    padding=6,
                    borderwidth=0)
    style.map("TButton",
              background=[("active", BUTTON_HOVER), ("!disabled", BUTTON)],
              relief=[("pressed", "groove"), ("!pressed", "flat")])
