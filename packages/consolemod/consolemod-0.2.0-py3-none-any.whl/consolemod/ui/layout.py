from enum import Enum
from typing import List, Optional, Tuple
from dataclasses import dataclass
import threading


class LayoutMode(Enum):
    """Layout arrangement modes"""
    VERTICAL = "vertical"      # Stack panes vertically (top to bottom)
    HORIZONTAL = "horizontal"  # Stack panes horizontally (left to right)
    GRID = "grid"              # Arrange in grid


@dataclass
class LayoutConstraints:
    """Constraints for pane layout"""
    min_width: int = 20
    min_height: int = 5
    weight: float = 1.0  # Relative size weight in layout


class Layout:
    """Thread-safe layout manager for pane arrangement"""
    
    def __init__(self, mode: LayoutMode = LayoutMode.VERTICAL) -> None:
        self.mode: LayoutMode = mode
        self.constraints: dict[str, LayoutConstraints] = {}
        self.lock: threading.RLock = threading.RLock()
    
    def set_mode(self, mode: LayoutMode) -> None:
        """Set layout mode (thread-safe)
        
        Args:
            mode: LayoutMode to use
        """
        with self.lock:
            self.mode = mode
    
    def set_constraints(self, pane_id: str, constraints: LayoutConstraints) -> None:
        """Set layout constraints for a pane (thread-safe)
        
        Args:
            pane_id: ID of pane
            constraints: LayoutConstraints to apply
        """
        with self.lock:
            self.constraints[pane_id] = constraints
    
    def get_constraints(self, pane_id: str) -> LayoutConstraints:
        """Get layout constraints for a pane (thread-safe)
        
        Args:
            pane_id: ID of pane
            
        Returns:
            LayoutConstraints or default
        """
        with self.lock:
            return self.constraints.get(pane_id, LayoutConstraints())
    
    def calculate_layout(
        self,
        pane_ids: List[str],
        total_width: int,
        total_height: int
    ) -> dict[str, Tuple[int, int, int, int]]:
        """Calculate pane positions and sizes
        
        Args:
            pane_ids: List of pane IDs
            total_width: Total available width
            total_height: Total available height
            
        Returns:
            Dict mapping pane_id to (x, y, width, height)
        """
        with self.lock:
            mode = self.mode
        
        if not pane_ids:
            return {}
        
        result: dict[str, Tuple[int, int, int, int]] = {}
        
        if mode == LayoutMode.VERTICAL:
            return self._calculate_vertical(pane_ids, total_width, total_height)
        elif mode == LayoutMode.HORIZONTAL:
            return self._calculate_horizontal(pane_ids, total_width, total_height)
        elif mode == LayoutMode.GRID:
            return self._calculate_grid(pane_ids, total_width, total_height)
        
        return result
    
    def _calculate_vertical(
        self,
        pane_ids: List[str],
        total_width: int,
        total_height: int
    ) -> dict[str, Tuple[int, int, int, int]]:
        """Calculate vertical stacking layout"""
        result: dict[str, Tuple[int, int, int, int]] = {}
        
        # Get weights for each pane
        weights = [self.constraints.get(pid, LayoutConstraints()).weight for pid in pane_ids]
        total_weight = sum(weights)
        
        y = 0
        for pane_id, weight in zip(pane_ids, weights):
            height = max(
                self.constraints.get(pane_id, LayoutConstraints()).min_height,
                int(total_height * weight / total_weight)
            )
            result[pane_id] = (0, y, total_width, height)
            y += height
        
        return result
    
    def _calculate_horizontal(
        self,
        pane_ids: List[str],
        total_width: int,
        total_height: int
    ) -> dict[str, Tuple[int, int, int, int]]:
        """Calculate horizontal stacking layout"""
        result: dict[str, Tuple[int, int, int, int]] = {}
        
        # Get weights for each pane
        weights = [self.constraints.get(pid, LayoutConstraints()).weight for pid in pane_ids]
        total_weight = sum(weights)
        
        x = 0
        for pane_id, weight in zip(pane_ids, weights):
            width = max(
                self.constraints.get(pane_id, LayoutConstraints()).min_width,
                int(total_width * weight / total_weight)
            )
            result[pane_id] = (x, 0, width, total_height)
            x += width
        
        return result
    
    def _calculate_grid(
        self,
        pane_ids: List[str],
        total_width: int,
        total_height: int
    ) -> dict[str, Tuple[int, int, int, int]]:
        """Calculate grid layout (auto-arrange in columns)"""
        result: dict[str, Tuple[int, int, int, int]] = {}
        
        if not pane_ids:
            return result
        
        # Calculate grid dimensions
        cols = max(1, int(len(pane_ids) ** 0.5))
        rows = (len(pane_ids) + cols - 1) // cols
        
        pane_width = total_width // cols
        pane_height = total_height // rows
        
        for idx, pane_id in enumerate(pane_ids):
            col = idx % cols
            row = idx // cols
            x = col * pane_width
            y = row * pane_height
            result[pane_id] = (x, y, pane_width, pane_height)
        
        return result


if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
