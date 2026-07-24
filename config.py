"""
Configuration constants for the NHCE Marketplace app.

The xAI (Grok) API key is read from the XAI_API_KEY environment variable.
Set it in your shell before running, e.g.:
    export XAI_API_KEY="your-key-here"   (Mac/Linux)
    set XAI_API_KEY=your-key-here        (Windows cmd)
"""
import os

XAI_API_KEY = os.getenv("XAI_API_KEY", "")
XAI_MODEL = "grok-4o"

# API base
XAI_API_BASE = "https://api.x.ai"

DB_PATH = "data/marketplace.db"
IMAGE_FOLDER = "data/images"
