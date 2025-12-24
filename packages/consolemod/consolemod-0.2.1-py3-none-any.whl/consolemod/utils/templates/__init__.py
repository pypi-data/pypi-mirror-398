"""Template system for common UI patterns"""
from .logger import LoggerTemplate
from .dashboard import DashboardTemplate
from .monitor import MonitorTemplate
from .progress import ProgressTemplate
from .table import TableTemplate

__all__ = [
    "LoggerTemplate",
    "DashboardTemplate",
    "MonitorTemplate",
    "ProgressTemplate",
    "TableTemplate",
]

if __name__ == '__main__':
    raise ImportError("This module is for import only and cannot be executed directly.")
