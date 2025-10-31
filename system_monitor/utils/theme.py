"""Theme and styling utilities for the application."""

#      Copyright (c) 2025 predator. All rights reserved.

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor


def apply_dark_theme(app: QApplication) -> None:
    """Apply modern dark theme with enhanced aesthetics."""
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(18, 18, 18))
    palette.setColor(QPalette.WindowText, QColor(224, 224, 224))
    palette.setColor(QPalette.Base, QColor(24, 24, 24))
    palette.setColor(QPalette.AlternateBase, QColor(30, 30, 30))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.Text, QColor(224, 224, 224))
    palette.setColor(QPalette.Button, QColor(30, 30, 30))
    palette.setColor(QPalette.ButtonText, QColor(224, 224, 224))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Highlight, QColor(53, 132, 228))
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)
    app.setStyleSheet(
        """
        QWidget { background-color: #121212; color: #e0e0e0; }
        QMainWindow { background-color: #0d0d0d; }
        
        /* Enhanced card design with depth */
        QFrame#Card { 
            background-color: #1e1e1e; 
            border: 1px solid #333333; 
            border-radius: 12px;
            padding: 4px;
        }
        QFrame#Card:hover {
            border: 1px solid #404040;
            background-color: #232323;
        }
        
        /* Typography improvements */
        QLabel#Title { 
            font-weight: 600; 
            font-size: 12pt; 
            color: #b0b0b0;
            letter-spacing: 0.5px;
        }
        QLabel#Value { 
            font-weight: 700; 
            font-size: 22pt; 
            color: #ffffff;
            letter-spacing: 0.3px;
        }
        
        /* Enhanced progress bars */
        QProgressBar { 
            background-color: #1a1a1a; 
            border: 1px solid #2a2a2a; 
            border-radius: 7px; 
            height: 16px;
            text-align: center;
        }
        QProgressBar::chunk { 
            background-color: #00c853; 
            border-radius: 6px;
        }
        
        /* Toolbar styling */
        QToolBar {
            background-color: #1a1a1a;
            border-bottom: 2px solid #2a2a2a;
            spacing: 8px;
            padding: 8px;
        }
        QToolBar QLabel {
            color: #b0b0b0;
            font-size: 10pt;
            padding: 0 4px;
        }
        QToolBar QSpinBox {
            background-color: #252525;
            border: 1px solid #3a3a3a;
            border-radius: 4px;
            padding: 4px 8px;
            color: #e0e0e0;
            min-width: 80px;
        }
        QToolBar QPushButton {
            background-color: #2a2a2a;
            border: 1px solid #3a3a3a;
            border-radius: 4px;
            padding: 6px 12px;
            color: #e0e0e0;
            font-weight: 500;
        }
        QToolBar QPushButton:hover {
            background-color: #333333;
            border: 1px solid #4a4a4a;
        }
        QToolBar QPushButton:pressed {
            background-color: #202020;
        }
        QToolBar QPushButton#PauseButton {
            background-color: #1976d2;
            border: 1px solid #2196f3;
        }
        QToolBar QPushButton#PauseButton:hover {
            background-color: #2196f3;
        }
        
        /* Tab improvements */
        QTabWidget::pane { 
            border: 1px solid #2a2a2a;
            background-color: #141414;
            top: -1px;
        }
        QTabBar::tab { 
            background: #1a1a1a; 
            padding: 8px 16px; 
            border: 1px solid #2a2a2a; 
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            margin-right: 2px;
        }
        QTabBar::tab:selected { 
            background: #2a2a2a;
            border-bottom: 2px solid #3584e4;
        }
        QTabBar::tab:hover:!selected {
            background: #222222;
        }
        
        /* Table styling */
        QTableWidget {
            background-color: #1a1a1a;
            alternate-background-color: #1e1e1e;
            gridline-color: #2a2a2a;
            selection-background-color: #3584e4;
        }
        QHeaderView::section {
            background-color: #252525;
            color: #b0b0b0;
            padding: 6px;
            border: 1px solid #2a2a2a;
            font-weight: 600;
        }
        """
    )
