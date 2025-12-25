#!/usr/bin/env python3
"""
Entry point for PyInstaller binary builds.
This wrapper uses absolute imports to avoid relative import issues.
"""

from app.__main__ import app

if __name__ == "__main__":
    app()
