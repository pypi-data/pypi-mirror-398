"""
Auto-update functionality for Claux.

Provides version checking and update capabilities using PyPI API.
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
from urllib.request import Request, urlopen
from urllib.error import URLError

from claux import __version__


class UpdateChecker:
    """Check for package updates using PyPI JSON API."""

    PYPI_JSON_URL = "https://pypi.org/pypi/{package}/json"
    CACHE_FILE = Path.home() / ".claux" / "update_cache.json"
    CACHE_TTL = timedelta(hours=24)

    def __init__(self, package_name: str = "claux"):
        """
        Initialize update checker.

        Args:
            package_name: Name of the package on PyPI
        """
        self.package_name = package_name
        self.current_version = __version__

    def check_for_updates(
        self, use_cache: bool = True
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if a newer version is available on PyPI.

        Args:
            use_cache: Whether to use cached result if available

        Returns:
            Tuple of (has_update, latest_version, error_message)
            - has_update: True if newer version available
            - latest_version: Latest version string from PyPI
            - error_message: Error message if check failed
        """
        # Check cache first
        if use_cache:
            cached_result = self._get_cached_result()
            if cached_result:
                return cached_result

        # Fetch latest version from PyPI
        try:
            latest_version = self._fetch_latest_version()

            if latest_version is None:
                return False, None, "Failed to fetch version from PyPI"

            # Compare versions
            has_update = self._is_newer_version(latest_version, self.current_version)

            # Cache the result
            self._cache_result(has_update, latest_version)

            return has_update, latest_version, None

        except Exception as e:
            return False, None, str(e)

    def _fetch_latest_version(self) -> Optional[str]:
        """
        Fetch latest version from PyPI JSON API.

        Returns:
            Latest version string or None if failed
        """
        url = self.PYPI_JSON_URL.format(package=self.package_name)

        try:
            # Create request with User-Agent header
            req = Request(url, headers={"User-Agent": f"claux/{self.current_version}"})

            with urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                return data.get("info", {}).get("version")

        except (URLError, json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Failed to fetch version from PyPI: {e}")
            return None

    def _is_newer_version(self, latest: str, current: str) -> bool:
        """
        Compare version strings (simple comparison).

        Args:
            latest: Latest version from PyPI
            current: Current installed version

        Returns:
            True if latest is newer than current
        """
        try:
            # Parse semantic versions
            latest_parts = [int(x) for x in latest.split(".")]
            current_parts = [int(x) for x in current.split(".")]

            # Pad shorter version with zeros
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts += [0] * (max_len - len(latest_parts))
            current_parts += [0] * (max_len - len(current_parts))

            # Compare part by part
            for latest_part, current_part in zip(latest_parts, current_parts):
                if latest_part > current_part:
                    return True
                elif latest_part < current_part:
                    return False

            return False  # Versions are equal

        except ValueError:
            # Fallback to string comparison if parsing fails
            return latest != current

    def _get_cached_result(self) -> Optional[Tuple[bool, Optional[str], Optional[str]]]:
        """
        Get cached update check result if valid.

        Returns:
            Cached result tuple or None if cache invalid/expired
        """
        if not self.CACHE_FILE.exists():
            return None

        try:
            with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)

            # Check if cache is for current version and not expired
            if cache.get("current_version") != self.current_version:
                return None

            cache_time = datetime.fromisoformat(cache.get("timestamp", ""))
            if datetime.now() - cache_time > self.CACHE_TTL:
                return None

            return (cache.get("has_update", False), cache.get("latest_version"), None)

        except (json.JSONDecodeError, KeyError, ValueError, OSError):
            return None

    def _cache_result(self, has_update: bool, latest_version: Optional[str]):
        """
        Cache update check result.

        Args:
            has_update: Whether update is available
            latest_version: Latest version from PyPI
        """
        # Ensure cache directory exists
        self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "current_version": self.current_version,
            "latest_version": latest_version,
            "has_update": has_update,
        }

        try:
            with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
        except OSError as e:
            # Fail silently if can't write cache
            print(f"Warning: Failed to write update cache: {e}")

    def perform_upgrade(self, package_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Perform package upgrade using pip.

        Args:
            package_name: Package to upgrade (default: self.package_name)

        Returns:
            Tuple of (success, message)
        """
        pkg = package_name or self.package_name

        try:
            # Run pip upgrade
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", pkg],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                return True, f"Successfully upgraded {pkg}"
            else:
                return False, f"Upgrade failed: {result.stderr}"

        except subprocess.TimeoutExpired:
            return False, "Upgrade timed out"
        except Exception as e:
            return False, f"Upgrade error: {str(e)}"

    def clear_cache(self):
        """Clear update check cache."""
        if self.CACHE_FILE.exists():
            try:
                self.CACHE_FILE.unlink()
            except OSError:
                pass


# Global instance
_update_checker = UpdateChecker()


def check_for_updates(use_cache: bool = True) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check for package updates (convenience function).

    Args:
        use_cache: Whether to use cached result

    Returns:
        Tuple of (has_update, latest_version, error_message)
    """
    return _update_checker.check_for_updates(use_cache=use_cache)


def perform_upgrade(package_name: Optional[str] = None) -> Tuple[bool, str]:
    """
    Perform package upgrade (convenience function).

    Args:
        package_name: Package to upgrade (default: "claux")

    Returns:
        Tuple of (success, message)
    """
    return _update_checker.perform_upgrade(package_name=package_name)


def clear_update_cache():
    """Clear update check cache (convenience function)."""
    _update_checker.clear_cache()
