from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class Style:
    """Style definition for UI elements"""
    color: str = "white"
    bgcolor: str = "default"
    bold: bool = False
    italic: bool = False
    underline: bool = False
    dim: bool = False
    
    def __str__(self) -> str:
        """String representation for debugging"""
        return f"Style(color={self.color}, bgcolor={self.bgcolor}, bold={self.bold})"

@dataclass
class Theme:
    """Theme definition with styles for different elements"""
    name: str
    pane_border: Style
    pane_title: Style
    pane_content: Style
    pane_focus: Style
    pane_blur: Style
    status_bar: Style
    cursor: Style
    
    def __str__(self) -> str:
        """String representation for debugging"""
        return f"Theme(name={self.name})"

# Pre-built themes
DARK_THEME = Theme(
    name="dark",
    pane_border=Style(color="cyan"),
    pane_title=Style(color="white", bold=True),
    pane_content=Style(color="white"),
    pane_focus=Style(color="yellow", bold=True),
    pane_blur=Style(color="gray50"),
    status_bar=Style(color="white", bgcolor="blue"),
    cursor=Style(color="black", bgcolor="white", bold=True)
)

LIGHT_THEME = Theme(
    name="light",
    pane_border=Style(color="blue"),
    pane_title=Style(color="black", bold=True),
    pane_content=Style(color="black"),
    pane_focus=Style(color="red", bold=True),
    pane_blur=Style(color="gray70"),
    status_bar=Style(color="black", bgcolor="white"),
    cursor=Style(color="white", bgcolor="black", bold=True)
)

SOLARIZED_THEME = Theme(
    name="solarized",
    pane_border=Style(color="bright_blue"),
    pane_title=Style(color="bright_yellow", bold=True),
    pane_content=Style(color="bright_white"),
    pane_focus=Style(color="bright_green", bold=True),
    pane_blur=Style(color="bright_black"),
    status_bar=Style(color="bright_white", bgcolor="bright_blue"),
    cursor=Style(color="bright_black", bgcolor="bright_cyan")
)

THEMES: Dict[str, Theme] = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
    "solarized": SOLARIZED_THEME,
}

def get_theme(name: str = "dark") -> Theme:
    """Get theme by name, default to dark
    
    Args:
        name: Theme name (dark, light, solarized)
        
    Returns:
        Theme object
    """
    return THEMES.get(name, DARK_THEME)

def style_to_rich(style: Style) -> str:
    """Convert Style to Rich style string (thread-safe)
    
    Args:
        style: Style object
        
    Returns:
        Rich style string
    """
    parts: list[str] = []
    if style.color != "default":
        parts.append(style.color)
    if style.bgcolor != "default":
        parts.append(f"on {style.bgcolor}")
    if style.bold:
        parts.append("bold")
    if style.italic:
        parts.append("italic")
    if style.underline:
        parts.append("underline")
    if style.dim:
        parts.append("dim")
    return " ".join(parts) if parts else "default"

def register_theme(name: str, theme: Theme) -> None:
    """Register a custom theme (thread-safe)
    
    Args:
        name: Theme name
        theme: Theme object
    """
    THEMES[name] = theme

if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
