"""
CLI commands for quality assurance.
"""

import json
import sys
from pathlib import Path
from typing import Optional

from pycharter.config import get_database_url
from pycharter.metadata_store import PostgresMetadataStore
from pycharter.quality import QualityCheck, QualityCheckOptions, QualityThresholds


def cmd_quality_check(
    schema_id: Optional[str],
    contract: Optional[str],
    data: str,
    database_url: Optional[str],
    record_violations: bool,
    check_thresholds: bool,
    thresholds_file: Optional[str],
    sample_size: Optional[int],
    output: Optional[str],
) -> int:
    """
    Run quality check command.

    Args:
        schema_id: Schema ID (for store-based validation)
        contract: Contract file path (for contract-based validation)
        data: Data file path or '-' for stdin
        database_url: Database connection string
        record_violations: Whether to record violations
        check_thresholds: Whether to check thresholds
        thresholds_file: Path to thresholds JSON file
        sample_size: Sample size for large datasets
        output: Output file path

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Validate arguments
        if not schema_id and not contract:
            print("❌ Error: Either --schema-id or --contract must be provided", file=sys.stderr)
            return 1

        if schema_id and not database_url:
            # Try to get from config
            database_url = get_database_url()
            if not database_url:
                print(
                    "❌ Error: --database-url required when using --schema-id",
                    file=sys.stderr,
                )
                return 1

        # Initialize store if needed
        store = None
        if schema_id:
            store = PostgresMetadataStore(connection_string=database_url)
            store.connect()
            print(f"✓ Connected to database")

        # Load thresholds if provided
        thresholds = None
        if check_thresholds:
            if thresholds_file:
                with open(thresholds_file, "r") as f:
                    thresholds_data = json.load(f)
                    thresholds = QualityThresholds(**thresholds_data)
            else:
                # Use default thresholds
                thresholds = QualityThresholds()

        # Create quality check
        quality_check = QualityCheck(store=store)

        # Build options
        options = QualityCheckOptions(
            record_violations=record_violations,
            calculate_metrics=True,
            check_thresholds=check_thresholds,
            thresholds=thresholds,
            include_field_metrics=True,
            sample_size=sample_size,
        )

        # Prepare data source
        if data == "-":
            # Read from stdin
            data_source = json.load(sys.stdin)
            if not isinstance(data_source, list):
                data_source = [data_source]
        else:
            data_path = Path(data)
            if not data_path.exists():
                print(f"❌ Error: Data file not found: {data}", file=sys.stderr)
                return 1
            data_source = data

        # Run quality check
        print(f"Running quality check...")
        if schema_id:
            print(f"  Schema ID: {schema_id}")
        if contract:
            print(f"  Contract: {contract}")
        print(f"  Data: {data}")

        report = quality_check.run(
            schema_id=schema_id,
            contract=contract,
            data=data_source,
            options=options,
        )

        # Display results
        print("\n" + "=" * 70)
        print("Quality Check Report")
        print("=" * 70)
        print(f"Schema ID: {report.schema_id}")
        print(f"Check Timestamp: {report.check_timestamp}")
        print(f"Record Count: {report.record_count}")
        print(f"Valid Records: {report.valid_count}")
        print(f"Invalid Records: {report.invalid_count}")

        if report.quality_score:
            print(f"\nQuality Score: {report.quality_score.overall_score:.2f}/100")
            print(f"  Accuracy: {report.quality_score.accuracy:.2%}")
            print(f"  Completeness: {report.quality_score.completeness:.2%}")
            print(f"  Violation Rate: {report.quality_score.violation_rate:.2%}")

        if report.threshold_breaches:
            print(f"\n⚠ Threshold Breaches:")
            for breach in report.threshold_breaches:
                print(f"  - {breach}")

        if report.violation_count > 0:
            print(f"\n⚠ Violations Recorded: {report.violation_count}")

        # Save report if output specified
        if output:
            output_path = Path(output)
            with open(output_path, "w") as f:
                json.dump(report.model_dump(), f, indent=2, default=str)
            print(f"\n✓ Report saved to: {output}")

        # Return exit code based on pass/fail
        if report.passed:
            print("\n✓ Quality check passed")
            return 0
        else:
            print("\n❌ Quality check failed")
            return 1

    except Exception as e:
        print(f"❌ Error running quality check: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1
    finally:
        if store:
            store.disconnect()


def cmd_quality_violations(
    schema_id: Optional[str],
    status: Optional[str],
    severity: Optional[str],
    output: Optional[str],
) -> int:
    """
    Query violations command.

    Args:
        schema_id: Filter by schema ID
        status: Filter by status
        severity: Filter by severity
        output: Output file path

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        print("⚠ Violation tracking requires a database connection")
        print("   This feature will be available when database persistence is implemented")
        return 0

    except Exception as e:
        print(f"❌ Error querying violations: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1

