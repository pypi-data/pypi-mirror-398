# Copyright (C) 2025 Celestir Inc.
# Proprietary and Confidential

"""Feature ablation analysis for causal tracing.

Identifies critical tokens by systematically removing them and
measuring the impact on the model's output.
"""

import logging
from typing import List, Optional, Tuple

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from gridseal_pro.causal_tracing.models import (
    AblationResult,
    AttentionFlow,
    CausalTrace,
)
from gridseal_pro.utils import rate_limit_analysis

logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_LENGTH = 100
DEFAULT_TOP_K_ATTENTION = 10
IMPORTANCE_THRESHOLD = 0.5


def edit_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein edit distance between two strings.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Edit distance (number of insertions, deletions, substitutions)
    """
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],  # deletion
                    dp[i][j - 1],  # insertion
                    dp[i - 1][j - 1],  # substitution
                )

    return dp[m][n]


class AblationAnalyzer:
    """Analyze code generation via feature ablation.

    This class implements token ablation to identify which specification
    tokens are critical for generating specific code tokens.
    """

    def __init__(
        self,
        model_name: str = "gpt2",
        device: str = "cpu",
        cache_dir: Optional[str] = None,
    ):
        """Initialize ablation analyzer.

        Args:
            model_name: HuggingFace model name (default: gpt2 for testing)
            device: Device to run on ('cpu' or 'cuda')
            cache_dir: Directory for caching model weights
        """
        self.model_name = model_name
        self.device = device
        self.cache_dir = cache_dir

        # Load model and tokenizer with error handling
        try:
            logger.info(f"Loading tokenizer: {model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=cache_dir,
            )

            logger.info(f"Loading model: {model_name} on {device}")
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                cache_dir=cache_dir,
                output_attentions=True,
            )

            # Move to device with GPU memory error handling
            try:
                self.model = self.model.to(device)
            except RuntimeError as e:
                if "out of memory" in str(e).lower() or "cuda" in str(e).lower():
                    logger.warning(f"GPU OOM or CUDA error: {e}")
                    logger.warning("Falling back to CPU")
                    self.device = "cpu"
                    self.model = self.model.to("cpu")
                else:
                    raise

            self.model.eval()  # Evaluation mode
            logger.info(f"Model loaded successfully on {self.device}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(
                f"Failed to load model '{model_name}': {e}. "
                f"Try a smaller model like 'gpt2' or check internet connection."
            ) from e

    @rate_limit_analysis
    def analyze(
        self,
        spec_text: str,
        code_text: str,
        importance_threshold: float = 0.5,
    ) -> CausalTrace:
        """Perform ablation analysis on spec-code pair.

        Args:
            spec_text: Specification text
            code_text: Generated code text
            importance_threshold: Threshold for marking tokens as critical (0-1)

        Returns:
            CausalTrace with ablation results
        """
        # Tokenize inputs
        spec_tokens = self.tokenizer.tokenize(spec_text)
        code_tokens = self.tokenizer.tokenize(code_text)

        # Create combined prompt
        prompt = f"# Specification: {spec_text}\n# Code:\n{code_text}"

        # Get baseline output
        baseline_output = self._generate(prompt)

        # Perform ablation for each spec token
        ablation_results = []
        for i, token in enumerate(spec_tokens):
            ablated_text = self._ablate_token(spec_text, i)
            ablated_prompt = f"# Specification: {ablated_text}\n# Code:\n{code_text}"
            ablated_output = self._generate(ablated_prompt)

            # Calculate importance score (edit distance or similarity)
            importance = self._calculate_importance(baseline_output, ablated_output)

            ablation_results.append(
                AblationResult(
                    ablated_token_index=i,
                    ablated_token_text=token,
                    baseline_output=baseline_output,
                    ablated_output=ablated_output,
                    importance_score=importance,
                    is_critical=importance >= importance_threshold,
                )
            )

        # Extract attention flows
        attention_flows = self._extract_attention_flows(prompt)

        # Identify critical tokens
        critical_spec_tokens = [
            i for i, result in enumerate(ablation_results) if result.is_critical
        ]

        return CausalTrace(
            spec_text=spec_text,
            code_text=code_text,
            spec_tokens=spec_tokens,
            code_tokens=code_tokens,
            attention_flows=attention_flows,
            ablation_results=ablation_results,
            critical_spec_tokens=critical_spec_tokens,
            critical_code_tokens=[],  # Computed by gradient analysis
            hallucinated_code_tokens=[],  # Computed by attribution analysis
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit - cleanup resources."""
        self.cleanup()

    def cleanup(self):
        """Free model resources."""
        if hasattr(self, "model"):
            logger.info("Cleaning up model resources")
            del self.model
            if torch.cuda.is_available() and self.device != "cpu":
                torch.cuda.empty_cache()

    def _generate(self, prompt: str, max_length: int = DEFAULT_MAX_LENGTH) -> str:
        """Generate text from prompt."""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                do_sample=False,  # Deterministic
                pad_token_id=self.tokenizer.eos_token_id,
            )

        generated = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return generated

    def _ablate_token(self, text: str, token_index: int) -> str:
        """Ablate (remove) token at index."""
        tokens = self.tokenizer.tokenize(text)
        ablated_tokens = tokens[:token_index] + tokens[token_index + 1 :]
        return self.tokenizer.convert_tokens_to_string(ablated_tokens)

    def _calculate_importance(self, baseline: str, ablated: str) -> float:
        """Calculate importance score based on output change.

        Uses normalized edit distance as proxy for importance.
        """
        distance = edit_distance(baseline, ablated)
        max_len = max(len(baseline), len(ablated), 1)

        # Normalize to 0-1
        return min(distance / max_len, 1.0)

    def _extract_attention_flows(
        self, prompt: str, top_k: int = DEFAULT_TOP_K_ATTENTION
    ) -> List[AttentionFlow]:
        """Extract top-k attention flows from model."""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs, output_attentions=True)

        attentions = outputs.attentions  # Tuple of (batch, heads, seq, seq)

        flows = []
        for layer_idx, attn in enumerate(attentions):
            # attn shape: (1, num_heads, seq_len, seq_len)
            attn = attn[0]  # Remove batch dimension

            for head_idx in range(attn.shape[0]):
                head_attn = attn[head_idx]  # (seq_len, seq_len)

                # Find top-k attention weights
                flat_attn = head_attn.flatten()
                top_k_values, top_k_indices = torch.topk(flat_attn, min(top_k, len(flat_attn)))

                for value, idx in zip(top_k_values, top_k_indices):
                    src = idx // head_attn.shape[1]
                    tgt = idx % head_attn.shape[1]

                    flows.append(
                        AttentionFlow(
                            layer=layer_idx,
                            head=head_idx,
                            source_token=src.item(),
                            target_token=tgt.item(),
                            attention_weight=value.item(),
                        )
                    )

        # Sort by attention weight and return top-k overall
        flows.sort(key=lambda f: f.attention_weight, reverse=True)
        return flows[:top_k]
