#!/usr/bin/env python3
"""
DAT Filter AI - A desktop application for filtering and curating video game collections
from XML-formatted .dat files using AI assistance.
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ui.main_window import MainWindow
from utils.logging_config import setup_logging
from utils.config import load_config

def main():
    """Main entry point of the application."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting DAT Filter AI application")

    # Load configuration
    config = load_config()
    logger.debug("Configuration loaded")

    # Check for OpenAI API key
    if not os.environ.get("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY environment variable not found.")
        # We'll continue and let the application handle this in the UI

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("DAT Filter AI")
    app.setApplicationDisplayName("DAT Filter AI")
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets/app_icon.svg")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Load stylesheet
    style_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets/style.qss")
    if os.path.exists(style_path):
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())
    
    # Create main window
    main_window = MainWindow(config)
    main_window.show()
    
    # Run application
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
