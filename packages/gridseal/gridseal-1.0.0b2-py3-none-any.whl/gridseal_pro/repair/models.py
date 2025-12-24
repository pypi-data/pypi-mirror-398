# Copyright (C) 2025 Celestir Inc.
# Proprietary and Confidential

"""Data models for automatic repair."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CounterExample(BaseModel):
    """Counterexample from Z3 verification."""

    inputs: Dict[str, Any] = Field(..., description="Input values that fail")
    expected_output: Any = Field(..., description="Expected output")
    actual_output: Any = Field(..., description="Actual output from buggy code")
    explanation: str = Field(..., description="Why this is a counterexample")

    class Config:
        json_schema_extra = {
            "example": {
                "inputs": {"a": 5, "b": 3},
                "expected_output": 2,
                "actual_output": 8,
                "explanation": "subtract(5, 3) should return 2, but returns 8 (uses + instead of -)",
            }
        }


class Patch(BaseModel):
    """Code patch suggestion."""

    patch_id: str = Field(..., description="Unique patch ID")
    original_code: str = Field(..., description="Original buggy code")
    patched_code: str = Field(..., description="Patched code")

    # Metadata
    line_number: Optional[int] = Field(None, description="Line number of fix")
    operation: str = Field(..., description="Type of fix: 'replace', 'insert', 'delete'")
    description: str = Field(..., description="Human-readable description")

    # Verification
    passes_all_tests: bool = Field(False, description="Whether patch passes all tests")
    fixes_counterexamples: List[str] = Field(
        default_factory=list, description="IDs of counterexamples fixed by this patch"
    )
    confidence_score: float = Field(0.0, description="Confidence in patch correctness (0-1)")

    class Config:
        json_schema_extra = {
            "example": {
                "patch_id": "patch_001",
                "original_code": "def subtract(a, b):\\n    return a + b",
                "patched_code": "def subtract(a, b):\\n    return a - b",
                "line_number": 2,
                "operation": "replace",
                "description": "Changed + to - to fix subtraction",
                "passes_all_tests": True,
                "fixes_counterexamples": ["ce_001", "ce_002"],
                "confidence_score": 0.95,
            }
        }


class RepairResult(BaseModel):
    """Result of repair attempt."""

    original_code: str = Field(..., description="Original buggy code")
    specification: str = Field(..., description="Specification")

    # Counterexamples found
    counterexamples: List[CounterExample] = Field(
        default_factory=list, description="Counterexamples from verification"
    )

    # Patches generated
    patches: List[Patch] = Field(
        default_factory=list, description="Generated patches (sorted by confidence)"
    )

    # Best patch
    best_patch: Optional[Patch] = Field(None, description="Highest-confidence patch")

    # Repair status
    repair_successful: bool = Field(False, description="Whether repair succeeded")
    iterations: int = Field(0, description="Number of CEGIS iterations")
    total_time_seconds: float = Field(0.0, description="Total repair time")

    class Config:
        json_schema_extra = {
            "example": {
                "original_code": "def subtract(a, b): return a + b",
                "specification": "Return a - b",
                "counterexamples": [
                    {"inputs": {"a": 5, "b": 3}, "expected_output": 2, "actual_output": 8}
                ],
                "patches": [{"patch_id": "patch_001", "confidence_score": 0.95}],
                "best_patch": {
                    "patch_id": "patch_001",
                    "patched_code": "def subtract(a, b): return a - b",
                },
                "repair_successful": True,
                "iterations": 3,
                "total_time_seconds": 1.5,
            }
        }
