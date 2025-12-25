"""
Hybrid Discovery Strategy

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Hybrid discovery - combines file-based and manifest-based discovery.
"""

from pathlib import Path
from typing import Optional, Any
from ...package.base import ADiscoveryStrategy
from .package_discovery_file import FileBasedDiscovery
from .package_discovery_manifest import ManifestBasedDiscovery

class HybridDiscovery(ADiscoveryStrategy):
    """
    Hybrid discovery strategy - combines file-based and manifest-based discovery.
    
    Priority: Manifest > File-based
    """
    
    def __init__(self, package_name: str = 'default', project_root: Optional[Path] = None):
        """
        Initialize hybrid discovery strategy.
        
        Args:
            package_name: Package name for isolation
            project_root: Project root directory (auto-detected if None)
        """
        self._package_name = package_name
        self._project_root = project_root
        self._file_discovery = FileBasedDiscovery(project_root)
        self._manifest_discovery = ManifestBasedDiscovery(package_name, project_root)
    
    def discover(self, project_root: Any = None) -> dict[str, str]:
        """
        Discover dependencies from all sources.
        
        Priority: Manifest > File-based
        
        Args:
            project_root: Optional project root (uses instance root if None)
            
        Returns:
            Dict mapping import_name -> package_name
        """
        dependencies = {}
        
        # First, get file-based dependencies
        file_deps = self._file_discovery.discover(project_root)
        dependencies.update(file_deps)
        
        # Then, overlay manifest dependencies (takes precedence)
        manifest_deps = self._manifest_discovery.discover(project_root)
        dependencies.update(manifest_deps)  # Manifest overrides file-based
        
        return dependencies
    
    def get_source(self, import_name: str) -> Optional[str]:
        """
        Get the source of a discovered dependency.
        
        Args:
            import_name: Import name to check
            
        Returns:
            Source file name or "hybrid"
        """
        # Check manifest first (higher priority)
        manifest_source = self._manifest_discovery.get_source(import_name)
        if manifest_source:
            return manifest_source
        
        # Check file-based
        file_source = self._file_discovery.get_source(import_name)
        if file_source:
            return file_source
        
        return None

