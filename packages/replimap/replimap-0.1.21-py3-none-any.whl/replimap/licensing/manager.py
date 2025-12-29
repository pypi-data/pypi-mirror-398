"""
License Manager for RepliMap.

Handles license validation, caching, and activation.
"""

from __future__ import annotations

import json
import logging
import os
import platform
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import httpx

from replimap import __version__
from replimap.licensing.models import (
    License,
    LicenseStatus,
    LicenseValidationError,
    Plan,
    get_machine_fingerprint,
    get_plan_features,
)

if TYPE_CHECKING:
    from replimap.licensing.models import PlanFeatures

logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL_DEV = "https://replimap-api.davidlu1001.workers.dev/v1"
API_BASE_URL_PROD = "https://api.replimap.io/v1"
API_TIMEOUT = 30  # seconds

# Default cache directory
DEFAULT_CACHE_DIR = Path.home() / ".replimap"
LICENSE_CACHE_FILE = "license.json"
LICENSE_CACHE_TTL = timedelta(hours=24)  # Re-validate after 24 hours


def is_dev_mode() -> bool:
    """
    Check if dev mode is enabled.

    Dev mode bypasses license restrictions for local development and testing.
    Enable with: REPLIMAP_DEV_MODE=1

    Returns:
        True if dev mode is enabled
    """
    return os.environ.get("REPLIMAP_DEV_MODE", "").lower() in ("1", "true", "yes")


class LicenseManager:
    """
    Manages license validation and caching.

    Supports both online validation and offline cached validation
    for reliability in various network conditions.
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        api_base_url: str | None = None,
    ) -> None:
        """
        Initialize the LicenseManager.

        Args:
            cache_dir: Directory for caching license data
            api_base_url: Base URL for license validation API
        """
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # Use dev API by default until production is ready
        self.api_base_url = api_base_url or os.environ.get(
            "REPLIMAP_LICENSE_API", API_BASE_URL_DEV
        )
        self._current_license: License | None = None
        self._cached_at: datetime | None = None

    @property
    def cache_path(self) -> Path:
        """Path to the license cache file."""
        return self.cache_dir / LICENSE_CACHE_FILE

    @property
    def current_license(self) -> License | None:
        """Get the currently active license."""
        if self._current_license is None:
            self._current_license = self._load_cached_license()
        return self._current_license

    @property
    def current_plan(self) -> Plan:
        """Get the current plan (FREE if no license)."""
        # Dev mode bypasses all license restrictions
        if is_dev_mode():
            return Plan.ENTERPRISE

        if self.current_license is None:
            return Plan.FREE
        if self.current_license.is_expired:
            return Plan.FREE
        return self.current_license.plan

    @property
    def current_features(self) -> PlanFeatures:
        """Get the features for the current plan."""
        return get_plan_features(self.current_plan)

    @property
    def is_dev_mode(self) -> bool:
        """Check if running in dev mode."""
        return is_dev_mode()

    def activate(self, license_key: str) -> License:
        """
        Activate a license key.

        Args:
            license_key: The license key to activate

        Returns:
            The activated License object

        Raises:
            LicenseValidationError: If activation fails
        """
        logger.info("Activating license key...")

        # Validate the license format
        if not self._validate_key_format(license_key):
            raise LicenseValidationError(
                "Invalid license key format. Expected: RM-XXXX-XXXX-XXXX-XXXX"
            )

        # Try online validation first
        try:
            license_data = self._validate_online(license_key)
        except Exception as e:
            logger.warning(f"Online validation failed: {e}")
            # Fall back to offline validation for existing cached licenses
            if self._has_valid_cache():
                cached = self._load_cached_license()
                if cached and cached.license_key == license_key:
                    logger.info("Using cached license (offline mode)")
                    return cached
            raise LicenseValidationError(f"Could not validate license: {e}") from e

        # Validate machine fingerprint
        fingerprint = get_machine_fingerprint()
        if not license_data.validate_machine(fingerprint):
            # For new activations, bind to this machine
            license_data.machine_fingerprint = fingerprint

        # Cache the validated license
        self._cache_license(license_data)
        self._current_license = license_data

        logger.info(f"License activated: {license_data.plan.value} plan")
        return license_data

    def deactivate(self) -> None:
        """Deactivate and remove the current license."""
        self._current_license = None
        self._cached_at = None
        if self.cache_path.exists():
            self.cache_path.unlink()
        logger.info("License deactivated")

    def validate(self) -> tuple[LicenseStatus, str]:
        """
        Validate the current license.

        Returns:
            Tuple of (status, message)
        """
        license_obj = self.current_license

        if license_obj is None:
            return LicenseStatus.VALID, "Using free tier"

        # Check expiration
        if license_obj.is_expired:
            return (
                LicenseStatus.EXPIRED,
                f"License expired on {license_obj.expires_at}",
            )

        # Check machine fingerprint
        fingerprint = get_machine_fingerprint()
        if not license_obj.validate_machine(fingerprint):
            return (
                LicenseStatus.MACHINE_MISMATCH,
                "License is bound to a different machine",
            )

        # Check if cache is stale and needs revalidation
        if self._is_cache_stale():
            try:
                self._revalidate_online()
            except Exception as e:
                logger.warning(f"Revalidation failed: {e}")
                # Continue with cached license if within grace period
                if not self._is_grace_period_expired():
                    logger.info("Within grace period, using cached license")
                else:
                    return (
                        LicenseStatus.INVALID,
                        "Could not revalidate license online",
                    )

        return LicenseStatus.VALID, f"{license_obj.plan.value} plan active"

    def check_feature(self, feature_name: str) -> bool:
        """
        Check if a feature is available in the current plan.

        Args:
            feature_name: The feature to check

        Returns:
            True if feature is available
        """
        from replimap.licensing.models import Feature

        try:
            feature = Feature(feature_name)
        except ValueError:
            logger.warning(f"Unknown feature: {feature_name}")
            return False

        return self.current_features.has_feature(feature)

    def get_usage_limits(self) -> dict[str, int | None]:
        """Get the usage limits for the current plan."""
        features = self.current_features
        return {
            "max_resources_per_scan": features.max_resources_per_scan,
            "max_scans_per_month": features.max_scans_per_month,
            "max_aws_accounts": features.max_aws_accounts,
        }

    def _validate_key_format(self, key: str) -> bool:
        """Validate the format of a license key.

        Expected format: RM-XXXX-XXXX-XXXX-XXXX
        - RM prefix (RepliMap brand identifier)
        - 4 groups of 4 uppercase alphanumeric characters
        """
        if not key:
            return False

        key = key.strip().upper()

        # Must start with RM-
        if not key.startswith("RM-"):
            return False

        # Remove RM- prefix and validate 4 segments
        parts = key[3:].split("-")
        if len(parts) != 4:
            return False

        return all(len(p) == 4 and p.isalnum() for p in parts)

    def _validate_online(self, license_key: str) -> License:
        """
        Validate license key with the online API.

        Makes an HTTP request to the license server to validate the key
        and retrieve license details.

        Args:
            license_key: The license key to validate (format: RM-XXXX-XXXX-XXXX-XXXX)

        Returns:
            License object with validated license details

        Raises:
            LicenseValidationError: If validation fails
        """
        machine_id = get_machine_fingerprint()

        try:
            response = httpx.post(
                f"{self.api_base_url}/license/validate",
                json={
                    "license_key": license_key.upper(),
                    "machine_id": machine_id,
                    "cli_version": __version__,
                },
                timeout=API_TIMEOUT,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("valid"):
                    # Parse expires_at if present
                    expires_at = None
                    if data.get("expires_at"):
                        expires_str = data["expires_at"]
                        # Handle both formats: with Z suffix or +00:00
                        if expires_str.endswith("Z"):
                            expires_str = expires_str[:-1] + "+00:00"
                        expires_at = datetime.fromisoformat(expires_str)

                    return License(
                        license_key=license_key.upper(),
                        plan=Plan(data.get("plan", "solo").lower()),
                        email=data.get("email", ""),
                        issued_at=datetime.now(UTC),
                        expires_at=expires_at,
                        machine_fingerprint=machine_id,
                        max_machines=data.get("max_machines", 1),
                        metadata=data.get("features", {}),
                    )
                else:
                    raise LicenseValidationError(
                        data.get("message", "License validation failed")
                    )

            elif response.status_code == 404:
                raise LicenseValidationError("License key not found")

            elif response.status_code == 403:
                data = response.json()
                error_code = data.get("error_code", "UNKNOWN")
                message = data.get("message", "License validation failed")
                raise LicenseValidationError(f"{error_code}: {message}")

            elif response.status_code == 429:
                raise LicenseValidationError(
                    "Rate limit exceeded. Please try again later."
                )

            else:
                raise LicenseValidationError(
                    f"Unexpected error: HTTP {response.status_code}"
                )

        except httpx.RequestError as e:
            logger.warning(f"Network error during license validation: {e}")
            raise LicenseValidationError(f"Network error: {e}") from e

    def _get_machine_name(self) -> str:
        """Get a human-readable machine name for activation."""
        return f"{platform.node()} ({platform.system()} {platform.machine()})"

    def _revalidate_online(self) -> None:
        """Revalidate the current license with the API."""
        if self._current_license is None:
            return

        # TODO: Implement actual API revalidation
        logger.debug("Revalidation would happen here")
        self._cached_at = datetime.now(UTC)

    def _cache_license(self, license_obj: License) -> None:
        """Cache the license to disk."""
        cache_data = {
            "license": license_obj.to_dict(),
            "cached_at": datetime.now(UTC).isoformat(),
            "fingerprint": get_machine_fingerprint(),
        }
        self.cache_path.write_text(json.dumps(cache_data, indent=2))
        self._cached_at = datetime.now(UTC)
        logger.debug(f"License cached to {self.cache_path}")

    def _load_cached_license(self) -> License | None:
        """Load license from cache."""
        if not self.cache_path.exists():
            return None

        try:
            data = json.loads(self.cache_path.read_text())
            self._cached_at = datetime.fromisoformat(data["cached_at"])
            return License.from_dict(data["license"])
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to load cached license: {e}")
            return None

    def _has_valid_cache(self) -> bool:
        """Check if there's a valid cached license."""
        return self.cache_path.exists()

    def _is_cache_stale(self) -> bool:
        """Check if the cache needs revalidation."""
        if self._cached_at is None:
            return True
        return datetime.now(UTC) - self._cached_at > LICENSE_CACHE_TTL

    def _is_grace_period_expired(self) -> bool:
        """Check if the offline grace period has expired."""
        grace_period = timedelta(days=7)  # 7 day grace period
        if self._cached_at is None:
            return True
        return datetime.now(UTC) - self._cached_at > grace_period


# Global license manager instance
_license_manager: LicenseManager | None = None


def get_license_manager() -> LicenseManager:
    """Get the global license manager instance."""
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager()
    return _license_manager


def set_license_manager(manager: LicenseManager) -> None:
    """Set the global license manager instance (useful for testing)."""
    global _license_manager
    _license_manager = manager
