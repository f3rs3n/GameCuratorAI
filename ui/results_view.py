"""
Results view for displaying original and filtered game collections.
"""

import logging
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QGroupBox, QTextEdit, QSplitter, QMenu, QAction
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QBrush

class ResultsView(QWidget):
    """Widget for displaying original and filtered game collections."""
    
    def __init__(self):
        """Initialize the results view widget."""
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.original_data = None
        self.filtered_games = []
        self.evaluations = []
        self.special_cases = {}
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Summary section
        summary_group = QGroupBox("Summary")
        summary_layout = QVBoxLayout(summary_group)
        
        self.summary_label = QLabel("No data loaded")
        summary_layout.addWidget(self.summary_label)
        
        main_layout.addWidget(summary_group)
        
        # Create tabs for different views
        self.tabs = QTabWidget()
        
        # Games list tab
        games_tab = QWidget()
        games_layout = QVBoxLayout(games_tab)
        
        # Create a splitter for games table and details
        games_splitter = QSplitter(Qt.Vertical)
        
        # Games table
        self.games_table = QTableWidget()
        self.games_table.setColumnCount(4)
        self.games_table.setHorizontalHeaderLabels(["Name", "Status", "Score", "Reason"])
        self.games_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.games_table.horizontalHeader().setMinimumSectionSize(80)
        self.games_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.games_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.games_table.setAlternatingRowColors(True)
        self.games_table.verticalHeader().setVisible(False)
        self.games_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.games_table.customContextMenuRequested.connect(self._show_context_menu)
        self.games_table.itemSelectionChanged.connect(self._on_game_selected)
        
        games_splitter.addWidget(self.games_table)
        
        # Game details
        details_group = QGroupBox("Game Details")
        details_layout = QVBoxLayout(details_group)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)
        
        games_splitter.addWidget(details_group)
        
        # Set initial sizes (70% table, 30% details)
        games_splitter.setSizes([700, 300])
        games_layout.addWidget(games_splitter)
        
        # Special cases tab
        special_cases_tab = QWidget()
        special_cases_layout = QVBoxLayout(special_cases_tab)
        
        self.special_cases_text = QTextEdit()
        self.special_cases_text.setReadOnly(True)
        special_cases_layout.addWidget(self.special_cases_text)
        
        # Statistics tab
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        stats_layout.addWidget(self.stats_text)
        
        # Add tabs
        self.tabs.addTab(games_tab, "Games")
        self.tabs.addTab(special_cases_tab, "Special Cases")
        self.tabs.addTab(stats_tab, "Statistics")
        
        main_layout.addWidget(self.tabs, 1)  # 1 = stretch factor
    
    def set_original_data(self, data: Dict[str, Any]):
        """
        Set the original DAT file data
        
        Args:
            data: Parsed DAT file data
        """
        self.original_data = data
        self.filtered_games = []
        self.evaluations = []
        
        # Update summary
        self._update_summary()
        
        # Populate games table with original data
        self._populate_games_table(data.get('games', []), None)
        
        # Update special cases if available
        if self.special_cases:
            self._update_special_cases_view()
        
        # Update statistics
        self._update_statistics()
    
    def set_filtered_data(self, 
                         filtered_games: List[Dict[str, Any]], 
                         evaluations: List[Dict[str, Any]],
                         special_cases: Optional[Dict[str, Any]] = None):
        """
        Set the filtered data
        
        Args:
            filtered_games: List of filtered games
            evaluations: List of evaluation results
            special_cases: Optional dictionary of special cases
        """
        self.filtered_games = filtered_games
        self.evaluations = evaluations
        
        if special_cases:
            self.special_cases = special_cases
        
        # Update summary
        self._update_summary()
        
        # Populate games table with filtered data
        self._populate_games_table(self.original_data.get('games', []), filtered_games)
        
        # Update special cases view
        self._update_special_cases_view()
        
        # Update statistics
        self._update_statistics()
        
        # Switch to games tab
        self.tabs.setCurrentIndex(0)
    
    def _update_summary(self):
        """Update the summary information."""
        if not self.original_data:
            self.summary_label.setText("No data loaded")
            return
        
        original_count = self.original_data.get('game_count', 0)
        filtered_count = len(self.filtered_games)
        
        if filtered_count > 0:
            reduction = original_count - filtered_count
            reduction_percent = 100 * reduction / original_count if original_count > 0 else 0
            
            summary = (
                f"Original collection: {original_count} games\n"
                f"Filtered collection: {filtered_count} games\n"
                f"Reduction: {reduction} games ({reduction_percent:.1f}%)"
            )
        else:
            summary = f"Original collection: {original_count} games\nNo filters applied yet"
        
        self.summary_label.setText(summary)
    
    def _populate_games_table(self, 
                             all_games: List[Dict[str, Any]], 
                             filtered_games: Optional[List[Dict[str, Any]]]):
        """
        Populate the games table with game data
        
        Args:
            all_games: List of all games
            filtered_games: Optional list of filtered games
        """
        self.games_table.setRowCount(0)
        
        if not all_games:
            return
        
        # If filtered_games is None, show all games without filtering indicators
        if filtered_games is None:
            for i, game in enumerate(all_games):
                self._add_game_row(i, game, included=True, evaluation=None)
            return
        
        # Create a set of filtered game IDs/names for faster lookup
        filtered_ids = {game.get('id', game.get('name', '')) for game in filtered_games}
        
        # Create a mapping of game ID/name to evaluation
        evaluation_map = {}
        for game in filtered_games:
            game_id = game.get('id', game.get('name', ''))
            if '_evaluation' in game:
                evaluation_map[game_id] = game['_evaluation']
        
        # Add all games to the table with appropriate status
        for i, game in enumerate(all_games):
            game_id = game.get('id', game.get('name', ''))
            included = game_id in filtered_ids
            evaluation = evaluation_map.get(game_id)
            
            self._add_game_row(i, game, included, evaluation)
    
    def _add_game_row(self, 
                     row_index: int, 
                     game: Dict[str, Any], 
                     included: bool,
                     evaluation: Optional[Dict[str, Any]]):
        """
        Add a row to the games table
        
        Args:
            row_index: Index of the row
            game: Game data
            included: Whether the game is included in filtered results
            evaluation: Evaluation data for the game
        """
        self.games_table.insertRow(row_index)
        
        # Get game name
        name = game.get('name', 'Unknown')
        
        # Create name item
        name_item = QTableWidgetItem(name)
        name_item.setData(Qt.UserRole, game)  # Store the game data
        self.games_table.setItem(row_index, 0, name_item)
        
        # Create status item
        if included:
            status_text = "Included"
            status_color = QColor(0, 128, 0)  # Green
        else:
            status_text = "Excluded"
            status_color = QColor(128, 0, 0)  # Red
        
        status_item = QTableWidgetItem(status_text)
        status_item.setForeground(QBrush(status_color))
        status_item.setTextAlignment(Qt.AlignCenter)
        self.games_table.setItem(row_index, 1, status_item)
        
        # Add score and reason if available
        if evaluation:
            # Overall score
            score = "N/A"
            
            # Get the overall recommendation
            if "overall_recommendation" in evaluation:
                reason = evaluation["overall_recommendation"].get("reason", "")
                
                # Calculate average score from evaluations
                if "evaluations" in evaluation:
                    scores = []
                    for criterion, eval_data in evaluation["evaluations"].items():
                        if "score" in eval_data:
                            scores.append(float(eval_data["score"]))
                    
                    if scores:
                        avg_score = sum(scores) / len(scores)
                        score = f"{avg_score:.1f}"
            else:
                reason = "No evaluation available"
            
            score_item = QTableWidgetItem(score)
            score_item.setTextAlignment(Qt.AlignCenter)
            self.games_table.setItem(row_index, 2, score_item)
            
            reason_item = QTableWidgetItem(reason)
            self.games_table.setItem(row_index, 3, reason_item)
    
    def _on_game_selected(self):
        """Handle selection of a game in the table."""
        selected_items = self.games_table.selectedItems()
        if not selected_items:
            self.details_text.clear()
            return
        
        # Get the first item in the selected row (name column)
        row = selected_items[0].row()
        name_item = self.games_table.item(row, 0)
        
        if name_item:
            # Get game data from item
            game = name_item.data(Qt.UserRole)
            
            if game:
                self._show_game_details(game)
    
    def _show_game_details(self, game: Dict[str, Any]):
        """
        Show details for a game
        
        Args:
            game: Game data
        """
        details = []
        
        # Basic game information
        name = game.get('name', 'Unknown')
        details.append(f"<h2>{name}</h2>")
        
        # Add available metadata
        if 'description' in game and isinstance(game['description'], dict):
            details.append(f"<p><b>Description:</b> {game['description'].get('text', '')}</p>")
        
        if 'developer' in game and isinstance(game['developer'], dict):
            details.append(f"<p><b>Developer:</b> {game['developer'].get('text', '')}</p>")
        
        if 'publisher' in game and isinstance(game['publisher'], dict):
            details.append(f"<p><b>Publisher:</b> {game['publisher'].get('text', '')}</p>")
        
        if 'year' in game and isinstance(game['year'], dict):
            details.append(f"<p><b>Year:</b> {game['year'].get('text', '')}</p>")
        
        # Show ROM/file information if available
        if 'rom' in game and isinstance(game['rom'], dict):
            details.append("<h3>ROM Information</h3>")
            details.append("<ul>")
            
            for key, value in game['rom'].items():
                if key != 'children':
                    details.append(f"<li><b>{key}:</b> {value}</li>")
            
            details.append("</ul>")
        
        # Show evaluation if available
        if '_evaluation' in game:
            evaluation = game['_evaluation']
            details.append("<h3>AI Evaluation</h3>")
            
            if "overall_recommendation" in evaluation:
                recommendation = evaluation["overall_recommendation"]
                include = recommendation.get("include", False)
                reason = recommendation.get("reason", "No reason provided")
                
                status = "Include" if include else "Exclude"
                status_color = "green" if include else "red"
                
                details.append(f"<p><b>Recommendation:</b> <span style='color:{status_color}'>{status}</span></p>")
                details.append(f"<p><b>Reason:</b> {reason}</p>")
            
            if "evaluations" in evaluation:
                details.append("<table border='1' cellpadding='4' style='border-collapse:collapse; width:100%'>")
                details.append("<tr><th>Criterion</th><th>Score</th><th>Explanation</th></tr>")
                
                for criterion, eval_data in evaluation["evaluations"].items():
                    score = eval_data.get("score", "N/A")
                    explanation = eval_data.get("explanation", "")
                    
                    details.append("<tr>")
                    details.append(f"<td>{criterion}</td>")
                    details.append(f"<td align='center'>{score}</td>")
                    details.append(f"<td>{explanation}</td>")
                    details.append("</tr>")
                
                details.append("</table>")
        
        # Set the details text
        self.details_text.setHtml("\n".join(details))
    
    def _update_special_cases_view(self):
        """Update the special cases view."""
        if not self.special_cases:
            self.special_cases_text.setPlainText("No special cases detected.")
            return
        
        details = []
        details.append("# Special Cases Detected\n")
        
        # Multi-disc games
        if "multi_disc" in self.special_cases:
            multi_disc = self.special_cases["multi_disc"]
            count = multi_disc.get("count", 0)
            groups = multi_disc.get("groups", [])
            
            details.append(f"## Multi-disc Games: {count} sets\n")
            
            for i, group in enumerate(groups, 1):
                details.append(f"### Set {i}:")
                for game in group:
                    details.append(f"- {game.get('name', 'Unknown')}")
                details.append("")
        
        # Regional variants
        if "regional_variants" in self.special_cases:
            regional = self.special_cases["regional_variants"]
            count = regional.get("count", 0)
            groups = regional.get("groups", [])
            
            details.append(f"## Regional Variants: {count} games\n")
            
            for i, group in enumerate(groups, 1):
                details.append(f"### Variant Set {i}:")
                for game in group:
                    details.append(f"- {game.get('name', 'Unknown')}")
                details.append("")
        
        # Console naming patterns
        if "console_naming" in self.special_cases:
            console = self.special_cases["console_naming"]
            count = console.get("count", 0)
            by_console = console.get("by_console", {})
            
            details.append(f"## Console Naming Patterns: {count} games\n")
            
            for console_name, console_count in by_console.items():
                details.append(f"- {console_name}: {console_count} games")
            details.append("")
        
        # Mods and hacks
        if "mods_hacks" in self.special_cases:
            mods = self.special_cases["mods_hacks"]
            count = mods.get("count", 0)
            games = mods.get("games", [])
            
            details.append(f"## Mods and Hacks: {count} games\n")
            
            for i, game in enumerate(games[:30], 1):
                details.append(f"{i}. {game.get('name', 'Unknown')}")
            
            if len(games) > 30:
                details.append(f"... and {len(games) - 30} more")
        
        self.special_cases_text.setPlainText("\n".join(details))
    
    def _update_statistics(self):
        """Update the statistics view."""
        if not self.original_data:
            self.stats_text.setPlainText("No data loaded.")
            return
        
        stats = []
        stats.append("# Collection Statistics\n")
        
        # Basic collection info
        original_count = self.original_data.get('game_count', 0)
        filtered_count = len(self.filtered_games)
        stats.append(f"## Collection Size\n")
        stats.append(f"- Original: {original_count} games")
        stats.append(f"- Filtered: {filtered_count} games")
        if original_count > 0:
            reduction = original_count - filtered_count
            reduction_percent = 100 * reduction / original_count
            stats.append(f"- Reduction: {reduction} games ({reduction_percent:.1f}%)")
        stats.append("")
        
        # Console distribution
        if 'consoles' in self.original_data:
            consoles = self.original_data['consoles']
            stats.append(f"## Console Distribution\n")
            for console in consoles:
                stats.append(f"- {console}")
            stats.append("")
        
        # Evaluation statistics
        if self.evaluations:
            stats.append("## Evaluation Summary\n")
            
            # Count by recommendation
            include_count = 0
            exclude_count = 0
            
            for eval_data in self.evaluations:
                if "overall_recommendation" in eval_data and "include" in eval_data["overall_recommendation"]:
                    if eval_data["overall_recommendation"]["include"]:
                        include_count += 1
                    else:
                        exclude_count += 1
            
            stats.append(f"- Recommended for inclusion: {include_count}")
            stats.append(f"- Recommended for exclusion: {exclude_count}")
            stats.append("")
            
            # Average scores by criterion
            if any("evaluations" in eval_data for eval_data in self.evaluations):
                stats.append("## Average Scores by Criterion\n")
                
                criterion_scores = {}
                criterion_counts = {}
                
                for eval_data in self.evaluations:
                    if "evaluations" in eval_data:
                        for criterion, crit_data in eval_data["evaluations"].items():
                            if "score" in crit_data:
                                score = float(crit_data["score"])
                                
                                if criterion not in criterion_scores:
                                    criterion_scores[criterion] = 0
                                    criterion_counts[criterion] = 0
                                
                                criterion_scores[criterion] += score
                                criterion_counts[criterion] += 1
                
                for criterion, total in criterion_scores.items():
                    count = criterion_counts[criterion]
                    if count > 0:
                        avg = total / count
                        stats.append(f"- {criterion}: {avg:.2f} / 10")
        
        self.stats_text.setPlainText("\n".join(stats))
    
    def _show_context_menu(self, position):
        """
        Show context menu for the games table
        
        Args:
            position: Position where the menu should be shown
        """
        menu = QMenu()
        
        # Get the item at the position
        item = self.games_table.itemAt(position)
        if not item:
            return
        
        row = item.row()
        name_item = self.games_table.item(row, 0)
        game = name_item.data(Qt.UserRole) if name_item else None
        
        if game:
            # Add actions
            view_action = QAction("View Details", self)
            view_action.triggered.connect(lambda: self._show_game_details(game))
            menu.addAction(view_action)
            
            # Add copy actions
            copy_name_action = QAction("Copy Game Name", self)
            copy_name_action.triggered.connect(lambda: self._copy_to_clipboard(game.get('name', '')))
            menu.addAction(copy_name_action)
            
            menu.exec_(self.games_table.viewport().mapToGlobal(position))
    
    def _copy_to_clipboard(self, text: str):
        """
        Copy text to clipboard
        
        Args:
            text: Text to copy
        """
        from PyQt5.QtWidgets import QApplication
        QApplication.clipboard().setText(text)
