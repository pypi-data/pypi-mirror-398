import asyncio
import sys
from typing import Optional, Dict
try:
    import readchar
except ImportError:
    readchar = None

from ..core.events import KeyCode, KeyEvent

class InputHandler:
    """Thread-safe keyboard input handler with async support"""
    
    # Class-level key mapping
    KEY_MAP: Dict[str, KeyCode] = {
        '\x1b[A': KeyCode.UP,
        '\x1b[B': KeyCode.DOWN,
        '\x1b[C': KeyCode.RIGHT,
        '\x1b[D': KeyCode.LEFT,
        '\r': KeyCode.ENTER,
        '\n': KeyCode.ENTER,
        '\x1b': KeyCode.ESC,
        '\t': KeyCode.TAB,
        '\x08': KeyCode.BACKSPACE,
        '\x7f': KeyCode.BACKSPACE,
        '\x1b[3~': KeyCode.DELETE,
        '\x1b[H': KeyCode.HOME,
        '\x1b[F': KeyCode.END,
        '\x1b[5~': KeyCode.PAGE_UP,
        '\x1b[6~': KeyCode.PAGE_DOWN,
        '\x03': KeyCode.CTRL_C,
        '\x04': KeyCode.CTRL_D,
    }
    
    def __init__(self) -> None:
        self.running: bool = False
    
    async def read_key(self) -> Optional[KeyEvent]:
        """Read a single key asynchronously (thread-safe)
        
        Returns:
            KeyEvent if key was read, None otherwise
        """
        if not readchar:
            return None
        
        try:
            # Use thread to avoid blocking async event loop
            key: Optional[str] = await asyncio.to_thread(self._read_raw_key)
            return self._parse_key(key)
        except Exception:
            return None
    
    def _read_raw_key(self) -> Optional[str]:
        """Read raw key from stdin (blocking, runs in thread)
        
        Returns:
            Raw key string or None
        """
        try:
            if sys.platform == 'win32':
                return self._read_win32_key()
            else:
                return readchar.readchar() if readchar else None
        except Exception:
            return None
    
    def _read_win32_key(self) -> Optional[str]:
        """Handle Windows-specific key input (blocking)
        
        Returns:
            Raw key string or None
        """
        try:
            import msvcrt
            if msvcrt.kbhit():
                return msvcrt.getch().decode('utf-8', errors='ignore')
        except Exception:
            pass
        return None
    
    def _parse_key(self, raw: Optional[str]) -> Optional[KeyEvent]:
        """Parse raw key input to KeyEvent
        
        Args:
            raw: Raw key string
            
        Returns:
            KeyEvent if valid key, None otherwise
        """
        if not raw:
            return None
        
        # Check for special key sequences
        if raw in self.KEY_MAP:
            return KeyEvent(key=self.KEY_MAP[raw], raw=raw)
        
        # Handle regular characters
        if len(raw) == 1 and ord(raw) >= 32:
            return KeyEvent(key=KeyCode.ENTER, raw=raw)  # Printable char
        
        return None

if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
