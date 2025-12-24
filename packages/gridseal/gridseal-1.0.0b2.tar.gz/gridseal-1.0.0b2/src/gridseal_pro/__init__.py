# Copyright (C) 2025 Celestir Inc.
# Proprietary and Confidential - All Rights Reserved
#
# This software is proprietary to Celestir Inc. and may not be used,
# copied, modified, or distributed except pursuant to the terms of a
# valid license agreement with Celestir Inc.

"""Gridseal Pro - Proprietary AI Code Verification Toolkit.

This module provides advanced features for AI code verification:
- Causal Tracing: Explain why verification failed
- Counterfactual Editing: Show what-if scenarios
- Automatic Repair: Fix bugs using CEGIS
- Enterprise Licensing: License key validation

Requires valid Gridseal Pro license key.
"""

__version__ = "0.1.0"
__author__ = "Celestir Inc."
__license__ = "Proprietary"

from gridseal_pro.causal_tracing import (
    AblationAnalyzer,
    CausalTrace,
    GradientAttributor,
)
from gridseal_pro.counterfactual import CounterfactualEditor
from gridseal_pro.licensing import LicenseError, LicenseValidator
from gridseal_pro.repair import CEGISRepairer

__all__ = [
    # Causal Tracing
    "AblationAnalyzer",
    "GradientAttributor",
    "CausalTrace",
    # Counterfactual
    "CounterfactualEditor",
    # Repair
    "CEGISRepairer",
    # Licensing
    "LicenseValidator",
    "LicenseError",
]
