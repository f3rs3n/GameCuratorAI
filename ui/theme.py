"""
Theme manager for the DAT Filter AI application.
"""

import logging
from typing import Dict, Any


class Theme:
    """Theme manager for the application."""
    
    def __init__(self):
        """Initialize the theme manager with default settings."""
        self.logger = logging.getLogger(__name__)
        
        # Default theme colors from requirements
        self.colors = {
            "primary": "#6200EE",       # deep purple
            "secondary": "#03DAC6",     # teal
            "background": "#FFFFFF",    # white
            "text": "#121212",          # near black
            "accent": "#BB86FC",        # light purple
            "error": "#CF6679",         # error red
            "success": "#4CAF50",       # success green
            "warning": "#FFC107",       # warning amber
            "info": "#2196F3",          # info blue
            "card": "#F5F5F5",          # light gray for cards
            "border": "#E0E0E0",        # light gray for borders
        }
        
        # Dark theme colors
        self.dark_colors = {
            "primary": "#BB86FC",       # light purple
            "secondary": "#03DAC6",     # teal
            "background": "#121212",    # dark background
            "text": "#FFFFFF",          # white text
            "accent": "#6200EE",        # deep purple
            "error": "#CF6679",         # error red
            "success": "#4CAF50",       # success green
            "warning": "#FFC107",       # warning amber
            "info": "#2196F3",          # info blue
            "card": "#1E1E1E",          # dark gray for cards
            "border": "#333333",        # dark gray for borders
        }
        
        # Font settings
        self.fonts = {
            "family": "Roboto, 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif",
            "size": {
                "small": 12,
                "normal": 14,
                "large": 16,
                "xlarge": 20,
                "title": 24,
            }
        }
        
        # Default to light theme
        self.current_theme = "light"
        self.is_dark = False
    
    def set_theme(self, theme_name: str):
        """
        Set the current theme
        
        Args:
            theme_name: The theme to use ('light' or 'dark')
        """
        if theme_name.lower() == "dark":
            self.current_theme = "dark"
            self.is_dark = True
        else:
            self.current_theme = "light"
            self.is_dark = False
        
        self.logger.info(f"Theme set to: {self.current_theme}")
    
    def get_current_colors(self) -> Dict[str, str]:
        """
        Get colors for the current theme
        
        Returns:
            Dictionary of color values
        """
        return self.dark_colors if self.is_dark else self.colors
    
    def get_color(self, color_name: str) -> str:
        """
        Get a specific color value
        
        Args:
            color_name: Name of the color to get
            
        Returns:
            Hex color value
        """
        colors = self.dark_colors if self.is_dark else self.colors
        return colors.get(color_name, self.colors.get(color_name, "#000000"))
    
    def get_font_family(self) -> str:
        """
        Get the font family for the theme
        
        Returns:
            Font family string
        """
        return self.fonts["family"]
    
    def get_font_size(self, size_name: str) -> int:
        """
        Get a specific font size
        
        Args:
            size_name: Name of the font size to get
            
        Returns:
            Font size in pixels
        """
        return self.fonts["size"].get(size_name, self.fonts["size"]["normal"])
    
    def get_stylesheet(self) -> str:
        """
        Get the QSS stylesheet for the current theme
        
        Returns:
            QSS stylesheet string
        """
        colors = self.dark_colors if self.is_dark else self.colors
        
        return f"""
        QWidget {{
            font-family: {self.fonts["family"]};
            font-size: {self.fonts["size"]["normal"]}px;
            color: {colors["text"]};
            background-color: {colors["background"]};
        }}
        
        QMainWindow, QDialog {{
            background-color: {colors["background"]};
        }}
        
        QPushButton {{
            background-color: {colors["primary"]};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        }}
        
        QPushButton:hover {{
            background-color: {self._lighten_darken(colors["primary"], 0.1)};
        }}
        
        QPushButton:pressed {{
            background-color: {self._lighten_darken(colors["primary"], -0.1)};
        }}
        
        QPushButton:disabled {{
            background-color: {colors["border"]};
            color: {self._lighten_darken(colors["text"], 0.5)};
        }}
        
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {{
            background-color: {self._lighten_darken(colors["background"], 0.05)};
            border: 1px solid {colors["border"]};
            border-radius: 4px;
            padding: 6px;
        }}
        
        QProgressBar {{
            border: 1px solid {colors["border"]};
            border-radius: 4px;
            background-color: {self._lighten_darken(colors["background"], 0.05)};
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background-color: {colors["primary"]};
        }}
        
        QTabWidget::pane {{
            border: 1px solid {colors["border"]};
            background-color: {colors["background"]};
        }}
        
        QTabBar::tab {{
            background-color: {self._lighten_darken(colors["background"], 0.05)};
            border: 1px solid {colors["border"]};
            border-bottom: none;
            padding: 8px 16px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors["background"]};
            border-bottom: 2px solid {colors["primary"]};
        }}
        
        QTabBar::tab:!selected {{
            margin-top: 2px;
        }}
        
        QTableView, QTreeView, QListView {{
            border: 1px solid {colors["border"]};
            background-color: {colors["background"]};
            alternate-background-color: {self._lighten_darken(colors["background"], 0.03)};
        }}
        
        QTableView::item, QTreeView::item, QListView::item {{
            padding: 4px;
        }}
        
        QTableView::item:selected, QTreeView::item:selected, QListView::item:selected {{
            background-color: {colors["primary"]};
            color: white;
        }}
        
        QHeaderView::section {{
            background-color: {self._lighten_darken(colors["background"], 0.05)};
            border: 1px solid {colors["border"]};
            padding: 4px;
        }}
        
        QStatusBar {{
            background-color: {self._lighten_darken(colors["background"], 0.03)};
            border-top: 1px solid {colors["border"]};
        }}
        
        QToolBar {{
            background-color: {self._lighten_darken(colors["background"], 0.05)};
            border-bottom: 1px solid {colors["border"]};
            spacing: 4px;
        }}
        
        QToolButton {{
            background-color: transparent;
            border: none;
            padding: 4px;
        }}
        
        QToolButton:hover {{
            background-color: {self._lighten_darken(colors["background"], 0.08)};
            border-radius: 4px;
        }}
        
        QGroupBox {{
            border: 1px solid {colors["border"]};
            border-radius: 4px;
            margin-top: 1em;
            padding-top: 10px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 3px;
            color: {colors["text"]};
        }}
        
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 18px;
            height: 18px;
        }}
        
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background-color: {colors["primary"]};
            border: 2px solid {colors["primary"]};
        }}
        """
    
    def _lighten_darken(self, color: str, amount: float) -> str:
        """
        Lighten or darken a color by the given amount
        
        Args:
            color: Hex color to adjust
            amount: Amount to adjust (-1.0 to 1.0, negative darkens, positive lightens)
            
        Returns:
            Adjusted hex color
        """
        if not color.startswith('#') or len(color) != 7:
            return color
        
        # Convert hex to RGB
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        
        # Adjust RGB
        if amount < 0:
            # Darken
            r = int(r * (1 + amount))
            g = int(g * (1 + amount))
            b = int(b * (1 + amount))
        else:
            # Lighten
            r = int(r + (255 - r) * amount)
            g = int(g + (255 - g) * amount)
            b = int(b + (255 - b) * amount)
        
        # Ensure values are in valid range
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
