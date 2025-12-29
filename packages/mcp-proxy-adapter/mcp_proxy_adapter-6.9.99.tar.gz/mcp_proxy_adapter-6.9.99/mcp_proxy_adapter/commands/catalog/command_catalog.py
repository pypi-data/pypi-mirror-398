"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Command catalog data model for MCP Proxy Adapter.
"""

from typing import Dict, List, Optional, Any


class CommandCatalog:
    """
    Represents a command in the catalog with metadata.
    """

    def __init__(
        self, name: str, version: str, source_url: str, file_path: Optional[str] = None
    ):
        """
        Initialize command catalog entry.

        Args:
            name: Command name
            version: Command version
            source_url: Source URL for the command
            file_path: Local file path (optional)
        """
        self.name = name
        self.version = version
        self.source_url = source_url
        self.file_path = file_path
        self.metadata: Dict[str, Any] = {}

        # Standard metadata fields
        self.plugin: Optional[str] = None
        self.descr: Optional[str] = None
        self.category: Optional[str] = None
        self.author: Optional[str] = None
        self.email: Optional[str] = None
        self.depends: Optional[List[str]] = None  # New field for dependencies

