# Copyright (C) 2025 Celestir Inc.
# Proprietary and Confidential

"""Counterfactual editor for what-if analysis.

Allows users to edit specifications and see how the generated code
would change, helping understand the relationship between spec and code.
"""

import difflib
import logging
from typing import List, Optional

from transformers import AutoModelForCausalLM, AutoTokenizer

from gridseal_pro.counterfactual.models import (
    CodeDelta,
    CounterfactualScenario,
)

logger = logging.getLogger(__name__)


class CounterfactualEditor:
    """Counterfactual editor for what-if spec changes.

    Generates alternative code based on modified specifications
    and analyzes the differences.
    """

    def __init__(
        self,
        model_name: str = "gpt2",
        device: str = "cpu",
        cache_dir: Optional[str] = None,
    ):
        """Initialize counterfactual editor.

        Args:
            model_name: HuggingFace model name for code generation
            device: Device to run on ('cpu' or 'cuda')
            cache_dir: Directory for caching model weights
        """
        self.model_name = model_name
        self.device = device

        # Load model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=cache_dir,
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            cache_dir=cache_dir,
        ).to(device)

        self.model.eval()

    def create_scenario(
        self,
        original_spec: str,
        counterfactual_spec: str,
        original_code: str,
    ) -> CounterfactualScenario:
        """Create counterfactual scenario.

        Args:
            original_spec: Original specification
            counterfactual_spec: Modified specification
            original_code: Code generated from original spec

        Returns:
            CounterfactualScenario with analysis
        """
        # Generate code from counterfactual spec
        # If specs are identical, use original code to avoid spurious differences
        if original_spec == counterfactual_spec:
            counterfactual_code = original_code
        else:
            counterfactual_code = self._generate_code(counterfactual_spec)

        # Analyze spec changes
        spec_changes = self._analyze_spec_changes(original_spec, counterfactual_spec)

        # Analyze code deltas
        code_deltas = self._analyze_code_deltas(original_code, counterfactual_code)

        # Calculate impact score
        impact_score = self._calculate_impact_score(original_code, counterfactual_code)

        # Safety check (placeholder - would integrate with gridseal-core)
        is_safe = self._check_safety(counterfactual_code)

        return CounterfactualScenario(
            original_spec=original_spec,
            counterfactual_spec=counterfactual_spec,
            original_code=original_code,
            counterfactual_code=counterfactual_code,
            spec_changes=spec_changes,
            code_deltas=code_deltas,
            impact_score=impact_score,
            is_safe=is_safe,
        )

    def suggest_edits(
        self,
        spec: str,
        num_suggestions: int = 3,
    ) -> List[str]:
        """Suggest possible spec edits for exploration.

        Args:
            spec: Original specification
            num_suggestions: Number of suggestions to generate

        Returns:
            List of suggested spec modifications
        """
        suggestions = []

        # Template-based suggestions (can be enhanced with LLM)
        templates = [
            lambda s: s.replace("ascending", "descending"),
            lambda s: s.replace("descending", "ascending"),
            lambda s: s + " and return the result as a string",
            lambda s: s + " with error handling",
            lambda s: s.replace("list", "array"),
            lambda s: "Optimize: " + s,
        ]

        for template in templates[:num_suggestions]:
            try:
                modified = template(spec)
                if modified != spec:
                    suggestions.append(modified)
            except Exception:
                pass

        return suggestions[:num_suggestions]

    def _generate_code(
        self,
        spec: str,
        max_length: int = 200,
    ) -> str:
        """Generate code from specification."""
        prompt = f"# Specification: {spec}\n# Code:\n"

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        outputs = self.model.generate(
            **inputs,
            max_length=max_length,
            do_sample=False,  # Deterministic
            pad_token_id=self.tokenizer.eos_token_id,
        )

        generated = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract code part (after "# Code:")
        if "# Code:" in generated:
            code = generated.split("# Code:")[1].strip()
        else:
            code = generated.strip()

        return code

    def _analyze_spec_changes(
        self,
        original: str,
        counterfactual: str,
    ) -> List[str]:
        """Analyze differences between specs."""
        changes = []

        # Split into words for better diff detection
        original_words = original.split()
        counterfactual_words = counterfactual.split()

        # Use difflib on words
        matcher = difflib.SequenceMatcher(None, original_words, counterfactual_words)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "replace":
                old_phrase = " ".join(original_words[i1:i2])
                new_phrase = " ".join(counterfactual_words[j1:j2])
                changes.append(f"{old_phrase} → {new_phrase}")
            elif tag == "delete":
                deleted = " ".join(original_words[i1:i2])
                changes.append(f"Removed: {deleted}")
            elif tag == "insert":
                added = " ".join(counterfactual_words[j1:j2])
                changes.append(f"Added: {added}")

        return changes

    def _analyze_code_deltas(
        self,
        original: str,
        counterfactual: str,
    ) -> List[CodeDelta]:
        """Analyze code differences line by line."""
        deltas = []

        original_lines = original.split("\n")
        counterfactual_lines = counterfactual.split("\n")

        # Use difflib for line-by-line comparison
        matcher = difflib.SequenceMatcher(None, original_lines, counterfactual_lines)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "replace":
                for i, (orig, new) in enumerate(
                    zip(original_lines[i1:i2], counterfactual_lines[j1:j2])
                ):
                    deltas.append(
                        CodeDelta(
                            line_number=i1 + i + 1,
                            operation="modify",
                            original_line=orig,
                            new_line=new,
                            explanation=f"Line modified due to spec change",
                        )
                    )
            elif tag == "delete":
                for i, line in enumerate(original_lines[i1:i2]):
                    deltas.append(
                        CodeDelta(
                            line_number=i1 + i + 1,
                            operation="remove",
                            original_line=line,
                            new_line=None,
                            explanation="Line removed",
                        )
                    )
            elif tag == "insert":
                for i, line in enumerate(counterfactual_lines[j1:j2]):
                    deltas.append(
                        CodeDelta(
                            line_number=j1 + i + 1,
                            operation="add",
                            original_line=None,
                            new_line=line,
                            explanation="Line added",
                        )
                    )

        return deltas

    def _calculate_impact_score(
        self,
        original: str,
        counterfactual: str,
    ) -> float:
        """Calculate impact score based on edit distance."""
        matcher = difflib.SequenceMatcher(None, original, counterfactual)
        similarity = matcher.ratio()
        impact = 1.0 - similarity
        return impact

    def _check_safety(self, code: str) -> bool:
        """Check if code is safe.

        Uses pattern matching and AST analysis to detect potentially dangerous code.
        Would integrate with gridseal-core verification for complete safety.
        """
        # Expanded unsafe pattern list
        unsafe_patterns = [
            # Code execution
            "eval(",
            "exec(",
            "compile(",
            # Import manipulation
            "__import__",
            "importlib.import_module",
            # System operations
            "os.system",
            "os.popen",
            "os.exec",
            "subprocess.",
            # File operations (potentially unsafe)
            "os.remove",
            "os.rmdir",
            "shutil.rmtree",
            # Network operations
            "urllib.",
            "requests.",
            "http.",
            "socket.",
            # Serialization risks
            "pickle.",
            "marshal.",
            # Low-level access
            "ctypes",
            "cffi",
            # Shell operations
            "popen",
            "Popen",
        ]

        # Check for unsafe patterns
        code_lower = code.lower()
        for pattern in unsafe_patterns:
            if pattern.lower() in code_lower:
                logger.warning(f"Unsafe pattern detected: {pattern}")
                return False

        # AST-based safety check
        try:
            import ast

            tree = ast.parse(code)

            # Check for dangerous AST nodes
            for node in ast.walk(tree):
                # Check for attribute access to dangerous modules
                if isinstance(node, ast.Attribute):
                    if isinstance(node.value, ast.Name):
                        if node.value.id in ["os", "sys", "subprocess"]:
                            logger.warning(f"Dangerous module access: {node.value.id}.{node.attr}")
                            return False

                # Check for calls to dangerous functions
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ["eval", "exec", "compile", "__import__"]:
                            logger.warning(f"Dangerous function call: {node.func.id}")
                            return False

        except SyntaxError:
            # If code doesn't parse, consider it unsafe
            logger.warning("Code has syntax errors - marking as unsafe")
            return False

        return True
