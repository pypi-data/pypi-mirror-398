"""Implementation of recsel functionality."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import TextIO

from .parser import Record, RecordSet, parse, parse_file, Field
from .sex import evaluate_sex


@dataclass
class RecselResult:
    """Result of a recsel operation."""

    records: list[Record]
    descriptor: Record | None = None

    def __str__(self) -> str:
        parts = []
        if self.descriptor:
            parts.append(str(self.descriptor))
        for record in self.records:
            parts.append(str(record))
        return "\n\n".join(parts)


def _parse_indexes(indexes_str: str) -> list[int]:
    """Parse index specification like '0,2,4-9' into a list of indexes."""
    result = set()
    for part in indexes_str.split(","):
        part = part.strip()
        if "-" in part:
            range_parts = part.split("-", 1)
            start = int(range_parts[0])
            end = int(range_parts[1])
            for i in range(start, end + 1):
                result.add(i)
        else:
            result.add(int(part))
    return sorted(result)


def _parse_field_list(field_list: str) -> list[tuple[str, str | None]]:
    """Parse a field expression like 'Name,Email:ElectronicMail'.

    Returns list of (field_name, alias) tuples.
    """
    result = []
    for part in field_list.split(","):
        part = part.strip()
        if ":" in part:
            field_parts = part.split(":", 1)
            # Handle subscripts like Email[0]
            field_name = field_parts[0].strip()
            alias = field_parts[1].strip()
        else:
            field_name = part
            alias = None
        result.append((field_name, alias))
    return result


def _extract_field_with_subscript(field_spec: str) -> tuple[str, int | None]:
    """Parse field name with optional subscript like 'Email[0]'."""
    match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\[(\d+)\]$", field_spec)
    if match:
        return match.group(1), int(match.group(2))
    return field_spec, None


def _select_fields(record: Record, fields: list[tuple[str, str | None]]) -> list[Field]:
    """Select and optionally rename fields from a record."""
    result = []
    for field_spec, alias in fields:
        field_name, subscript = _extract_field_with_subscript(field_spec)
        output_name = alias if alias else field_name

        if subscript is not None:
            values = record.get_fields(field_name)
            if subscript < len(values):
                result.append(Field(output_name, values[subscript]))
        else:
            for f in record.fields:
                if f.name == field_name:
                    result.append(Field(output_name, f.value))
    return result


def _quick_match(
    record: Record, substring: str, case_insensitive: bool = False
) -> bool:
    """Check if any field value contains the substring."""
    search_str = substring.lower() if case_insensitive else substring
    for field in record.fields:
        value = field.value.lower() if case_insensitive else field.value
        if search_str in value:
            return True
    return False


def _sort_records(
    records: list[Record], sort_fields: list[str], record_set: RecordSet | None = None
) -> list[Record]:
    """Sort records by the specified fields."""
    if not sort_fields:
        return records

    def sort_key(record: Record) -> tuple:
        keys = []
        for field_name in sort_fields:
            value = record.get_field(field_name)
            if value is None:
                value = ""
            # Try numeric sort first
            try:
                if "." in value:
                    keys.append((0, float(value), value))
                else:
                    keys.append((0, int(value), value))
            except (ValueError, TypeError):
                keys.append((1, 0, value))  # String sort
        return tuple(keys)

    return sorted(records, key=sort_key)


def _group_records(records: list[Record], group_fields: list[str]) -> list[Record]:
    """Group records by the specified fields, merging them."""
    if not group_fields:
        return records

    groups: dict[tuple, Record] = {}

    for record in records:
        # Create group key from field values
        key = tuple(record.get_field(f) or "" for f in group_fields)

        if key not in groups:
            # Create new group record
            groups[key] = Record(fields=list(record.fields))
        else:
            # Merge fields into existing group
            existing = groups[key]
            for field in record.fields:
                # Add fields that are not group fields
                if field.name not in group_fields:
                    existing.fields.append(field)

    return list(groups.values())


def _remove_duplicate_fields(record: Record) -> Record:
    """Remove duplicate fields (same name and value)."""
    seen = set()
    unique_fields = []
    for field in record.fields:
        key = (field.name, field.value)
        if key not in seen:
            seen.add(key)
            unique_fields.append(field)
    return Record(fields=unique_fields)


def recsel(
    input_data: str | TextIO | list[str],
    *,
    record_type: str | None = None,
    indexes: str | None = None,
    expression: str | None = None,
    quick: str | None = None,
    random_count: int | None = None,
    print_fields: str | None = None,
    print_values: str | None = None,
    print_row: str | None = None,
    count: bool = False,
    include_descriptors: bool = False,
    collapse: bool = False,
    case_insensitive: bool = False,
    sort: str | None = None,
    group_by: str | None = None,
    uniq: bool = False,
) -> RecselResult | int | str | list[str]:
    """Select records from rec data.

    Args:
        input_data: Rec format string, file object, or list of file paths.
        record_type: Select records of this type only (-t).
        indexes: Select records at these positions (-n), e.g. "0,2,4-9".
        expression: Selection expression to filter records (-e).
        quick: Select records with field containing this substring (-q).
        random_count: Select this many random records (-m).
        print_fields: Print only these fields with names (-p), e.g. "Name,Email".
        print_values: Print only field values (-P), e.g. "Name,Email".
        print_row: Print field values on single row (-R), e.g. "Name,Email".
        count: Return count of matching records (-c).
        include_descriptors: Include record descriptors in output (-d).
        collapse: Don't separate records with blank lines (-C).
        case_insensitive: Case-insensitive matching in expressions (-i).
        sort: Sort by these fields (-S), e.g. "Name,Date".
        group_by: Group by these fields (-G), e.g. "Category".
        uniq: Remove duplicate fields (-U).

    Returns:
        RecselResult containing matching records, or int if count=True,
        or str/list[str] if print_values or print_row is specified.
    """
    # Parse input
    if isinstance(input_data, str):
        record_sets = parse(input_data)
    elif isinstance(input_data, list):
        # List of file paths
        all_sets = []
        for path in input_data:
            with open(path, "r") as f:
                all_sets.extend(parse_file(f))
        record_sets = all_sets
    else:
        record_sets = parse_file(input_data)

    # Find the appropriate record set(s)
    target_sets: list[RecordSet] = []
    if record_type:
        for rs in record_sets:
            if rs.record_type == record_type:
                target_sets.append(rs)
        if not target_sets:
            # Type not found, return empty result
            if count:
                return 0
            return RecselResult(records=[])
    else:
        # If no type specified
        if len(record_sets) == 1:
            target_sets = record_sets
        else:
            # Check if there are multiple typed record sets
            typed_sets = [rs for rs in record_sets if rs.record_type]
            if len(typed_sets) > 1:
                raise ValueError(
                    "several record types found. Please use record_type to specify one."
                )
            target_sets = record_sets

    # Collect all records from target sets
    all_records: list[Record] = []
    descriptor = None
    for rs in target_sets:
        if rs.descriptor and descriptor is None:
            descriptor = rs.descriptor
        all_records.extend(rs.records)

    # Apply selection criteria
    selected = all_records

    # Filter by indexes
    if indexes is not None:
        idx_list = _parse_indexes(indexes)
        selected = [r for i, r in enumerate(selected) if i in idx_list]

    # Filter by expression
    if expression:
        selected = [
            r for r in selected if evaluate_sex(expression, r, case_insensitive)
        ]

    # Filter by quick substring search
    if quick:
        selected = [r for r in selected if _quick_match(r, quick, case_insensitive)]

    # Random selection
    if random_count is not None:
        if random_count == 0:
            pass  # Select all
        elif random_count < len(selected):
            selected = random.sample(selected, random_count)

    # Group records
    if group_by:
        group_fields = [f.strip() for f in group_by.split(",")]
        selected = _group_records(selected, group_fields)

    # Sort records
    sort_fields = []
    if sort:
        sort_fields = [f.strip() for f in sort.split(",")]
    elif descriptor and hasattr(descriptor, "sort_fields") and descriptor.sort_fields:
        sort_fields = descriptor.sort_fields

    if sort_fields:
        selected = _sort_records(selected, sort_fields)

    # Remove duplicate fields
    if uniq:
        selected = [_remove_duplicate_fields(r) for r in selected]

    # Return count if requested
    if count:
        return len(selected)

    # Handle field selection and output formatting
    if print_fields or print_values or print_row:
        field_spec = print_fields or print_values or print_row
        assert field_spec is not None  # Guaranteed by the if condition above
        fields = _parse_field_list(field_spec)

        if print_row:
            # Return values on single row, space-separated per record
            rows = []
            for record in selected:
                selected_fields = _select_fields(record, fields)
                row_values = [fld.value for fld in selected_fields]
                rows.append(" ".join(row_values))
            return rows

        if print_values:
            # Return just values
            result_lines = []
            for record in selected:
                selected_fields = _select_fields(record, fields)
                for fld in selected_fields:
                    result_lines.append(fld.value)
            return "\n".join(result_lines) if not collapse else " ".join(result_lines)

        # print_fields: return records with only selected fields
        output_records = []
        for record in selected:
            selected_fields = _select_fields(record, fields)
            output_records.append(Record(fields=selected_fields))
        selected = output_records

    # Build result
    result_descriptor = descriptor if include_descriptors else None
    return RecselResult(records=selected, descriptor=result_descriptor)


def format_recsel_output(
    result: RecselResult | int | str | list[str],
    collapse: bool = False,
) -> str:
    """Format recsel result for output."""
    if isinstance(result, int):
        return str(result)

    if isinstance(result, str):
        return result

    if isinstance(result, list):
        separator = " " if collapse else "\n"
        return separator.join(result)

    # RecselResult
    parts = []
    if result.descriptor:
        parts.append(str(result.descriptor))

    for record in result.records:
        parts.append(str(record))

    separator = "\n" if collapse else "\n\n"
    return separator.join(parts)
