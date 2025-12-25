"""
Kailash DataFlow - Clean Modular Architecture

This is the modernized DataFlow framework with proper modular structure.
The monolithic 526-line implementation has been refactored into focused modules:

- core/engine.py: Main DataFlow class
- core/models.py: Configuration and base models
- core/nodes.py: Dynamic node generation
- features/bulk.py: High-performance bulk operations
- features/transactions.py: Enterprise transaction management
- features/multi_tenant.py: Multi-tenant data isolation
- utils/connection.py: Connection pooling and management
- configuration/: Progressive disclosure configuration system
- migrations/: Auto-migration and visual builder system
- optimization/: Query optimization and performance system

This maintains 100% functional compatibility while providing:
- Better maintainability
- Improved testability
- Clear separation of concerns
- Easier contribution and extension
- Progressive complexity (zero-config to enterprise)
"""

# Progressive Configuration System
from .configuration import (
    ConfigurationLevel,
    FeatureFlag,
    ProgressiveConfiguration,
    basic_config,
    enterprise_config,
    production_config,
    zero_config,
)
from .core.config import DataFlowConfig
from .core.engine import DataFlow
from .core.model_registry import ModelRegistry
from .core.models import DataFlowModel
from .utils.suppress_warnings import suppress_core_sdk_warnings

# Suppress verbose Core SDK warnings on import
suppress_core_sdk_warnings()

# Legacy compatibility - maintain the original imports
__version__ = "0.10.5"

__all__ = [
    "DataFlow",
    "DataFlowConfig",
    "DataFlowModel",
    "ModelRegistry",
    "ProgressiveConfiguration",
    "ConfigurationLevel",
    "FeatureFlag",
    "zero_config",
    "basic_config",
    "production_config",
    "enterprise_config",
]

# Backward compatibility note:
# All existing code using `from dataflow import DataFlow` will continue to work.
# The internal architecture is now modular, but the public API remains unchanged.
