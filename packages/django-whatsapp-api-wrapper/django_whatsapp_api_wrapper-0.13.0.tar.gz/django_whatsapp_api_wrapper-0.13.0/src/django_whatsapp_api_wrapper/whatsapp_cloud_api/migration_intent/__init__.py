"""
Migration Intent API module for WhatsApp Business Account migrations.

This module provides endpoints for managing WABA migrations between
multi-partner solutions via the Meta Graph API.
"""

from .client import MigrationIntentAPI

__all__ = ["MigrationIntentAPI"]
