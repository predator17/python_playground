"""Tests for theme utilities."""

#      Copyright (c) 2025 predator. All rights reserved.

from unittest.mock import MagicMock, patch
import pytest


class TestTheme:
    """Test theme utility functions."""

    def test_apply_dark_theme(self, qapp):
        """Test apply_dark_theme sets style, palette, and stylesheet."""
        from system_monitor.utils.theme import apply_dark_theme
        from PySide6.QtGui import QPalette, QColor
        
        # Apply theme
        apply_dark_theme(qapp)
        
        # Verify style is set (Fusion style applied)
        # Note: objectName might be empty, but style should be set
        assert qapp.style() is not None
        
        # Verify palette is set with dark colors
        palette = qapp.palette()
        
        # Check Window color (18, 18, 18)
        window_color = palette.color(QPalette.Window)
        assert window_color.red() == 18
        assert window_color.green() == 18
        assert window_color.blue() == 18
        
        # Check WindowText color (224, 224, 224)
        window_text = palette.color(QPalette.WindowText)
        assert window_text.red() == 224
        assert window_text.green() == 224
        assert window_text.blue() == 224
        
        # Check Base color (24, 24, 24)
        base_color = palette.color(QPalette.Base)
        assert base_color.red() == 24
        assert base_color.green() == 24
        assert base_color.blue() == 24
        
        # Check AlternateBase color (30, 30, 30)
        alt_base = palette.color(QPalette.AlternateBase)
        assert alt_base.red() == 30
        assert alt_base.green() == 30
        assert alt_base.blue() == 30
        
        # Check Text color (224, 224, 224)
        text_color = palette.color(QPalette.Text)
        assert text_color.red() == 224
        assert text_color.green() == 224
        assert text_color.blue() == 224
        
        # Check Button color (30, 30, 30)
        button_color = palette.color(QPalette.Button)
        assert button_color.red() == 30
        assert button_color.green() == 30
        assert button_color.blue() == 30
        
        # Check ButtonText color (224, 224, 224)
        button_text = palette.color(QPalette.ButtonText)
        assert button_text.red() == 224
        assert button_text.green() == 224
        assert button_text.blue() == 224
        
        # Check Highlight color (53, 132, 228)
        highlight = palette.color(QPalette.Highlight)
        assert highlight.red() == 53
        assert highlight.green() == 132
        assert highlight.blue() == 228
        
        # Check HighlightedText color (0, 0, 0)
        highlighted_text = palette.color(QPalette.HighlightedText)
        assert highlighted_text.red() == 0
        assert highlighted_text.green() == 0
        assert highlighted_text.blue() == 0
        
        # Verify stylesheet is set
        stylesheet = qapp.styleSheet()
        assert stylesheet is not None
        assert len(stylesheet) > 0
        
        # Check key stylesheet components
        assert "QWidget" in stylesheet
        assert "background-color" in stylesheet
        assert "#121212" in stylesheet or "#0d0d0d" in stylesheet
        assert "QFrame#Card" in stylesheet
        assert "QLabel#Title" in stylesheet
        assert "QLabel#Value" in stylesheet
        assert "QProgressBar" in stylesheet
        assert "QToolBar" in stylesheet
        assert "QTabWidget" in stylesheet
        assert "QTableWidget" in stylesheet

    def test_apply_dark_theme_called_multiple_times(self, qapp):
        """Test apply_dark_theme can be called multiple times without errors."""
        from system_monitor.utils.theme import apply_dark_theme
        
        # Should not raise any exceptions
        apply_dark_theme(qapp)
        apply_dark_theme(qapp)
        apply_dark_theme(qapp)
        
        # Verify theme is still applied
        assert qapp.style() is not None
        stylesheet = qapp.styleSheet()
        assert len(stylesheet) > 0
