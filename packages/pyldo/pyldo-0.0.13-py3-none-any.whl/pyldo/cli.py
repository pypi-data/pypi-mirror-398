"""
PyLDO Command Line Interface

Provides commands for generating Python code from ShEx and LinkML schemas.

Usage:
    pyldo generate shapes/*.shex --output .ldo/
    pyldo generate schemas/*.yaml --output .ldo/
    pyldo init
"""

import sys
from pathlib import Path

import click


@click.group()
@click.version_option()
def main():
    """PyLDO - Linked Data Objects for Python.

    Generate type-safe Python code from ShEx or LinkML schemas for working with RDF data.
    """
    pass


@main.command()
@click.argument("schema_files", nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=Path(".ldo"),
    help="Output directory for generated files (default: .ldo/)",
)
@click.option(
    "--base-iri",
    "-b",
    type=str,
    default="http://example.org/",
    help="Base IRI for resolving relative IRIs",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["auto", "shex", "linkml"]),
    default="auto",
    help="Schema format (auto-detect by extension if not specified)",
)
def generate(schema_files: tuple[Path, ...], output: Path, base_iri: str, format: str):
    """Generate Python types and JSON-LD contexts from ShEx or LinkML schemas.

    SCHEMA_FILES: One or more .shex or .yaml/.yml files to process

    Example:
        pyldo generate shapes/person.shex shapes/post.shex -o .ldo/
        pyldo generate schemas/person.yaml -o .ldo/
    """
    if not schema_files:
        click.echo("Error: No schema files specified", err=True)
        click.echo("Usage: pyldo generate <schema_files> [--output <dir>]", err=True)
        sys.exit(1)

    # Ensure output directory exists
    output.mkdir(parents=True, exist_ok=True)

    try:
        from pyldo.converter import (
            generate_jsonld_context,
            generate_python_types,
            generate_schema_file,
            generate_shapetypes_file,
            parse_linkml,
            parse_shex,
        )
        from pyldo.converter.context_generator import generate_context_file
    except ImportError as e:
        click.echo(f"Error: Missing dependency - {e}", err=True)
        click.echo("Install dependencies with: pip install pyldo[dev]", err=True)
        sys.exit(1)

    for schema_path in schema_files:
        click.echo(f"Processing {schema_path}...")

        try:
            # Read schema source
            schema_source = schema_path.read_text()
            
            # Determine format
            detected_format = format
            if detected_format == "auto":
                suffix = schema_path.suffix.lower()
                if suffix in (".yaml", ".yml"):
                    detected_format = "linkml"
                elif suffix == ".shex":
                    detected_format = "shex"
                else:
                    # Try to auto-detect by content
                    if schema_source.strip().startswith(("prefixes:", "classes:", "id:", "name:")):
                        detected_format = "linkml"
                    else:
                        detected_format = "shex"
            
            # Parse based on format
            if detected_format == "linkml":
                click.echo(f"  Format: LinkML")
                schema = parse_linkml(schema_source, base_iri)
            else:
                click.echo(f"  Format: ShEx")
                schema = parse_shex(schema_source, base_iri)

            if not schema.shapes:
                click.echo(f"  Warning: No shapes found in {schema_path}", err=True)
                continue

            # Generate base filename
            base_name = schema_path.stem

            # Generate Python types
            types_code = generate_python_types(schema, base_name)
            types_path = output / f"{base_name}_types.py"
            types_path.write_text(types_code)
            click.echo(f"  Generated {types_path}")

            # Generate JSON-LD context
            context_var_name = f"{base_name}_context"
            context_code = generate_context_file(schema, context_var_name)
            context_path = output / f"{base_name}_context.py"
            context_path.write_text(context_code)
            click.echo(f"  Generated {context_path}")

            # Generate ShEx schema as JSON
            schema_var_name = f"{base_name}_schema"
            schema_code = generate_schema_file(schema, schema_var_name)
            schema_path_out = output / f"{base_name}_schema.py"
            schema_path_out.write_text(schema_code)
            click.echo(f"  Generated {schema_path_out}")

            # Generate ShapeTypes
            shapetypes_code = generate_shapetypes_file(
                schema,
                types_module=f"{base_name}_types",
                context_module=context_var_name,
                schema_module=schema_var_name,
            )
            shapetypes_path = output / f"{base_name}_shapetypes.py"
            shapetypes_path.write_text(shapetypes_code)
            click.echo(f"  Generated {shapetypes_path}")

            # Report shapes found
            shape_names = [s.id.rsplit("#", 1)[-1].rsplit("/", 1)[-1] for s in schema.shapes]
            click.echo(f"  Shapes: {', '.join(shape_names)}")

        except Exception as e:
            click.echo(f"  Error processing {schema_path}: {e}", err=True)
            continue

    click.echo("Done!")


@main.command()
@click.option(
    "--shapes-dir",
    "-s",
    type=click.Path(path_type=Path),
    default=Path("shapes"),
    help="Directory for ShEx schemas (default: shapes/)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=Path(".ldo"),
    help="Output directory for generated files (default: .ldo/)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["shex", "linkml", "both"]),
    default="both",
    help="Which sample schemas to create (default: both)",
)
def init(shapes_dir: Path, output_dir: Path, format: str):
    """Initialize a new pyldo project structure.

    Creates the necessary directories and sample schemas in ShEx and/or LinkML format.
    """
    # Create directories
    shapes_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create sample ShEx schema
    if format in ("shex", "both"):
        sample_shex = shapes_dir / "profile.shex"
        if not sample_shex.exists():
            sample_shex.write_text(
                '''# Sample profile shape for Solid Pod profiles
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

<ProfileShape> {
    a [ foaf:Person ] ;
    foaf:name xsd:string ;
    foaf:nick xsd:string ? ;
    foaf:mbox IRI ? ;
    foaf:knows @<ProfileShape> *
}
'''
            )
            click.echo(f"Created sample ShEx schema: {sample_shex}")
        else:
            click.echo(f"Sample ShEx schema already exists: {sample_shex}")

    # Create sample LinkML schema
    if format in ("linkml", "both"):
        sample_linkml = shapes_dir / "profile.yaml"
        if not sample_linkml.exists():
            sample_linkml.write_text(
                '''# Sample profile schema for Solid Pod profiles (LinkML format)
# LinkML is often easier to write than ShEx for many developers

id: https://example.org/solid/profile
name: solid-profile
description: A simple profile schema for Solid Pods

prefixes:
  foaf: http://xmlns.com/foaf/0.1/
  vcard: http://www.w3.org/2006/vcard/ns#

classes:
  Profile:
    description: A person's profile
    class_uri: foaf:Person
    attributes:
      name:
        description: The person's full name
        slot_uri: foaf:name
        range: string
        required: true
      nickname:
        description: The person's nickname
        slot_uri: foaf:nick
        range: string
      email:
        description: Email address
        slot_uri: foaf:mbox
        range: uri
      knows:
        description: People this person knows
        slot_uri: foaf:knows
        range: Profile
        multivalued: true
'''
            )
            click.echo(f"Created sample LinkML schema: {sample_linkml}")
        else:
            click.echo(f"Sample LinkML schema already exists: {sample_linkml}")

    # Create __init__.py in output dir
    init_file = output_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text(
            '"""Generated pyldo types and contexts."""\n'
        )
        click.echo(f"Created {init_file}")

    click.echo()
    click.echo("Project initialized! Next steps:")
    click.echo(f"  1. Edit your schemas in {shapes_dir}/")
    click.echo(f"     - Use .shex files for ShEx format")
    click.echo(f"     - Use .yaml files for LinkML format (often easier!)")
    click.echo(f"  2. Run: pyldo generate {shapes_dir}/* -o {output_dir}/")
    click.echo("  3. Import generated types in your code")


@main.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--to",
    "-t",
    type=click.Choice(["shex"]),
    default="shex",
    help="Output format (currently only linkml-to-shex is supported)",
)
def convert(input_file: Path, to: str):
    """Convert between schema formats.

    Currently supports converting LinkML (.yaml) to ShEx format.

    Example:
        pyldo convert schemas/profile.yaml --to shex
    """
    try:
        from pyldo.converter import linkml_to_shex
    except ImportError as e:
        click.echo(f"Error: Missing dependency - {e}", err=True)
        sys.exit(1)

    suffix = input_file.suffix.lower()
    if suffix not in (".yaml", ".yml"):
        click.echo("Error: Input file must be a LinkML YAML file (.yaml or .yml)", err=True)
        sys.exit(1)

    try:
        yaml_source = input_file.read_text()
        shex_output = linkml_to_shex(yaml_source)
        click.echo(shex_output)
    except Exception as e:
        click.echo(f"Error converting: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("schema_file", type=click.Path(exists=True, path_type=Path))
def validate(schema_file: Path):
    """Validate a ShEx or LinkML schema file.

    Checks if the schema can be parsed without generating any output.
    Supports both .shex and .yaml/.yml files.
    """
    try:
        from pyldo.converter import parse_linkml, parse_shex
    except ImportError as e:
        click.echo(f"Error: Missing dependency - {e}", err=True)
        sys.exit(1)

    try:
        schema_source = schema_file.read_text()
        
        # Detect format
        suffix = schema_file.suffix.lower()
        if suffix in (".yaml", ".yml"):
            schema = parse_linkml(schema_source)
            format_name = "LinkML"
        else:
            schema = parse_shex(schema_source)
            format_name = "ShEx"

        click.echo(f"✓ Valid {format_name} schema: {schema_file}")
        click.echo(f"  Shapes: {len(schema.shapes)}")
        for shape in schema.shapes:
            name = shape.id.rsplit("#", 1)[-1].rsplit("/", 1)[-1]
            click.echo(f"    - {name}")

    except Exception as e:
        click.echo(f"✗ Invalid schema: {schema_file}", err=True)
        click.echo(f"  Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
