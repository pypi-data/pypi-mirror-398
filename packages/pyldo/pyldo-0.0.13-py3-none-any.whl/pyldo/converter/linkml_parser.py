"""
LinkML Parser - transforms LinkML YAML schemas to internal representation.

LinkML (Linked Data Modeling Language) is a YAML-based schema language that's
often easier to write than ShEx. This module parses LinkML schemas and converts
them to the same internal representation used by the ShEx parser.

Example LinkML schema:
    ```yaml
    id: https://example.org/person
    name: person-schema
    prefixes:
      foaf: http://xmlns.com/foaf/0.1/
      schema: http://schema.org/
    
    classes:
      Person:
        class_uri: foaf:Person
        attributes:
          name:
            slot_uri: foaf:name
            range: string
            required: true
          age:
            slot_uri: foaf:age
            range: integer
          knows:
            slot_uri: foaf:knows
            range: Person
            multivalued: true
    ```

Usage:
    >>> from pyldo.converter.linkml_parser import parse_linkml
    >>> 
    >>> schema = parse_linkml(yaml_content)
    >>> # schema is compatible with generate_python_types(), generate_jsonld_context(), etc.
"""

from typing import Optional, Union

import yaml

from .shex_parser import (
    Cardinality,
    EachOf,
    NodeConstraint,
    Shape,
    ShapeRef,
    ShExSchema,
    TripleConstraint,
)


# XSD type mappings
LINKML_TO_XSD = {
    "string": "http://www.w3.org/2001/XMLSchema#string",
    "integer": "http://www.w3.org/2001/XMLSchema#integer",
    "int": "http://www.w3.org/2001/XMLSchema#integer",
    "float": "http://www.w3.org/2001/XMLSchema#float",
    "double": "http://www.w3.org/2001/XMLSchema#double",
    "decimal": "http://www.w3.org/2001/XMLSchema#decimal",
    "boolean": "http://www.w3.org/2001/XMLSchema#boolean",
    "bool": "http://www.w3.org/2001/XMLSchema#boolean",
    "date": "http://www.w3.org/2001/XMLSchema#date",
    "datetime": "http://www.w3.org/2001/XMLSchema#dateTime",
    "time": "http://www.w3.org/2001/XMLSchema#time",
    "uri": "http://www.w3.org/2001/XMLSchema#anyURI",
    "uriorcurie": "http://www.w3.org/2001/XMLSchema#anyURI",
    "ncname": "http://www.w3.org/2001/XMLSchema#NCName",
}


def expand_prefix(value: str, prefixes: dict[str, str]) -> str:
    """Expand a prefixed IRI like 'foaf:name' to full IRI."""
    if not value or "://" in value:
        return value
    
    if ":" in value:
        prefix, local = value.split(":", 1)
        if prefix in prefixes:
            return prefixes[prefix] + local
    
    return value


def parse_linkml(yaml_source: str, base_iri: str = "http://example.org/") -> ShExSchema:
    """
    Parse a LinkML YAML schema and return a ShExSchema representation.
    
    Args:
        yaml_source: The LinkML schema as a YAML string
        base_iri: Base IRI for resolving relative IRIs
    
    Returns:
        ShExSchema that can be used with generate_python_types(), etc.
    
    Example:
        >>> schema = parse_linkml('''
        ... prefixes:
        ...   foaf: http://xmlns.com/foaf/0.1/
        ... classes:
        ...   Person:
        ...     attributes:
        ...       name:
        ...         slot_uri: foaf:name
        ...         range: string
        ... ''')
    """
    data = yaml.safe_load(yaml_source)
    
    if not data:
        return ShExSchema(shapes=[], prefixes={})
    
    # Extract prefixes
    prefixes = data.get("prefixes", {})
    if isinstance(prefixes, dict):
        # Ensure all values are strings
        prefixes = {k: str(v) for k, v in prefixes.items()}
    else:
        prefixes = {}
    
    # Add common prefixes if not present
    default_prefixes = {
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    }
    for k, v in default_prefixes.items():
        if k not in prefixes:
            prefixes[k] = v
    
    # Get schema base IRI
    schema_id = data.get("id", base_iri)
    
    # Parse classes into shapes
    shapes = []
    classes = data.get("classes", {})
    
    # Build a map of class names for reference resolution
    class_names = set(classes.keys())
    
    for class_name, class_def in classes.items():
        if class_def is None:
            class_def = {}
        
        # Build shape ID
        shape_id = f"{schema_id}#{class_name}Shape" if "#" not in schema_id else f"{schema_id.split('#')[0]}#{class_name}Shape"
        
        # Parse attributes into triple constraints
        constraints = []
        attributes = class_def.get("attributes", {})
        
        for attr_name, attr_def in attributes.items():
            if attr_def is None:
                attr_def = {}
            
            # Get the slot URI (predicate)
            slot_uri = attr_def.get("slot_uri")
            if slot_uri:
                predicate = expand_prefix(slot_uri, prefixes)
            else:
                # Default to schema base + attribute name
                predicate = f"{schema_id}/{attr_name}"
            
            # Determine the value type
            range_type = attr_def.get("range", "string")
            
            # Check if it references another class
            if range_type in class_names:
                # Reference to another shape
                ref_shape_id = f"{schema_id}#{range_type}Shape" if "#" not in schema_id else f"{schema_id.split('#')[0]}#{range_type}Shape"
                value_expr: Optional[Union[NodeConstraint, ShapeRef]] = ShapeRef(shape_iri=ref_shape_id)
            elif range_type.lower() in LINKML_TO_XSD:
                # XSD datatype
                value_expr = NodeConstraint(datatype=LINKML_TO_XSD[range_type.lower()])
            else:
                # Try to expand as a prefixed IRI
                expanded = expand_prefix(range_type, prefixes)
                if expanded != range_type:
                    value_expr = NodeConstraint(datatype=expanded)
                else:
                    # Default to string
                    value_expr = NodeConstraint(datatype=LINKML_TO_XSD["string"])
            
            # Determine cardinality
            required = attr_def.get("required", False)
            multivalued = attr_def.get("multivalued", False)
            
            if multivalued:
                min_count = 1 if required else 0
                max_count = -1  # unlimited
                cardinality = Cardinality.PLUS if required else Cardinality.STAR
            else:
                min_count = 1 if required else 0
                max_count = 1
                cardinality = Cardinality.ONE if required else Cardinality.OPTIONAL
            
            constraint = TripleConstraint(
                predicate=predicate,
                value_expr=value_expr,
                cardinality=cardinality,
                min_count=min_count,
                max_count=max_count,
            )
            constraints.append(constraint)
        
        # Build the shape with EachOf expression containing all constraints
        expression = EachOf(expressions=constraints) if len(constraints) > 1 else (constraints[0] if constraints else None)
        
        shape = Shape(
            id=shape_id,
            expression=expression,
        )
        shapes.append(shape)
    
    return ShExSchema(shapes=shapes, prefixes=prefixes, base=schema_id)


def linkml_to_shex(yaml_source: str) -> str:
    """
    Convert a LinkML schema to ShEx syntax.
    
    This is useful for users who want to see the equivalent ShEx
    or for debugging purposes.
    
    Args:
        yaml_source: The LinkML schema as a YAML string
    
    Returns:
        Equivalent ShEx schema as a string
    """
    schema = parse_linkml(yaml_source)
    
    lines = []
    
    # Add prefix declarations
    for prefix, iri in schema.prefixes.items():
        lines.append(f"PREFIX {prefix}: <{iri}>")
    
    lines.append("")
    
    # Add shape definitions
    for shape in schema.shapes:
        shape_name = shape.id.split("#")[-1] if "#" in shape.id else shape.id.split("/")[-1]
        lines.append(f"<{shape_name}> {{")
        
        # Get constraints from expression
        constraints = []
        if isinstance(shape.expression, EachOf):
            constraints = shape.expression.expressions
        elif isinstance(shape.expression, TripleConstraint):
            constraints = [shape.expression]
        
        for i, constraint in enumerate(constraints):
            if not isinstance(constraint, TripleConstraint):
                continue
                
            # Format the predicate
            predicate = constraint.predicate
            for prefix, iri in schema.prefixes.items():
                if predicate.startswith(iri):
                    predicate = f"{prefix}:{predicate[len(iri):]}"
                    break
            else:
                predicate = f"<{predicate}>"
            
            # Format the value type
            if isinstance(constraint.value_expr, ShapeRef):
                value_name = constraint.value_expr.shape_iri.split("#")[-1] if "#" in constraint.value_expr.shape_iri else constraint.value_expr.shape_iri.split("/")[-1]
                value = f"@<{value_name}>"
            elif isinstance(constraint.value_expr, NodeConstraint) and constraint.value_expr.datatype:
                value = constraint.value_expr.datatype
                for prefix, iri in schema.prefixes.items():
                    if value.startswith(iri):
                        value = f"{prefix}:{value[len(iri):]}"
                        break
                else:
                    value = f"<{value}>"
            else:
                value = "xsd:string"
            
            # Format cardinality
            if constraint.cardinality == Cardinality.OPTIONAL:
                cardinality = " ?"
            elif constraint.cardinality == Cardinality.STAR:
                cardinality = " *"
            elif constraint.cardinality == Cardinality.PLUS:
                cardinality = " +"
            else:
                cardinality = ""
            
            # Add semicolon except for last constraint
            separator = " ;" if i < len(constraints) - 1 else ""
            
            lines.append(f"    {predicate} {value}{cardinality}{separator}")
        
        lines.append("}")
        lines.append("")
    
    return "\n".join(lines)
