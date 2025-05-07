"""
Filter panel for selecting and configuring filtering criteria.
"""

import logging
from typing import Dict, List, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QCheckBox, QGroupBox, QSlider, QComboBox, QSpinBox,
    QScrollArea, QTabWidget, QFormLayout, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal

class FilterPanel(QWidget):
    """Widget for selecting and configuring filtering criteria."""
    
    # Signal emitted when filtering is requested
    filter_requested = pyqtSignal()
    
    def __init__(self, config: Dict[str, Any], filter_engine=None):
        """
        Initialize the filter panel
        
        Args:
            config: Application configuration
            filter_engine: Optional reference to the filter engine
        """
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.filter_engine = filter_engine
        self.available_consoles = []
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create a scroll area to handle content that might overflow
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tabs for different filtering options
        tab_widget = QTabWidget()
        
        # Criteria tab
        criteria_tab = QWidget()
        criteria_layout = QVBoxLayout(criteria_tab)
        
        # Criteria group
        criteria_group = QGroupBox("Filtering Criteria")
        criteria_group_layout = QVBoxLayout(criteria_group)
        
        # Create checkboxes for each criterion
        self.criteria_checkboxes = {}
        
        criteria_options = [
            ("metacritic", "Metacritic Scores & Critical Acclaim", True),
            ("historical", "Historical Significance & Impact", True),
            ("v_list", "Presence in V's Recommended Games List", False),
            ("console_significance", "Console-specific Significance", False),
            ("mods_hacks", "Notable Mods or Hacks", False)
        ]
        
        for criterion_id, criterion_label, default_checked in criteria_options:
            checkbox = QCheckBox(criterion_label)
            checkbox.setChecked(default_checked)
            criteria_group_layout.addWidget(checkbox)
            self.criteria_checkboxes[criterion_id] = checkbox
        
        criteria_layout.addWidget(criteria_group)
        
        # Thresholds group
        thresholds_group = QGroupBox("Score Thresholds")
        thresholds_layout = QFormLayout(thresholds_group)
        
        self.threshold_sliders = {}
        
        for criterion_id, criterion_label, _ in criteria_options:
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 10)
            slider.setValue(5)  # Default threshold of 5
            slider.setTickPosition(QSlider.TicksBelow)
            slider.setTickInterval(1)
            
            # Create a layout for the slider with value label
            slider_layout = QHBoxLayout()
            slider_layout.addWidget(slider)
            
            value_label = QLabel("5")
            slider.valueChanged.connect(lambda val, lbl=value_label: lbl.setText(str(val)))
            slider_layout.addWidget(value_label)
            
            thresholds_layout.addRow(criterion_label, slider_layout)
            self.threshold_sliders[criterion_id] = slider
            
            # Connect to filter engine if available
            if self.filter_engine:
                slider.valueChanged.connect(
                    lambda val, crit=criterion_id: self.filter_engine.set_threshold(crit, val)
                )
        
        criteria_layout.addWidget(thresholds_group)
        
        # Special Cases tab
        special_cases_tab = QWidget()
        special_cases_layout = QVBoxLayout(special_cases_tab)
        
        # Multi-disc handling
        multi_disc_group = QGroupBox("Multi-disc Games")
        multi_disc_layout = QVBoxLayout(multi_disc_group)
        
        self.multi_disc_mode = QComboBox()
        self.multi_disc_mode.addItem("Include complete sets only (all or none)", "all_or_none")
        self.multi_disc_mode.addItem("Keep first disc only", "first_disc_only")
        
        multi_disc_layout.addWidget(QLabel("Handling mode:"))
        multi_disc_layout.addWidget(self.multi_disc_mode)
        
        special_cases_layout.addWidget(multi_disc_group)
        
        # Regional variants handling
        regional_group = QGroupBox("Regional Variants")
        regional_layout = QVBoxLayout(regional_group)
        
        self.regional_mode = QComboBox()
        self.regional_mode.addItem("Keep preferred region only", "prefer_region")
        self.regional_mode.addItem("Keep all regional variants", "keep_all")
        
        regional_layout.addWidget(QLabel("Handling mode:"))
        regional_layout.addWidget(self.regional_mode)
        
        # Region preference order
        regional_layout.addWidget(QLabel("Region preference order:"))
        
        self.region_preference = QComboBox()
        self.region_preference.addItem("USA, Europe, World, Japan", ["USA", "Europe", "World", "Japan"])
        self.region_preference.addItem("Japan, USA, Europe, World", ["Japan", "USA", "Europe", "World"])
        self.region_preference.addItem("Europe, USA, World, Japan", ["Europe", "USA", "World", "Japan"])
        
        regional_layout.addWidget(self.region_preference)
        
        special_cases_layout.addWidget(regional_group)
        
        # Mods and hacks handling
        mods_group = QGroupBox("Mods and Hacks")
        mods_layout = QVBoxLayout(mods_group)
        
        self.mods_mode = QComboBox()
        self.mods_mode.addItem("Include only notable mods/hacks", "include_notable")
        self.mods_mode.addItem("Exclude all mods/hacks", "exclude_all")
        
        mods_layout.addWidget(QLabel("Handling mode:"))
        mods_layout.addWidget(self.mods_mode)
        
        special_cases_layout.addWidget(mods_group)
        
        # Advanced Options tab
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        
        # AI settings
        ai_group = QGroupBox("AI Settings")
        ai_layout = QVBoxLayout(ai_group)
        
        # AI model selection (for future expansion)
        ai_layout.addWidget(QLabel("AI Model:"))
        self.ai_model = QComboBox()
        self.ai_model.addItem("GPT-4o (Recommended)", "gpt-4o")
        self.ai_model.addItem("GPT-3.5 Turbo (Faster, less accurate)", "gpt-3.5-turbo")
        ai_layout.addWidget(self.ai_model)
        
        # Batch size for processing
        ai_layout.addWidget(QLabel("Batch Size (games per API call):"))
        self.batch_size = QSpinBox()
        self.batch_size.setRange(1, 50)
        self.batch_size.setValue(10)
        self.batch_size.setSingleStep(5)
        ai_layout.addWidget(self.batch_size)
        
        advanced_layout.addWidget(ai_group)
        
        # Console filter settings (dynamic based on loaded DAT)
        self.console_group = QGroupBox("Console Filters")
        self.console_layout = QVBoxLayout(self.console_group)
        
        self.console_layout.addWidget(QLabel("Filter by specific console:"))
        self.console_filter = QComboBox()
        self.console_filter.addItem("All Consoles", "all")
        self.console_layout.addWidget(self.console_filter)
        
        advanced_layout.addWidget(self.console_group)
        
        # Add tabs
        tab_widget.addTab(criteria_tab, "Criteria")
        tab_widget.addTab(special_cases_tab, "Special Cases")
        tab_widget.addTab(advanced_tab, "Advanced")
        
        scroll_layout.addWidget(tab_widget)
        
        # Apply button
        apply_button_layout = QHBoxLayout()
        apply_button_layout.addStretch()
        
        self.apply_button = QPushButton("Apply Filters")
        self.apply_button.setEnabled(False)  # Disabled until a file is loaded
        self.apply_button.clicked.connect(self.filter_requested.emit)
        self.apply_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        apply_button_layout.addWidget(self.apply_button)
        scroll_layout.addLayout(apply_button_layout)
        
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
    
    def set_enabled(self, enabled: bool):
        """
        Enable or disable the filter panel
        
        Args:
            enabled: True to enable, False to disable
        """
        self.apply_button.setEnabled(enabled)
    
    def set_available_consoles(self, consoles: List[str]):
        """
        Set the available consoles for filtering
        
        Args:
            consoles: List of console names
        """
        self.available_consoles = consoles
        
        # Update console filter dropdown
        self.console_filter.clear()
        self.console_filter.addItem("All Consoles", "all")
        
        for console in sorted(consoles):
            self.console_filter.addItem(console, console)
    
    def get_criteria(self) -> List[str]:
        """
        Get the selected filtering criteria
        
        Returns:
            List of selected criteria IDs
        """
        return [
            criterion_id
            for criterion_id, checkbox in self.criteria_checkboxes.items()
            if checkbox.isChecked()
        ]
    
    def get_thresholds(self) -> Dict[str, float]:
        """
        Get the threshold values for each criterion
        
        Returns:
            Dictionary mapping criteria IDs to threshold values
        """
        return {
            criterion_id: slider.value()
            for criterion_id, slider in self.threshold_sliders.items()
        }
    
    def get_rule_config(self) -> Dict[str, Any]:
        """
        Get the configuration for special case handling rules
        
        Returns:
            Dictionary with rule configuration
        """
        # Get selected region preference
        region_preference = self.region_preference.currentData()
        
        return {
            "multi_disc": {
                "mode": self.multi_disc_mode.currentData(),
                "prefer": "complete"  # Always prefer complete sets when mode is all_or_none
            },
            "regional_variants": {
                "mode": self.regional_mode.currentData(),
                "preferred_regions": region_preference
            },
            "mods_hacks": {
                "mode": self.mods_mode.currentData()
            }
        }
    
    def get_advanced_settings(self) -> Dict[str, Any]:
        """
        Get advanced settings
        
        Returns:
            Dictionary with advanced settings
        """
        return {
            "ai_model": self.ai_model.currentData(),
            "batch_size": self.batch_size.value(),
            "console_filter": self.console_filter.currentData()
        }
