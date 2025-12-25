"""
Manifest-Based Discovery Strategy

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Manifest-based discovery - discovers dependencies from manifest files.
"""

from pathlib import Path
from typing import Optional, Any
from ...package.base import ADiscoveryStrategy

class ManifestBasedDiscovery(ADiscoveryStrategy):
    """
    Manifest-based discovery strategy - discovers dependencies from manifest files.
    
    Reads from xwlazy.manifest.json or pyproject.toml [tool.xwlazy] section.
    """
    
    def __init__(self, package_name: str = 'default', project_root: Optional[Path] = None):
        """
        Initialize manifest-based discovery strategy.
        
        Args:
            package_name: Package name for isolation
            project_root: Project root directory (auto-detected if None)
        """
        self._package_name = package_name
        self._project_root = project_root or self._detect_project_root()
    
    def _detect_project_root(self) -> Path:
        """Detect project root directory."""
        import os
        cwd = Path.cwd()
        
        # Look for manifest files
        markers = ['xwlazy.manifest.json', 'lazy.manifest.json', '.xwlazy.manifest.json', 'pyproject.toml']
        for marker in markers:
            current = cwd
            for _ in range(5):  # Search up to 5 levels
                if (current / marker).exists():
                    return current
                parent = current.parent
                if parent == current:  # Reached filesystem root
                    break
                current = parent
        
        return cwd
    
    def discover(self, project_root: Any = None) -> dict[str, str]:
        """
        Discover dependencies from manifest files.
        
        Args:
            project_root: Optional project root (uses instance root if None)
            
        Returns:
            Dict mapping import_name -> package_name
        """
        # Lazy import to avoid circular dependency
        from ...package.manifest import get_manifest_loader
        
        loader = get_manifest_loader()
        manifest = loader.get_manifest(self._package_name)
        
        if manifest and manifest.dependencies:
            return manifest.dependencies.copy()
        
        return {}
    
    def get_source(self, import_name: str) -> Optional[str]:
        """
        Get the source of a discovered dependency.
        
        Args:
            import_name: Import name to check
            
        Returns:
            Source file name (e.g., "xwlazy.manifest.json")
        """
        from ...package.manifest import get_manifest_loader
        
        loader = get_manifest_loader()
        manifest = loader.get_manifest(self._package_name)
        
        if manifest and manifest.dependencies and import_name in manifest.dependencies:
            # Try to find which file was used
            root = self._project_root
            for filename in ['xwlazy.manifest.json', 'lazy.manifest.json', '.xwlazy.manifest.json']:
                if (root / filename).exists():
                    return filename
            # Check pyproject.toml
            if (root / "pyproject.toml").exists():
                return "pyproject.toml [tool.xwlazy]"
        
        return None

