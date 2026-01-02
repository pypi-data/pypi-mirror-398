"""Parser for the rec format."""

from __future__ import annotations

import re
from dataclasses import dataclass, field as dataclass_field
from typing import TextIO


# Field name regex: starts with letter or %, followed by alphanumeric or underscore
FIELD_NAME_RE = re.compile(r"^([a-zA-Z%][a-zA-Z0-9_]*):\s?(.*)$")

# Continuation line: starts with + and optional space
CONTINUATION_RE = re.compile(r"^\+\s?(.*)$")

# Line continuation (backslash at end of line)
LINE_CONTINUATION_RE = re.compile(r"^(.*)\\$")


@dataclass
class Field:
    """A field in a record."""

    name: str
    value: str

    def __str__(self) -> str:
        # Encode multi-line values
        lines = self.value.split("\n")
        if len(lines) == 1:
            return f"{self.name}: {self.value}"
        else:
            result = [f"{self.name}: {lines[0]}"]
            for line in lines[1:]:
                result.append(f"+ {line}")
            return "\n".join(result)


@dataclass
class Record:
    """A record containing fields."""

    fields: list[Field] = dataclass_field(default_factory=list)

    def get_field(self, name: str) -> str | None:
        """Get the value of the first field with the given name."""
        for f in self.fields:
            if f.name == name:
                return f.value
        return None

    def get_fields(self, name: str) -> list[str]:
        """Get all values for fields with the given name."""
        return [f.value for f in self.fields if f.name == name]

    def get_field_count(self, name: str) -> int:
        """Get the count of fields with the given name."""
        return sum(1 for f in self.fields if f.name == name)

    def has_field(self, name: str) -> bool:
        """Check if the record has a field with the given name."""
        return any(f.name == name for f in self.fields)

    def get_all_field_names(self) -> set[str]:
        """Get all unique field names in this record."""
        return {f.name for f in self.fields}

    def __str__(self) -> str:
        return "\n".join(str(f) for f in self.fields)


@dataclass
class RecordDescriptor(Record):
    """A record descriptor (starts with %rec field)."""

    @property
    def record_type(self) -> str | None:
        """Get the type name from %rec field."""
        rec = self.get_field("%rec")
        if rec:
            # Type may be followed by URL/path for remote descriptor
            parts = rec.split(None, 1)
            return parts[0] if parts else None
        return None

    @property
    def mandatory_fields(self) -> set[str]:
        """Get the set of mandatory field names."""
        result = set()
        for value in self.get_fields("%mandatory"):
            result.update(value.split())
        return result

    @property
    def key_field(self) -> str | None:
        """Get the key field name if specified."""
        return self.get_field("%key")

    @property
    def sort_fields(self) -> list[str]:
        """Get the list of sort field names."""
        sort_value = self.get_field("%sort")
        if sort_value:
            return sort_value.split()
        return []


@dataclass
class RecordSet:
    """A set of records with an optional descriptor."""

    descriptor: RecordDescriptor | None = None
    records: list[Record] = dataclass_field(default_factory=list)

    @property
    def record_type(self) -> str | None:
        """Get the type name from the descriptor."""
        if self.descriptor:
            return self.descriptor.record_type
        return None


def _parse_lines(lines: list[str]) -> list[Record | RecordDescriptor]:
    """Parse lines into records."""
    result: list[Record | RecordDescriptor] = []
    current_fields: list[Field] = []
    current_field_name: str | None = None
    current_field_value_lines: list[str] = []
    line_continued = False

    def finish_field():
        nonlocal current_field_name, current_field_value_lines
        if current_field_name is not None:
            value = "\n".join(current_field_value_lines)
            current_fields.append(Field(current_field_name, value))
            current_field_name = None
            current_field_value_lines = []

    def finish_record():
        nonlocal current_fields
        finish_field()
        if current_fields:
            # Check if this is a descriptor (has %rec field)
            is_descriptor = any(f.name == "%rec" for f in current_fields)
            if is_descriptor:
                result.append(RecordDescriptor(fields=current_fields))
            else:
                result.append(Record(fields=current_fields))
            current_fields = []

    for line in lines:
        # Skip comment lines
        if line.startswith("#"):
            continue

        # Handle line continuation from previous line
        if line_continued:
            line_continued = False
            # Check for another continuation
            match = LINE_CONTINUATION_RE.match(line)
            if match:
                current_field_value_lines[-1] += match.group(1)
                line_continued = True
            else:
                current_field_value_lines[-1] += line
            continue

        # Check for blank line (record separator)
        if not line.strip():
            finish_record()
            continue

        # Check for continuation line (starts with +)
        cont_match = CONTINUATION_RE.match(line)
        if cont_match:
            if current_field_name is not None:
                current_field_value_lines.append(cont_match.group(1))
            continue

        # Check for field line
        field_match = FIELD_NAME_RE.match(line)
        if field_match:
            finish_field()
            current_field_name = field_match.group(1)
            value = field_match.group(2)

            # Check for line continuation (backslash at end)
            line_cont_match = LINE_CONTINUATION_RE.match(value)
            if line_cont_match:
                current_field_value_lines = [line_cont_match.group(1)]
                line_continued = True
            else:
                current_field_value_lines = [value]

    # Finish any remaining record
    finish_record()

    return result


def _organize_record_sets(items: list[Record | RecordDescriptor]) -> list[RecordSet]:
    """Organize parsed items into record sets."""
    result: list[RecordSet] = []
    current_set: RecordSet | None = None

    for item in items:
        if isinstance(item, RecordDescriptor):
            # Start a new record set with this descriptor
            if current_set is not None:
                result.append(current_set)
            current_set = RecordSet(descriptor=item)
        else:
            # Add record to current set
            if current_set is None:
                # Anonymous records before any descriptor
                current_set = RecordSet()
            current_set.records.append(item)

    # Add the last record set
    if current_set is not None:
        result.append(current_set)

    return result


def parse(text: str) -> list[RecordSet]:
    """Parse rec format text into record sets."""
    lines = text.split("\n")
    items = _parse_lines(lines)
    return _organize_record_sets(items)


def parse_file(file: TextIO) -> list[RecordSet]:
    """Parse rec format from a file object."""
    return parse(file.read())
