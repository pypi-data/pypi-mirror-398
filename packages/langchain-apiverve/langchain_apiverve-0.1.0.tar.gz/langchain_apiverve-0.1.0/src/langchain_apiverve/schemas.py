"""
Pydantic schemas for APIVerve API inputs and outputs.

These schemas provide type safety and validation for API parameters.
"""

from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    """Standard APIVerve API response format."""

    status: str = Field(description="Response status: 'ok' or 'error'")
    error: Optional[str] = Field(default=None, description="Error message if status is 'error'")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")


class EmailValidationResult(BaseModel):
    """Result of email validation."""

    valid: bool = Field(description="Whether the email is valid")
    email: str = Field(description="The email address that was validated")
    domain: Optional[str] = Field(default=None, description="The email domain")
    disposable: Optional[bool] = Field(default=None, description="Whether the email is from a disposable provider")
    mx_found: Optional[bool] = Field(default=None, description="Whether MX records were found")
    syntax_valid: Optional[bool] = Field(default=None, description="Whether the email syntax is valid")


class DNSRecord(BaseModel):
    """A DNS record."""

    type: str = Field(description="Record type (A, AAAA, MX, TXT, etc.)")
    value: str = Field(description="Record value")
    ttl: Optional[int] = Field(default=None, description="Time to live in seconds")
    priority: Optional[int] = Field(default=None, description="Priority (for MX records)")


class IPGeolocationResult(BaseModel):
    """Result of IP geolocation lookup."""

    ip: str = Field(description="The IP address")
    country: Optional[str] = Field(default=None, description="Country name")
    country_code: Optional[str] = Field(default=None, description="ISO country code")
    region: Optional[str] = Field(default=None, description="Region/state name")
    city: Optional[str] = Field(default=None, description="City name")
    latitude: Optional[float] = Field(default=None, description="Latitude coordinate")
    longitude: Optional[float] = Field(default=None, description="Longitude coordinate")
    timezone: Optional[str] = Field(default=None, description="Timezone")
    isp: Optional[str] = Field(default=None, description="Internet Service Provider")
