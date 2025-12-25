"""Lightweight CSV to YAML and YAML to CSV converter."""

import argparse
import csv
import io
import sys
from pathlib import Path

import yaml


def csv_to_yaml(csv_input: str | Path, *, as_string: bool = False) -> str | list[dict]:
    """Convert CSV to YAML.

    Args:
        csv_input: CSV string or path to CSV file
        as_string: If True, return YAML string; otherwise return list of dicts

    Returns:
        YAML string or list of dictionaries
    """
    if isinstance(csv_input, Path) or (isinstance(csv_input, str) and Path(csv_input).exists()):
        with open(csv_input, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            data = list(reader)
    else:
        # Strip BOM from string input if present
        if csv_input.startswith('\ufeff'):
            csv_input = csv_input[1:]
        reader = csv.DictReader(io.StringIO(csv_input))
        data = list(reader)

    # Convert list to dict with row numbers as keys (1-indexed)
    data = {i: row for i, row in enumerate(data, start=1)}

    if as_string:
        return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return data


def yaml_to_csv(yaml_input: str | Path, *, as_string: bool = False) -> str | list[dict]:
    """Convert YAML to CSV.

    Args:
        yaml_input: YAML string or path to YAML file
        as_string: If True, return CSV string; otherwise return list of dicts

    Returns:
        CSV string or list of dictionaries
    """
    if isinstance(yaml_input, Path) or (isinstance(yaml_input, str) and Path(yaml_input).exists()):
        with open(yaml_input, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    else:
        data = yaml.safe_load(yaml_input)

    # Handle dict with row numbers as keys (convert to list)
    if isinstance(data, dict):
        # Check if all keys are integers (row number format)
        if data and all(isinstance(k, int) for k in data.keys()):
            # Sort by key to preserve row order, then extract values
            data = [data[k] for k in sorted(data.keys())]
        else:
            # Single object dict - wrap in list
            data = [data]
    elif not isinstance(data, list):
        data = [data]

    if as_string:
        if not data:
            return ""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()
    return data


def csv_file_to_yaml_file(csv_path: str | Path, yaml_path: str | Path) -> None:
    """Convert CSV file to YAML file."""
    yaml_str = csv_to_yaml(csv_path, as_string=True)
    Path(yaml_path).write_text(yaml_str, encoding="utf-8")


def yaml_file_to_csv_file(yaml_path: str | Path, csv_path: str | Path) -> None:
    """Convert YAML file to CSV file."""
    csv_str = yaml_to_csv(yaml_path, as_string=True)
    Path(csv_path).write_text(csv_str, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Convert between CSV and YAML formats",
        prog="csv-to-yaml"
    )
    parser.add_argument("input", help="Input file path")
    parser.add_argument("-o", "--output", help="Output file path (default: stdout)")
    parser.add_argument(
        "-f", "--format",
        choices=["csv", "yaml"],
        help="Output format (auto-detected from file extension if not specified)"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)

    input_ext = input_path.suffix.lower()

    if args.format:
        output_format = args.format
    elif args.output:
        output_ext = Path(args.output).suffix.lower()
        output_format = "yaml" if output_ext in (".yaml", ".yml") else "csv"
    else:
        output_format = "yaml" if input_ext == ".csv" else "csv"

    if output_format == "yaml":
        result = csv_to_yaml(input_path, as_string=True)
    else:
        result = yaml_to_csv(input_path, as_string=True)

    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"Converted to {args.output}")
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
