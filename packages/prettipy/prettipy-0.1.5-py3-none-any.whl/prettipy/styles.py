"""
PDF styling and theme management.

This module defines PDF styles, themes, and layout configurations
for the generated documents.
"""

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path
from typing import Dict, Tuple, Optional
import platform


class StyleManager:
    """Manages PDF styles and themes."""

    # Common monospace fonts by platform
    MONOSPACE_FONTS = {
        "darwin": [  # macOS
            "~/Library/Fonts/FiraCodeNerdFontMono-Regular.ttf",
            "/Library/Fonts/Courier New.ttf",
            "/System/Library/Fonts/Monaco.ttf",
        ],
        "linux": [
            "~/.local/share/fonts/FiraCode-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        ],
        "win32": [
            "C:\\Windows\\Fonts\\FiraCode-Regular.ttf",
            "C:\\Windows\\Fonts\\consola.ttf",
            "C:\\Windows\\Fonts\\cour.ttf",
        ],
    }

    def __init__(self, theme: str = "default"):
        """
        Initialize the style manager.

        Args:
            theme: Theme name (currently only 'default' supported)
        """
        self.theme = theme
        self.base_styles = getSampleStyleSheet()
        self.font_name = self._register_monospace_font()
        self._init_custom_styles()

    def _register_monospace_font(self) -> str:
        """
        Register a monospace font for code display.

        Returns:
            Name of the registered font
        """
        system = platform.system().lower()
        font_paths = self.MONOSPACE_FONTS.get(
            "darwin" if system == "darwin" else "linux" if "linux" in system else "win32", []
        )

        # Try to register fonts in order of preference
        for font_path in font_paths:
            expanded_path = Path(font_path).expanduser()
            if expanded_path.exists():
                try:
                    pdfmetrics.registerFont(TTFont("CodeFont", str(expanded_path)))
                    return "CodeFont"
                except Exception:
                    continue

        # Fallback to Courier
        return "Courier"

    def _init_custom_styles(self):
        """Initialize all custom paragraph styles."""
        self.title_style = ParagraphStyle(
            "CustomTitle",
            parent=self.base_styles["Heading1"],
            fontSize=24,
            textColor=HexColor("#1a1a1a"),
            spaceAfter=12,
            fontName="Helvetica-Bold",
        )

        self.file_header_style = ParagraphStyle(
            "FileHeader",
            parent=self.base_styles["Heading2"],
            fontSize=12,
            textColor=HexColor("#0066cc"),
            spaceAfter=20,
            spaceBefore=12,
            fontName="Helvetica-Bold",
        )

        self.code_container_style = ParagraphStyle(
            "CodeContainer",
            fontName=self.font_name,
            fontSize=9,
            leading=14,
            leftIndent=0,
            rightIndent=0,
            spaceBefore=0,
            spaceAfter=10,
            backColor=HexColor("#f8f8f8"),
            borderColor=HexColor("#e0e0e0"),
            borderWidth=1,
            borderPadding=12,
            alignment=TA_LEFT,
        )

        self.info_style = ParagraphStyle(
            "InfoStyle",
            parent=self.base_styles["Normal"],
            fontSize=10,
            textColor=HexColor("#333333"),
            spaceAfter=6,
        )

        self.error_style = ParagraphStyle(
            "ErrorStyle",
            parent=self.base_styles["Normal"],
            fontSize=10,
            textColor=HexColor("#cc0000"),
            fontName="Helvetica-Oblique",
        )

        self.tree_style = ParagraphStyle(
            "TreeStyle",
            fontName=self.font_name,
            fontSize=9,
            leading=14,
            leftIndent=12,
            rightIndent=0,
            spaceBefore=12,
            spaceAfter=12,
            backColor=HexColor("#f8f8f8"),
            borderColor=HexColor("#e0e0e0"),
            borderWidth=1,
            borderPadding=12,
            alignment=TA_LEFT,
        )

    def get_page_margins(self) -> Tuple[float, float, float, float]:
        """
        Get page margins.

        Returns:
            Tuple of (top, bottom, left, right) margins in points
        """
        return (0.75 * inch, 0.75 * inch, 0.75 * inch, 0.75 * inch)

    def get_styles(self) -> Dict[str, ParagraphStyle]:
        """
        Get all custom styles as a dictionary.

        Returns:
            Dictionary mapping style names to ParagraphStyle objects
        """
        return {
            "title": self.title_style,
            "file_header": self.file_header_style,
            "code": self.code_container_style,
            "info": self.info_style,
            "error": self.error_style,
            "tree": self.tree_style,
        }
