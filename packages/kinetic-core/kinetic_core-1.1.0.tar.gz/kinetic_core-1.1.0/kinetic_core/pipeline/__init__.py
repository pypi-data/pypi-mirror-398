"""
Pipeline module for Salesforce Toolkit.

Provides ETL pipeline framework for data synchronization.
"""

from kinetic_core.pipeline.sync_pipeline import (
    SyncPipeline,
    SyncMode,
    SyncStatus,
    SyncResult
)

__all__ = ["SyncPipeline", "SyncMode", "SyncStatus", "SyncResult"]
