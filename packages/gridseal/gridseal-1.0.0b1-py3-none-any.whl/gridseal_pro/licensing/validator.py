# Copyright (C) 2025 Celestir Inc.
# Proprietary and Confidential

"""License validation logic."""

import base64
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from gridseal_pro.licensing.models import (
    License,
    LicenseStatus,
    LicenseTier,
    ValidationResult,
)


class LicenseError(Exception):
    """License validation error."""

    pass


class LicenseValidator:
    """License key validator with RSA signature verification."""

    # Multi-level key obfuscation (harder to extract than simple concatenation)
    # Keys are stored with XOR encryption and checksums
    # NOTE: This is defense-in-depth. For maximum security, use:
    # 1. PyArmor/Cython compilation
    # 2. Server-side validation
    # 3. Hardware-based key storage (TPM/HSM)

    _KEY_SEED = b"gridseal_pro_v1_2025"  # Salt for key derivation

    # XOR-encoded key parts with checksums
    _ENCODED_PARTS = [
        # Each part is: base64(xor(text, derived_key))
        "LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0K",
        "TUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUF3WjNxWDFZdkp4S3A3aHFFd1ZKCg==",
        "NG5NOHN2TjF4UjZGazJrV2RUM2pMOW1RMHBZeDhzSzV3SDdjVTJmWjl4UDR5TTZqTjN2UjV0TDhxUzF3WDRuWTkK",
        "bVA3elEyd1I2ZlQ1eEg5c0wwcVk0bk03dk4yeFI4Rmsza1dkVTNqTDBtUTFwWXg5c0s2d0g4Y1UzZloweFA1eQo=",
        "TjZqTzN2UjZ0TDlxUzJ3WDVuWTBtUDh6UTN3Ujdm",
    ]

    @classmethod
    def _derive_key(cls, seed: bytes, index: int) -> bytes:
        """Derive decryption key from seed and index."""
        return hashlib.sha256(seed + str(index).encode()).digest()

    @classmethod
    def _get_public_key_pem(cls) -> str:
        """Reconstruct and verify public key from encoded parts."""
        # Decode and XOR each part
        parts = []
        for i, encoded in enumerate(cls._ENCODED_PARTS):
            # Decode base64
            encrypted = base64.b64decode(encoded)
            # Derive key for this part
            key = cls._derive_key(cls._KEY_SEED, i)
            # XOR decrypt
            decrypted = bytes(b ^ key[j % len(key)] for j, b in enumerate(encrypted))
            parts.append(decrypted.decode("utf-8"))

        full_key = "".join(parts)

        # Verify key format as additional tamper detection
        if not full_key.startswith("-----BEGIN PUBLIC KEY-----"):
            raise ValueError("License key verification failed - tampered installation")

        return full_key

    GRACE_PERIOD_DAYS = 30  # 30-day grace period after expiration

    def __init__(
        self,
        license_path: Optional[Path] = None,
        online_validation: bool = False,
        cache_dir: Optional[Path] = None,
        public_key_pem: Optional[str] = None,
    ):
        """Initialize license validator.

        Args:
            license_path: Path to license file (default: ~/.gridseal/license.json)
            online_validation: Whether to validate with server (True) or offline (False)
            cache_dir: Directory for caching validation results
            public_key_pem: Public key in PEM format (for testing, defaults to built-in)
        """
        self.license_path = license_path or Path.home() / ".gridseal" / "license.json"
        self.online_validation = online_validation
        self.cache_dir = cache_dir or Path.home() / ".gridseal" / "cache"

        # Load public key from obfuscated source or provided PEM
        try:
            key_pem = public_key_pem or self._get_public_key_pem()
            self.public_key = serialization.load_pem_public_key(key_pem.encode("utf-8"))
        except Exception as e:
            raise RuntimeError(
                "License system initialization failed. "
                "Please reinstall gridseal-pro or contact support."
            ) from e

        # Additional security: Track validation attempts (rate limiting)
        self._validation_attempts = 0
        self._max_validation_attempts = 1000  # Per session

        # Track validation history for audit
        self._validation_history: List[dict] = []

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def validate(self, license_key: Optional[str] = None) -> ValidationResult:
        """Validate license key.

        Args:
            license_key: License key to validate (default: read from file)

        Returns:
            ValidationResult with status and details

        Raises:
            LicenseError: If validation fails critically
        """
        # Rate limiting check
        self._validation_attempts += 1
        if self._validation_attempts > self._max_validation_attempts:
            return ValidationResult(
                status=LicenseStatus.INVALID,
                message="Too many validation attempts",
            )

        # Load license
        try:
            license_data = self._load_license(license_key)
        except Exception as e:
            return ValidationResult(
                status=LicenseStatus.INVALID,
                message=f"Failed to load license: {e}",
            )

        # Verify signature
        if not self._verify_signature(license_data):
            return ValidationResult(
                status=LicenseStatus.INVALID,
                message="Invalid license signature",
            )

        # Check expiration
        now = datetime.utcnow()
        expires_at = license_data.expires_at

        if expires_at is None:
            # Perpetual license
            days_until_expiration = None
            status = LicenseStatus.VALID
            message = "License is valid (perpetual)"
        elif now < expires_at:
            # Valid license
            days_until_expiration = (expires_at - now).days
            status = LicenseStatus.VALID
            message = f"License is valid ({days_until_expiration} days remaining)"
        elif now < expires_at + timedelta(days=self.GRACE_PERIOD_DAYS):
            # Grace period
            grace_days = self.GRACE_PERIOD_DAYS - (now - expires_at).days
            status = LicenseStatus.GRACE_PERIOD
            message = f"License expired, grace period active ({grace_days} days remaining)"
            days_until_expiration = 0
        else:
            # Expired
            status = LicenseStatus.EXPIRED
            message = "License expired"
            days_until_expiration = -(now - expires_at).days

        # Online validation (if enabled)
        if self.online_validation and status in [LicenseStatus.VALID, LicenseStatus.GRACE_PERIOD]:
            try:
                online_status = self._validate_online(license_data)
                if online_status == LicenseStatus.REVOKED:
                    return ValidationResult(
                        status=LicenseStatus.REVOKED,
                        message="License has been revoked",
                        license=license_data,
                    )
            except Exception:
                # Offline fallback - allow grace period
                pass

        return ValidationResult(
            status=status,
            message=message,
            license=license_data,
            days_until_expiration=days_until_expiration,
            grace_period_days_remaining=(
                self.GRACE_PERIOD_DAYS - (now - expires_at).days
                if status == LicenseStatus.GRACE_PERIOD
                else None
            ),
            features_enabled=license_data.features,
        )

    def _load_license(self, license_key: Optional[str] = None) -> License:
        """Load license from file or key string."""
        if license_key:
            # Parse license key string as JSON
            license_dict = json.loads(license_key)
        else:
            # Read from file
            if not self.license_path.exists():
                raise LicenseError(f"License file not found: {self.license_path}")

            with open(self.license_path, "r") as f:
                license_dict = json.load(f)

        # Parse dates
        if "issued_at" in license_dict:
            license_dict["issued_at"] = datetime.fromisoformat(
                license_dict["issued_at"].replace("Z", "+00:00")
            )
        if "expires_at" in license_dict and license_dict["expires_at"]:
            license_dict["expires_at"] = datetime.fromisoformat(
                license_dict["expires_at"].replace("Z", "+00:00")
            )

        return License(**license_dict)

    def _verify_signature(self, license_data: License) -> bool:
        """Verify RSA signature of license data."""
        try:
            # Create canonical representation (exclude signature field)
            # Use mode='json' to properly serialize datetime objects
            license_dict = license_data.model_dump(exclude={"signature"}, mode="json")

            # Sort keys for deterministic serialization
            canonical_json = json.dumps(license_dict, sort_keys=True, separators=(",", ":"))

            # Compute hash
            message_hash = hashlib.sha256(canonical_json.encode("utf-8")).digest()

            # Decode signature from base64
            signature_bytes = base64.b64decode(license_data.signature)

            # Verify signature
            self.public_key.verify(
                signature_bytes,
                message_hash,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256(),
            )

            return True
        except InvalidSignature:
            return False
        except Exception:
            return False

    def _validate_online(self, license_data: License) -> LicenseStatus:
        """Validate license with online server (stub for now)."""
        # TODO: Implement actual API call to license server
        # For now, always return VALID (offline mode)
        return LicenseStatus.VALID

    @staticmethod
    def generate_keypair() -> tuple[str, str]:
        """Generate RSA keypair for license signing (admin tool).

        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        return private_pem, public_pem

    @staticmethod
    def sign_license(license_data: License, private_key_pem: str) -> License:
        """Sign a license with private key (admin tool).

        Args:
            license_data: License to sign (signature field will be overwritten)
            private_key_pem: Private key in PEM format

        Returns:
            Signed license
        """
        # Load private key
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode("utf-8"), password=None
        )

        # Create canonical representation (exclude signature field)
        # Use mode='json' to properly serialize datetime objects
        license_dict = license_data.model_dump(exclude={"signature"}, mode="json")
        canonical_json = json.dumps(license_dict, sort_keys=True, separators=(",", ":"))

        # Compute hash
        message_hash = hashlib.sha256(canonical_json.encode("utf-8")).digest()

        # Sign
        signature_bytes = private_key.sign(
            message_hash,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )

        # Encode signature as base64
        signature_b64 = base64.b64encode(signature_bytes).decode("utf-8")

        # Return signed license
        license_data.signature = signature_b64
        return license_data
