import json
from typing import List, Tuple, Optional
from pathlib import Path
import threading


class PaneExporter:
    """Thread-safe pane content export/import"""
    
    def __init__(self) -> None:
        """Initialize exporter"""
        self.lock: threading.RLock = threading.RLock()
    
    def export_text(self, content: List[Tuple[str, str]], filepath: str) -> bool:
        """Export pane content as plain text (thread-safe)
        
        Args:
            content: List of (message, style) tuples
            filepath: Path to write to
            
        Returns:
            True if successful
        """
        try:
            with self.lock:
                with open(filepath, 'w', encoding='utf-8') as f:
                    for message, _ in content:
                        f.write(message + '\n')
            return True
        except Exception:
            return False
    
    def export_json(self, content: List[Tuple[str, str]], filepath: str) -> bool:
        """Export pane content as JSON with styling (thread-safe)
        
        Args:
            content: List of (message, style) tuples
            filepath: Path to write to
            
        Returns:
            True if successful
        """
        try:
            with self.lock:
                data = {
                    "messages": [
                        {"text": message, "style": style}
                        for message, style in content
                    ]
                }
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def export_csv(self, content: List[Tuple[str, str]], filepath: str) -> bool:
        """Export pane content as CSV (thread-safe)
        
        Args:
            content: List of (message, style) tuples
            filepath: Path to write to
            
        Returns:
            True if successful
        """
        try:
            import csv
            with self.lock:
                with open(filepath, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Message', 'Style'])
                    for message, style in content:
                        writer.writerow([message, style])
            return True
        except Exception:
            return False
    
    def export_html(self, content: List[Tuple[str, str]], filepath: str, title: str = "Pane Export") -> bool:
        """Export pane content as HTML (thread-safe)
        
        Args:
            content: List of (message, style) tuples
            filepath: Path to write to
            title: HTML title
            
        Returns:
            True if successful
        """
        try:
            with self.lock:
                html = self._build_html(content, title)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html)
            return True
        except Exception:
            return False
    
    def _build_html(self, content: List[Tuple[str, str]], title: str) -> str:
        """Build HTML document
        
        Args:
            content: List of (message, style) tuples
            title: Document title
            
        Returns:
            HTML string
        """
        style_map = {
            'green': '#90ee90',
            'red': '#ff6b6b',
            'yellow': '#ffd700',
            'cyan': '#00ffff',
            'blue': '#6495ed',
            'white': '#ffffff',
            'gray': '#808080',
        }
        
        lines = ['<!DOCTYPE html>', '<html>', '<head>']
        lines.append(f'<title>{title}</title>')
        lines.append('<meta charset="utf-8">')
        lines.append('<style>')
        lines.append('body { font-family: monospace; background: #1e1e1e; color: #d4d4d4; }')
        lines.append('.line { white-space: pre-wrap; word-wrap: break-word; }')
        for style, color in style_map.items():
            lines.append(f'.{style} {{ color: {color}; }}')
        lines.append('</style>')
        lines.append('</head>')
        lines.append('<body>')
        lines.append('<pre>')
        
        for message, style in content:
            safe_msg = self._escape_html(message)
            if style in style_map:
                lines.append(f'<span class="{style}">{safe_msg}</span>')
            else:
                lines.append(safe_msg)
            lines.append('\n')
        
        lines.append('</pre>')
        lines.append('</body>')
        lines.append('</html>')
        
        return '\n'.join(lines)
    
    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text
        """
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    def import_text(self, filepath: str) -> List[Tuple[str, str]]:
        """Import text file as pane content (thread-safe)
        
        Args:
            filepath: Path to read from
            
        Returns:
            List of (message, style) tuples
        """
        try:
            with self.lock:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return [(line.rstrip('\n'), 'white') for line in f.readlines()]
        except Exception:
            return []
    
    def import_json(self, filepath: str) -> List[Tuple[str, str]]:
        """Import JSON file with styling (thread-safe)
        
        Args:
            filepath: Path to read from
            
        Returns:
            List of (message, style) tuples
        """
        try:
            with self.lock:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [
                        (msg['text'], msg.get('style', 'white'))
                        for msg in data.get('messages', [])
                    ]
        except Exception:
            return []


if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
