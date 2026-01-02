"""
PowerTrack SDK - Python SDK for AlsoEnergy PowerTrack API

A comprehensive SDK for interacting with the AlsoEnergy PowerTrack platform,
providing easy access to site data, hardware configurations, alerts, and modeling.

Example:
    from powertrack_sdk import PowerTrackClient

    client = PowerTrackClient()
    sites = client.get_sites()
"""

__version__ = "1.0.0"
__author__ = "PowerTrack SDK Team"

from .auth import AuthManager
from .client import PowerTrackClient
from .exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    PowerTrackError,
    ValidationError,
)
from .models import (
    AlertSummary,
    AlertSummaryResponse,
    AlertTrigger,
    ChartData,
    ChartSeries,
    Hardware,
    HardwareDetails,
    HardwareDiagnostics,
    ModelingData,
    PortfolioMetrics,
    ReportingCapabilities,
    Site,
    SiteConfig,
    SiteData,
    SiteDetailedInfo,
    SiteList,
    SiteOverview,
    UpdateResult,
)

__all__ = [
    "PowerTrackClient",
    "AuthManager",
    "PowerTrackError",
    "AuthenticationError",
    "APIError",
    "ValidationError",
    "ConfigurationError",
    "Site",
    "Hardware",
    "AlertTrigger",
    "SiteConfig",
    "ModelingData",
    "HardwareDetails",
    "SiteData",
    "SiteList",
    "SiteOverview",
    "PortfolioMetrics",
    "ChartData",
    "ChartSeries",
    "AlertSummary",
    "AlertSummaryResponse",
    "HardwareDiagnostics",
    "SiteDetailedInfo",
    "ReportingCapabilities",
    "UpdateResult",
]
