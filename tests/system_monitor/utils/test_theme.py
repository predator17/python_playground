"""Unit tests for system_monitor.utils.theme module."""

import unittest
from unittest.mock import MagicMock, patch

from system_monitor.utils.theme import apply_dark_theme


class TestApplyDarkTheme(unittest.TestCase):
    """Test apply_dark_theme function."""

    def test_apply_dark_theme(self):
        """Test applying dark theme to QApplication."""
        mock_app = MagicMock()
        
        apply_dark_theme(mock_app)
        
        mock_app.setStyle.assert_called_once_with("Fusion")
        mock_app.setPalette.assert_called_once()
        mock_app.setStyleSheet.assert_called_once()

    def test_dark_theme_palette_colors(self):
        """Test that dark theme sets correct palette colors."""
        mock_app = MagicMock()
        
        apply_dark_theme(mock_app)
        
        palette_arg = mock_app.setPalette.call_args[0][0]
        self.assertIsNotNone(palette_arg)

    def test_dark_theme_stylesheet(self):
        """Test that dark theme sets a non-empty stylesheet."""
        mock_app = MagicMock()
        
        apply_dark_theme(mock_app)
        
        stylesheet_arg = mock_app.setStyleSheet.call_args[0][0]
        self.assertIsInstance(stylesheet_arg, str)
        self.assertGreater(len(stylesheet_arg), 0)
        self.assertIn('QWidget', stylesheet_arg)
        self.assertIn('background-color', stylesheet_arg)


if __name__ == '__main__':
    unittest.main()
