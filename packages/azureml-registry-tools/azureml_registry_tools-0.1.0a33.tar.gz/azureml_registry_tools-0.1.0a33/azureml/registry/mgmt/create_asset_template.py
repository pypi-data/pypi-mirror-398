# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
"""Asset template creation commands for registry-mgmt CLI."""

from pathlib import Path
from .create_model_spec import generate_model_spec_content


def asset_template(folder_path: Path, dry_run: bool = False) -> bool:
    """Create asset template files in the specified folder.

    Args:
        folder_path (Path): Path to the folder where template files will be created
        dry_run (bool): If True, perform a dry run without creating files

    Returns:
        bool: True if template creation succeeds, False otherwise
    """
    if dry_run:
        print(f"[DRY RUN] Would create asset template files in: {folder_path}")
        return True

    folder_path = folder_path.resolve()
    print(f"Creating asset template files in {folder_path} ...")

    # Check if folder path exists, create if it doesn't
    if not folder_path.exists():
        try:
            print(f"Folder path does not exist, creating directory {folder_path} ...")
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {folder_path}")
        except Exception as e:
            print(f"[ERROR] Failed to create directory {folder_path}: {e}")
            return False

    # Get the data directory path (relative to this module)
    data_dir = Path(__file__).parent.parent / "data"

    # List of template files to create
    template_files = ["asset.yaml", "spec.yaml", "model.yaml", "notes.md", "evaluation.md", "description.md"]

    # Create each template file
    try:
        for output_name in template_files:
            output_path = folder_path / output_name

            # Special handling for spec.yaml (generate from schema)
            if output_name == "spec.yaml":
                schema_path = data_dir / "model.schema.json"
                if not schema_path.exists():
                    print(f"[ERROR] Schema file not found: {schema_path}")
                    return False

                try:
                    spec_content = generate_model_spec_content(schema_path)
                    with open(output_path, "w", encoding="utf-8") as output_file:
                        output_file.write(spec_content)
                    print(f"Created {output_path}")
                except Exception as e:
                    print(f"[ERROR] Failed to generate spec.yaml: {e}")
                    return False
            else:
                # Handle other template files from data/ folder
                template_name = f"{output_name}.template"
                template_path = data_dir / template_name

                # Check if template file exists
                if not template_path.exists():
                    print(f"[ERROR] Template file not found: {template_path}")
                    return False

                # Read template content and write to output file
                with open(template_path, "r", encoding="utf-8") as template_file:
                    content = template_file.read()

                with open(output_path, "w", encoding="utf-8") as output_file:
                    output_file.write(content)

                print(f"Created {output_path}")

        print(f"Created {len(template_files)} template files in {folder_path}")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to create template files: {e}")
        return False
