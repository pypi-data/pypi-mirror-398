# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
"""Generate model template spec.yaml file from model.schema.json."""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple


class ModelTemplateGenerator:
    """ModelTemplateGenerator class."""

    def __init__(self, schema_path: Path, output_path: Path):
        """Init for ModelTemplateGenerator."""
        self.schema_path = schema_path
        self.output_path = output_path
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict[str, Any]:
        """Load and parse the JSON schema file."""
        with open(self.schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _get_enum_values(self, prop_def: Dict[str, Any]) -> List[str]:
        """Extract enum values from property definition."""
        if "enum" in prop_def:
            return prop_def["enum"]
        return []

    def _get_pattern_examples(self, pattern: str, prop_name: str) -> List[str]:
        """Generate examples from regex patterns by extracting options."""
        # Special handling for trainingDataDate pattern
        if prop_name == "trainingDataDate":
            return ["January 2024"]

        # Extract options from regex patterns
        if "(" in pattern and "|" in pattern:
            # Look for the main pattern group - typically the first group that has multiple options
            # Handle patterns like ^(option1|option2|option3)(?:...)
            main_match = re.search(r"\^?\(([^)]+\|[^)]*)\)", pattern)
            if main_match:
                options_str = main_match.group(1)
                options = []

                # Split by | and clean up each option
                for opt in options_str.split("|"):
                    # Clean up the option - remove anchors, whitespace, escape chars
                    cleaned = opt.strip().replace("\\", "")

                    # Skip empty options and regex artifacts
                    if (cleaned and
                            len(cleaned) > 1 and
                            not cleaned.startswith("?") and
                            not cleaned.startswith("*") and
                            not cleaned.startswith("+") and
                            not re.match(r"^[^a-zA-Z0-9-]+$", cleaned)):  # Skip pure symbol patterns
                        options.append(cleaned)

                if options:
                    # Return up to 6 unique options
                    unique_options = list(dict.fromkeys(options))  # Remove duplicates while preserving order
                    if len(unique_options) > 6:
                        return unique_options[:6] + ["etc."]
                    return unique_options[:6]

        return []

    def _get_example_value(self, prop_def: Dict[str, Any], prop_name: str) -> Tuple[str, str]:
        """Generate a generic example value based on property type and schema constraints."""
        prop_type = prop_def.get("type", "string")

        # Handle special cases first
        if prop_name == "notes":
            description = prop_def.get("description", "Reference to notes documentation")
            return '"notes.md"', description
        elif prop_name == "evaluation":
            description = prop_def.get("description", "Reference to evaluation documentation")
            return '"evaluation.md"', description

        # Handle enum values
        enum_values = self._get_enum_values(prop_def)
        if enum_values:
            if enum_values == [""]:
                return '""', "Empty string means enabled. Remove if disabled."
            return f'"{enum_values[0]}"', f"options: {', '.join(enum_values)}"

        # Handle patterns - extract options if available
        if "pattern" in prop_def:
            pattern = prop_def["pattern"]
            examples = self._get_pattern_examples(pattern, prop_name)
            if examples:
                if len(examples) > 1:
                    value = ",".join(examples[:3])
                    return f'"{value}"', f"options: {', '.join(examples)} (comma-separated)"
                else:
                    return f'"{examples[0]}"', f"pattern: {pattern[:50]}..." if len(pattern) > 50 else f"pattern: {pattern}"
            else:
                return '"example-value"', f"pattern: {pattern[:50]}..." if len(pattern) > 50 else f"pattern: {pattern}"

        # Handle oneOf types
        if "oneOf" in prop_def:
            type_info = []
            minimum = None
            for oneof in prop_def["oneOf"]:
                if oneof.get("type"):
                    type_info.append(oneof["type"])
                if oneof.get("type") == "integer" and "minimum" in oneof:
                    minimum = oneof["minimum"]
            types_str = " or ".join(set(type_info))
            min_info = f" (minimum: {minimum})" if minimum else ""
            return "1", f"can be {types_str}{min_info}"

        # Handle arrays
        if prop_type == "array":
            items_def = prop_def.get("items", {})
            if "enum" in items_def:
                return f'["{items_def["enum"][0]}"]', f"options: {', '.join(items_def['enum'])}"
            else:
                return '["example-value"]', "Array of values"

        # Handle objects
        if prop_type == "object":
            return None, "Object type"

        # Handle basic types with constraints
        if prop_type == "integer":
            minimum = prop_def.get("minimum", 1)
            return str(minimum), f"minimum: {minimum}"
        elif prop_type == "number":
            return "1.0", "Number type"
        elif prop_type == "boolean":
            return "true", "Boolean type"
        else:
            # String type
            return '"example-value"', "String type"

    def _format_comment(self, comment: str, is_required: bool, additional_info: str = "") -> str:
        """Format the inline comment for a property."""
        if additional_info and additional_info != comment:
            comment += f" ({additional_info})"

        required_text = "required" if is_required else "optional"
        return f"# {comment} ({required_text})"

    def _generate_property_line(self, prop_name: str, prop_def: Dict[str, Any],
                                indent: int = 0, is_required: bool = False) -> List[str]:
        """Generate YAML lines for a single property."""
        description = prop_def.get("description", prop_name.replace("_", " ").replace("-", " ").title())
        example_value, additional_info = self._get_example_value(prop_def, prop_name)

        indent_str = "  " * indent

        # Handle object types that need special formatting
        if example_value is None and prop_def.get("type") == "object":
            comment = self._format_comment(description, is_required, additional_info)
            # For generic objects, just show the key with comment
            return [f"{indent_str}{prop_name}: {comment}"]

        comment = self._format_comment(description, is_required, additional_info)
        return [f"{indent_str}{prop_name}: {example_value} {comment}"]

    def generate_template(self) -> str:
        """Generate the complete template file content."""
        lines = [
            "# AzureML Model Specification Template",
            "# Generated from schema - Fill in the values below to create your model specification",
            "",
        ]

        # Get required fields
        required_fields = set(self.schema.get("required", []))

        # Add top-level required fields first
        for field in ["$schema", "name", "path"]:
            if field in self.schema["properties"]:
                prop_def = self.schema["properties"][field]
                is_required = field in required_fields
                if field == "$schema":
                    lines.append('$schema: "https://azuremlschemas.azureedge.net/latest/model.schema.json" # JSON schema reference (required)')
                elif field == "name":
                    lines.append('name: "example-model-name" # Model name (required)')
                elif field == "path":
                    lines.append('path: "./" # Path to model files (required)')

        lines.append("")

        # Add all other sections dynamically (excluding the ones we already handled)
        handled_fields = {"$schema", "name", "path", "version"}
        required_fields = set(self.schema.get("required", []))

        for section_name, section_def in self.schema["properties"].items():
            if section_name in handled_fields:
                continue
            # Check if this section has properties (indicating it's a structured section)
            if isinstance(section_def, dict) and "properties" in section_def:
                is_required = section_name in required_fields
                required_text = "required" if is_required else "optional"
                lines.append(f"{section_name}: # {section_name.title()} ({required_text})")

                # Add all properties within this section
                for prop_name, prop_def in section_def["properties"].items():
                    lines.extend(self._generate_property_line(prop_name, prop_def, indent=1))

                lines.append("")

        # Add version at the end
        if "version" in self.schema["properties"]:
            version_def = self.schema["properties"]["version"]
            is_required = "version" in required_fields
            lines.extend(self._generate_property_line("version", version_def, is_required=is_required))

        return "\n".join(lines)

    def write_template(self):
        """Generate and write the template file."""
        template_content = self.generate_template()

        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(template_content)

        print(f"Template generated successfully: {self.output_path}")


def generate_model_spec_content(schema_path: Path) -> str:
    """Generate model spec content from schema file.

    Args:
        schema_path (Path): Path to the model.schema.json file

    Returns:
        str: Generated model spec YAML content
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    generator = ModelTemplateGenerator(schema_path, "")
    return generator.generate_template()
