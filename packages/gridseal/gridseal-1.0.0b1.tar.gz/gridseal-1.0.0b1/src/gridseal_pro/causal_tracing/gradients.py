# Copyright (C) 2025 Celestir Inc.
# Proprietary and Confidential

"""Gradient-based attribution for causal tracing.

Uses integrated gradients to attribute code generation to specific
spec tokens, identifying which parts of the spec influenced which
parts of the code.
"""

import logging
from typing import List, Optional, Tuple

import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer

from gridseal_pro.causal_tracing.models import Attribution, CausalTrace
from gridseal_pro.utils import rate_limit_analysis

logger = logging.getLogger(__name__)

# Constants
DEFAULT_NUM_GRADIENT_STEPS = 50
ATTRIBUTION_THRESHOLD = 0.1


class GradientAttributor:
    """Gradient-based attribution analyzer.

    Implements integrated gradients to attribute model outputs to input tokens.
    """

    def __init__(
        self,
        model_name: str = "gpt2",
        device: str = "cpu",
        cache_dir: Optional[str] = None,
    ):
        """Initialize gradient attributor.

        Args:
            model_name: HuggingFace model name
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

            self.model.eval()
            logger.info(f"Model loaded successfully on {self.device}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(
                f"Failed to load model '{model_name}': {e}. "
                f"Try a smaller model like 'gpt2' or check internet connection."
            ) from e

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

    @rate_limit_analysis
    def analyze(
        self,
        spec_text: str,
        code_text: str,
        num_steps: int = DEFAULT_NUM_GRADIENT_STEPS,
        attribution_threshold: float = ATTRIBUTION_THRESHOLD,
    ) -> CausalTrace:
        """Perform gradient attribution analysis.

        Args:
            spec_text: Specification text
            code_text: Generated code text
            num_steps: Number of integration steps (higher = more accurate)
            attribution_threshold: Threshold for marking tokens as critical

        Returns:
            CausalTrace with attribution results
        """
        # Tokenize
        spec_tokens = self.tokenizer.tokenize(spec_text)
        code_tokens = self.tokenizer.tokenize(code_text)

        # Create combined prompt
        prompt = f"# Specification: {spec_text}\n# Code:\n{code_text}"

        # Compute integrated gradients
        attributions = self._integrated_gradients(prompt, num_steps=num_steps)

        # Identify critical and hallucinated tokens
        critical_spec_tokens = []
        hallucinated_code_tokens = []

        # Get token offsets
        spec_start = len(self.tokenizer.tokenize("# Specification: "))
        spec_end = spec_start + len(spec_tokens)

        for i, attr in enumerate(attributions):
            # Check if token is in spec range
            if spec_start <= i < spec_end:
                if attr.attribution_score >= attribution_threshold:
                    critical_spec_tokens.append(i - spec_start)

            # Check if token is in code range (low attribution = hallucination)
            elif attr.is_code_token and attr.attribution_score < attribution_threshold:
                hallucinated_code_tokens.append(i)

        return CausalTrace(
            spec_text=spec_text,
            code_text=code_text,
            spec_tokens=spec_tokens,
            code_tokens=code_tokens,
            attributions=attributions,
            critical_spec_tokens=critical_spec_tokens,
            hallucinated_code_tokens=hallucinated_code_tokens,
            critical_code_tokens=[],
            attention_flows=[],
            ablation_results=[],
        )

    def _integrated_gradients(
        self,
        text: str,
        num_steps: int = DEFAULT_NUM_GRADIENT_STEPS,
    ) -> List[Attribution]:
        """Compute integrated gradients for each token.

        Integrated Gradients formula:
        IG(x) = (x - x') * ∫[0,1] ∂F(x' + α(x - x'))/∂x dα

        where x is the input, x' is the baseline (zero embedding), and F is the model.
        """
        # Tokenize
        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
        input_ids = inputs["input_ids"]

        # Get embeddings
        embeddings = self.model.get_input_embeddings()(input_ids)

        # Baseline: zero embeddings
        baseline = torch.zeros_like(embeddings)

        # Compute gradients along the path from baseline to input
        # FIX: Process in batches to avoid memory leak
        gradients = []

        for step in range(num_steps + 1):
            alpha = step / num_steps

            # Interpolated embedding (detach first to create a leaf)
            interpolated = (baseline + alpha * (embeddings - baseline)).detach()
            interpolated.requires_grad = True

            # Forward pass
            outputs = self.model(inputs_embeds=interpolated)
            logits = outputs.logits

            # Target: next token prediction
            # Use mean of log probabilities as scalar output
            target_logits = logits[:, :-1, :]  # All but last
            target_probs = F.log_softmax(target_logits, dim=-1)
            target_score = target_probs.mean()

            # Backward pass
            if interpolated.grad is not None:
                interpolated.grad.zero_()
            target_score.backward()

            # Store gradients (FIX: Clone to avoid memory leak)
            if interpolated.grad is not None:
                # Clone and detach to free graph
                grad_copy = interpolated.grad.detach().cpu().clone().numpy()
                gradients.append(grad_copy)

                # Clear gradients immediately to free memory
                interpolated.grad = None
                del interpolated

            # Clear intermediate tensors
            del outputs, logits, target_logits, target_probs, target_score

            # Periodic garbage collection for long sequences
            if step % 10 == 0 and torch.cuda.is_available():
                torch.cuda.empty_cache()

        # Average gradients (Riemann sum approximation)
        if len(gradients) == 0:
            return []  # No gradients for empty input

        avg_gradients = np.mean(gradients, axis=0)  # (1, seq_len, embed_dim)

        # Numerical stability check: detect gradient explosion/vanishing
        grad_magnitude = np.abs(avg_gradients).max() if avg_gradients.size > 0 else 0.0
        if grad_magnitude > 1000.0:
            logger.warning(
                f"Large gradient detected ({grad_magnitude:.2f}). "
                "Results may be unstable. Consider reducing num_steps or using a smaller model."
            )
        elif grad_magnitude < 1e-6:
            logger.warning(
                "Vanishing gradients detected. "
                "Results may be unreliable. Consider using more integration steps."
            )

        # Compute attribution: (x - x') * grad
        delta = (embeddings - baseline).detach().cpu().numpy()
        attributions_raw = delta * avg_gradients  # (1, seq_len, embed_dim)

        # Sum over embedding dimension to get per-token attribution
        token_attributions = np.sum(attributions_raw, axis=-1)[0]  # (seq_len,)

        # Normalize to 0-1
        min_attr = token_attributions.min()
        max_attr = token_attributions.max()
        if max_attr > min_attr:
            token_attributions = (token_attributions - min_attr) / (max_attr - min_attr)

        # Create Attribution objects
        tokens = self.tokenizer.convert_ids_to_tokens(input_ids[0])
        attributions = []

        for i, (token, score) in enumerate(zip(tokens, token_attributions)):
            # Determine if spec or code token (heuristic)
            is_spec = "Specification:" in text and i < len(text.split("\n")[0]) // 2
            is_code = "Code:" in text and i > len(text.split("\n")[0]) // 2

            attributions.append(
                Attribution(
                    token_index=i,
                    token_text=token,
                    attribution_score=float(score),
                    is_spec_token=is_spec,
                    is_code_token=is_code,
                )
            )

        return attributions

    def visualize_attributions(
        self,
        trace: CausalTrace,
        output_path: Optional[str] = None,
    ) -> str:
        """Create HTML visualization of attributions.

        Args:
            trace: CausalTrace with attribution results
            output_path: Optional path to save HTML file

        Returns:
            HTML string
        """
        html = ["<html><head><style>"]
        html.append(
            ".token { display: inline-block; padding: 2px 4px; margin: 2px; border-radius: 3px; }"
        )
        html.append(".spec-token { background-color: rgba(0, 255, 0, 0.3); }")
        html.append(".code-token { background-color: rgba(0, 0, 255, 0.3); }")
        html.append(".critical { border: 2px solid red; }")
        html.append(".hallucinated { border: 2px solid orange; }")
        html.append("</style></head><body>")

        html.append("<h2>Specification</h2><div>")
        for i, token in enumerate(trace.spec_tokens):
            is_critical = i in trace.critical_spec_tokens
            css_class = "token spec-token" + (" critical" if is_critical else "")
            html.append(f'<span class="{css_class}">{token}</span>')
        html.append("</div>")

        html.append("<h2>Code</h2><div>")
        for i, token in enumerate(trace.code_tokens):
            is_hallucinated = i in trace.hallucinated_code_tokens
            css_class = "token code-token" + (" hallucinated" if is_hallucinated else "")
            html.append(f'<span class="{css_class}">{token}</span>')
        html.append("</div>")

        html.append("</body></html>")

        html_str = "\n".join(html)

        if output_path:
            with open(output_path, "w") as f:
                f.write(html_str)

        return html_str
