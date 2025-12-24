# Copyright (C) 2025 Celestir Inc.
# Proprietary and Confidential

"""License data models."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LicenseStatus(str, Enum):
    """License status enum."""

    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    GRACE_PERIOD = "grace_period"
    REVOKED = "revoked"


class LicenseTier(str, Enum):
    """License tier enum."""

    TRIAL = "trial"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class License(BaseModel):
    """License key data model."""

    license_key: str = Field(..., description="Unique license key (UUID)")
    customer_id: str = Field(..., description="Customer ID")
    customer_email: str = Field(..., description="Customer email")
    tier: LicenseTier = Field(..., description="License tier")
    issued_at: datetime = Field(..., description="Issuance timestamp")
    expires_at: Optional[datetime] = Field(
        None, description="Expiration timestamp (None = perpetual)"
    )
    max_users: int = Field(1, description="Maximum number of concurrent users")
    max_calls_per_day: Optional[int] = Field(None, description="API call limit per day")
    features: list[str] = Field(default_factory=list, description="Enabled features")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    # Signature (RSA-signed hash of the above fields)
    signature: str = Field(..., description="RSA signature for validation")

    class Config:
        json_schema_extra = {
            "example": {
                "license_key": "550e8400-e29b-41d4-a716-446655440000",
                "customer_id": "cust_123",
                "customer_email": "user@example.com",
                "tier": "professional",
                "issued_at": "2025-01-01T00:00:00Z",
                "expires_at": "2026-01-01T00:00:00Z",
                "max_users": 5,
                "max_calls_per_day": 10000,
                "features": ["causal_tracing", "repair", "counterfactual"],
                "metadata": {},
                "signature": "base64_encoded_signature",
            }
        }


class ValidationResult(BaseModel):
    """License validation result."""

    status: LicenseStatus
    message: str
    license: Optional[License] = None
    days_until_expiration: Optional[int] = None
    grace_period_days_remaining: Optional[int] = None
    features_enabled: list[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "status": "valid",
                "message": "License is valid",
                "license": {"license_key": "...", "tier": "professional"},
                "days_until_expiration": 365,
                "grace_period_days_remaining": None,
                "features_enabled": ["causal_tracing", "repair"],
            }
        }
