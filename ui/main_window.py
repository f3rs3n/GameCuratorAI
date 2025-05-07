"""
Main window implementation for the DAT Filter AI application.
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QProgressBar, QMessageBox,
    QSplitter, QTabWidget, QStatusBar, QAction, QMenu,
    QToolBar, QFileDialog, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QSize, QSettings, QUrl
from PyQt5.QtGui import QIcon, QDesktopServices

from ui.theme import Theme
from ui.file_selector import FileSelector
from ui.filter_panel import FilterPanel
from ui.results_view import ResultsView

from core.dat_parser import DatParser
from core.filter_engine import FilterEngine
from core.rule_engine import RuleEngine
from core.export import ExportManager

from ai_providers import get_provider

class MainWindow(QMainWindow):
    """Main window for the DAT Filter AI application."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the main window
        
        Args:
            config: Application configuration
        """
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # Initialize core components
        self.dat_parser = DatParser()
        
        # Initialize AI provider based on config
        provider_name = config.get('ai_provider', 'openai')
        try:
            self.ai_provider = get_provider(provider_name)
            self.ai_provider.initialize()
        except Exception as e:
            self.logger.error(f"Failed to initialize AI provider: {e}")
            self.ai_provider = None
        
        self.filter_engine = FilterEngine(self.ai_provider)
        self.rule_engine = RuleEngine()
        self.export_manager = ExportManager()
        
        # Application state
        self.current_dat_file = None
        self.parsed_data = None
        self.filtered_games = []
        self.evaluations = []
        self.special_cases = {}
        
        # Setup UI
        self.setWindowTitle("DAT Filter AI")
        self.setMinimumSize(1024, 768)
        
        # Create theme
        self.theme = Theme()
        
        self._create_menus()
        self._create_toolbar()
        self._create_status_bar()
        self._create_central_widget()
        
        # Load window state from settings
        self._load_settings()
        
        # Check API key on startup
        if not self.ai_provider or not self.ai_provider.is_available():
            self._show_api_key_warning()
    
    def closeEvent(self, event):
        """
        Handle window close event to save settings
        
        Args:
            event: Close event
        """
        self._save_settings()
        event.accept()
    
    def _load_settings(self):
        """Load application settings"""
        settings = QSettings("DAT Filter AI", "DAT Filter AI")
        
        # Window geometry
        if settings.contains("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        else:
            # Default position and size
            self.resize(1200, 800)
        
        # Window state
        if settings.contains("windowState"):
            self.restoreState(settings.value("windowState"))
        
        # Recent files
        recent_files = settings.value("recentFiles", [])
        if recent_files:
            self.file_selector.set_recent_files(recent_files)
    
    def _save_settings(self):
        """Save application settings"""
        settings = QSettings("DAT Filter AI", "DAT Filter AI")
        
        # Window geometry
        settings.setValue("geometry", self.saveGeometry())
        
        # Window state
        settings.setValue("windowState", self.saveState())
        
        # Recent files
        settings.setValue("recentFiles", self.file_selector.get_recent_files())
    
    def _create_menus(self):
        """Create application menus"""
        # File Menu
        file_menu = self.menuBar().addMenu("&File")
        
        open_action = QAction("&Open DAT File...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_dat_file)
        file_menu.addAction(open_action)
        
        export_menu = QMenu("&Export", self)
        
        export_dat_action = QAction("Export Filtered &DAT...", self)
        export_dat_action.triggered.connect(self._export_filtered_dat)
        export_menu.addAction(export_dat_action)
        
        export_report_action = QAction("Export &JSON Report...", self)
        export_report_action.triggered.connect(self._export_json_report)
        export_menu.addAction(export_report_action)
        
        export_summary_action = QAction("Export &Text Summary...", self)
        export_summary_action.triggered.connect(self._export_text_summary)
        export_menu.addAction(export_summary_action)
        
        file_menu.addMenu(export_menu)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings Menu
        settings_menu = self.menuBar().addMenu("&Settings")
        
        api_key_action = QAction("Configure &API Key...", self)
        api_key_action.triggered.connect(self._configure_api_key)
        settings_menu.addAction(api_key_action)
        
        settings_menu.addSeparator()
        
        theme_menu = QMenu("&Theme", self)
        
        light_theme_action = QAction("&Light", self)
        light_theme_action.setCheckable(True)
        light_theme_action.setChecked(self.theme.current_theme == "light")
        light_theme_action.triggered.connect(lambda: self._change_theme("light"))
        theme_menu.addAction(light_theme_action)
        
        dark_theme_action = QAction("&Dark", self)
        dark_theme_action.setCheckable(True)
        dark_theme_action.setChecked(self.theme.current_theme == "dark")
        dark_theme_action.triggered.connect(lambda: self._change_theme("dark"))
        theme_menu.addAction(dark_theme_action)
        
        settings_menu.addMenu(theme_menu)
        
        # Help Menu
        help_menu = self.menuBar().addMenu("&Help")
        
        about_action = QAction("&About DAT Filter AI", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)
        
        help_menu.addSeparator()
        
        docs_action = QAction("&Documentation", self)
        docs_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/datfilterai/documentation")))
        help_menu.addAction(docs_action)
    
    def _create_toolbar(self):
        """Create application toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Open DAT file button
        open_action = QAction(QIcon.fromTheme("document-open"), "Open DAT File", self)
        open_action.triggered.connect(self._open_dat_file)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        # Filter button
        filter_action = QAction(QIcon.fromTheme("view-filter"), "Apply Filters", self)
        filter_action.triggered.connect(self._apply_filters)
        toolbar.addAction(filter_action)
        
        # Export button
        export_action = QAction(QIcon.fromTheme("document-save-as"), "Export Filtered DAT", self)
        export_action.triggered.connect(self._export_filtered_dat)
        toolbar.addAction(export_action)
        
        toolbar.addSeparator()
        
        # Settings button
        settings_action = QAction(QIcon.fromTheme("preferences-system"), "Settings", self)
        settings_action.triggered.connect(self._show_settings)
        toolbar.addAction(settings_action)
    
    def _create_status_bar(self):
        """Create application status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Provider status label
        self.provider_status = QLabel("AI Provider: Not connected")
        self.status_bar.addPermanentWidget(self.provider_status)
        
        # Update provider status
        self._update_provider_status()
    
    def _update_provider_status(self):
        """Update the AI provider status display"""
        if self.ai_provider and self.ai_provider.is_available():
            provider_name = self.ai_provider.get_provider_name()
            self.provider_status.setText(f"AI Provider: {provider_name} (Connected)")
            self.provider_status.setStyleSheet("color: green;")
        else:
            self.provider_status.setText("AI Provider: Not connected")
            self.provider_status.setStyleSheet("color: red;")
    
    def _create_central_widget(self):
        """Create and set the central widget"""
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create top section with file selector
        self.file_selector = FileSelector()
        self.file_selector.file_selected.connect(self._load_dat_file)
        main_layout.addWidget(self.file_selector)
        
        # Create splitter for filter panel and results
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Filter Panel
        self.filter_panel = FilterPanel(self.config, self.filter_engine)
        self.filter_panel.filter_requested.connect(self._apply_filters)
        splitter.addWidget(self.filter_panel)
        
        # Right side - Results View
        self.results_view = ResultsView()
        splitter.addWidget(self.results_view)
        
        # Set initial sizes (30% filter panel, 70% results)
        splitter.setSizes([300, 700])
        main_layout.addWidget(splitter, 1)  # 1 = stretch factor
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        self.setCentralWidget(central_widget)
    
    def _open_dat_file(self):
        """Open a DAT file using file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open DAT File", "", "DAT Files (*.dat);;XML Files (*.xml);;All Files (*.*)"
        )
        
        if file_path:
            self._load_dat_file(file_path)
    
    def _load_dat_file(self, file_path: str):
        """
        Load and parse a DAT file
        
        Args:
            file_path: Path to the DAT file
        """
        self.status_bar.showMessage(f"Loading DAT file: {file_path}...")
        
        try:
            # Parse the DAT file
            self.parsed_data = self.dat_parser.parse_file(file_path)
            self.current_dat_file = file_path
            
            # Update file selector
            self.file_selector.set_current_file(file_path)
            
            # Update results view
            self.results_view.set_original_data(self.parsed_data)
            
            # Reset filtered games
            self.filtered_games = []
            self.evaluations = []
            
            # Process the collection to identify special cases
            result = self.rule_engine.process_collection(self.parsed_data['games'])
            self.special_cases = result['special_cases']
            
            # Update available consoles in filter panel
            if 'consoles' in self.parsed_data:
                self.filter_panel.set_available_consoles(self.parsed_data['consoles'])
            
            # Update status bar
            game_count = self.parsed_data['game_count']
            self.status_bar.showMessage(f"Loaded DAT file with {game_count} games", 5000)
            
            # Enable filter panel
            self.filter_panel.set_enabled(True)
            
            # Add to recent files
            self.file_selector.add_recent_file(file_path)
            
        except Exception as e:
            self.logger.error(f"Error loading DAT file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load DAT file: {str(e)}")
            self.status_bar.showMessage("Error loading DAT file", 5000)
    
    def _update_progress(self, current: int, total: int):
        """
        Update progress bar
        
        Args:
            current: Current progress value
            total: Total progress value
        """
        percentage = int(100 * current / total) if total > 0 else 0
        self.progress_bar.setValue(percentage)
        self.status_bar.showMessage(f"Processing: {current}/{total} games ({percentage}%)")
        
        # Process events to update UI
        QApplication.processEvents()
    
    def _apply_filters(self):
        """Apply filters to the loaded DAT file"""
        if not self.parsed_data:
            QMessageBox.warning(self, "Warning", "Please load a DAT file first.")
            return
        
        if not self.ai_provider or not self.ai_provider.is_available():
            result = QMessageBox.warning(
                self, 
                "AI Provider Not Available", 
                "The AI provider is not available. Filtering requires AI capabilities.\n\n" +
                "Would you like to configure the API key?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if result == QMessageBox.Yes:
                self._configure_api_key()
            
            return
        
        # Get filter criteria from panel
        criteria = self.filter_panel.get_criteria()
        rule_config = self.filter_panel.get_rule_config()
        advanced_settings = self.filter_panel.get_advanced_settings()
        
        # Validate criteria
        if not criteria:
            QMessageBox.warning(self, "Warning", "Please select at least one filter criterion.")
            return
        
        # Show progress bar
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        
        # Apply filters
        try:
            # Get settings from advanced panel
            batch_size = advanced_settings.get('batch_size', 10)
            provider_name = advanced_settings.get('ai_provider', self.config.get('ai_provider', 'random'))
            ai_model = advanced_settings.get('ai_model')
            
            # Check if we need to switch providers
            current_provider_name = getattr(self.ai_provider, 'get_provider_name', lambda: 'unknown')().lower() if self.ai_provider else 'none'
            
            # If the provider changed or isn't initialized
            if current_provider_name != provider_name or not self.ai_provider or not self.ai_provider.is_available():
                self.logger.info(f"Switching AI provider to {provider_name}")
                
                # Initialize the new provider
                try:
                    self.ai_provider = get_provider(provider_name)
                    
                    # If we have an API model, set it
                    if ai_model and hasattr(self.ai_provider, 'set_model'):
                        self.ai_provider.set_model(ai_model)
                    
                    # Initialize the provider
                    self.ai_provider.initialize()
                    
                    # Update the filter engine with the new provider
                    self.filter_engine = FilterEngine(self.ai_provider)
                    
                except Exception as e:
                    self.logger.error(f"Failed to initialize {provider_name} provider: {e}")
                    QMessageBox.critical(self, "Error", f"Failed to initialize {provider_name} provider: {str(e)}")
                    return
            
            # Update the provider status display
            self._update_provider_status()
            
            # Show process info in status bar
            provider_info = self.ai_provider.get_provider_name()
            self.status_bar.showMessage(f"Processing with {provider_info}, batch size: {batch_size} games per API call")
            
            # Filter collection
            self.filtered_games, self.evaluations = self.filter_engine.filter_collection(
                self.parsed_data['games'],
                criteria,
                batch_size,  # batch size from advanced settings
                self._update_progress
            )
            
            # Apply special case rules
            if rule_config:
                self.filtered_games = self.rule_engine.apply_rules_to_filtered_games(
                    self.filtered_games,
                    rule_config
                )
            
            # Update results view
            self.results_view.set_filtered_data(self.filtered_games, self.evaluations, self.special_cases)
            
            # Update status
            self.status_bar.showMessage(
                f"Filtering complete: {len(self.filtered_games)} of {self.parsed_data['game_count']} games kept",
                5000
            )
            
        except Exception as e:
            self.logger.error(f"Error applying filters: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply filters: {str(e)}")
            self.status_bar.showMessage("Error applying filters", 5000)
        
        # Hide progress bar
        self.progress_bar.setVisible(False)
    
    def _export_filtered_dat(self):
        """Export filtered games to a DAT file"""
        if not self.filtered_games:
            QMessageBox.warning(self, "Warning", "No filtered data to export. Please apply filters first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Filtered DAT", "", "DAT Files (*.dat);;XML Files (*.xml);;All Files (*.*)"
        )
        
        if file_path:
            # Get metadata for the export
            criteria = self.filter_panel.get_criteria()
            metadata = {
                "filtered_by": "DAT Filter AI",
                "filter_criteria": ", ".join(criteria),
                "original_count": str(self.parsed_data['game_count']),
                "filtered_count": str(len(self.filtered_games))
            }
            
            success, message = self.export_manager.export_dat_file(
                self.filtered_games,
                self.parsed_data,
                file_path,
                metadata
            )
            
            if success:
                QMessageBox.information(self, "Export Successful", message)
                self.status_bar.showMessage(message, 5000)
            else:
                QMessageBox.critical(self, "Export Failed", message)
                self.status_bar.showMessage("Export failed", 5000)
    
    def _export_json_report(self):
        """Export a JSON report of the filtering results"""
        if not self.filtered_games:
            QMessageBox.warning(self, "Warning", "No filtered data to export. Please apply filters first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export JSON Report", "", "JSON Files (*.json);;All Files (*.*)"
        )
        
        if file_path:
            success, message = self.export_manager.export_json_report(
                self.filtered_games,
                self.evaluations,
                self.special_cases,
                file_path
            )
            
            if success:
                QMessageBox.information(self, "Export Successful", message)
                self.status_bar.showMessage(message, 5000)
            else:
                QMessageBox.critical(self, "Export Failed", message)
                self.status_bar.showMessage("Export failed", 5000)
    
    def _export_text_summary(self):
        """Export a text summary of the filtering results"""
        if not self.filtered_games:
            QMessageBox.warning(self, "Warning", "No filtered data to export. Please apply filters first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Text Summary", "", "Text Files (*.txt);;All Files (*.*)"
        )
        
        if file_path:
            criteria = self.filter_panel.get_criteria()
            
            success, message = self.export_manager.export_text_summary(
                self.filtered_games,
                self.parsed_data['game_count'],
                criteria,
                file_path
            )
            
            if success:
                QMessageBox.information(self, "Export Successful", message)
                self.status_bar.showMessage(message, 5000)
            else:
                QMessageBox.critical(self, "Export Failed", message)
                self.status_bar.showMessage("Export failed", 5000)
    
    def _configure_api_key(self):
        """Configure API keys for providers"""
        from PyQt5.QtWidgets import QInputDialog, QLineEdit, QDialog, QVBoxLayout, QFormLayout, QPushButton, QTabWidget, QWidget
        
        # Create dialog for API key configuration
        dialog = QDialog(self)
        dialog.setWindowTitle("Configure API Keys")
        dialog.setMinimumWidth(400)
        
        # Create tabs for different providers
        layout = QVBoxLayout(dialog)
        tab_widget = QTabWidget()
        
        # OpenAI tab
        openai_tab = QWidget()
        openai_layout = QFormLayout(openai_tab)
        
        # OpenAI API Key
        current_openai_key = os.environ.get("OPENAI_API_KEY", "")
        openai_key_input = QLineEdit()
        openai_key_input.setEchoMode(QLineEdit.Password)
        openai_key_input.setText(current_openai_key)
        openai_layout.addRow("OpenAI API Key:", openai_key_input)
        
        # Gemini tab
        gemini_tab = QWidget()
        gemini_layout = QFormLayout(gemini_tab)
        
        # Gemini API Key
        current_gemini_key = os.environ.get("GEMINI_API_KEY", "")
        gemini_key_input = QLineEdit()
        gemini_key_input.setEchoMode(QLineEdit.Password)
        gemini_key_input.setText(current_gemini_key)
        gemini_layout.addRow("Gemini API Key:", gemini_key_input)
        
        # Add tabs
        tab_widget.addTab(openai_tab, "OpenAI")
        tab_widget.addTab(gemini_tab, "Gemini")
        
        layout.addWidget(tab_widget)
        
        # Button box
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # Connect buttons
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        # Show dialog
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            # Save OpenAI key
            openai_key = openai_key_input.text()
            if openai_key:
                os.environ["OPENAI_API_KEY"] = openai_key
                self.logger.info("OpenAI API key configured")
            
            # Save Gemini key
            gemini_key = gemini_key_input.text()
            if gemini_key:
                os.environ["GEMINI_API_KEY"] = gemini_key
                self.logger.info("Gemini API key configured")
            
            # Reinitialize the AI provider
            try:
                # Get current provider from settings panel
                provider_name = self.filter_panel.ai_provider.currentData()
                
                # Create or reinitialize the provider
                self.ai_provider = get_provider(provider_name)
                self.ai_provider.initialize()
                self.filter_engine = FilterEngine(self.ai_provider)
                
                self._update_provider_status()
                
                if self.ai_provider.is_available():
                    QMessageBox.information(self, "Success", "API keys configured successfully.")
                else:
                    QMessageBox.warning(self, "Warning", 
                        f"API keys set but {provider_name} provider initialization failed.")
            except Exception as e:
                self.logger.error(f"Failed to initialize AI provider: {e}")
                QMessageBox.critical(self, "Error", f"Failed to initialize AI provider: {str(e)}")
    
    def _show_api_key_warning(self):
        """Show a warning about missing API keys"""
        result = QMessageBox.warning(
            self, 
            "API Keys Required", 
            "API keys are required for AI-powered filtering functionality.\n\n" +
            "• OpenAI requires an API key for GPT models\n" +
            "• Google Gemini requires an API key for Gemini models\n" +
            "• Random provider requires no API key (for testing)\n\n" +
            "Would you like to configure API keys now?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if result == QMessageBox.Yes:
            self._configure_api_key()
    
    def _change_theme(self, theme_name: str):
        """
        Change the application theme
        
        Args:
            theme_name: Name of the theme to apply ("light" or "dark")
        """
        self.theme.set_theme(theme_name)
        
        # Apply theme to application (would be implemented with QSS in practice)
        self.status_bar.showMessage(f"Theme changed to {theme_name}", 3000)
    
    def _show_settings(self):
        """Show settings dialog"""
        # For now, just show API key configuration
        self._configure_api_key()
    
    def _show_about_dialog(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About DAT Filter AI",
            "<h1>DAT Filter AI</h1>"
            "<p>Version 1.5.0</p>"
            "<p>A desktop application that uses AI to filter and curate "
            "video game collections from XML-formatted .dat files based on "
            "various criteria while maintaining original data structure.</p>"
            "<p><b>Supported AI Providers:</b><br>"
            "• OpenAI (GPT-4o, GPT-3.5 Turbo)<br>"
            "• Google Gemini (Gemini 1.5 Flash, Gemini 1.5 Pro)<br>"
            "• Random (Testing mode, no API key needed)</p>"
            "<p>Optimized with batch processing for improved API efficiency.</p>"
            "<p>&copy; 2025 DAT Filter AI Team</p>"
        )
