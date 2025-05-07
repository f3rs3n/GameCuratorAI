"""
File selector widget for choosing DAT files.
"""

import os
import logging
from typing import List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QFileDialog, QListWidget, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal

class FileSelector(QWidget):
    """Widget for selecting and handling DAT files."""
    
    # Signal emitted when a file is selected
    file_selected = pyqtSignal(str)
    
    def __init__(self):
        """Initialize the file selector widget."""
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self._recent_files: List[str] = []
        self._current_file: Optional[str] = None
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # File selection section
        file_group = QGroupBox("Select DAT File")
        file_layout = QVBoxLayout(file_group)
        
        # Current file display
        current_file_layout = QHBoxLayout()
        current_file_layout.addWidget(QLabel("Current File:"))
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        self.file_path_edit.setPlaceholderText("No file selected")
        current_file_layout.addWidget(self.file_path_edit, 1)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self._browse_for_file)
        current_file_layout.addWidget(self.browse_button)
        
        file_layout.addLayout(current_file_layout)
        
        # Recent files section
        recent_layout = QHBoxLayout()
        recent_layout.addWidget(QLabel("Recent Files:"))
        
        self.recent_files_list = QListWidget()
        self.recent_files_list.itemClicked.connect(self._recent_file_selected)
        recent_layout.addWidget(self.recent_files_list)
        
        file_layout.addLayout(recent_layout)
        
        main_layout.addWidget(file_group)
    
    def _browse_for_file(self):
        """Open a file dialog to browse for a DAT file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open DAT File", "", "DAT Files (*.dat);;XML Files (*.xml);;All Files (*.*)"
        )
        
        if file_path:
            self.set_current_file(file_path)
            self.file_selected.emit(file_path)
    
    def _recent_file_selected(self, item):
        """
        Handle selection of a recent file
        
        Args:
            item: Selected list item
        """
        file_path = item.data(Qt.UserRole)
        if file_path and os.path.exists(file_path):
            self.set_current_file(file_path)
            self.file_selected.emit(file_path)
        else:
            # Remove invalid file from list
            self.logger.warning(f"Recent file not found: {file_path}")
            self.remove_recent_file(file_path)
    
    def set_current_file(self, file_path: str):
        """
        Set the current file
        
        Args:
            file_path: Path to the current file
        """
        self._current_file = file_path
        self.file_path_edit.setText(file_path)
        
        # Add to recent files
        self.add_recent_file(file_path)
    
    def get_current_file(self) -> Optional[str]:
        """
        Get the current file path
        
        Returns:
            Path to the current file, or None if no file is selected
        """
        return self._current_file
    
    def add_recent_file(self, file_path: str):
        """
        Add a file to the recent files list
        
        Args:
            file_path: File path to add
        """
        # Don't add if it doesn't exist
        if not os.path.exists(file_path):
            return
        
        # Remove if already in list (to move it to the top)
        self.remove_recent_file(file_path)
        
        # Add to the beginning of the list
        self._recent_files.insert(0, file_path)
        
        # Limit to 10 recent files
        if len(self._recent_files) > 10:
            self._recent_files = self._recent_files[:10]
        
        # Update the list widget
        self._update_recent_files_list()
    
    def remove_recent_file(self, file_path: str):
        """
        Remove a file from the recent files list
        
        Args:
            file_path: File path to remove
        """
        if file_path in self._recent_files:
            self._recent_files.remove(file_path)
            self._update_recent_files_list()
    
    def set_recent_files(self, file_paths: List[str]):
        """
        Set the list of recent files
        
        Args:
            file_paths: List of file paths
        """
        # Filter out files that don't exist
        self._recent_files = [path for path in file_paths if os.path.exists(path)]
        self._update_recent_files_list()
    
    def get_recent_files(self) -> List[str]:
        """
        Get the list of recent files
        
        Returns:
            List of recent file paths
        """
        return self._recent_files.copy()
    
    def _update_recent_files_list(self):
        """Update the recent files list widget."""
        self.recent_files_list.clear()
        
        for file_path in self._recent_files:
            # Use just the filename in the display
            display_name = os.path.basename(file_path)
            
            item = QListWidgetItem(display_name)
            # Store the full path as user data
            item.setData(Qt.UserRole, file_path)
            # Show the full path as a tooltip
            item.setToolTip(file_path)
            
            self.recent_files_list.addItem(item)
