# Copyright (C) 2025 Celestir Inc.
# Proprietary and Confidential

"""Command-line interface for Gridseal Pro."""

import argparse
import json
import sys
from pathlib import Path

from gridseal_pro.causal_tracing import AblationAnalyzer, GradientAttributor
from gridseal_pro.counterfactual import CounterfactualEditor
from gridseal_pro.licensing import LicenseError, LicenseValidator
from gridseal_pro.repair import CEGISRepairer


def parse_args(args=None):
    """Parse command-line arguments.

    Args:
        args: List of arguments (for testing), or None to use sys.argv

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Gridseal Pro - Advanced AI Code Verification")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # License command
    license_parser = subparsers.add_parser("license", help="Check license status")
    license_parser.add_argument("--key", help="License key (or use ~/.gridseal/license.json)")

    # Causal tracing command
    trace_parser = subparsers.add_parser("trace", help="Run causal tracing analysis")
    trace_parser.add_argument("--code", required=True, help="Code file")
    trace_parser.add_argument("--spec", help="Specification file (default: code docstring)")
    trace_parser.add_argument("--output", help="Output HTML file")

    # Counterfactual command
    cf_parser = subparsers.add_parser("counterfactual", help="Generate counterfactual scenario")
    cf_parser.add_argument("--code", required=True, help="Code file")
    cf_parser.add_argument("--spec", required=True, help="Original specification")
    cf_parser.add_argument("--new-spec", required=True, help="Counterfactual specification")
    cf_parser.add_argument("--output", help="Output JSON file")

    # Repair command
    repair_parser = subparsers.add_parser("repair", help="Automatic code repair")
    repair_parser.add_argument("--code", required=True, help="Buggy code file")
    repair_parser.add_argument("--spec", required=True, help="Specification file")
    repair_parser.add_argument("--output", help="Output JSON file with patches")
    repair_parser.add_argument(
        "--max-iterations", type=int, default=10, help="Maximum CEGIS iterations"
    )

    return parser.parse_args(args)


def main():
    """Main CLI entry point."""
    args = parse_args()

    if not args.command:
        print("Error: No command specified")
        print("Usage: gridseal-pro {license|trace|counterfactual|repair} [options]")
        sys.exit(1)

    # Check license (except for license command itself)
    if args.command != "license":
        try:
            validator = LicenseValidator()
            result = validator.validate()

            if result.status not in ["valid", "grace_period"]:
                print(f" License error: {result.message}")
                print("Please contact support@gridseal.ai")
                sys.exit(1)

            if result.status == "grace_period":
                print(f"️  Warning: {result.message}")
        except Exception as e:
            print(f" License validation failed: {e}")
            sys.exit(1)

    # Execute command
    if args.command == "license":
        return cmd_license(args)
    elif args.command == "trace":
        return cmd_trace(args)
    elif args.command == "counterfactual":
        return cmd_counterfactual(args)
    elif args.command == "repair":
        return cmd_repair(args)

    return 0


def cmd_license(args):
    """Check license status."""
    try:
        validator = LicenseValidator()
        result = validator.validate(args.key)

        print(f"Status: {result.status}")
        print(f"Message: {result.message}")

        if result.license:
            print(f"Tier: {result.license.tier}")
            print(f"Customer: {result.license.customer_email}")
            if result.days_until_expiration is not None:
                print(f"Days until expiration: {result.days_until_expiration}")
            print(f"Features: {', '.join(result.features_enabled)}")

        return 0 if result.status == "valid" else 1

    except Exception as e:
        print(f" Error: {e}")
        return 1


def cmd_trace(args):
    """Run causal tracing analysis."""
    code = Path(args.code).read_text()
    spec = Path(args.spec).read_text() if args.spec else ""

    analyzer = AblationAnalyzer()
    trace = analyzer.analyze(code, spec)

    print(f" Analysis complete")
    print(f"Critical spec tokens: {trace.critical_spec_tokens}")
    print(f"Ablation results: {len(trace.ablation_results)}")

    if args.output:
        attributor = GradientAttributor()
        html = attributor.visualize_attributions(trace, args.output)
        print(f" Saved visualization to {args.output}")

    return 0


def cmd_counterfactual(args):
    """Generate counterfactual scenario."""
    code = Path(args.code).read_text()
    spec = args.spec
    new_spec = args.new_spec

    editor = CounterfactualEditor()
    scenario = editor.create_scenario(spec, new_spec, code)

    print(f" Counterfactual generated")
    print(f"Impact score: {scenario.impact_score:.2f}")
    print(f"Code deltas: {len(scenario.code_deltas)}")
    print(f"Safe: {scenario.is_safe}")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(scenario.model_dump(), f, indent=2)
        print(f" Saved to {args.output}")

    return 0


def cmd_repair(args):
    """Automatic code repair."""
    code = Path(args.code).read_text()
    spec = Path(args.spec).read_text()

    repairer = CEGISRepairer()
    result = repairer.repair(code, spec)

    print(f" Repair {'succeeded' if result.repair_successful else 'failed'}")
    print(f"Iterations: {result.iterations}")
    print(f"Time: {result.total_time_seconds:.2f}s")
    print(f"Patches generated: {len(result.patches)}")

    if result.best_patch:
        print(f"\n Best patch (confidence: {result.best_patch.confidence_score:.2f}):")
        print(result.best_patch.patched_code)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result.model_dump(), f, indent=2, default=str)
        print(f" Saved to {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
