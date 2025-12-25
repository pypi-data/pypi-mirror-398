"""
Interactive Installation Mixin

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Mixin for interactive user prompts during installation.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .lazy_installer import LazyInstaller

class InteractiveInstallMixin:
    """Mixin for interactive user prompts during installation."""
    
    def _ask_user_permission(self, package_name: str, module_name: str) -> bool:
        """Ask user for permission to install a package."""
        if self._auto_approve_all:  # type: ignore[attr-defined]
            return True
        
        print(f"\n{'='*60}")
        print(f"Lazy Installation Active - {self._package_name}")  # type: ignore[attr-defined]
        print(f"{'='*60}")
        print(f"Package: {package_name}")
        print(f"Module:  {module_name}")
        print(f"{'='*60}")
        print(f"\nThe module '{module_name}' is not installed.")
        print(f"Would you like to install '{package_name}'?")
        print(f"\nOptions:")
        print(f"  [Y] Yes - Install this package")
        print(f"  [N] No  - Skip this package")
        print(f"  [A] All - Install this and all future packages without asking")
        print(f"  [Q] Quit - Cancel and raise ImportError")
        print(f"{'='*60}")
        
        while True:
            try:
                choice = input("Your choice [Y/N/A/Q]: ").strip().upper()
                
                if choice in ('Y', 'YES', ''):
                    return True
                elif choice in ('N', 'NO'):
                    return False
                elif choice in ('A', 'ALL'):
                    self._auto_approve_all = True  # type: ignore[attr-defined]
                    return True
                elif choice in ('Q', 'QUIT'):
                    raise KeyboardInterrupt("User cancelled installation")
                else:
                    print(f"Invalid choice '{choice}'. Please enter Y, N, A, or Q.")
            except (EOFError, KeyboardInterrupt):
                print("\n❌ Installation cancelled by user")
                return False

