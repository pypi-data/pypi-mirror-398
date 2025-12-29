"""
Clarvynn CLI - Command-line interface for Clarvynn operations.

Usage:
    clarvynn init [file]
    clarvynn version
    clarvynn validate <policy-file>
    clarvynn test <policy-file>
"""

import os
import sys
from typing import Optional

import yaml
from clarvynn.logging import get_logger

logger = get_logger("cli")


def init_policy(filename: Optional[str] = None):
    """
    Create a template policy file with helpful comments.

    Args:
        filename: Optional custom filename (default: clarvynn-policy.yaml)
    """
    if filename is None:
        filename = "clarvynn-policy.yaml"

    if os.path.exists(filename):
        response = input(f"⚠️  File '{filename}' already exists. Overwrite? [y/N]: ")
        if response.lower() != "y":
            print("❌ Cancelled")
            return False

    template = """# Clarvynn Policy Configuration
# Intelligent telemetry sampling - keep what matters, drop the noise.
# https://github.com/clarvynn/clarvynn

version: "1.0"  # CPL schema version

# Service identification
service:
  name: my-service          # Your service name
  namespace: production     # Environment/namespace
  version: 1.0.0            # Your app version (for tracking)

# Sampling configuration
sampling:
  # Base rate: percentage of successful traffic to sample (0.0 to 1.0)
  # Recommended: 0.01 (1%) to 0.1 (10%) for production
  base_rate: 0.1  # 10% of routine traffic

  # Conditions: Requests matching ANY condition are ALWAYS captured (100%)
  # These override base_rate - you'll never miss critical signals
  conditions:
    # ━━━ RELIABILITY: Never miss production issues ━━━
    
    - name: errors
      when: "status_code >= 400"
      # Captures all HTTP 4xx client errors and 5xx server errors
    
    - name: slow_requests
      when: "duration_ms > 1000"
      # Captures requests taking more than 1 second
      # Adjust threshold based on your SLOs (e.g., 500 for APIs, 3000 for batch)
    
    # ━━━ OPTIONAL: Uncomment based on your needs ━━━
    
    # Critical business paths (always capture)
    # - name: checkout
    #   when: "path contains '/checkout' OR path contains '/payment'"
    
    # Auth/security flows (always capture)
    # - name: auth
    #   when: "path contains '/auth' OR path contains '/login'"
    
    # State-changing operations (higher visibility)
    # - name: mutations
    #   when: "method == 'POST' OR method == 'PUT' OR method == 'DELETE'"

# Quick Reference:
# - base_rate=0.1 + error/slow conditions → ~85% cost reduction
# - Validate: clarvynn validate clarvynn-policy.yaml
# - Test: clarvynn test clarvynn-policy.yaml
"""

    try:
        with open(filename, "w") as f:
            f.write(template)

        print(f"✅ Created policy template: {filename}")
        print("\n📝 Next steps:")
        print(f"   1. Edit the policy to match your needs")
        print(f"   2. Validate: clarvynn validate {filename}")
        print(f"   3. Test: clarvynn test {filename}")
        print(f"   4. Run: export CLARVYNN_POLICY_PATH={filename}")
        print(f"      opentelemetry-instrument python your_app.py")

        return True

    except Exception as e:
        print(f"❌ Error creating policy file: {e}")
        return False


def version():
    """Print version information."""
    from clarvynn import __version__

    print(f"Clarvynn version {__version__}")
    print("Intelligent Deferred Head Sampling for OpenTelemetry with policy-driven governance")


def validate(policy_file: str) -> bool:
    """
    Validate a CPL policy file.

    Args:
        policy_file: Path to policy YAML file

    Returns:
        True if valid, False otherwise
    """
    try:
        with open(policy_file, "r") as f:
            policy = yaml.safe_load(f)

        errors = []
        warnings = []

        if not policy:
            print(f"❌ Error: Policy file is empty")
            return False

        if not isinstance(policy, dict):
            print(f"❌ Error: Policy must be a dictionary/object")
            return False

        if "version" not in policy:
            errors.append("Missing required field 'version'")

        if "sampling" not in policy:
            errors.append("Missing required section 'sampling'")
        else:
            sampling = policy["sampling"]

            if not isinstance(sampling, dict):
                errors.append("'sampling' must be a dictionary/object")
            else:
                if "base_rate" not in sampling:
                    errors.append("Sampling section missing required 'base_rate' field")
                else:
                    base_rate = sampling["base_rate"]
                    if not isinstance(base_rate, (int, float)):
                        errors.append(f"base_rate must be a number, got {type(base_rate).__name__}")
                    elif not (0.0 <= base_rate <= 1.0):
                        errors.append(f"base_rate must be between 0.0 and 1.0, got {base_rate}")
                    elif base_rate > 0.5:
                        warnings.append(
                            f"High base_rate ({base_rate}) may result in high costs. Consider 0.01-0.1 for production."
                        )

                if "conditions" in sampling:
                    conditions = sampling["conditions"]
                    if not isinstance(conditions, list):
                        errors.append("'conditions' must be a list")
                    else:
                        for i, condition in enumerate(conditions):
                            if not isinstance(condition, dict):
                                errors.append(f"Condition {i} must be a dictionary/object")
                                continue

                            if "name" not in condition:
                                errors.append(f"Condition {i} missing required 'name' field")

                            if "when" not in condition:
                                errors.append(
                                    f"Condition {i} ('{condition.get('name', 'unnamed')}') missing required 'when' field"
                                )

                            if "enabled" in condition:
                                if not isinstance(condition["enabled"], bool):
                                    errors.append(
                                        f"Condition {i} 'enabled' must be a boolean (true/false)"
                                    )

        if "service" not in policy:
            warnings.append("Missing optional 'service' section (recommended for production)")

        if errors:
            print(f"❌ Validation failed with {len(errors)} error(s):\n")
            for error in errors:
                print(f"   • {error}")
            return False

        print(f"✅ Policy validation successful!")
        print(f"\n📋 Summary:")
        print(f"   Version: {policy.get('version', 'N/A')}")
        print(f"   Base rate: {policy['sampling']['base_rate'] * 100}%")
        print(f"   Conditions: {len(policy['sampling'].get('conditions', []))}")

        if policy.get("service"):
            print(f"   Service: {policy['service'].get('name', 'N/A')}")

        if warnings:
            print(f"\n⚠️  Warnings ({len(warnings)}):")
            for warning in warnings:
                print(f"   • {warning}")

        return True

    except FileNotFoundError:
        print(f"❌ Error: Policy file not found: {policy_file}")
        print(f"   Run 'clarvynn init {policy_file}' to create a template")
        return False
    except yaml.YAMLError as e:
        print(f"❌ Error: Invalid YAML syntax")
        print(f"   {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test(policy_file: str):
    """
    Test a CPL policy with sample requests.

    Args:
        policy_file: Path to policy YAML file
    """
    from core.cpl_engine.python.base import RequestData

    if not validate(policy_file):
        sys.exit(1)

    try:
        from core.cpl_engine.python.production_cpl_adapter import ProductionCPLAdapter

        print("\n🧪 Testing policy with sample requests...")

        adapter = ProductionCPLAdapter(policy_file=policy_file)
        adapter.setup()

        test_cases = [
            RequestData(path="/api/users", method="GET", status_code=200, duration_ms=50),
            RequestData(path="/api/users", method="GET", status_code=500, duration_ms=100),
            RequestData(path="/api/slow", method="POST", status_code=200, duration_ms=2000),
            RequestData(path="/api/normal", method="GET", status_code=200, duration_ms=30),
        ]

        for i, request in enumerate(test_cases, 1):
            decision = adapter.apply_governance(request)
            status_emoji = "✅" if decision.should_sample else "❌"
            print(f"\n Test {i}: {request.method} {request.path}")
            print(f"   Status: {request.status_code}, Duration: {request.duration_ms}ms")
            print(f"   {status_emoji} Decision: {'KEEP' if decision.should_sample else 'DROP'}")
            print(f"   Reason: {decision.reason}")

    except Exception as e:
        print(f"\n❌ Error testing policy: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: clarvynn <command> [args]")
        print("\nCommands:")
        print("  init [file]             Create a template policy file")
        print("  validate <file>         Validate a policy file")
        print("  test <file>             Test a policy file with sample requests")
        print("  version                 Show version information")
        sys.exit(1)

    command = sys.argv[1]

    if command == "version":
        version()
    elif command == "init":
        filename = sys.argv[2] if len(sys.argv) > 2 else None
        if not init_policy(filename):
            sys.exit(1)
    elif command == "validate":
        if len(sys.argv) < 3:
            print("❌ Error: Missing policy file argument")
            print("Usage: clarvynn validate <policy-file>")
            sys.exit(1)
        policy_file = sys.argv[2]
        if not validate(policy_file):
            sys.exit(1)
    elif command == "test":
        if len(sys.argv) < 3:
            print("❌ Error: Missing policy file argument")
            print("Usage: clarvynn test <policy-file>")
            sys.exit(1)
        policy_file = sys.argv[2]
        test(policy_file)
    else:
        print(f"❌ Unknown command: {command}")
        print("\n📚 Available commands:")
        print("  init [file]             Create a template policy file")
        print("  validate <file>         Validate a policy file")
        print("  test <file>             Test a policy file with sample requests")
        print("  version                 Show version information")
        sys.exit(1)


if __name__ == "__main__":
    main()
