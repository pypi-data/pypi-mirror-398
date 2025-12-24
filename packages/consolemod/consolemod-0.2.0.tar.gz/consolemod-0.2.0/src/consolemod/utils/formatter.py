from typing import Optional, List, Tuple
from enum import Enum


class TextAlign(Enum):
    """Text alignment options"""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


def wrap_text(text: str, width: int) -> List[str]:
    """Wrap text to specified width (thread-safe)
    
    Args:
        text: Text to wrap
        width: Width in characters
        
    Returns:
        List of wrapped lines
    """
    if width <= 0:
        return []
    
    lines = text.split('\n')
    wrapped = []
    
    for line in lines:
        if not line:
            wrapped.append("")
            continue
        
        # Simple word wrapping
        words = line.split()
        current_line = ""
        
        for word in words:
            if not current_line:
                current_line = word
            elif len(current_line) + 1 + len(word) <= width:
                current_line += " " + word
            else:
                if current_line:
                    wrapped.append(current_line)
                current_line = word
        
        if current_line:
            wrapped.append(current_line)
    
    return wrapped


def align_text(text: str, width: int, align: TextAlign = TextAlign.LEFT) -> str:
    """Align text within width (thread-safe)
    
    Args:
        text: Text to align
        width: Width in characters
        align: Alignment option
        
    Returns:
        Aligned text
    """
    text_width = len(text)
    
    if text_width >= width:
        return text[:width]
    
    padding = width - text_width
    
    if align == TextAlign.LEFT:
        return text + " " * padding
    elif align == TextAlign.RIGHT:
        return " " * padding + text
    elif align == TextAlign.CENTER:
        left_pad = padding // 2
        right_pad = padding - left_pad
        return " " * left_pad + text + " " * right_pad
    
    return text


def truncate_text(text: str, max_length: int, suffix: str = "..") -> str:
    """Truncate text to max length (thread-safe)
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    truncated_length = max_length - len(suffix)
    if truncated_length < 0:
        return text[:max_length]
    
    return text[:truncated_length] + suffix


def highlight_text(text: str, search: str, color: str = "yellow") -> str:
    """Highlight search term in text (simple version, thread-safe)
    
    Args:
        text: Text to highlight in
        search: Term to highlight
        color: Color for highlighting
        
    Returns:
        Text with highlighting markup
    """
    if not search or not text:
        return text
    
    # Simple case-insensitive highlighting
    lower_text = text.lower()
    lower_search = search.lower()
    result = ""
    pos = 0
    
    while True:
        idx = lower_text.find(lower_search, pos)
        if idx == -1:
            result += text[pos:]
            break
        
        result += text[pos:idx]
        result += f"[{color}]{text[idx:idx+len(search)]}[/{color}]"
        pos = idx + len(search)
    
    return result


def format_bytes(num_bytes: int) -> str:
    """Format bytes as human-readable string (thread-safe)
    
    Args:
        num_bytes: Number of bytes
        
    Returns:
        Formatted string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    
    return f"{num_bytes:.1f} PB"


def format_duration(seconds: float) -> str:
    """Format duration as human-readable string (thread-safe)
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"


def create_box(text: str, style: str = "single") -> str:
    """Create a box around text (thread-safe)
    
    Args:
        text: Text to box
        style: Box style (single, double)
        
    Returns:
        Boxed text
    """
    if style == "double":
        top_left = "╔"
        top_right = "╗"
        bottom_left = "╚"
        bottom_right = "╝"
        horizontal = "═"
        vertical = "║"
    else:  # single
        top_left = "┌"
        top_right = "┐"
        bottom_left = "└"
        bottom_right = "┘"
        horizontal = "─"
        vertical = "│"
    
    lines = text.split('\n')
    max_width = max(len(line) for line in lines) if lines else 0
    
    result = []
    result.append(top_left + horizontal * (max_width + 2) + top_right)
    
    for line in lines:
        padded = line.ljust(max_width)
        result.append(vertical + " " + padded + " " + vertical)
    
    result.append(bottom_left + horizontal * (max_width + 2) + bottom_right)
    
    return "\n".join(result)


if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
