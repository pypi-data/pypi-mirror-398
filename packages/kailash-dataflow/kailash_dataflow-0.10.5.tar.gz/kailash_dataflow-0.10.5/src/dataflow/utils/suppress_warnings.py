"""
Suppress verbose Core SDK warnings in DataFlow.

This module provides utilities to suppress console warnings from Core SDK
that flood the output when DataFlow initializes. These warnings are benign
(node registration overwriting is expected in DataFlow) but distract from
actual errors.
"""

import logging


def suppress_core_sdk_warnings():
    """
    Suppress verbose Core SDK warnings that flood console output.

    Warnings suppressed:
    - kailash.nodes.base: "Overwriting existing node registration"
    - kailash.resources.registry: "Overwriting existing factory for resource"

    These warnings are benign in DataFlow context where node registration
    overwriting is expected during model decoration.

    Usage:
        from dataflow.utils.suppress_warnings import suppress_core_sdk_warnings
        suppress_core_sdk_warnings()
    """
    # Suppress node registration warnings
    logging.getLogger("kailash.nodes.base").setLevel(logging.ERROR)

    # Suppress resource factory warnings
    logging.getLogger("kailash.resources.registry").setLevel(logging.ERROR)


def restore_core_sdk_warnings():
    """
    Restore Core SDK warning levels to default (WARNING).

    Use this to re-enable warnings for debugging if needed.

    Usage:
        from dataflow.utils.suppress_warnings import restore_core_sdk_warnings
        restore_core_sdk_warnings()
    """
    # Restore node registration warnings
    logging.getLogger("kailash.nodes.base").setLevel(logging.WARNING)

    # Restore resource factory warnings
    logging.getLogger("kailash.resources.registry").setLevel(logging.WARNING)
