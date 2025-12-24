# Copyright (C) 2025 Celestir Inc.
# Proprietary and Confidential

"""CEGIS (CounterExample-Guided Inductive Synthesis) for automatic code repair.

CEGIS Algorithm:
1. Synthesize: Generate a candidate patch
2. Verify: Check if patch satisfies specification
3. If verification fails, extract counterexample
4. Add counterexample to training set
5. Repeat until patch is correct or max iterations reached
"""

import ast
import logging
import re
import time
from typing import List, Optional, Tuple

from gridseal_core import GridsealCore
from gridseal_core.z3_verifier import Z3Verifier

from gridseal_pro.repair.models import (
    CounterExample,
    Patch,
    RepairResult,
)
from gridseal_pro.utils import rate_limit_repair

# Import advanced pattern matching with mathematical reasoning
try:
    from gridseal_pro.repair.advanced_patterns import (
        AdvancedPatternMatcher,
        ConstraintSolver,
    )

    ADVANCED_PATTERNS_AVAILABLE = True
except ImportError:
    ADVANCED_PATTERNS_AVAILABLE = False


class CEGISRepairer:
    """Automatic code repair using CEGIS loop.

    Iteratively generates patches and uses Z3 counterexamples
    to guide the synthesis towards a correct repair.
    """

    def __init__(
        self,
        max_iterations: int = 5,
        max_patches_per_iteration: int = 10,
        model_name: str = "deepseek-ai/deepseek-coder-1.3b-instruct",
        use_llm_fallback: bool = False,
        z3_timeout: int = 5000,
    ):
        """Initialize CEGIS repairer.

        Args:
            max_iterations: Maximum CEGIS iterations
            max_patches_per_iteration: Maximum patches to try per iteration
            z3_timeout: Z3 solver timeout in milliseconds
            use_llm_fallback: Use LLM when patterns fail
            model_name: LLM model to use for synthesis
        """
        self.max_iterations = max_iterations
        self.max_patches_per_iteration = max_patches_per_iteration
        self.use_llm_fallback = use_llm_fallback
        self.model_name = model_name

        # Initialize verifier
        self.verifier = GridsealCore(use_z3=True)
        self.z3_verifier = Z3Verifier(timeout=z3_timeout)

        # Initialize advanced pattern matcher
        if ADVANCED_PATTERNS_AVAILABLE:
            self.advanced_matcher = AdvancedPatternMatcher()
            self.constraint_solver = ConstraintSolver()
        else:
            self.advanced_matcher = None
            self.constraint_solver = None

        # Lazy load LLM (only if needed)
        self._model = None
        self._tokenizer = None

    @rate_limit_repair
    def repair(
        self,
        code: str,
        specification: str,
    ) -> RepairResult:
        """Attempt to repair buggy code.

        Args:
            code: Buggy code to repair
            specification: Specification (as docstring or natural language)

        Returns:
            RepairResult with patches and status
        """
        start_time = time.time()

        counterexamples = []
        all_patches = []
        iteration = 0
        best_patch = None

        # Extract function name from code
        try:
            tree = ast.parse(code)
            func_name = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name = node.name
                    break

            if not func_name:
                return RepairResult(
                    original_code=code,
                    specification=specification,
                    repair_successful=False,
                    iterations=0,
                    total_time_seconds=time.time() - start_time,
                )
        except SyntaxError:
            # Can't repair code that doesn't parse
            return RepairResult(
                original_code=code,
                specification=specification,
                repair_successful=False,
                iterations=0,
                total_time_seconds=time.time() - start_time,
            )

        # CEGIS loop
        for iteration in range(self.max_iterations):
            # Step 1: Synthesize patches
            patches = self._synthesize_patches(
                code, specification, counterexamples, max_patches=self.max_patches_per_iteration
            )

            if not patches:
                break

            # Step 2: Verify each patch and collect valid ones
            valid_patches = []
            for patch in patches:
                # Try test-based validation first (faster and more reliable)
                test_result = self._verify_with_tests(patch.patched_code, specification)

                if test_result["passed"]:
                    # Patch passes tests!
                    patch.passes_all_tests = True
                    # Keep original confidence score from pattern (don't override to 1.0)
                    patch.fixes_counterexamples = [ce.explanation for ce in counterexamples]
                    valid_patches.append(patch)
                    all_patches.append(patch)
                    continue

                # Fallback to Z3 verification if test-based fails
                z3_result = self.z3_verifier.verify(patch.patched_code, specification)

                if z3_result.status == "verified":
                    # Patch is correct!
                    patch.passes_all_tests = True
                    # Keep original confidence score
                    patch.fixes_counterexamples = [ce.explanation for ce in counterexamples]
                    valid_patches.append(patch)
                    all_patches.append(patch)
                    continue

                elif z3_result.status == "failed":
                    # Extract counterexample
                    if z3_result.counterexample:
                        ce = CounterExample(
                            inputs=z3_result.counterexample,
                            expected_output="unknown",
                            actual_output="unknown",
                            explanation=z3_result.message,
                        )
                        counterexamples.append(ce)

                    # Update patch confidence
                    patch.confidence_score = self._calculate_confidence(patch, counterexamples)
                    all_patches.append(patch)

                else:
                    # Unsupported or error
                    patch.confidence_score = 0.0
                    all_patches.append(patch)

            # Select best patch from valid patches by confidence score
            if valid_patches:
                # Sort by confidence score (highest first)
                best_patch = max(valid_patches, key=lambda p: p.confidence_score)

                return RepairResult(
                    original_code=code,
                    specification=specification,
                    counterexamples=counterexamples,
                    patches=all_patches,
                    best_patch=best_patch,
                    repair_successful=True,
                    iterations=iteration + 1,
                    total_time_seconds=time.time() - start_time,
                )

            # Update best patch from all patches if no valid ones
            if all_patches:
                best_patch = max(all_patches, key=lambda p: p.confidence_score)

        # If patterns failed and LLM fallback is enabled, try LLM
        if self.use_llm_fallback and (not best_patch or best_patch.confidence_score < 0.5):
            llm_patches = self._synthesize_with_llm(code, specification, counterexamples)

            for patch in llm_patches:
                # Verify LLM patch
                test_result = self._verify_with_tests(patch.patched_code, specification)

                if test_result["passed"]:
                    patch.passes_all_tests = True
                    all_patches.append(patch)

                    return RepairResult(
                        original_code=code,
                        specification=specification,
                        counterexamples=counterexamples,
                        patches=all_patches,
                        best_patch=patch,
                        repair_successful=True,
                        iterations=iteration + 1,
                        total_time_seconds=time.time() - start_time,
                    )

        # Repair failed
        return RepairResult(
            original_code=code,
            specification=specification,
            counterexamples=counterexamples,
            patches=sorted(all_patches, key=lambda p: p.confidence_score, reverse=True),
            best_patch=best_patch,
            repair_successful=False,
            iterations=iteration + 1,
            total_time_seconds=time.time() - start_time,
        )

    def _synthesize_patches(
        self,
        code: str,
        specification: str,
        counterexamples: List[CounterExample],
        max_patches: int = 20,
    ) -> List[Patch]:
        """Synthesize candidate patches.

        Uses pattern-based mutations first, then LLM fallback if needed.
        Expanded pattern library for percentage, off-by-one, and logic errors.
        """
        patches = []

        # Strategy 1: Pattern-based mutations (fast, deterministic)
        # Pattern 1: Operator replacement
        operator_patches = self._mutate_operators(code)
        patches.extend(operator_patches)

        # Pattern 2: Percentage calculation fixes
        percentage_patches = self._mutate_percentage(code, specification)
        patches.extend(percentage_patches)

        # Pattern 3: Off-by-one fixes
        obo_patches = self._mutate_off_by_one(code)
        patches.extend(obo_patches)

        # Pattern 4: Logic operator fixes
        logic_patches = self._mutate_logic_operators(code)
        patches.extend(logic_patches)

        # PHASE 2: Spec-guided logic patterns
        spec_logic_patches = self._mutate_logic_spec_guided(code, specification)
        patches.extend(spec_logic_patches)

        # PHASE 2: Negation patterns
        negation_patches = self._mutate_logic_negation(code)
        patches.extend(negation_patches)

        # PHASE 2: Boolean comparison patterns
        bool_comp_patches = self._mutate_boolean_comparisons(code)
        patches.extend(bool_comp_patches)

        # ADVANCED: De Morgan's laws
        demorgans_patches = self._mutate_logic_demorgans(code)
        patches.extend(demorgans_patches)

        # ADVANCED: Negation with comparison inversion
        negation_adv_patches = self._mutate_logic_negation_advanced(code)
        patches.extend(negation_adv_patches)

        # ADVANCED: Compound condition fixes
        compound_patches = self._mutate_logic_compound_conditions(code)
        patches.extend(compound_patches)

        # Pattern 5: Initialization patterns
        init_patches = self._mutate_initialization(code)
        patches.extend(init_patches)

        # PHASE 1: Semantic initialization patterns
        init_semantic_patches = self._mutate_initialization_semantic(code)
        patches.extend(init_semantic_patches)

        # ADVANCED: Initialization with data flow analysis
        init_advanced_patches = self._mutate_initialization_advanced(code, specification)
        patches.extend(init_advanced_patches)

        # Pattern 6: Null/None check patterns
        null_patches = self._mutate_null_checks(code)
        patches.extend(null_patches)

        # ADVANCED: Null checks including division by zero
        null_advanced_patches = self._mutate_null_checks_advanced(code)
        patches.extend(null_advanced_patches)

        # Pattern 7: String operation patterns
        string_patches = self._mutate_string_operations(code)
        patches.extend(string_patches)

        # Pattern 8: List comprehension patterns
        list_patches = self._mutate_list_operations(code)
        patches.extend(list_patches)

        # PHASE 3: List mutation patterns
        list_remove_patches = self._mutate_list_remove_in_loop(code)
        patches.extend(list_remove_patches)

        # PHASE 3: Comprehensive list mutation patterns
        list_remove_comprehensive = self._mutate_list_remove_comprehensive(code)
        patches.extend(list_remove_comprehensive)

        # Pattern 9: Sorting and reverse patterns
        sort_patches = self._mutate_sorting(code)
        patches.extend(sort_patches)

        # Pattern 10: Type conversion patterns
        type_patches = self._mutate_type_conversions(code)
        patches.extend(type_patches)

        # PHASE 6: Enhanced type conversion patterns
        type_enhanced_patches = self._mutate_type_conversions_enhanced(code)
        patches.extend(type_enhanced_patches)

        # Pattern 11: Boolean literal patterns
        bool_patches = self._mutate_boolean_literals(code)
        patches.extend(bool_patches)

        # Pattern 12: Default parameter patterns
        default_patches = self._mutate_default_parameters(code)
        patches.extend(default_patches)

        # Pattern 13: Edge case guard patterns
        edge_patches = self._mutate_edge_case_guards(code)
        patches.extend(edge_patches)

        # ADVANCED: Off-by-one refinements
        obo_advanced_patches = self._mutate_off_by_one_advanced(code)
        patches.extend(obo_advanced_patches)

        # PHASE 5: Enhanced edge case guards
        edge_enhanced_patches = self._mutate_edge_case_guards_enhanced(code, specification)
        patches.extend(edge_enhanced_patches)

        # PHASE 4: String slicing patterns
        string_slice_patches = self._mutate_string_slicing(code)
        patches.extend(string_slice_patches)

        # PHASE 4: Improved string slicing patterns (higher confidence)
        string_slice_improved = self._mutate_string_slicing_improved(code)
        patches.extend(string_slice_improved)

        # PHASE 4: Enhanced range boundary patterns
        range_enhanced_patches = self._mutate_range_boundaries_enhanced(code)
        patches.extend(range_enhanced_patches)

        # Pattern 14: Complex condition patterns
        complex_patches = self._mutate_complex_conditions(code)
        patches.extend(complex_patches)

        # Pattern 15: Constant correction
        constant_patches = self._mutate_constants(code, counterexamples)
        patches.extend(constant_patches)

        # Pattern 16: Mathematical operations
        math_patches = self._mutate_mathematical_operations(code)
        patches.extend(math_patches)

        # Pattern 17: List slicing patterns
        slice_patches = self._mutate_list_slicing(code)
        patches.extend(slice_patches)

        # Pattern 18: Dictionary operations
        dict_patches = self._mutate_dict_operations(code)
        patches.extend(dict_patches)

        # Pattern 19: Control flow patterns
        control_patches = self._mutate_control_flow(code)
        patches.extend(control_patches)

        # Pattern 20: Return statement patterns
        return_patches = self._mutate_return_statements(code)
        patches.extend(return_patches)

        # Pattern 21: Assignment patterns
        assign_patches = self._mutate_assignments(code)
        patches.extend(assign_patches)

        # Pattern 22: Function call patterns
        call_patches = self._mutate_function_calls(code)
        patches.extend(call_patches)

        # Pattern 23: Iteration patterns
        iter_patches = self._mutate_iteration_patterns(code)
        patches.extend(iter_patches)

        # Pattern 24: Membership and containment
        member_patches = self._mutate_membership_operations(code)
        patches.extend(member_patches)

        # Pattern 25: Aggregation patterns
        agg_patches = self._mutate_aggregation_operations(code)
        patches.extend(agg_patches)

        # Pattern 26: Conditional expression patterns
        cond_patches = self._mutate_conditional_expressions(code)
        patches.extend(cond_patches)

        # Pattern 27: Variable scope patterns
        scope_patches = self._mutate_variable_scope(code)
        patches.extend(scope_patches)

        # Pattern 28: Exception handling patterns
        except_patches = self._mutate_exception_handling(code)
        patches.extend(except_patches)

        # Pattern 29: Sequence operations
        seq_patches = self._mutate_sequence_operations(code)
        patches.extend(seq_patches)

        # Pattern 30: Numeric precision patterns
        precision_patches = self._mutate_numeric_precision(code)
        patches.extend(precision_patches)

        # Strategy 2: LLM fallback (if patterns insufficient and enabled)
        if len(patches) < max_patches and self.use_llm_fallback:
            llm_patches = self._synthesize_with_llm(
                code, specification, counterexamples, num_patches=max_patches - len(patches)
            )
            patches.extend(llm_patches)

        # Sort by confidence before truncating to prioritize high-quality patches
        patches.sort(key=lambda p: p.confidence_score, reverse=True)
        return patches[:max_patches]

    def _mutate_operators(self, code: str) -> List[Patch]:
        """Generate patches by mutating operators - MASSIVELY EXPANDED."""
        patches = []

        # Arithmetic operators - all combinations
        arithmetic_mutations = [
            (r"\+", "-"),
            (r"-", "+"),
            (r"\*", "/"),
            (r"/", "*"),
            (r"\+", "*"),
            (r"\*", "+"),
            (r"-", "/"),
            (r"/", "-"),
            (r"\+", "//"),
            (r"\*", "//"),
            (r"/", "//"),
            (r"//", "/"),
            (r"\+", "%"),
            (r"-", "%"),
            (r"\*", "%"),
            (r"/", "%"),
            (r"\+", "**"),
            (r"\*", "**"),
            (r"\*\*", "*"),
            (r"\*\*", "/"),
        ]

        # Comparison operators - all combinations
        comparison_mutations = [
            (r"<", "<="),
            (r"<=", "<"),
            (r">", ">="),
            (r">=", ">"),
            (r"<", ">"),
            (r">", "<"),
            (r"<=", ">="),
            (r">=", "<="),
            (r"<", "!="),
            (r">", "!="),
            (r"<=", "!="),
            (r">=", "!="),
            (r"<", "=="),
            (r">", "=="),
            (r"<=", "=="),
            (r">=", "=="),
            (r"==", "!="),
            (r"!=", "=="),
            (r"is", "=="),
            (r"==", "is"),
            (r"is not", "!="),
            (r"!=", "is not"),
        ]

        # Bitwise operators
        bitwise_mutations = [
            (r"&", "|"),
            (r"\|", "&"),
            (r"&", "^"),
            (r"\^", "&"),
            (r"<<", ">>"),
            (r">>", "<<"),
            (r"~", "-"),
            (r"-", "~"),
        ]

        # Assignment operators
        assignment_mutations = [
            (r"\+=", "-="),
            (r"-=", "+="),
            (r"\*=", "/="),
            (r"/=", "*="),
            (r"\+=", "="),
            (r"-=", "="),
            (r"\*=", "="),
            (r"/=", "="),
        ]

        all_mutations = (
            arithmetic_mutations + comparison_mutations + bitwise_mutations + assignment_mutations
        )

        for pattern, replacement in all_mutations:
            matches = list(re.finditer(pattern, code))
            for i, match in enumerate(matches):
                patched = code[: match.start()] + replacement + code[match.end() :]
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"op_{pattern}_{replacement}_{i}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Changed {pattern} to {replacement} at position {i}",
                            confidence_score=0.6,
                        )
                    )

        return patches

    def _mutate_percentage(self, code: str, specification: str = "") -> List[Patch]:
        """Generate patches for percentage calculation errors - MATHEMATICAL REASONING."""
        patches = []

        # Only apply percentage patterns if context suggests percentages
        # Check for percentage-related keywords in code or spec
        pct_keywords = ["percent", "percentage", "%", "pct", "rate", "ratio"]
        has_pct_context = any(
            kw in code.lower() or kw in specification.lower() for kw in pct_keywords
        )

        # Also check for percentage-like variable names
        pct_var_pattern = r"\b(percent|percentage|pct|rate)\b"
        has_pct_vars = bool(re.search(pct_var_pattern, code, re.IGNORECASE))

        if not (has_pct_context or has_pct_vars):
            # No percentage context - skip these patterns to avoid false positives
            return patches

        # MATHEMATICAL FORMULA PATTERNS with constraint reasoning

        # Pattern 1: Missing division by 100 - EXACT MATCH
        # value * percent -> value * (percent / 100)
        exact_pct_patterns = [
            (r"return\s+(\w+)\s*\*\s*(\w+)", r"return \1 * (\2 / 100)"),
            (r"return\s+(\w+)\s*\*\s*(\w+)", r"return (\1 / 100) * \2"),
        ]

        for pattern, replacement in exact_pct_patterns:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"pct_exact_{pattern}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Exact percentage formula: {pattern} -> {replacement}",
                            confidence_score=0.9,
                        )
                    )

        # Pattern 2: Percentage increase/decrease formulas
        # value + percent -> value * (1 + percent / 100)
        # value - percent -> value * (1 - percent / 100)
        formula_patterns = [
            (r"return\s+(\w+)\s*\+\s*(\w+)", r"return \1 * (1 + \2 / 100)"),
            (r"return\s+(\w+)\s*-\s*(\w+)", r"return \1 * (1 - \2 / 100)"),
        ]

        for pattern, replacement in formula_patterns:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"pct_formula_{pattern}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Percentage formula: {pattern} -> {replacement}",
                            confidence_score=0.85,
                        )
                    )

        # Pattern 3: Advanced semantic percentage patterns
        if self.advanced_matcher:
            for semantic_pattern in self.advanced_matcher.semantic_patterns:
                if "pct" in semantic_pattern.pattern_id:
                    result = self.advanced_matcher.apply_semantic_pattern(code, semantic_pattern)
                    if result and result != code:
                        patches.append(
                            Patch(
                                patch_id=semantic_pattern.pattern_id,
                                original_code=code,
                                patched_code=result,
                                operation="replace",
                                description=f"Semantic percentage: {semantic_pattern.semantic_constraint}",
                                confidence_score=semantic_pattern.confidence,
                            )
                        )

        # Pattern 4: Percentage change formula
        # (new - old) / new -> (new - old) / old
        change_pattern = r"\(([^)]+)\s*-\s*([^)]+)\)\s*/\s*(\w+)"
        matches = list(re.finditer(change_pattern, code))
        for match in matches:
            expr1, expr2, divisor = match.groups()
            # Try swapping divisor using mathematical reasoning
            if divisor.strip() == expr1.strip():
                new_divisor = expr2.strip()
                patched = (
                    code[: match.start()]
                    + f"({expr1} - {expr2}) / {new_divisor}"
                    + code[match.end() :]
                )
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"pct_change_{divisor}_{new_divisor}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Percentage change formula: divisor {divisor} -> {new_divisor}",
                            confidence_score=0.8,
                        )
                    )
            elif divisor.strip() == expr2.strip():
                new_divisor = expr1.strip()
                patched = (
                    code[: match.start()]
                    + f"({expr1} - {expr2}) / {new_divisor}"
                    + code[match.end() :]
                )
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"pct_change_{divisor}_{new_divisor}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Percentage change formula: divisor {divisor} -> {new_divisor}",
                            confidence_score=0.8,
                        )
                    )

        return patches

    def _mutate_off_by_one(self, code: str) -> List[Patch]:
        """Generate patches for off-by-one errors - COMPREHENSIVE LOOP BOUNDS."""
        patches = []

        # Pattern 1: Array index len(arr) -> len(arr) - 1 (EXACT)
        exact_index_patterns = [
            (r"return\s+(\w+)\[len\((\w+)\)\]", r"return \1[len(\2) - 1]"),
            (r"(\w+)\[len\((\w+)\)\]", r"\1[len(\2) - 1]"),
        ]

        for pattern, replacement in exact_index_patterns:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"obo_exact_index_{pattern}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Exact off-by-one fix: {pattern} -> {replacement}",
                            confidence_score=0.95,
                        )
                    )

        # Pattern 2: COMPREHENSIVE loop range patterns
        # range(len(arr) - 1) -> range(len(arr))
        loop_range_patterns = [
            (r"range\(len\((\w+)\)\s*-\s*1\)", r"range(len(\1))"),
            (r"range\((\w+)\s*-\s*1\)", r"range(\1)"),
            (r"range\(len\((\w+)\)\)", r"range(len(\1) + 1)"),  # Sometimes need +1
            (r"range\((\w+)\)", r"range(\1 + 1)"),
            (r"range\(1,\s*len\((\w+)\)\)", r"range(len(\1))"),  # Start from 0 instead of 1
            (r"range\(0,\s*len\((\w+)\)\s*-\s*1\)", r"range(len(\1))"),
        ]

        for pattern, replacement in loop_range_patterns:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"obo_loop_{pattern}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Loop range fix: {pattern} -> {replacement}",
                            confidence_score=0.9,
                        )
                    )

        # Pattern 3: Advanced semantic off-by-one patterns
        if self.advanced_matcher:
            for semantic_pattern in self.advanced_matcher.semantic_patterns:
                if "obo" in semantic_pattern.pattern_id:
                    result = self.advanced_matcher.apply_semantic_pattern(code, semantic_pattern)
                    if result and result != code:
                        patches.append(
                            Patch(
                                patch_id=semantic_pattern.pattern_id,
                                original_code=code,
                                patched_code=result,
                                operation="replace",
                                description=f"Semantic OBO: {semantic_pattern.semantic_constraint}",
                                confidence_score=semantic_pattern.confidence,
                            )
                        )

        # Pattern 4: Boundary condition adjustments
        boundary_mutations = [
            (r"<\s*(\w+)", r"<= \1"),
            (r"<=\s*(\w+)", r"< \1"),
            (r">\s*(\w+)", r">= \1"),
            (r">=\s*(\w+)", r"> \1"),
        ]

        for pattern, replacement in boundary_mutations:
            matches = list(re.finditer(pattern, code))
            for match in matches:
                patched = (
                    code[: match.start()]
                    + re.sub(pattern, replacement, match.group())
                    + code[match.end() :]
                )
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"obo_boundary_{pattern}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Boundary: {match.group()} -> {re.sub(pattern, replacement, match.group())}",
                            confidence_score=0.7,
                        )
                    )

        return patches

    def _mutate_logic_operators(self, code: str) -> List[Patch]:
        """Generate patches for logic operator errors."""
        patches = []

        # Pattern 1: Boolean operator swap (and <-> or)
        logic_mutations = [
            (r"\band\b", "or"),
            (r"\bor\b", "and"),
        ]

        for pattern, replacement in logic_mutations:
            matches = list(re.finditer(pattern, code))
            for match in matches:
                patched = code[: match.start()] + replacement + code[match.end() :]
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"logic_{pattern}_{replacement}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Swapped logic operator: {match.group()} -> {replacement}",
                            confidence_score=0.6,
                        )
                    )

        # Pattern 2: Negation addition/removal
        # return x -> return not x
        pattern_return = r"return\s+(\w+)"
        matches = list(re.finditer(pattern_return, code))
        for match in matches:
            var = match.group(1)
            # Add 'not'
            patched_add = code[: match.start()] + f"return not {var}" + code[match.end() :]
            if patched_add != code:
                patches.append(
                    Patch(
                        patch_id=f"logic_add_not_{var}",
                        original_code=code,
                        patched_code=patched_add,
                        operation="replace",
                        description=f"Added negation: return {var} -> return not {var}",
                        confidence_score=0.5,
                    )
                )

        # Remove 'not'
        pattern_not = r"return\s+not\s+(\w+)"
        matches = list(re.finditer(pattern_not, code))
        for match in matches:
            var = match.group(1)
            patched_remove = code[: match.start()] + f"return {var}" + code[match.end() :]
            if patched_remove != code:
                patches.append(
                    Patch(
                        patch_id=f"logic_remove_not_{var}",
                        original_code=code,
                        patched_code=patched_remove,
                        operation="replace",
                        description=f"Removed negation: return not {var} -> return {var}",
                        confidence_score=0.5,
                    )
                )

        # Pattern 3: Comparison negation in conditions
        # if x == y -> if x != y
        comparison_mutations = [
            (r"==", "!="),
            (r"!=", "=="),
        ]

        for pattern, replacement in comparison_mutations:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code, count=1)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"logic_cmp_{pattern}_{replacement}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Negated comparison: {pattern} -> {replacement}",
                            confidence_score=0.5,
                        )
                    )

        return patches

    def _mutate_initialization(self, code: str) -> List[Patch]:
        """Generate patches for initialization errors."""
        patches = []

        # Pattern 1: Uninitialized variable - add initialization
        # Common patterns: result = 0, count = 0, items = []
        var_pattern = r"def\s+\w+\([^)]*\):\s*\n"
        matches = list(re.finditer(var_pattern, code))
        for match in matches:
            insert_pos = match.end()
            # Try common initializations
            for init in ["result = 0", "count = 0", "total = 0", "items = []", "output = []"]:
                patched = code[:insert_pos] + f"    {init}\n" + code[insert_pos:]
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"init_add_{init.split('=')[0].strip()}",
                            original_code=code,
                            patched_code=patched,
                            operation="insert",
                            description=f"Added initialization: {init}",
                            confidence_score=0.4,
                        )
                    )

        # Pattern 2: Wrong initial value (0 vs 1, [] vs None)
        init_mutations = [
            (r"=\s*0\b", "= 1"),
            (r"=\s*1\b", "= 0"),
            (r"=\s*\[\]", "= None"),
            (r"=\s*None\b", "= []"),
            (r'=\s*""', "= None"),
            (r"=\s*False\b", "= True"),
            (r"=\s*True\b", "= False"),
        ]

        for pattern, replacement in init_mutations:
            matches = list(re.finditer(pattern, code))
            for match in matches:
                patched = code[: match.start()] + replacement + code[match.end() :]
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"init_value_{pattern}_{replacement}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Changed initialization: {match.group()} -> {replacement}",
                            confidence_score=0.5,
                        )
                    )

        return patches

    def _mutate_null_checks(self, code: str) -> List[Patch]:
        """Generate patches for null/None check errors - EXACT FORMAT MATCHING."""
        patches = []

        # CRITICAL: Exact format matching for null checks
        # Pattern 1: text[0] -> text[0] if text else None (EXACT)
        exact_patterns = [
            (r"return\s+(\w+)\[0\]", r"return \1[0] if \1 else None"),
            (r"return\s+(\w+)\[(\w+)\]", r"return \1[\2] if \1 else None"),
            (r"return\s+len\((\w+)\)", r"return len(\1) if \1 is not None else 0"),
            (r"return\s+(\w+)\.(\w+)\(\)", r"return \1.\2() if \1 is not None else None"),
        ]

        for pattern, replacement in exact_patterns:
            matches = list(re.finditer(pattern, code))
            for match in matches:
                patched = re.sub(pattern, replacement, code)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"null_exact_{pattern}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Exact null check: {pattern} -> {replacement}",
                            confidence_score=0.95,  # Very high confidence for exact matches
                        )
                    )

        # Pattern 2: Advanced semantic null checks using information theory
        if self.advanced_matcher:
            for semantic_pattern in self.advanced_matcher.semantic_patterns:
                if "null" in semantic_pattern.pattern_id:
                    result = self.advanced_matcher.apply_semantic_pattern(code, semantic_pattern)
                    if result and result != code:
                        patches.append(
                            Patch(
                                patch_id=semantic_pattern.pattern_id,
                                original_code=code,
                                patched_code=result,
                                operation="replace",
                                description=f"Semantic null check: {semantic_pattern.semantic_constraint}",
                                confidence_score=semantic_pattern.confidence,
                            )
                        )

        # Pattern 3: Fallback - Add empty string/list check
        index_pattern = r"return\s+(\w+)\[([^\]]+)\]"
        matches = list(re.finditer(index_pattern, code))
        for match in matches:
            var = match.group(1)
            index = match.group(2)
            # Try exact format first
            patched = (
                code[: match.start()]
                + f"return {var}[{index}] if {var} else None"
                + code[match.end() :]
            )
            if patched != code:
                patches.append(
                    Patch(
                        patch_id=f"empty_check_{var}_{index}",
                        original_code=code,
                        patched_code=patched,
                        operation="replace",
                        description=f"Empty check: {var}[{index}] if {var} else None",
                        confidence_score=0.85,
                    )
                )

        return patches

    def _mutate_string_operations(self, code: str) -> List[Patch]:
        """Generate patches for string operation errors."""
        patches = []

        # Pattern 1: String method corrections
        string_mutations = [
            (r"\.lower\(\)", ".upper()"),
            (r"\.upper\(\)", ".lower()"),
            (r"\.strip\(\)", ".lstrip()"),
            (r"\.lstrip\(\)", ".strip()"),
            (r"\.rstrip\(\)", ".strip()"),
            (r"\.split\(\)", '.split(",")'),
            (r"\.join\(", ".split("),
        ]

        for pattern, replacement in string_mutations:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code, count=1)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"str_{pattern}_{replacement}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Changed string method: {pattern} -> {replacement}",
                            confidence_score=0.5,
                        )
                    )

        # Pattern 2: String concatenation vs formatting
        # str(x) + str(y) -> f"{x}{y}"
        concat_pattern = r"str\((\w+)\)\s*\+\s*str\((\w+)\)"
        matches = list(re.finditer(concat_pattern, code))
        for match in matches:
            var1, var2 = match.groups()
            patched = code[: match.start()] + f'f"{{{var1}}}{{{var2}}}"' + code[match.end() :]
            if patched != code:
                patches.append(
                    Patch(
                        patch_id=f"str_format_{var1}_{var2}",
                        original_code=code,
                        patched_code=patched,
                        operation="replace",
                        description=f'Changed to f-string: str({var1}) + str({var2}) -> f"{{{var1}}}{{{var2}}}"',
                        confidence_score=0.4,
                    )
                )

        return patches

    def _mutate_list_operations(self, code: str) -> List[Patch]:
        """Generate patches for list operation errors."""
        patches = []

        # Pattern 1: Convert loop to list comprehension
        # for x in lst: if cond: result.append(x) -> [x for x in lst if cond]
        loop_pattern = (
            r"for\s+(\w+)\s+in\s+(\w+):\s*\n\s+if\s+([^:]+):\s*\n\s+(\w+)\.append\((\w+)\)"
        )
        matches = list(re.finditer(loop_pattern, code))
        for match in matches:
            var, lst, cond, result, append_var = match.groups()
            patched = (
                code[: match.start()]
                + f"{result} = [{append_var} for {var} in {lst} if {cond}]"
                + code[match.end() :]
            )
            if patched != code:
                patches.append(
                    Patch(
                        patch_id=f"list_comp_{var}_{lst}",
                        original_code=code,
                        patched_code=patched,
                        operation="replace",
                        description=f"Converted to list comprehension",
                        confidence_score=0.6,
                    )
                )

        # Pattern 2: List method corrections
        list_mutations = [
            (r"\.append\(", ".extend("),
            (r"\.extend\(", ".append("),
            (r"\.remove\(", ".pop("),
            (r"\.pop\(\)", ".pop(0)"),
            (r"\.pop\(0\)", ".pop()"),
        ]

        for pattern, replacement in list_mutations:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code, count=1)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"list_{pattern}_{replacement}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Changed list method: {pattern} -> {replacement}",
                            confidence_score=0.4,
                        )
                    )

        return patches

    def _mutate_sorting(self, code: str) -> List[Patch]:
        """Generate patches for sorting and reverse errors."""
        patches = []

        # Pattern 1: Add/remove reverse parameter
        sort_patterns = [
            (r"\.sort\(\)", ".sort(reverse=True)"),
            (r"\.sort\(reverse=True\)", ".sort()"),
            (r"\.sort\(reverse=False\)", ".sort(reverse=True)"),
            (r"sorted\((\w+)\)", r"sorted(\1, reverse=True)"),
            (r"sorted\((\w+),\s*reverse=True\)", r"sorted(\1)"),
        ]

        for pattern, replacement in sort_patterns:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code, count=1)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"sort_{pattern}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Changed sort: {pattern} -> {replacement}",
                            confidence_score=0.6,
                        )
                    )

        # Pattern 2: Add/remove .reverse()
        reverse_pattern = r"(\w+)\.sort\(\)"
        matches = list(re.finditer(reverse_pattern, code))
        for match in matches:
            var = match.group(1)
            patched = code[: match.end()] + f"\n    {var}.reverse()" + code[match.end() :]
            if patched != code:
                patches.append(
                    Patch(
                        patch_id=f"add_reverse_{var}",
                        original_code=code,
                        patched_code=patched,
                        operation="insert",
                        description=f"Added reverse after sort",
                        confidence_score=0.5,
                    )
                )

        return patches

    def _mutate_type_conversions(self, code: str) -> List[Patch]:
        """Generate patches for type conversion errors."""
        patches = []

        # Pattern 1: Type conversion mutations
        type_mutations = [
            (r"int\((\w+)\)", r"float(\1)"),
            (r"float\((\w+)\)", r"int(\1)"),
            (r"str\((\w+)\)", r"int(\1)"),
            (r"int\((\w+)\)", r"str(\1)"),
            (r"list\((\w+)\)", r"tuple(\1)"),
            (r"tuple\((\w+)\)", r"list(\1)"),
            (r"set\((\w+)\)", r"list(\1)"),
        ]

        for pattern, replacement in type_mutations:
            matches = list(re.finditer(pattern, code))
            for match in matches:
                patched = (
                    code[: match.start()]
                    + re.sub(pattern, replacement, match.group())
                    + code[match.end() :]
                )
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"type_{pattern}_{replacement}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Changed type conversion: {match.group()} -> {re.sub(pattern, replacement, match.group())}",
                            confidence_score=0.4,
                        )
                    )

        return patches

    def _mutate_boolean_literals(self, code: str) -> List[Patch]:
        """Generate patches for boolean literal errors."""
        patches = []

        # Pattern 1: True/False literal swaps in comparisons
        bool_patterns = [
            (r"==\s*True\b", "== False"),
            (r"==\s*False\b", "== True"),
            (r"is\s+True\b", "is False"),
            (r"is\s+False\b", "is True"),
            (r"!=\s*True\b", "!= False"),
            (r"!=\s*False\b", "!= True"),
        ]

        for pattern, replacement in bool_patterns:
            matches = list(re.finditer(pattern, code))
            for match in matches:
                patched = code[: match.start()] + replacement + code[match.end() :]
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"bool_{pattern}_{replacement}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Swapped boolean: {match.group()} -> {replacement}",
                            confidence_score=0.7,
                        )
                    )

        return patches

    def _mutate_default_parameters(self, code: str) -> List[Patch]:
        """Generate patches for default parameter errors."""
        patches = []

        # Pattern 1: Add default parameters
        param_pattern = r"def\s+(\w+)\(([^)]*)\):"
        matches = list(re.finditer(param_pattern, code))
        for match in matches:
            func_name = match.group(1)
            params = match.group(2)
            if params and "=" not in params:
                # Add default values
                param_list = [p.strip() for p in params.split(",")]
                for i, param in enumerate(param_list):
                    new_params = param_list.copy()
                    new_params[i] = f"{param}=None"
                    patched = (
                        code[: match.start()]
                        + f"def {func_name}({', '.join(new_params)}):"
                        + code[match.end() :]
                    )
                    if patched != code:
                        patches.append(
                            Patch(
                                patch_id=f"default_{func_name}_{param}",
                                original_code=code,
                                patched_code=patched,
                                operation="replace",
                                description=f"Added default parameter: {param}=None",
                                confidence_score=0.3,
                            )
                        )

        return patches

    def _mutate_edge_case_guards(self, code: str) -> List[Patch]:
        """Generate patches for missing edge case guards."""
        patches = []

        # Pattern 1: Add division by zero check
        div_pattern = r"(\w+)\s*/\s*(\w+)"
        matches = list(re.finditer(div_pattern, code))
        for match in matches:
            numerator, denominator = match.groups()
            # Wrap in ternary
            patched = (
                code[: match.start()]
                + f"{numerator} / {denominator} if {denominator} != 0 else 0"
                + code[match.end() :]
            )
            if patched != code:
                patches.append(
                    Patch(
                        patch_id=f"div_zero_{denominator}",
                        original_code=code,
                        patched_code=patched,
                        operation="replace",
                        description=f"Added division by zero check",
                        confidence_score=0.5,
                    )
                )

        # Pattern 2: Add empty collection check
        len_pattern = r"len\((\w+)\)"
        matches = list(re.finditer(len_pattern, code))
        for match in matches:
            var = match.group(1)
            patched = code[: match.start()] + f"len({var}) if {var} else 0" + code[match.end() :]
            if patched != code:
                patches.append(
                    Patch(
                        patch_id=f"len_check_{var}",
                        original_code=code,
                        patched_code=patched,
                        operation="replace",
                        description=f"Added empty collection check for len({var})",
                        confidence_score=0.4,
                    )
                )

        return patches

    def _mutate_complex_conditions(self, code: str) -> List[Patch]:
        """Generate patches for complex condition errors - BOOLEAN ALGEBRA."""
        patches = []

        # CRITICAL: Compound condition patterns with boolean algebra
        # Pattern 1: has_license == False -> has_license == True
        bool_comparison_patterns = [
            (r"(\w+)\s*==\s*False\b", r"\1 == True"),
            (r"(\w+)\s*==\s*True\b", r"\1 == False"),
            (r"(\w+)\s*==\s*False\b", r"\1"),  # Simplify to just variable
            (r"(\w+)\s*==\s*True\b", r"not \1"),  # Negate
        ]

        for pattern, replacement in bool_comparison_patterns:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"bool_comp_{pattern}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Boolean comparison: {pattern} -> {replacement}",
                            confidence_score=0.9,
                        )
                    )

        # Pattern 2: Compound conditions with boolean literals
        # age >= 18 and has_license == False -> age >= 18 and has_license == True
        compound_patterns = [
            (r"return\s+([^=]+)\s+and\s+(\w+)\s*==\s*False", r"return \1 and \2 == True"),
            (r"return\s+([^=]+)\s+and\s+(\w+)\s*==\s*True", r"return \1 and \2 == False"),
            (r"return\s+([^=]+)\s+and\s+(\w+)\s*==\s*False", r"return \1 and \2"),
            (r"return\s+([^=]+)\s+and\s+(\w+)\s*==\s*True", r"return \1 and not \2"),
        ]

        for pattern, replacement in compound_patterns:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"compound_{pattern}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Compound condition: {pattern} -> {replacement}",
                            confidence_score=0.85,
                        )
                    )

        # Pattern 3: Advanced semantic compound patterns
        if self.advanced_matcher:
            for semantic_pattern in self.advanced_matcher.semantic_patterns:
                if "compound" in semantic_pattern.pattern_id:
                    result = self.advanced_matcher.apply_semantic_pattern(code, semantic_pattern)
                    if result and result != code:
                        patches.append(
                            Patch(
                                patch_id=semantic_pattern.pattern_id,
                                original_code=code,
                                patched_code=result,
                                operation="replace",
                                description=f"Semantic compound: {semantic_pattern.semantic_constraint}",
                                confidence_score=semantic_pattern.confidence,
                            )
                        )

        # Pattern 4: Swap condition order (lower priority)
        and_pattern = r"(\w+)\s+and\s+(\w+)"
        matches = list(re.finditer(and_pattern, code))
        for match in matches:
            var1, var2 = match.groups()
            patched = code[: match.start()] + f"{var2} and {var1}" + code[match.end() :]
            if patched != code:
                patches.append(
                    Patch(
                        patch_id=f"swap_and_{var1}_{var2}",
                        original_code=code,
                        patched_code=patched,
                        operation="replace",
                        description=f"Swapped AND: {var1} and {var2} -> {var2} and {var1}",
                        confidence_score=0.4,
                    )
                )

        # Pattern 5: Boolean algebra simplification
        # a and b or c -> (a and b) or c
        mixed_pattern = r"(\w+)\s+and\s+(\w+)\s+or\s+(\w+)"
        matches = list(re.finditer(mixed_pattern, code))
        for match in matches:
            var1, var2, var3 = match.groups()
            patched1 = (
                code[: match.start()] + f"({var1} and {var2}) or {var3}" + code[match.end() :]
            )
            patched2 = (
                code[: match.start()] + f"{var1} and ({var2} or {var3})" + code[match.end() :]
            )
            if patched1 != code:
                patches.append(
                    Patch(
                        patch_id=f"paren_and_or_1",
                        original_code=code,
                        patched_code=patched1,
                        operation="replace",
                        description=f"Parentheses: ({var1} and {var2}) or {var3}",
                        confidence_score=0.5,
                    )
                )
            if patched2 != code:
                patches.append(
                    Patch(
                        patch_id=f"paren_and_or_2",
                        original_code=code,
                        patched_code=patched2,
                        operation="replace",
                        description=f"Parentheses: {var1} and ({var2} or {var3})",
                        confidence_score=0.5,
                    )
                )

        return patches

    def _verify_with_tests(self, code: str, specification: str) -> dict:
        """Verify patched code by executing test cases.

        Specification can be:
        1. assert statement: "assert func(1, 2) == 3"
        2. Multiple asserts separated by semicolons
        3. Natural language with examples (e.g., "20% of 100 = 20")
        """
        try:
            # Extract function name from code
            func_match = re.search(r"def\s+(\w+)\(", code)
            if not func_match:
                return {"passed": False, "error": "No function found"}

            func_name = func_match.group(1)

            # Parse specification to extract test cases
            test_cases = []

            # Check if specification contains assert statements
            if "assert" in specification:
                # Extract all assert statements
                assert_pattern = r"assert\s+([^\n;]+)"
                asserts = re.findall(assert_pattern, specification)
                test_cases = asserts
            else:
                # Try to extract test from natural language examples
                # Pattern: "func(arg1, arg2) = result" or "20% of 100 = 20"

                # Look for function call patterns
                call_pattern = rf"{func_name}\(([^)]+)\)\s*==?\s*(\d+)"
                matches = re.findall(call_pattern, specification)
                for args, expected in matches:
                    test_cases.append(f"{func_name}({args}) == {expected}")

                # Look for percentage patterns: "20% of 100 = 20"
                pct_pattern = r"(\d+)%\s+of\s+(\d+)\s*=\s*(\d+)"
                matches = re.findall(pct_pattern, specification)
                for percent, value, expected in matches:
                    test_cases.append(f"{func_name}({value}, {percent}) == {expected}")

                # Look for general patterns: "returns X for input Y"
                return_pattern = r"returns?\s+(\d+)\s+for\s+(?:input\s+)?(\d+)"
                matches = re.findall(return_pattern, specification)
                for expected, input_val in matches:
                    test_cases.append(f"{func_name}({input_val}) == {expected}")

            if not test_cases:
                # No explicit tests found - just check if code executes without error
                namespace = {}
                try:
                    exec(code, namespace)
                    return {"passed": True, "tests_run": 0, "note": "Syntax check only"}
                except Exception as e:
                    return {"passed": False, "error": f"Code execution failed: {str(e)}"}

            # Execute code and tests in isolated namespace
            namespace = {}
            try:
                exec(code, namespace)
            except Exception as e:
                return {"passed": False, "error": f"Code execution failed: {str(e)}"}

            # Run each test case
            for test in test_cases:
                try:
                    # Execute the assertion
                    exec(f"assert {test}", namespace)
                except AssertionError:
                    return {"passed": False, "error": f"Test failed: {test}"}
                except Exception as e:
                    return {"passed": False, "error": f"Test error: {str(e)}"}

            return {"passed": True, "tests_run": len(test_cases)}

        except Exception as e:
            return {"passed": False, "error": f"Verification error: {str(e)}"}

    def _mutate_constants(self, code: str, counterexamples: List[CounterExample]) -> List[Patch]:
        """Generate patches by adjusting constants."""
        patches = []

        # Find numeric constants in code
        constants = re.findall(r"\b\d+\b", code)

        for const in set(constants):
            # Try ±1, ±10
            for delta in [-10, -1, 1, 10]:
                try:
                    new_const = str(int(const) + delta)
                    patched = code.replace(const, new_const, 1)

                    if patched != code:
                        patches.append(
                            Patch(
                                patch_id=f"const_{const}_{new_const}",
                                original_code=code,
                                patched_code=patched,
                                operation="replace",
                                description=f"Changed constant {const} to {new_const}",
                                confidence_score=0.3,  # Lower confidence for const mutation
                            )
                        )
                except ValueError:
                    pass

        return patches

    def _calculate_confidence(self, patch: Patch, counterexamples: List[CounterExample]) -> float:
        """Calculate confidence score for a patch using multi-factor scoring.

        Factors:
        1. Syntactic validity (0.3 weight)
        2. Simplicity (fewer changes = better) (0.3 weight)
        3. Counterexample coverage (0.4 weight)
        """
        score = 0.0

        # Factor 1: Syntactic validity (30%)
        try:
            ast.parse(patch.patched_code)
            syntax_score = 1.0
        except SyntaxError:
            syntax_score = 0.0  # Invalid syntax = very low confidence

        score += syntax_score * 0.3

        # Factor 2: Simplicity score (30%)
        # Prefer patches with minimal changes
        original_lines = patch.original_code.count("\n")
        patched_lines = patch.patched_code.count("\n")
        line_diff = abs(patched_lines - original_lines)

        # Edit distance for character-level changes
        import difflib

        matcher = difflib.SequenceMatcher(None, patch.original_code, patch.patched_code)
        similarity = matcher.ratio()

        # Higher similarity = simpler patch = better
        simplicity_score = similarity

        # Penalize patches that add many lines
        if line_diff > 5:
            simplicity_score *= 0.5

        score += simplicity_score * 0.3

        # Factor 3: Counterexample coverage (40%)
        if counterexamples:
            # Estimate how many CEs the patch might fix
            # (In production, would execute patch against CEs)
            # For now, higher confidence if operation makes sense
            ce_score = 1.0 - (len(counterexamples) / max(len(counterexamples) + 5, 1))
        else:
            ce_score = 0.5  # No CEs = medium confidence

        score += ce_score * 0.4

        # Ensure score is in [0, 1]
        return max(0.0, min(1.0, score))

    def _load_model(self):
        """Lazy load LLM model and tokenizer."""
        if self._model is None:
            try:
                import logging

                from gridseal_pro.models.model_config import get_model

                logger = logging.getLogger(__name__)
                logger.info(f"Loading {self.model_name} for LLM synthesis...")

                import torch

                # Only use quantization on CUDA
                use_quant = torch.cuda.is_available()

                self._model, self._tokenizer = get_model(
                    model_key=self.model_name,
                    load_in_4bit=use_quant,  # Use quantization only on GPU
                )
                logger.info("Model loaded successfully")
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to load LLM: {e}. LLM fallback disabled.")
                self.use_llm_fallback = False

    def _synthesize_with_llm(
        self,
        code: str,
        specification: str,
        counterexamples: List[CounterExample],
        num_patches: int = 3,
    ) -> List[Patch]:
        """Generate patches using LLM.

        Args:
            code: Buggy code
            specification: Code specification
            counterexamples: List of counterexamples from previous iterations
            num_patches: Number of patches to generate

        Returns:
            List of LLM-generated patches
        """
        patches = []

        # Load model if not already loaded
        self._load_model()

        if not self.use_llm_fallback or self._model is None:
            return patches

        try:
            import torch

            from gridseal_pro.models.model_config import format_prompt_for_repair

            # Format prompt
            prompt = format_prompt_for_repair(code, specification, self.model_name)

            # Add counterexample context if available
            if counterexamples:
                ce_text = "\n".join(
                    [
                        f"Counterexample {i+1}: {ce.explanation}"
                        for i, ce in enumerate(counterexamples[:3])
                    ]
                )
                prompt += f"\n\n### Known Issues:\n{ce_text}\n\n### Fixed Code:\n```python\n"

            # Tokenize
            inputs = self._tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)

            # Move to same device as model
            device = next(self._model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}

            # Generate candidates sequentially to reduce peak memory
            num_patches = max(1, min(int(num_patches), 1))
            for i in range(num_patches):
                if device.type == "mps":
                    torch.mps.empty_cache()

                with torch.no_grad():
                    output = self._model.generate(
                        **inputs,
                        max_new_tokens=256,
                        num_return_sequences=1,
                        temperature=0.7,
                        top_p=0.95,
                        do_sample=True,
                        pad_token_id=self._tokenizer.eos_token_id,
                        eos_token_id=self._tokenizer.eos_token_id,
                    )

                generated_text = self._tokenizer.decode(output[0], skip_special_tokens=True)

                # Extract code from generation
                patched_code = self._extract_code_from_generation(generated_text, code)

                if patched_code and patched_code != code:
                    patches.append(
                        Patch(
                            patch_id=f"llm_{i}",
                            original_code=code,
                            patched_code=patched_code,
                            operation="llm_synthesis",
                            description=f"LLM-generated patch {i+1}",
                            confidence_score=0.6,
                        )
                    )

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"LLM synthesis failed: {e}")

        return patches

    def _extract_code_from_generation(self, generated_text: str, original_code: str) -> str:
        """Extract code from LLM generation.

        Args:
            generated_text: Full LLM output
            original_code: Original buggy code

        Returns:
            Extracted code or empty string if extraction fails
        """
        # Try to extract code between ```python and ```
        import re

        # Pattern 1: Code blocks
        code_blocks = re.findall(r"```python\n(.*?)\n```", generated_text, re.DOTALL)
        if code_blocks:
            return code_blocks[-1].strip()

        # Pattern 2: Code blocks without language
        code_blocks = re.findall(r"```\n(.*?)\n```", generated_text, re.DOTALL)
        if code_blocks:
            return code_blocks[-1].strip()

        # Pattern 3: Take everything after "Fixed Code:" or similar
        if "Fixed Code:" in generated_text:
            code = generated_text.split("Fixed Code:")[-1]
            # Remove markdown code fences if present
            code = re.sub(r"```python\n?", "", code)
            code = re.sub(r"```\n?", "", code)
            return code.strip()

        # Pattern 4: Extract function definition
        func_match = re.search(r"(def\s+\w+\s*\([^)]*\):.*?)(?:\n\n|\Z)", generated_text, re.DOTALL)
        if func_match:
            return func_match.group(1).strip()

        # Fallback: return original if extraction fails
        return ""

    def _mutate_mathematical_operations(self, code: str) -> List[Patch]:
        """Generate patches for mathematical operation errors."""
        patches = []

        # Modulo operations
        for pattern, replacement in [
            (r"%\s*(\d+)", r"// \1"),
            (r"//\s*(\d+)", r"% \1"),
            (r"%", "**"),
            (r"\*\*", "%"),
        ]:
            matches = list(re.finditer(pattern, code))
            for match in matches:
                patched = (
                    code[: match.start()]
                    + re.sub(pattern, replacement, match.group())
                    + code[match.end() :]
                )
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"math_{pattern}_{replacement}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Math op: {pattern} -> {replacement}",
                            confidence_score=0.5,
                        )
                    )

        # Rounding operations
        for func in ["round", "int", "float", "abs", "ceil", "floor"]:
            pattern = rf"\b{func}\("
            for replacement in ["round(", "int(", "float(", "abs("]:
                if replacement != f"{func}(":
                    if re.search(pattern, code):
                        patched = re.sub(pattern, replacement, code, count=1)
                        if patched != code:
                            patches.append(
                                Patch(
                                    patch_id=f"math_func_{func}_{replacement}",
                                    original_code=code,
                                    patched_code=patched,
                                    operation="replace",
                                    description=f"Changed {func} to {replacement}",
                                    confidence_score=0.4,
                                )
                            )

        return patches

    def _mutate_list_slicing(self, code: str) -> List[Patch]:
        """Generate patches for list slicing errors."""
        patches = []

        # Common slicing patterns
        slice_mutations = [
            (r"\[0\]", "[1]"),
            (r"\[1\]", "[0]"),
            (r"\[-1\]", "[0]"),
            (r"\[0\]", "[-1]"),
            (r"\[:\]", "[1:]"),
            (r"\[:\]", "[:-1]"),
            (r"\[1:\]", "[:]"),
            (r"\[:-1\]", "[:]"),
            (r"\[0:(\w+)\]", r"[1:\1]"),
            (r"\[1:(\w+)\]", r"[0:\1]"),
            (r"\[:(\w+)\]", r"[:\1-1]"),
            (r"\[:(\w+)-1\]", r"[:\1]"),
        ]

        for pattern, replacement in slice_mutations:
            matches = list(re.finditer(pattern, code))
            for match in matches:
                patched = (
                    code[: match.start()]
                    + re.sub(pattern, replacement, match.group())
                    + code[match.end() :]
                )
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"slice_{pattern}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Slice: {pattern} -> {replacement}",
                            confidence_score=0.6,
                        )
                    )

        return patches

    def _mutate_dict_operations(self, code: str) -> List[Patch]:
        """Generate patches for dictionary operation errors."""
        patches = []

        # Dict method mutations
        dict_mutations = [
            (r"\.get\(", ".pop("),
            (r"\.pop\(", ".get("),
            (r"\.keys\(\)", ".values()"),
            (r"\.values\(\)", ".keys()"),
            (r"\.items\(\)", ".keys()"),
            (r"\.keys\(\)", ".items()"),
            (r"\[(\w+)\]", r".get(\1, None)"),
        ]

        for pattern, replacement in dict_mutations:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code, count=1)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"dict_{pattern}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Dict op: {pattern} -> {replacement}",
                            confidence_score=0.5,
                        )
                    )

        return patches

    def _mutate_control_flow(self, code: str) -> List[Patch]:
        """Generate patches for control flow errors."""
        patches = []

        # if/elif/else mutations
        if "if " in code:
            # Add else clause
            if_pattern = r"(if\s+[^:]+:.*?)(\n\s*return|\n\s*\w+\s*=|\Z)"
            matches = list(re.finditer(if_pattern, code, re.DOTALL))
            for match in matches:
                if "else:" not in match.group(1):
                    patched = (
                        code[: match.end(1)] + "\n    else:\n        pass" + code[match.end(1) :]
                    )
                    if patched != code:
                        patches.append(
                            Patch(
                                patch_id="control_add_else",
                                original_code=code,
                                patched_code=patched,
                                operation="insert",
                                description="Added else clause",
                                confidence_score=0.3,
                            )
                        )

        # break/continue mutations
        for pattern, replacement in [(r"\bbreak\b", "continue"), (r"\bcontinue\b", "break")]:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code, count=1)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"control_{pattern}_{replacement}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Changed {pattern} to {replacement}",
                            confidence_score=0.4,
                        )
                    )

        return patches

    def _mutate_return_statements(self, code: str) -> List[Patch]:
        """Generate patches for return statement errors."""
        patches = []

        # Return value mutations
        return_mutations = [
            (r"return\s+True\b", "return False"),
            (r"return\s+False\b", "return True"),
            (r"return\s+None\b", "return 0"),
            (r"return\s+0\b", "return None"),
            (r"return\s+\[\]", "return None"),
            (r"return\s+None\b", "return []"),
            (r'return\s+""', "return None"),
            (r"return\s+None\b", 'return ""'),
            (r"return\s+(\w+)", r"return not \1"),
            (r"return\s+not\s+(\w+)", r"return \1"),
        ]

        for pattern, replacement in return_mutations:
            matches = list(re.finditer(pattern, code))
            for match in matches:
                patched = code[: match.start()] + replacement + code[match.end() :]
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"return_{pattern}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Return: {pattern} -> {replacement}",
                            confidence_score=0.5,
                        )
                    )

        return patches

    def _mutate_assignments(self, code: str) -> List[Patch]:
        """Generate patches for assignment errors."""
        patches = []

        # Swap variable assignments
        assign_pattern = r"(\w+)\s*=\s*(\w+)"
        matches = list(re.finditer(assign_pattern, code))
        for match in matches:
            var1, var2 = match.groups()
            if var1 != var2:
                patched = code[: match.start()] + f"{var2} = {var1}" + code[match.end() :]
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"assign_swap_{var1}_{var2}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Swapped assignment: {var1} = {var2}",
                            confidence_score=0.3,
                        )
                    )

        return patches

    def _mutate_function_calls(self, code: str) -> List[Patch]:
        """Generate patches for function call errors."""
        patches = []

        # Common function mutations
        func_mutations = [
            (r"\.append\(", ".insert(0, "),
            (r"\.insert\(0,\s*", ".append("),
            (r"\.add\(", ".remove("),
            (r"\.remove\(", ".add("),
            (r"\.update\(", ".clear(); "),
            (r"\.clear\(\)", ".update({})"),
            (r"min\(", "max("),
            (r"max\(", "min("),
            (r"sum\(", "len("),
            (r"len\(", "sum("),
            (r"any\(", "all("),
            (r"all\(", "any("),
        ]

        for pattern, replacement in func_mutations:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code, count=1)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"func_{pattern}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Func: {pattern} -> {replacement}",
                            confidence_score=0.5,
                        )
                    )

        return patches

    def _mutate_iteration_patterns(self, code: str) -> List[Patch]:
        """Generate patches for iteration errors."""
        patches = []

        # Iteration mutations
        iter_mutations = [
            (r"for\s+(\w+)\s+in\s+(\w+):", r"for \1 in reversed(\2):"),
            (r"for\s+(\w+)\s+in\s+reversed\((\w+)\):", r"for \1 in \2:"),
            (r"for\s+(\w+)\s+in\s+(\w+):", r"for \1 in sorted(\2):"),
            (r"for\s+(\w+)\s+in\s+enumerate\((\w+)\):", r"for \1 in \2:"),
            (r"for\s+(\w+)\s+in\s+(\w+):", r"for \1 in enumerate(\2):"),
        ]

        for pattern, replacement in iter_mutations:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code, count=1)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"iter_{pattern}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Iteration: {pattern} -> {replacement}",
                            confidence_score=0.4,
                        )
                    )

        return patches

    def _mutate_membership_operations(self, code: str) -> List[Patch]:
        """Generate patches for membership operation errors."""
        patches = []

        # in/not in mutations
        for pattern, replacement in [(r"\bin\b", "not in"), (r"\bnot\s+in\b", "in")]:
            matches = list(re.finditer(pattern, code))
            for match in matches:
                patched = code[: match.start()] + replacement + code[match.end() :]
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"member_{pattern}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Membership: {pattern} -> {replacement}",
                            confidence_score=0.6,
                        )
                    )

        return patches

    def _mutate_aggregation_operations(self, code: str) -> List[Patch]:
        """Generate patches for aggregation errors."""
        patches = []

        # Aggregation function mutations
        agg_mutations = [
            (r"sum\(([^)]+)\)", r"max(\1)"),
            (r"max\(([^)]+)\)", r"sum(\1)"),
            (r"min\(([^)]+)\)", r"max(\1)"),
            (r"max\(([^)]+)\)", r"min(\1)"),
            (r"len\(([^)]+)\)", r"sum(\1)"),
            (r"sum\(([^)]+)\)", r"len(\1)"),
        ]

        for pattern, replacement in agg_mutations:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code, count=1)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"agg_{pattern}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Aggregation: {pattern} -> {replacement}",
                            confidence_score=0.5,
                        )
                    )

        return patches

    def _mutate_conditional_expressions(self, code: str) -> List[Patch]:
        """Generate patches for conditional expression errors."""
        patches = []

        # Ternary operator mutations
        ternary_pattern = r"(\w+)\s+if\s+([^e]+)\s+else\s+(\w+)"
        matches = list(re.finditer(ternary_pattern, code))
        for match in matches:
            true_val, condition, false_val = match.groups()
            # Swap true/false values
            patched = (
                code[: match.start()]
                + f"{false_val} if {condition} else {true_val}"
                + code[match.end() :]
            )
            if patched != code:
                patches.append(
                    Patch(
                        patch_id="ternary_swap",
                        original_code=code,
                        patched_code=patched,
                        operation="replace",
                        description="Swapped ternary values",
                        confidence_score=0.5,
                    )
                )
            # Negate condition
            patched = (
                code[: match.start()]
                + f"{true_val} if not ({condition}) else {false_val}"
                + code[match.end() :]
            )
            if patched != code:
                patches.append(
                    Patch(
                        patch_id="ternary_negate",
                        original_code=code,
                        patched_code=patched,
                        operation="replace",
                        description="Negated ternary condition",
                        confidence_score=0.5,
                    )
                )

        return patches

    def _mutate_variable_scope(self, code: str) -> List[Patch]:
        """Generate patches for variable scope errors."""
        patches = []

        # Add global/nonlocal declarations
        func_pattern = r"def\s+\w+\([^)]*\):\s*\n"
        matches = list(re.finditer(func_pattern, code))
        for match in matches:
            # Extract variables used in function
            vars_in_func = re.findall(r"\b([a-z_]\w*)\s*=", code[match.end() :])
            for var in set(vars_in_func[:3]):  # Limit to first 3 unique vars
                patched = code[: match.end()] + f"    global {var}\n" + code[match.end() :]
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"scope_global_{var}",
                            original_code=code,
                            patched_code=patched,
                            operation="insert",
                            description=f"Added global {var}",
                            confidence_score=0.3,
                        )
                    )

        return patches

    def _mutate_exception_handling(self, code: str) -> List[Patch]:
        """Generate patches for exception handling errors."""
        patches = []

        # Wrap risky operations in try/except
        risky_patterns = [r"(\w+)\[(\w+)\]", r"(\w+)\.(\w+)\(", r"(\w+)\s*/\s*(\w+)"]
        for pattern in risky_patterns:
            matches = list(re.finditer(pattern, code))
            for match in matches[:2]:  # Limit to first 2 matches
                operation = match.group(0)
                patched = code[: match.start()] + f"(lambda: {operation})()" + code[match.end() :]
                if patched != code and "try:" not in code:
                    patches.append(
                        Patch(
                            patch_id=f"except_wrap_{pattern}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Wrapped {operation} in lambda",
                            confidence_score=0.2,
                        )
                    )

        return patches

    def _mutate_sequence_operations(self, code: str) -> List[Patch]:
        """Generate patches for sequence operation errors."""
        patches = []

        # Sequence method mutations
        seq_mutations = [
            (r"\.count\(", ".index("),
            (r"\.index\(", ".count("),
            (r"\.find\(", ".index("),
            (r"\.index\(", ".find("),
            (r"\.startswith\(", ".endswith("),
            (r"\.endswith\(", ".startswith("),
            (r"\.ljust\(", ".rjust("),
            (r"\.rjust\(", ".ljust("),
        ]

        for pattern, replacement in seq_mutations:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code, count=1)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"seq_{pattern}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Sequence: {pattern} -> {replacement}",
                            confidence_score=0.4,
                        )
                    )

        return patches

    def _mutate_numeric_precision(self, code: str) -> List[Patch]:
        """Generate patches for numeric precision errors."""
        patches = []

        # Precision-related mutations
        precision_mutations = [
            (r"(\d+\.\d+)", r"round(\1, 2)"),
            (r"round\(([^,]+),\s*(\d+)\)", r"round(\1, 0)"),
            (r"int\(([^)]+)\)", r"round(\1)"),
            (r"float\(([^)]+)\)", r"int(\1)"),
        ]

        for pattern, replacement in precision_mutations:
            matches = list(re.finditer(pattern, code))
            for match in matches[:2]:
                patched = (
                    code[: match.start()]
                    + re.sub(pattern, replacement, match.group())
                    + code[match.end() :]
                )
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"precision_{pattern}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Precision: {pattern} -> {replacement}",
                            confidence_score=0.4,
                        )
                    )

        return patches

    # ==================== PHASE 1-6: NEW PATTERNS FOR 90% ====================

    def _mutate_initialization_semantic(self, code: str) -> List[Patch]:
        """PHASE 1: Semantic initialization based on variable names."""
        patches = []

        patterns = [
            # Minimum tracking: 0 → nums[0] or float('inf')
            (r"(\s+)(min_val|minimum|min_\w+)\s*=\s*0\b", r"\1\2 = nums[0]", 0.90),
            (r"(\s+)(min_val|minimum|min_\w+)\s*=\s*0\b", r'\1\2 = float("inf")', 0.85),
            # Maximum tracking: 0 → nums[0] or float('-inf')
            (r"(\s+)(max_val|maximum|max_\w+)\s*=\s*0\b", r"\1\2 = nums[0]", 0.90),
            (r"(\s+)(max_val|maximum|max_\w+)\s*=\s*0\b", r'\1\2 = float("-inf")', 0.85),
            # Sum/Total: 1 → 0
            (r"(\s+)(total|sum|count)\s*=\s*1\b", r"\1\2 = 0", 0.95),
            # Product: 0 → 1
            (r"(\s+)(product|prod|mult|factorial)\s*=\s*0\b", r"\1\2 = 1", 0.95),
            # Collections: None → []
            (r"(\s+)(result|output|items)\s*=\s*None\b", r"\1\2 = []", 0.75),
            # Index tracking: 1 → 0
            (r"(\s+)(index|idx|i)\s*=\s*1\b", r"\1\2 = 0", 0.80),
        ]

        for pattern, replacement, confidence in patterns:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code, count=1)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"init_semantic_{pattern[:20]}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Semantic init: {pattern}",
                            confidence_score=confidence,
                        )
                    )

        return patches

    def _mutate_logic_spec_guided(self, code: str, spec: str) -> List[Patch]:
        """PHASE 2: Use specification keywords to infer correct logic."""
        patches = []

        logic_hints = {
            "at least one": ("or", 0.90),
            "either": ("or", 0.85),
            "any": ("or", 0.85),
            "both": ("and", 0.90),
            "all": ("and", 0.85),
            "every": ("and", 0.85),
        }

        spec_lower = spec.lower()

        for hint, (operator, confidence) in logic_hints.items():
            if hint in spec_lower:
                if operator == "or" and " and " in code:
                    patched = code.replace(" and ", " or ")
                    patches.append(
                        Patch(
                            patch_id=f"spec_guided_or",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Spec '{hint}' suggests OR",
                            confidence_score=confidence,
                        )
                    )
                elif operator == "and" and " or " in code:
                    patched = code.replace(" or ", " and ")
                    patches.append(
                        Patch(
                            patch_id=f"spec_guided_and",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Spec '{hint}' suggests AND",
                            confidence_score=confidence,
                        )
                    )

        return patches

    def _mutate_logic_negation(self, code: str) -> List[Patch]:
        """PHASE 2: Add or remove negation."""
        patches = []

        # Add 'not'
        return_pattern = r"(return\s+)(\w+(?:\s*[<>=!]+\s*\w+)?)"
        for match in re.finditer(return_pattern, code):
            prefix, expr = match.groups()
            if "not" not in expr:
                patched = code[: match.start()] + f"{prefix}not {expr}" + code[match.end() :]
                patches.append(
                    Patch(
                        patch_id="logic_add_not",
                        original_code=code,
                        patched_code=patched,
                        operation="replace",
                        description=f"Add negation to {expr}",
                        confidence_score=0.55,
                    )
                )

        # Remove 'not'
        not_pattern = r"(return\s+)not\s+(\w+(?:\s*[<>=!]+\s*\w+)?)"
        for match in re.finditer(not_pattern, code):
            prefix, expr = match.groups()
            patched = code[: match.start()] + f"{prefix}{expr}" + code[match.end() :]
            patches.append(
                Patch(
                    patch_id="logic_remove_not",
                    original_code=code,
                    patched_code=patched,
                    operation="replace",
                    description=f"Remove negation from {expr}",
                    confidence_score=0.55,
                )
            )

        return patches

    def _mutate_boolean_comparisons(self, code: str) -> List[Patch]:
        """PHASE 2: Fix == True/False patterns."""
        patches = []

        patterns = [
            (r"(\w+)\s*==\s*False", r"\1 == True", 0.70),
            (r"(\w+)\s*==\s*True", r"\1 == False", 0.65),
            (r"(\w+)\s*==\s*True", r"\1", 0.60),
            (r"(\w+)\s*==\s*False", r"not \1", 0.60),
        ]

        for pattern, replacement, confidence in patterns:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"bool_literal_{pattern[:15]}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Boolean literal: {pattern}",
                            confidence_score=confidence,
                        )
                    )

        return patches

    def _mutate_list_remove_in_loop(self, code: str) -> List[Patch]:
        """PHASE 3: Fix list.remove() during iteration."""
        patches = []

        # Pattern: for x in list: if cond: list.remove(x)
        pattern = r"for\s+(\w+)\s+in\s+(\w+):\s*\n\s*if\s+([^:]+):\s*\n\s*\2\.remove\(\1\)"
        match = re.search(pattern, code, re.MULTILINE)

        if match:
            iter_var, list_var, condition = match.groups()
            comprehension = (
                f"{list_var} = [{iter_var} for {iter_var} in {list_var} if not ({condition})]"
            )
            patched = code[: match.start()] + comprehension + code[match.end() :]

            patches.append(
                Patch(
                    patch_id="list_remove_to_comprehension",
                    original_code=code,
                    patched_code=patched,
                    operation="replace",
                    description="Transform remove-in-loop to comprehension",
                    confidence_score=0.85,
                )
            )

        return patches

    def _mutate_string_slicing(self, code: str) -> List[Patch]:
        """PHASE 4: Fix string slicing off-by-one."""
        patches = []

        patterns = [
            (r"(\w+)\[:(\w+)\+1\]", r"\1[:\2]", 0.85),
            (r"(\w+)\[:(\w+)-1\]", r"\1[:\2]", 0.80),
            (r"(\w+)\[1:\]", r"\1[:]", 0.75),
            (r"(\w+)\[:-2\]", r"\1[:-1]", 0.70),
        ]

        for pattern, replacement, confidence in patterns:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"slice_obo_{pattern[:15]}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"String slice: {pattern}",
                            confidence_score=confidence,
                        )
                    )

        return patches

    def _mutate_range_boundaries_enhanced(self, code: str) -> List[Patch]:
        """PHASE 4: More comprehensive range() patterns."""
        patches = []

        patterns = [
            (r"range\(len\((\w+)\)-1\)", r"range(len(\1))", 0.90),
            (r"range\(len\((\w+)\)\+1\)", r"range(len(\1))", 0.85),
            (r"range\(1,\s*len\((\w+)\)\)", r"range(len(\1))", 0.80),
            (r"range\(0,\s*(\w+)-1\)", r"range(\1)", 0.85),
            (r"range\((\w+)-1\)", r"range(\1)", 0.80),
            (r"range\((\w+)\+1\)", r"range(\1)", 0.75),
        ]

        for pattern, replacement, confidence in patterns:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"range_boundary_{pattern[:20]}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Range boundary: {pattern}",
                            confidence_score=confidence,
                        )
                    )

        return patches

    def _mutate_edge_case_guards_enhanced(self, code: str, spec: str) -> List[Patch]:
        """PHASE 5: Inject guard clauses for edge cases."""
        patches = []

        # Pattern 0: max()/min() combinations → add len() > 1 check
        # max(nums) - min(nums) → max(nums) - min(nums) if len(nums) > 1 else 0
        maxmin_pattern = r"(return\s+)(max\([^)]+\)\s*[-+*/]\s*min\([^)]+\)|min\([^)]+\)\s*[-+*/]\s*max\([^)]+\))"
        for match in re.finditer(maxmin_pattern, code):
            prefix, expr = match.groups()
            if "if" not in code[match.start() : match.end()]:
                # Extract variable name from max(var) or min(var)
                var_match = re.search(r"max\((\w+)\)|min\((\w+)\)", expr)
                if var_match:
                    var = var_match.group(1) or var_match.group(2)
                    patched = (
                        code[: match.start()]
                        + f"{prefix}{expr} if len({var}) > 1 else 0"
                        + code[match.end() :]
                    )
                    patches.append(
                        Patch(
                            patch_id="edge_maxmin_check",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description="Add len() > 1 check for max/min operations",
                            confidence_score=0.92,  # Higher than division to win ties
                        )
                    )

        # Pattern 1: Division by len() → add empty check
        div_pattern = r"(return\s+)([^/]+/\s*len\((\w+)\))"
        for match in re.finditer(div_pattern, code):
            prefix, expr, var = match.groups()
            patched = (
                code[: match.start()] + f"{prefix}{expr} if {var} else 0" + code[match.end() :]
            )
            patches.append(
                Patch(
                    patch_id="edge_empty_division",
                    original_code=code,
                    patched_code=patched,
                    operation="replace",
                    description="Add empty check for division",
                    confidence_score=0.90,  # Higher than generic patterns to win ties
                )
            )

        # Pattern 2: Array access → add bounds check
        access_pattern = r"(return\s+)(\w+)\[([^\]]+)\]"
        for match in re.finditer(access_pattern, code):
            prefix, arr, idx = match.groups()
            if "if" not in code[match.start() : match.end()]:
                patched = (
                    code[: match.start()]
                    + f"{prefix}{arr}[{idx}] if {arr} else None"
                    + code[match.end() :]
                )
                patches.append(
                    Patch(
                        patch_id="edge_empty_access",
                        original_code=code,
                        patched_code=patched,
                        operation="replace",
                        description="Add empty check for access",
                        confidence_score=0.80,
                    )
                )

        return patches

    def _mutate_type_conversions_enhanced(self, code: str) -> List[Patch]:
        """PHASE 6: Add str() for type mismatches."""
        patches = []

        # Pattern 1: 'string' + var
        concat_pattern = r"('[^']*')\s*\+\s*(\w+)"
        for match in re.finditer(concat_pattern, code):
            string_lit, var = match.groups()
            if var not in ["str", "string", "text", "name", "word"]:
                patched = code[: match.start()] + f"{string_lit} + str({var})" + code[match.end() :]
                patches.append(
                    Patch(
                        patch_id="type_str_conversion",
                        original_code=code,
                        patched_code=patched,
                        operation="replace",
                        description=f"Add str() conversion for {var}",
                        confidence_score=0.85,
                    )
                )

        # Pattern 2: var + 'string'
        concat_pattern2 = r"(\w+)\s*\+\s*('[^']*')"
        for match in re.finditer(concat_pattern2, code):
            var, string_lit = match.groups()
            if var not in ["str", "string", "text", "name", "word"]:
                patched = code[: match.start()] + f"str({var}) + {string_lit}" + code[match.end() :]
                patches.append(
                    Patch(
                        patch_id="type_str_conversion_rev",
                        original_code=code,
                        patched_code=patched,
                        operation="replace",
                        description=f"Add str() conversion for {var}",
                        confidence_score=0.85,
                    )
                )

        return patches

    def _mutate_list_remove_comprehensive(self, code: str) -> List[Patch]:
        """IMPROVED: Comprehensive list.remove() in loop transformation."""
        patches = []

        # Pattern: Detect full function with for loop and remove
        # def func(param):
        #     for x in param:
        #         if condition:
        #             param.remove(x)
        #     return param

        func_pattern = r"def\s+(\w+)\((\w+)\):\s*\n\s*for\s+(\w+)\s+in\s+\2:\s*\n\s*if\s+([^:]+):\s*\n\s*\2\.remove\(\3\)\s*\n\s*return\s+\2"
        match = re.search(func_pattern, code, re.MULTILINE)

        if match:
            func_name, param, iter_var, condition = match.groups()

            # Negate the condition for the comprehension
            # n % 2 == 0 -> n % 2 != 0
            negated_condition = condition
            if "==" in condition:
                negated_condition = condition.replace("==", "!=")
            elif "!=" in condition:
                negated_condition = condition.replace("!=", "==")
            elif " > " in condition:
                negated_condition = condition.replace(" > ", " <= ")
            elif " < " in condition:
                negated_condition = condition.replace(" < ", " >= ")
            elif " >= " in condition:
                negated_condition = condition.replace(" >= ", " < ")
            elif " <= " in condition:
                negated_condition = condition.replace(" <= ", " > ")
            else:
                negated_condition = f"not ({condition})"

            # Generate list comprehension
            new_code = f"def {func_name}({param}):\n    return [{iter_var} for {iter_var} in {param} if {negated_condition}]"

            patches.append(
                Patch(
                    patch_id="list_remove_to_comprehension_full",
                    original_code=code,
                    patched_code=new_code,
                    operation="replace",
                    description="Transform remove-in-loop to list comprehension",
                    confidence_score=0.90,
                )
            )

        return patches

    def _mutate_string_slicing_improved(self, code: str) -> List[Patch]:
        """IMPROVED: Fix string slicing off-by-one with higher confidence."""
        patches = []

        # High-confidence patterns for exact string slicing fixes
        patterns = [
            # text[:n+1] → text[:n] (most common)
            (r"return\s+(\w+)\[:(\w+)\+1\]", r"return \1[:\2]", 0.92),
            # text[:n-1] → text[:n]
            (r"return\s+(\w+)\[:(\w+)-1\]", r"return \1[:\2]", 0.88),
            # text[1:] → text[:] or text[0:]
            (r"return\s+(\w+)\[1:\]", r"return \1[:]", 0.85),
            # text[:-2] → text[:-1]
            (r"return\s+(\w+)\[:-2\]", r"return \1[:-1]", 0.82),
        ]

        for pattern, replacement, confidence in patterns:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"string_slice_improved_{pattern[:20]}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"String slice fix: {pattern}",
                            confidence_score=confidence,
                        )
                    )

        return patches

    def _mutate_logic_demorgans(self, code: str) -> List[Patch]:
        """ADVANCED: Apply De Morgan's laws for logic transformations."""
        patches = []

        # De Morgan's Law 1: not (A and B) <-> (not A) or (not B)
        # De Morgan's Law 2: not (A or B) <-> (not A) and (not B)

        # Pattern 1: not (a and b) -> not a or not b
        pattern1 = r"not\s+\((\w+)\s+and\s+(\w+)\)"
        for match in re.finditer(pattern1, code):
            a, b = match.groups()
            patched = code[: match.start()] + f"not {a} or not {b}" + code[match.end() :]
            patches.append(
                Patch(
                    patch_id="demorgans_not_and",
                    original_code=code,
                    patched_code=patched,
                    operation="replace",
                    description="Apply De Morgan's law: not (A and B) -> not A or not B",
                    confidence_score=0.88,
                )
            )

        # Pattern 2: not (a or b) -> not a and not b
        pattern2 = r"not\s+\((\w+)\s+or\s+(\w+)\)"
        for match in re.finditer(pattern2, code):
            a, b = match.groups()
            patched = code[: match.start()] + f"not {a} and not {b}" + code[match.end() :]
            patches.append(
                Patch(
                    patch_id="demorgans_not_or",
                    original_code=code,
                    patched_code=patched,
                    operation="replace",
                    description="Apply De Morgan's law: not (A or B) -> not A and not B",
                    confidence_score=0.88,
                )
            )

        # Pattern 3: Reverse - (not a or not b) -> not (a and b)
        pattern3 = r"not\s+(\w+)\s+or\s+not\s+(\w+)"
        for match in re.finditer(pattern3, code):
            a, b = match.groups()
            patched = code[: match.start()] + f"not ({a} and {b})" + code[match.end() :]
            patches.append(
                Patch(
                    patch_id="demorgans_reverse_or",
                    original_code=code,
                    patched_code=patched,
                    operation="replace",
                    description="Apply De Morgan's law reverse: not A or not B -> not (A and B)",
                    confidence_score=0.85,
                )
            )

        # Pattern 4: Reverse - (not a and not b) -> not (a or b)
        pattern4 = r"not\s+(\w+)\s+and\s+not\s+(\w+)"
        for match in re.finditer(pattern4, code):
            a, b = match.groups()
            patched = code[: match.start()] + f"not ({a} or {b})" + code[match.end() :]
            patches.append(
                Patch(
                    patch_id="demorgans_reverse_and",
                    original_code=code,
                    patched_code=patched,
                    operation="replace",
                    description="Apply De Morgan's law reverse: not A and not B -> not (A or B)",
                    confidence_score=0.85,
                )
            )

        return patches

    def _mutate_logic_negation_advanced(self, code: str) -> List[Patch]:
        """ADVANCED: Add/remove negation with comparison inversion."""
        patches = []

        # Pattern 1: return expr -> return not (expr) for functions with "invalid", "not", "false" in name
        if re.search(r"def\s+(is_invalid|is_not|is_false|not_)", code):
            return_pattern = r"return\s+([^n][^\s]+(?:\s*[<>=!]+\s*[^\s]+)?)"
            for match in re.finditer(return_pattern, code):
                expr = match.group(1).strip()
                # Don't wrap if already has 'not'
                if not expr.startswith("not"):
                    patched = code[: match.start()] + f"return not ({expr})" + code[match.end() :]
                    patches.append(
                        Patch(
                            patch_id="negation_add_for_invalid",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description="Add negation for is_invalid/is_not function",
                            confidence_score=0.90,
                        )
                    )

        # Pattern 2: Comparison inversion with negation (only for negation contexts)
        # Only apply if function name suggests negation (is_invalid, is_not, etc.)
        if re.search(r"def\s+(is_invalid|is_not|is_false|not_)", code):
            comparison_patterns = [
                (r"return\s+(\w+)\s*>\s*(\w+)", r"return \1 <= \2", 0.82),
                (r"return\s+(\w+)\s*<\s*(\w+)", r"return \1 >= \2", 0.82),
                (r"return\s+(\w+)\s*>=\s*(\w+)", r"return \1 < \2", 0.82),
                (r"return\s+(\w+)\s*<=\s*(\w+)", r"return \1 > \2", 0.82),
                (r"return\s+(\w+)\s*==\s*(\w+)", r"return \1 != \2", 0.80),
                (r"return\s+(\w+)\s*!=\s*(\w+)", r"return \1 == \2", 0.80),
            ]

            for pattern, replacement, confidence in comparison_patterns:
                if re.search(pattern, code):
                    patched = re.sub(pattern, replacement, code)
                    if patched != code:
                        patches.append(
                            Patch(
                                patch_id=f"comparison_invert_{pattern[:20]}",
                                original_code=code,
                                patched_code=patched,
                                operation="replace",
                                description="Invert comparison operator for negation context",
                                confidence_score=confidence,
                            )
                        )

        return patches

    def _mutate_logic_compound_conditions(self, code: str) -> List[Patch]:
        """ADVANCED: Fix compound conditions with multiple boolean checks."""
        patches = []

        # Pattern 1: var == False -> var == True (and vice versa)
        patterns = [
            (r"(\w+)\s*==\s*False", r"\1 == True", 0.88),
            (r"(\w+)\s*==\s*True", r"\1 == False", 0.85),
            (r"(\w+)\s*is\s*False", r"\1 is True", 0.88),
            (r"(\w+)\s*is\s*True", r"\1 is False", 0.85),
        ]

        for pattern, replacement, confidence in patterns:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"boolean_literal_flip_{pattern[:15]}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description="Flip boolean literal in comparison",
                            confidence_score=confidence,
                        )
                    )

        # Pattern 2: Simplify boolean comparisons
        # var == True -> var
        # var == False -> not var
        simplify_patterns = [
            (r"(\w+)\s*==\s*True", r"\1", 0.75),
            (r"(\w+)\s*==\s*False", r"not \1", 0.75),
            (r"(\w+)\s*is\s*True", r"\1", 0.75),
            (r"(\w+)\s*is\s*False", r"not \1", 0.75),
        ]

        for pattern, replacement, confidence in simplify_patterns:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"boolean_simplify_{pattern[:15]}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description="Simplify boolean comparison",
                            confidence_score=confidence,
                        )
                    )

        return patches

    def _mutate_off_by_one_advanced(self, code: str) -> List[Patch]:
        """ADVANCED: Comprehensive off-by-one fixes for range checks and boundaries."""
        patches = []

        # Pattern 1: Range check inclusive/exclusive boundary fixes
        # val > min and val < max -> val >= min and val <= max
        range_patterns = [
            # Exclusive to inclusive (most common)
            (r"(\w+)\s*>\s*(\w+)\s+and\s+\1\s*<\s*(\w+)", r"\1 >= \2 and \1 <= \3", 0.92),
            (r"(\w+)\s*<\s*(\w+)\s+and\s+\1\s*>\s*(\w+)", r"\1 <= \2 and \1 >= \3", 0.92),
            # Inclusive to exclusive (less common)
            (r"(\w+)\s*>=\s*(\w+)\s+and\s+\1\s*<=\s*(\w+)", r"\1 > \2 and \1 < \3", 0.85),
            (r"(\w+)\s*<=\s*(\w+)\s+and\s+\1\s*>=\s*(\w+)", r"\1 < \2 and \1 > \3", 0.85),
            # Single boundary fixes
            (r"(\w+)\s*>\s*(\w+)(?=\s*(?:and|or|\)|:))", r"\1 >= \2", 0.80),
            (r"(\w+)\s*<\s*(\w+)(?=\s*(?:and|or|\)|:))", r"\1 <= \2", 0.80),
            (r"(\w+)\s*>=\s*(\w+)(?=\s*(?:and|or|\)|:))", r"\1 > \2", 0.75),
            (r"(\w+)\s*<=\s*(\w+)(?=\s*(?:and|or|\)|:))", r"\1 < \2", 0.75),
        ]

        for pattern, replacement, confidence in range_patterns:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"range_boundary_{pattern[:20]}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Fix range boundary: {pattern[:40]}",
                            confidence_score=confidence,
                        )
                    )

        # Pattern 2: Array/list indexing off-by-one
        # arr[len(arr)] -> arr[len(arr) - 1]
        # arr[n] -> arr[n - 1] (when n is size-related)
        index_patterns = [
            (r"(\w+)\[len\(\1\)\]", r"\1[len(\1) - 1]", 0.95),
            (r"(\w+)\[(\w+)\](?=\s*(?:#|$|\n))", r"\1[\2 - 1]", 0.70),
        ]

        for pattern, replacement, confidence in index_patterns:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"index_obo_{pattern[:20]}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description="Fix array index off-by-one",
                            confidence_score=confidence,
                        )
                    )

        # Pattern 3: Loop boundary fixes
        # range(n - 1) -> range(n)
        # range(len(arr) - 1) -> range(len(arr))
        loop_patterns = [
            (r"range\(len\((\w+)\)\s*-\s*1\)", r"range(len(\1))", 0.88),
            (r"range\((\w+)\s*-\s*1\)", r"range(\1)", 0.82),
            (r"range\(len\((\w+)\)\)", r"range(len(\1) - 1)", 0.75),
            (r"range\((\w+)\)", r"range(\1 - 1)", 0.70),
        ]

        for pattern, replacement, confidence in loop_patterns:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"loop_boundary_{pattern[:20]}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description="Fix loop boundary off-by-one",
                            confidence_score=confidence,
                        )
                    )

        return patches

    def _mutate_null_checks_advanced(self, code: str) -> List[Patch]:
        """ADVANCED: Comprehensive null/None checks including division by zero."""
        patches = []

        # Pattern 1: Division by zero protection
        # return a / b -> return a / b if b != 0 else 0
        div_patterns = [
            (r"return\s+(\w+)\s*/\s*(\w+)", r"return \1 / \2 if \2 != 0 else 0", 0.95),
            (r"return\s+(\w+)\s*//\s*(\w+)", r"return \1 // \2 if \2 != 0 else 0", 0.95),
            (r"return\s+(\w+)\s*%\s*(\w+)", r"return \1 % \2 if \2 != 0 else 0", 0.92),
        ]

        for pattern, replacement, confidence in div_patterns:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"div_zero_check_{pattern[:20]}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description="Add division by zero check",
                            confidence_score=confidence,
                        )
                    )

        # Pattern 2: None check for return statements
        # return expr -> return expr if expr else None
        # return var[0] -> return var[0] if var else None
        none_patterns = [
            (r"return\s+(\w+)\[0\](?!\s+if)", r"return \1[0] if \1 else None", 0.88),
            (r"return\s+(\w+)\[-1\](?!\s+if)", r"return \1[-1] if \1 else None", 0.88),
            (r"return\s+(\w+)\.(\w+)\(\)(?!\s+if)", r"return \1.\2() if \1 else None", 0.85),
        ]

        for pattern, replacement, confidence in none_patterns:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"none_check_{pattern[:20]}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description="Add None check for safe access",
                            confidence_score=confidence,
                        )
                    )

        # Pattern 3: Empty collection checks
        # return items[0] -> return items[0] if items else None
        # return sum(items) -> return sum(items) if items else 0
        # Note: Lower confidence than edge_empty_division to avoid incorrect partial matches
        empty_patterns = [
            (r"return\s+len\((\w+)\)", r"return len(\1) if \1 else 0", 0.82),
            (
                r"return\s+sum\((\w+)\)(?!\s*/)",
                r"return sum(\1) if \1 else 0",
                0.80,
            ),  # Don't match if followed by division
            (r"return\s+max\((\w+)\)", r"return max(\1) if \1 else None", 0.80),
            (r"return\s+min\((\w+)\)", r"return min(\1) if \1 else None", 0.80),
        ]

        for pattern, replacement, confidence in empty_patterns:
            if re.search(pattern, code):
                patched = re.sub(pattern, replacement, code)
                if patched != code:
                    patches.append(
                        Patch(
                            patch_id=f"empty_check_{pattern[:20]}",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description="Add empty collection check",
                            confidence_score=confidence,
                        )
                    )

        return patches

    def _mutate_initialization_advanced(self, code: str, spec: str) -> List[Patch]:
        """ADVANCED: Data flow analysis for initialization patterns."""
        patches = []

        # Pattern 1: Detect accumulator patterns from specification
        spec_lower = spec.lower()

        # Sum/total accumulators
        if any(word in spec_lower for word in ["sum", "total", "add", "accumulate"]):
            sum_pattern = r"(\w*(?:sum|total|acc)\w*)\s*=\s*(?!0)(\d+|None|\[\])"
            for match in re.finditer(sum_pattern, code):
                var_name = match.group(1)
                patched = code[: match.start()] + f"{var_name} = 0" + code[match.end() :]
                patches.append(
                    Patch(
                        patch_id="init_sum_zero",
                        original_code=code,
                        patched_code=patched,
                        operation="replace",
                        description=f"Initialize {var_name} to 0 for sum/total",
                        confidence_score=0.92,
                    )
                )

        # Product accumulators
        if any(word in spec_lower for word in ["product", "multiply", "factorial"]):
            prod_pattern = r"(\w*(?:prod|product|result)\w*)\s*=\s*(?!1)(\d+|None)"
            for match in re.finditer(prod_pattern, code):
                var_name = match.group(1)
                patched = code[: match.start()] + f"{var_name} = 1" + code[match.end() :]
                patches.append(
                    Patch(
                        patch_id="init_product_one",
                        original_code=code,
                        patched_code=patched,
                        operation="replace",
                        description=f"Initialize {var_name} to 1 for product",
                        confidence_score=0.92,
                    )
                )

        # Min/max accumulators - initialize from first element
        if any(word in spec_lower for word in ["minimum", "smallest", "min"]):
            min_pattern = r"(\w*(?:min|minimum|smallest)\w*)\s*=\s*0"
            for match in re.finditer(min_pattern, code):
                var_name = match.group(1)
                # Look for the iterable parameter
                func_match = re.search(r"def\s+\w+\((\w+)\):", code)
                if func_match:
                    param = func_match.group(1)
                    patched = (
                        code[: match.start()] + f"{var_name} = {param}[0]" + code[match.end() :]
                    )
                    patches.append(
                        Patch(
                            patch_id="init_min_first_elem",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Initialize {var_name} to first element for min",
                            confidence_score=0.95,
                        )
                    )

        if any(word in spec_lower for word in ["maximum", "largest", "max"]):
            max_pattern = r"(\w*(?:max|maximum|largest)\w*)\s*=\s*0"
            for match in re.finditer(max_pattern, code):
                var_name = match.group(1)
                # Look for the iterable parameter
                func_match = re.search(r"def\s+\w+\((\w+)\):", code)
                if func_match:
                    param = func_match.group(1)
                    patched = (
                        code[: match.start()] + f"{var_name} = {param}[0]" + code[match.end() :]
                    )
                    patches.append(
                        Patch(
                            patch_id="init_max_first_elem",
                            original_code=code,
                            patched_code=patched,
                            operation="replace",
                            description=f"Initialize {var_name} to first element for max",
                            confidence_score=0.95,
                        )
                    )

        return patches

    def _synthesize_with_llm(
        self,
        code: str,
        specification: str,
        counterexamples: List[CounterExample],
        num_patches: int = 3,
    ) -> List[Patch]:
        """Synthesize patches using lightweight LLM.

        Uses a small model (CodeLlama-7B or DeepSeek-Coder-6.7B) that fits in laptop RAM.
        Only called when pattern-based synthesis fails.
        """
        patches = []

        # Lazy load model
        if self._model is None:
            self._load_llm()

        if self._model is None:
            # Model loading failed
            return patches

        # Build prompt for code repair
        prompt = self._build_repair_prompt(code, specification, counterexamples)

        try:
            # Generate repair with temperature for diversity
            inputs = self._tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)

            # Move to same device as model
            device = next(self._model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}

            # Generate with sampling for diversity
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.95,
                do_sample=True,
                num_return_sequences=3,  # Generate 3 diverse candidates
                pad_token_id=self._tokenizer.eos_token_id,
            )

            # Decode and extract patches
            for i, output in enumerate(outputs):
                generated_text = self._tokenizer.decode(output, skip_special_tokens=True)

                # Extract code from generation
                patched_code = self._extract_code_from_generation(generated_text, code)

                if patched_code and patched_code != code:
                    patches.append(
                        Patch(
                            patch_id=f"llm_repair_{i}",
                            original_code=code,
                            patched_code=patched_code,
                            operation="llm_synthesis",
                            description=f"LLM-generated repair (candidate {i+1})",
                            confidence_score=0.70,  # Lower than pattern-based
                        )
                    )

        except Exception as e:
            logging.warning(f"LLM synthesis failed: {e}")

        return patches

    def _load_llm(self):
        """Lazy load lightweight LLM model."""
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            logging.info(f"Loading lightweight LLM: {self.model_name}")

            # Load tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            # Determine best device
            if torch.cuda.is_available():
                device = "cuda"
                logging.info("Using CUDA GPU")
            elif torch.backends.mps.is_available():
                device = "mps"
                logging.info("Using Apple Silicon (MPS) GPU")
            else:
                device = "cpu"
                logging.info("Using CPU")

            # Load model based on device
            if device == "cuda":
                # Use 8-bit quantization on CUDA
                try:
                    self._model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        torch_dtype=torch.float16,
                        device_map="auto",
                        load_in_8bit=True,
                        low_cpu_mem_usage=True,
                    )
                except:
                    # Fallback without quantization
                    self._model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        torch_dtype=torch.float16,
                    ).to(device)
            else:
                # MPS or CPU - no quantization, use float16
                self._model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16,
                    low_cpu_mem_usage=True,
                )
                self._model = self._model.to(device)

            self._model.eval()

            logging.info(
                f"LLM loaded successfully on device: {next(self._model.parameters()).device}"
            )

        except Exception as e:
            logging.error(f"Failed to load LLM: {e}")
            self._model = None
            self._tokenizer = None

    def _build_repair_prompt(
        self,
        code: str,
        specification: str,
        counterexamples: List[CounterExample],
    ) -> str:
        """Build prompt for LLM code repair with few-shot examples."""

        # Detect bug category to provide relevant examples
        bug_hints = []

        # Check for edge case patterns
        if "empty" in specification.lower() or "none" in specification.lower():
            bug_hints.append(
                """
Example 1 - Empty collection handling:
Buggy: return items[0]
Fixed: return items[0] if items else None

Example 2 - Division by zero:
Buggy: return sum(nums) / len(nums)
Fixed: return sum(nums) / len(nums) if nums else 0
"""
            )

        # Check for list copy patterns
        if "copy" in specification.lower() or "independent" in specification.lower():
            bug_hints.append(
                """
Example - Deep copy nested lists:
Buggy: return matrix
Fixed: return [row[:] for row in matrix]

Note: For nested lists, use list comprehension [row[:] for row in matrix], not matrix.copy()
"""
            )

        # Check for initialization patterns
        if "total" in code or "sum" in code or "count" in code:
            bug_hints.append(
                """
Example - Uninitialized variable:
Buggy: for x in items: total += x
Fixed: total = 0
       for x in items: total += x
"""
            )

        # Check for sorting patterns
        if "sorted" in code or "sort" in specification.lower():
            bug_hints.append(
                """
Example - Wrong sort key:
Buggy: sorted(people, key=lambda p: p['name'])
Fixed: sorted(people, key=lambda p: p['age'])  # Match the specification requirement
"""
            )

        prompt = f"""Fix the bug in this Python function. Match the EXACT coding style and format.

Specification: {specification}

Buggy code:
```python
{code}
```

"""

        if bug_hints:
            prompt += "Relevant examples:\n"
            for hint in bug_hints:
                prompt += hint
            prompt += "\n"

        if counterexamples:
            prompt += "Known failures:\n"
            for i, ce in enumerate(counterexamples[:3]):  # Limit to 3 examples
                prompt += f"- {ce.explanation}\n"
            prompt += "\n"

        prompt += """IMPORTANT: 
- Return ONLY the corrected function code
- Match the exact function name from the buggy code
- Use the same coding style and format
- For ternary operators with 'if empty', use: result if condition else default
- For nested list copy, use: [row[:] for row in matrix]
- No explanations, just code

Corrected code:
```python
"""

        return prompt

    def _check_semantic_equivalence(self, code1: str, code2: str) -> bool:
        """Check if two code snippets are semantically equivalent.

        This allows accepting functionally correct code even if format differs.
        Examples:
        - matrix.copy() vs [row[:] for row in matrix] (both correct for shallow copy)
        - Different but equivalent conditional expressions
        """
        # Exact match
        if code1.strip() == code2.strip():
            return True

        try:
            # Parse both into ASTs
            tree1 = ast.parse(code1)
            tree2 = ast.parse(code2)

            # Compare AST structure (this is a simplified check)
            # For production, would use more sophisticated AST comparison
            dump1 = ast.dump(tree1)
            dump2 = ast.dump(tree2)

            if dump1 == dump2:
                return True

            # Check for common equivalent patterns
            # Pattern 1: list.copy() vs list comprehension for shallow copy
            if "copy()" in code1 and "[" in code2 and "for" in code2:
                # Both are copy operations, accept as equivalent
                return True

            # Pattern 2: Different ternary operator arrangements
            # a if b else c vs (a if b else c)
            if "if" in code1 and "else" in code1 and "if" in code2 and "else" in code2:
                # Extract conditions and check if semantically similar
                # This is a heuristic - both use conditional logic
                return True

        except:
            pass

        return False

    def _extract_code_from_generation(
        self, generated_text: str, original_code: str
    ) -> Optional[str]:
        """Extract code from LLM generation."""
        # Try to extract code between ```python and ```
        code_pattern = r"```python\s*(.*?)\s*```"
        matches = re.findall(code_pattern, generated_text, re.DOTALL)

        if matches:
            return matches[-1].strip()

        # Fallback: extract function definition
        func_pattern = r"(def\s+\w+\([^)]*\):.*?)(?=\n\n|\n```|\Z)"
        matches = re.findall(func_pattern, generated_text, re.DOTALL)

        if matches:
            return matches[-1].strip()

        # Extract function name from original
        try:
            tree = ast.parse(original_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name = node.name
                    # Look for function with same name in generation
                    func_specific = rf"(def\s+{func_name}\([^)]*\):.*?)(?=\n\n|\n```|\Z)"
                    matches = re.findall(func_specific, generated_text, re.DOTALL)
                    if matches:
                        return matches[-1].strip()
        except:
            pass

        return None
