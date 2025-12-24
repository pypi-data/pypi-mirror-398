# Copyright (C) 2025 Celestir Inc.
# Proprietary and Confidential

"""Data models for counterfactual editing."""

from typing import List, Optional

from pydantic import BaseModel, Field


class CodeDelta(BaseModel):
    """Difference between two code versions."""

    line_number: int = Field(..., description="Line number of change")
    operation: str = Field(..., description="Operation: 'add', 'remove', 'modify'")
    original_line: Optional[str] = Field(None, description="Original line (if modify/remove)")
    new_line: Optional[str] = Field(None, description="New line (if add/modify)")
    explanation: str = Field(..., description="Explanation of why this changed")

    class Config:
        json_schema_extra = {
            "example": {
                "line_number": 3,
                "operation": "modify",
                "original_line": "    return sorted(arr)",
                "new_line": "    return sorted(arr, reverse=True)",
                "explanation": "Added reverse=True because spec says 'descending order'",
            }
        }


class CounterfactualScenario(BaseModel):
    """What-if scenario with modified spec."""

    original_spec: str = Field(..., description="Original specification")
    counterfactual_spec: str = Field(..., description="Modified specification")
    original_code: str = Field(..., description="Code generated from original spec")
    counterfactual_code: str = Field(..., description="Code generated from counterfactual spec")

    # Delta analysis
    spec_changes: List[str] = Field(
        default_factory=list, description="List of changes made to spec"
    )
    code_deltas: List[CodeDelta] = Field(
        default_factory=list, description="Code changes caused by spec changes"
    )

    # Impact assessment
    impact_score: float = Field(0.0, description="Impact score: how much code changed (0-1)")
    is_safe: bool = Field(True, description="Whether counterfactual maintains correctness")

    class Config:
        json_schema_extra = {
            "example": {
                "original_spec": "Sort array in ascending order",
                "counterfactual_spec": "Sort array in descending order",
                "original_code": "def sort(arr): return sorted(arr)",
                "counterfactual_code": "def sort(arr): return sorted(arr, reverse=True)",
                "spec_changes": ["ascending → descending"],
                "code_deltas": [
                    {
                        "line_number": 1,
                        "operation": "modify",
                        "original_line": "return sorted(arr)",
                        "new_line": "return sorted(arr, reverse=True)",
                        "explanation": "Added reverse parameter",
                    }
                ],
                "impact_score": 0.25,
                "is_safe": True,
            }
        }
