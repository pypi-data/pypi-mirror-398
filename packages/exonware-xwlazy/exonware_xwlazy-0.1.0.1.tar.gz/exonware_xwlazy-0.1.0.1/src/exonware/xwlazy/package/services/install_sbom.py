"""
SBOM and Audit Mixin

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Mixin for SBOM generation and vulnerability auditing.
"""

import json
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import

from .install_policy import LazyInstallPolicy

# Lazy imports
def _get_logger():
    """Get logger (lazy import to avoid circular dependency)."""
    from ...common.logger import get_logger
    return get_logger("xwlazy.lazy_installer")

def _get_log_event():
    """Get log_event function (lazy import to avoid circular dependency)."""
    from ...common.logger import log_event
    return log_event

logger = None
_log = None

def _ensure_logging_initialized():
    """Ensure logging utilities are initialized."""
    global logger, _log
    if logger is None:
        logger = _get_logger()
    if _log is None:
        _log = _get_log_event()

class SBOMAuditMixin:
    """Mixin for SBOM generation and vulnerability auditing."""
    
    def _run_vulnerability_audit(self, package_name: str) -> None:
        """Run vulnerability audit on installed package using pip-audit."""
        _ensure_logging_initialized()
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip_audit', '-r', '-', '--format', 'json'],
                input=package_name,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                _log("audit", f"Vulnerability audit passed for {package_name}")
            else:
                try:
                    audit_data = json.loads(result.stdout)
                    if audit_data.get('vulnerabilities'):
                        logger.warning(f"[SECURITY] Vulnerabilities found in {package_name}: {audit_data}")
                        print(f"[SECURITY WARNING] Package '{package_name}' has known vulnerabilities")
                        print(f"Run 'pip-audit' for details")
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse audit results for {package_name}")
        except subprocess.TimeoutExpired:
            logger.warning(f"Vulnerability audit timed out for {package_name}")
        except Exception as e:
            logger.debug(f"Vulnerability audit skipped for {package_name}: {e}")
    
    def _update_lockfile(self, package_name: str) -> None:
        """Update lockfile with newly installed package."""
        _ensure_logging_initialized()
        lockfile_path = LazyInstallPolicy.get_lockfile_path(self._package_name)  # type: ignore[attr-defined]
        if not lockfile_path:
            return
        
        try:
            version = self._get_installed_version(package_name)  # type: ignore[attr-defined]
            if not version:
                return
            
            lockfile_path = Path(lockfile_path)
            if lockfile_path.exists():
                with open(lockfile_path, 'r', encoding='utf-8') as f:
                    lockdata = json.load(f)
            else:
                lockdata = {
                    "metadata": {
                        "generated_by": f"xwlazy-{self._package_name}",  # type: ignore[attr-defined]
                        "version": "1.0"
                    },
                    "packages": {}
                }
            
            lockdata["packages"][package_name] = {
                "version": version,
                "installed_at": datetime.now().isoformat(),
                "installer": self._package_name  # type: ignore[attr-defined]
            }
            
            lockfile_path.parent.mkdir(parents=True, exist_ok=True)
            with open(lockfile_path, 'w', encoding='utf-8') as f:
                json.dump(lockdata, f, indent=2)
            
            _log("sbom", f"Updated lockfile: {lockfile_path}")
        except Exception as e:
            logger.warning(f"Failed to update lockfile: {e}")
    
    def generate_sbom(self) -> Dict:
        """Generate Software Bill of Materials (SBOM) for installed packages."""
        sbom = {
            "metadata": {
                "format": "xwlazy-sbom",
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "installer_package": self._package_name  # type: ignore[attr-defined]
            },
            "packages": []
        }
        
        for pkg in self._installed_packages:  # type: ignore[attr-defined]
            version = self._get_installed_version(pkg)  # type: ignore[attr-defined]
            sbom["packages"].append({
                "name": pkg,
                "version": version or "unknown",
                "installed_by": self._package_name,  # type: ignore[attr-defined]
                "source": "pypi"
            })
        
        return sbom
    
    def export_sbom(self, output_path: str) -> bool:
        """Export SBOM to file."""
        _ensure_logging_initialized()
        try:
            sbom = self.generate_sbom()
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(sbom, f, indent=2)
            
            _log("sbom", f"Exported SBOM to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export SBOM: {e}")
            return False

