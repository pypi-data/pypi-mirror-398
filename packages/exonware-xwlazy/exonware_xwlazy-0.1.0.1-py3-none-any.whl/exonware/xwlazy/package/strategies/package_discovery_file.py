"""
File-Based Discovery Strategy

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

File-based discovery - discovers dependencies from project files.
"""

from pathlib import Path
from typing import Optional, Any
from ...package.base import ADiscoveryStrategy

class FileBasedDiscovery(ADiscoveryStrategy):
    """
    File-based discovery strategy - discovers dependencies from project files.
    
    Reads from pyproject.toml, requirements.txt, setup.py, etc.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize file-based discovery strategy.
        
        Args:
            project_root: Project root directory (auto-detected if None)
        """
        self._project_root = project_root or self._detect_project_root()
    
    def _detect_project_root(self) -> Path:
        """Detect project root directory."""
        import os
        cwd = Path.cwd()
        
        # Look for common project markers
        markers = ['pyproject.toml', 'requirements.txt', 'setup.py', '.git']
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
        Discover dependencies from project files.
        
        Args:
            project_root: Optional project root (uses instance root if None)
            
        Returns:
            Dict mapping import_name -> package_name
        """
        root = Path(project_root) if project_root else self._project_root
        dependencies = {}
        
        # Check pyproject.toml
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib
            except ImportError:
                try:
                    import tomli as tomllib
                except ImportError:
                    tomllib = None
            
            if tomllib:
                with open(pyproject, 'rb') as f:
                    data = tomllib.load(f)
                    project = data.get('project', {})
                    deps = project.get('dependencies', [])
                    for dep in deps:
                        # Parse dependency spec (e.g., "pandas>=1.0" -> "pandas")
                        package_name = dep.split('>=')[0].split('==')[0].split('!=')[0].strip()
                        # Use package name as import name (heuristic)
                        import_name = package_name.replace('-', '_')
                        dependencies[import_name] = package_name
        
        # Check requirements.txt
        requirements = root / "requirements.txt"
        if requirements.exists():
            with open(requirements, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Parse requirement (e.g., "pandas>=1.0" -> "pandas")
                        package_name = line.split('>=')[0].split('==')[0].split('!=')[0].strip()
                        import_name = package_name.replace('-', '_')
                        dependencies[import_name] = package_name
        
        return dependencies
    
    def get_source(self, import_name: str) -> Optional[str]:
        """
        Get the source of a discovered dependency.
        
        Args:
            import_name: Import name to check
            
        Returns:
            Source file name or None
        """
        root = self._project_root
        
        # Check pyproject.toml
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            deps = self.discover()
            if import_name in deps:
                return "pyproject.toml"
        
        # Check requirements.txt
        requirements = root / "requirements.txt"
        if requirements.exists():
            deps = self.discover()
            if import_name in deps:
                return "requirements.txt"
        
        return None

