# Copyright (C) 2025 Celestir Inc.
# Proprietary and Confidential

"""Data models for causal tracing."""

from typing import Dict, List, Optional

import numpy as np
from pydantic import BaseModel, Field


class AttentionFlow(BaseModel):
    """Attention flow between tokens."""

    layer: int = Field(..., description="Transformer layer index")
    head: int = Field(..., description="Attention head index")
    source_token: int = Field(..., description="Source token index")
    target_token: int = Field(..., description="Target token index")
    attention_weight: float = Field(..., description="Attention weight (0-1)")

    class Config:
        arbitrary_types_allowed = True


class Attribution(BaseModel):
    """Token attribution score."""

    token_index: int = Field(..., description="Token index")
    token_text: str = Field(..., description="Token text")
    attribution_score: float = Field(..., description="Attribution score")
    is_spec_token: bool = Field(..., description="Whether token is from spec")
    is_code_token: bool = Field(..., description="Whether token is from code")

    class Config:
        json_schema_extra = {
            "example": {
                "token_index": 5,
                "token_text": "return",
                "attribution_score": 0.85,
                "is_spec_token": False,
                "is_code_token": True,
            }
        }


class AblationResult(BaseModel):
    """Result of feature ablation experiment."""

    ablated_token_index: int = Field(..., description="Index of ablated token")
    ablated_token_text: str = Field(..., description="Text of ablated token")
    baseline_output: str = Field(..., description="Output without ablation")
    ablated_output: str = Field(..., description="Output with ablation")
    importance_score: float = Field(..., description="Importance score (0-1)")
    is_critical: bool = Field(..., description="Whether token is critical")

    class Config:
        json_schema_extra = {
            "example": {
                "ablated_token_index": 3,
                "ablated_token_text": "sorted",
                "baseline_output": "def sort(arr): return sorted(arr)",
                "ablated_output": "def sort(arr): return arr",
                "importance_score": 0.92,
                "is_critical": True,
            }
        }


class CausalTrace(BaseModel):
    """Complete causal trace of a verification."""

    spec_text: str = Field(..., description="Specification text")
    code_text: str = Field(..., description="Generated code text")
    spec_tokens: List[str] = Field(..., description="Tokenized spec")
    code_tokens: List[str] = Field(..., description="Tokenized code")

    # Attention analysis
    attention_flows: List[AttentionFlow] = Field(
        default_factory=list, description="Attention flows between tokens"
    )

    # Attribution analysis
    attributions: List[Attribution] = Field(default_factory=list, description="Token attributions")

    # Ablation analysis
    ablation_results: List[AblationResult] = Field(
        default_factory=list, description="Ablation experiment results"
    )

    # Summary stats
    critical_spec_tokens: List[int] = Field(
        default_factory=list, description="Indices of critical spec tokens"
    )
    critical_code_tokens: List[int] = Field(
        default_factory=list, description="Indices of critical code tokens"
    )
    hallucinated_code_tokens: List[int] = Field(
        default_factory=list, description="Indices of hallucinated code tokens (low attribution)"
    )

    class Config:
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "spec_text": "Sort a list of numbers",
                "code_text": "def sort(arr): return sorted(arr)",
                "spec_tokens": ["Sort", "a", "list", "of", "numbers"],
                "code_tokens": [
                    "def",
                    "sort",
                    "(",
                    "arr",
                    ")",
                    ":",
                    "return",
                    "sorted",
                    "(",
                    "arr",
                    ")",
                ],
                "attention_flows": [],
                "attributions": [],
                "ablation_results": [],
                "critical_spec_tokens": [0, 4],  # "Sort", "numbers"
                "critical_code_tokens": [7],  # "sorted"
                "hallucinated_code_tokens": [],
            }
        }
