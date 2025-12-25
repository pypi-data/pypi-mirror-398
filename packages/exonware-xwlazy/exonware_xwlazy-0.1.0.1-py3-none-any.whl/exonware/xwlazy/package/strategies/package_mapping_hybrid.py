"""
Hybrid Mapping Strategy

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Hybrid mapping strategy - tries both manifest and discovery, uses best match.
"""

from typing import Optional
from ...package.base import AMappingStrategy
from ...package.services.manifest import get_manifest_loader

class HybridMapping(AMappingStrategy):
    """
    Hybrid mapping strategy.
    
    Tries both manifest and discovery, uses the best match.
    If both exist, prefers the one that's more specific.
    """
    
    def __init__(self, package_name: str = 'default'):
        """
        Initialize hybrid mapping strategy.
        
        Args:
            package_name: Package name for isolation
        """
        self._package_name = package_name
        self._discovery = None  # Lazy init
    
    def _get_discovery(self):
        """Get discovery instance (lazy init)."""
        if self._discovery is None:
            from ...package.services.discovery import LazyDiscovery
            self._discovery = LazyDiscovery(self._package_name)
        return self._discovery
    
    def map_import_to_package(self, import_name: str) -> Optional[str]:
        """
        Map import name to package name.
        
        Tries both manifest and discovery, prefers more specific match.
        
        Args:
            import_name: Import name (e.g., 'cv2')
            
        Returns:
            Package name (e.g., 'opencv-python') or None
        """
        # Try manifest first
        loader = get_manifest_loader()
        manifest = loader.get_manifest(self._package_name)
        manifest_package = None
        if manifest:
            manifest_package = manifest.get_dependency(import_name)
        
        # Try discovery
        discovery = self._get_discovery()
        discovery_mapping = discovery.get_import_package_mapping()
        discovery_package = discovery_mapping.get(import_name)
        
        # Prefer manifest if both exist (more explicit)
        if manifest_package:
            return manifest_package
        
        if discovery_package:
            return discovery_package
        
        # Fallback to common mappings
        common_mappings = discovery.COMMON_MAPPINGS
        return common_mappings.get(import_name)
    
    def map_package_to_imports(self, package_name: str) -> list[str]:
        """
        Map package name to possible import names.
        
        Args:
            package_name: Package name (e.g., 'opencv-python')
            
        Returns:
            List of possible import names (e.g., ['cv2'])
        """
        imports = []
        
        # Check discovery mappings
        discovery = self._get_discovery()
        package_mapping = discovery.get_package_import_mapping()
        discovery_imports = package_mapping.get(package_name, [])
        imports.extend(discovery_imports)
        
        # Check manifest (reverse lookup)
        loader = get_manifest_loader()
        manifest = loader.get_manifest(self._package_name)
        if manifest:
            for import_name, pkg in manifest.dependencies.items():
                if pkg.lower() == package_name.lower():
                    if import_name not in imports:
                        imports.append(import_name)
        
        return imports if imports else [package_name]

