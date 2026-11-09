"""
ThesisFlow Configuration Module
Centralized settings for database, paths, models, and UI constants.
"""

from pathlib import Path
import os
import sys

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
DEMO_DIR = DATA_DIR / "demo_papers"
ASSETS_DIR = BASE_DIR / "assets"
DB_PATH = DATA_DIR / "thesisflow.db"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
DEMO_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# App branding
APP_NAME = "ThesisFlow"
APP_SUBTITLE = "The Interactive Math & Physics Research Paper Deconstructer"
APP_VERSION = "1.0.0"

# Application constraints
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "35"))
MAX_PAGES_TO_PROCESS = int(os.getenv("MAX_PAGES_TO_PROCESS", "100"))
ALLOWED_EXTENSIONS = [".pdf"]

# AI Model Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
DEFAULT_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

# UI Palette Presets
THEME_CONFIG = {
    "dark": {
        "bg_primary": "#0A0E1A",
        "bg_secondary": "#111827",
        "bg_card": "#182234",
        "bg_hover": "#1E293B",
        "text_primary": "#F8FAFC",
        "text_secondary": "#94A3B8",
        "text_muted": "#64748B",
        "border": "#243248",
        "accent_cyan": "#00E5FF",
        "accent_blue": "#3B82F6",
        "accent_violet": "#8B5CF6",
        "accent_emerald": "#10B981",
        "accent_amber": "#F59E0B",
        "accent_rose": "#F43F5E",
    },
    "light": {
        "bg_primary": "#F8FAFC",
        "bg_secondary": "#FFFFFF",
        "bg_card": "#F1F5F9",
        "bg_hover": "#E2E8F0",
        "text_primary": "#0F172A",
        "text_secondary": "#475569",
        "text_muted": "#94A3B8",
        "border": "#CBD5E1",
        "accent_cyan": "#0891B2",
        "accent_blue": "#2563EB",
        "accent_violet": "#7C3AED",
        "accent_emerald": "#059669",
        "accent_amber": "#D97706",
        "accent_rose": "#E11D48",
    }
}
