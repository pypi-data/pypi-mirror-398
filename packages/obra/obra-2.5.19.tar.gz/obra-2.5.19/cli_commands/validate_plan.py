"""CLI command for validating MACHINE_PLAN files (JSON/YAML).

This module provides the ValidatePlanCommand class which implements
the 'obra validate-plan' command. Uses unified PlanValidator with
Pydantic schema validation (FEAT-PLAN-VALIDATION-REDESIGN-001).

Validation matches PlanImporter behavior exactly:
- Pydantic schema validation (MachinePlanSchema)
- Support for both JSON and YAML formats
- Clear error messages with field context
- Feature flag support (derivation.plan_validation.use_pydantic)

Usage:
    $ obra validate-plan docs/development/MACHINE_PLAN.json
    $ obra validate-plan --verbose plan.yaml
    $ obra validate-plan --format yaml plan.yaml

Reference: FEAT-PLAN-VALIDATION-REDESIGN-001 Story S1.T5
"""

import logging
import sys
from pathlib import Path

import click

# New Pydantic validator (FEAT-PLAN-VALIDATION-REDESIGN-001)
from obra.validation.plan_validator import PlanValidationError, PlanValidator

logger = logging.getLogger(__name__)


class ValidatePlanCommand:
    """Command handler for validating MACHINE_PLAN files (JSON/YAML).

    This class implements the 'obra validate-plan' CLI command using unified
    PlanValidator with Pydantic schema validation. Matches PlanImporter
    validation behavior exactly.

    Features:
    - Pydantic schema validation (MachinePlanSchema)
    - JSON and YAML format support
    - Clear error messages with field context
    - Colored output for success/failure
    - Exit code handling (0 for valid, 1 for invalid)

    Example:
        >>> cmd = ValidatePlanCommand()
        >>> cmd.execute("plan.json", verbose=False)
        0  # Returns exit code
    """

    def __init__(self) -> None:
        """Initialize ValidatePlanCommand with PlanValidator."""
        self.validator = PlanValidator()

    def execute(
        self,
        file_path: str,
        verbose: bool = False,
    ) -> int:
        """Execute plan validation using unified PlanValidator.

        Validates the specified plan file using Pydantic schema validation.
        Matches PlanImporter validation behavior exactly.

        Args:
            file_path: Path to the JSON/YAML plan file to validate
            verbose: Enable verbose output with additional details

        Returns:
            Exit code: 0 if validation passed, 1 if validation failed

        Example:
            >>> cmd = ValidatePlanCommand()
            >>> exit_code = cmd.execute("plan.json")
            >>> sys.exit(exit_code)
        """
        # Validate file path
        path = Path(file_path)

        if not path.exists():
            click.echo()
            click.echo(click.style("✗ File not found", fg="red", bold=True))
            click.echo(f"\nPath: {path}")
            click.echo()
            return 1

        if verbose:
            click.echo(f"\nValidating: {path}")
            click.echo(f"Absolute path: {path.absolute()}\n")

        # Validate with unified PlanValidator
        try:
            plan = self.validator.validate_file(str(path))

            # Success - display plan info
            click.echo()
            click.echo(click.style("✓ Validation PASSED", fg="green", bold=True))
            click.echo()
            click.echo(f"File: {path}")
            click.echo(f"Format: {path.suffix.upper().lstrip('.')}")
            click.echo()

            if verbose:
                click.echo(click.style("Plan Details:", fg="blue", bold=True))
                click.echo(f"  Work ID: {plan.work_id}")
                click.echo(f"  Stories: {len(plan.stories)}")
                click.echo(f"  Completion checklist items: {len(plan.completion_checklist)}")
                if plan.version:
                    click.echo(f"  Version: {plan.version}")
                click.echo()

            click.echo(click.style("Plan file is valid and ready for import.", fg="green"))
            click.echo()
            return 0

        except PlanValidationError as e:
            # Pydantic validation error - display formatted errors
            click.echo()
            click.echo(click.style("✗ Validation FAILED", fg="red", bold=True))
            click.echo()
            click.echo(f"File: {path}")
            click.echo(f"Format: {e.format.upper()}")
            click.echo()
            click.echo(click.style("Errors:", fg="red", bold=True))
            for error in e.errors:
                click.echo(f"  {error}")
            click.echo()
            click.echo(click.style("Next steps:", fg="blue"))
            click.echo("  1. Fix the validation errors in the file and retry")
            click.echo("  2. See docs/guides/migration/plan-validation-v2-migration.md for migration help")
            click.echo()
            return 1

        except FileNotFoundError as e:
            click.echo()
            click.echo(click.style("✗ File not found", fg="red", bold=True))
            click.echo()
            click.echo(f"Error: {e}")
            click.echo()
            return 1

        except ValueError as e:
            # Format detection or parsing error
            click.echo()
            click.echo(click.style("✗ Validation Error", fg="red", bold=True))
            click.echo()
            click.echo(f"File: {path}")
            click.echo()
            click.echo(click.style("ERROR: ", fg="red", bold=True) + str(e))
            click.echo()
            return 1

        except Exception as e:
            # Unexpected error
            click.echo()
            click.echo(click.style("✗ Unexpected Error", fg="red", bold=True))
            click.echo()
            click.echo(click.style("ERROR: ", fg="red", bold=True) + str(e))
            if verbose:
                import traceback
                click.echo()
                click.echo(click.style("Traceback:", fg="yellow"))
                click.echo(traceback.format_exc())
            click.echo()
            return 1


# Click command decorator for CLI integration
@click.command(name="validate-plan")
@click.argument(
    "file_path",
    type=click.Path(exists=True),
    required=True,
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output with plan details",
)
def validate_plan_cli(file_path: str, verbose: bool) -> None:
    """Validate MACHINE_PLAN file (JSON/YAML) against schema.

    Validates the specified plan file using Pydantic schema validation.
    Supports both JSON (.json) and YAML (.yaml, .yml) formats.

    Validation matches PlanImporter behavior exactly, ensuring that files
    validated here will import successfully.

    Examples:

        \b
        # Validate a JSON plan file
        $ obra validate-plan docs/development/FEAT-001_MACHINE_PLAN.json

        \b
        # Validate a YAML plan file
        $ obra validate-plan docs/development/FEAT-001_MACHINE_PLAN.yaml

        \b
        # Validate with verbose output (shows plan details)
        $ obra validate-plan --verbose plan.json

    Exit Codes:
        0: Validation passed - Plan is valid and ready for import
        1: Validation failed - Schema validation errors found
    """
    command = ValidatePlanCommand()
    exit_code = command.execute(file_path, verbose)
    sys.exit(exit_code)


if __name__ == "__main__":
    # Allow running as standalone script
    validate_plan_cli()
