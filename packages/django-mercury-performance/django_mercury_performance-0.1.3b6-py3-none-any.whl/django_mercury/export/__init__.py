"""HTML export functionality for Mercury performance reports."""

from .single import export_html
from .summary import export_summary_html

__all__ = ['export_html', 'export_summary_html']
