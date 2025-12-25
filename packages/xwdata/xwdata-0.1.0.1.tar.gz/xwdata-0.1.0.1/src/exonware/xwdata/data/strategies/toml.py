#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/data/strategies/toml.py

TOML Format Strategy

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 15-Nov-2025
"""

from typing import Any, Optional
from pathlib import Path

try:
    import tomli
    import tomli_w
    TOML_AVAILABLE = True
except ImportError:
    try:
        import toml
        TOML_AVAILABLE = True
        tomli = toml
        tomli_w = toml
    except ImportError:
        TOML_AVAILABLE = False
        tomli = None
        tomli_w = None

from ...base import AFormatStrategy
from ...errors import XWDataStrategyError


class TOMLFormatStrategy(AFormatStrategy):
    """
    TOML format strategy.
    
    Supports TOML (Tom's Obvious Minimal Language) format.
    """
    
    def __init__(self):
        """Initialize TOML format strategy."""
        super().__init__()
        self._name = 'toml'
        self._extensions = ['toml']
        
        if not TOML_AVAILABLE:
            # Don't raise - allow lazy loading
            pass
    
    @property
    def name(self) -> str:
        """Format name."""
        return self._name
    
    @property
    def extensions(self) -> list[str]:
        """Supported file extensions."""
        return [f".{ext}" for ext in self._extensions]
    
    @property
    def mime_types(self) -> list[str]:
        """Supported MIME types."""
        return ["application/toml"]
    
    def can_handle(self, path: Optional[Path] = None, mime_type: Optional[str] = None) -> bool:
        """Check if this strategy can handle the given path or MIME type."""
        if path:
            return path.suffix.lower() == ".toml"
        if mime_type:
            return mime_type.lower() in self.mime_types
        return False
    
    async def load(self, path: Path) -> Any:
        """
        Load TOML file.
        
        Args:
            path: Path to TOML file
            
        Returns:
            Loaded data (dict)
            
        Raises:
            XWDataStrategyError: If loading fails
        """
        if not TOML_AVAILABLE:
            raise XWDataStrategyError("TOML library not available")
        
        try:
            toml_data = path.read_bytes()
            if hasattr(tomli, 'loads'):
                return tomli.loads(toml_data.decode('utf-8'))
            else:
                return tomli.load(toml_data.decode('utf-8'))
        except Exception as e:
            raise XWDataStrategyError(f"Failed to load TOML file: {e}") from e
    
    async def save(self, data: Any, path: Path) -> None:
        """
        Save data to TOML file.
        
        Args:
            data: Data to save (dict)
            path: Path to output file
            
        Raises:
            XWDataStrategyError: If saving fails
        """
        if not TOML_AVAILABLE:
            raise XWDataStrategyError("TOML library not available")
        
        try:
            if hasattr(tomli_w, 'dumps'):
                toml_str = tomli_w.dumps(data)
            else:
                toml_str = tomli_w.dump(data)
            path.write_text(toml_str, encoding='utf-8')
        except Exception as e:
            raise XWDataStrategyError(f"Failed to save TOML file: {e}") from e
    
    async def parse(self, content: str) -> Any:
        """
        Parse TOML content.
        
        Args:
            content: TOML content string
            
        Returns:
            Parsed data (dict)
        """
        if not TOML_AVAILABLE:
            raise XWDataStrategyError("TOML library not available")
        
        try:
            if hasattr(tomli, 'loads'):
                return tomli.loads(content)
            else:
                return tomli.load(content)
        except Exception as e:
            raise XWDataStrategyError(f"Failed to parse TOML: {e}") from e
    
    async def serialize(self, data: Any) -> str:
        """
        Serialize data to TOML.
        
        Args:
            data: Data to serialize (dict)
            
        Returns:
            TOML string
        """
        if not TOML_AVAILABLE:
            raise XWDataStrategyError("TOML library not available")
        
        try:
            if hasattr(tomli_w, 'dumps'):
                return tomli_w.dumps(data)
            else:
                return tomli_w.dump(data)
        except Exception as e:
            raise XWDataStrategyError(f"Failed to serialize TOML: {e}") from e

