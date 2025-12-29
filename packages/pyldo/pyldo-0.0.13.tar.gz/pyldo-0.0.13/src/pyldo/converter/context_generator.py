"""
JSON-LD Context Generator

Generates JSON-LD context dictionaries from parsed ShEx schemas.
This is equivalent to the context generation in @ldo/schema-converter-shex.

The generated context:
- Maps property names to RDF predicates
- Specifies @type for typed literals
- Specifies @id for IRI-valued properties
- Supports @container for multi-valued properties
"""

from typing import Any, Union

from .shex_parser import (
    Cardinality,
    EachOf,
    NodeConstraint,
    NodeKind,
    OneOf,
    Shape,
    ShapeRef,
    ShExSchema,
    TripleConstraint,
)

# Common RDF type IRI
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"


def generate_jsonld_context(schema: ShExSchema) -> dict[str, Any]:
    """
    Generate a JSON-LD context from a ShEx schema.

    Args:
        schema: Parsed ShEx schema

    Returns:
        JSON-LD context dictionary

    Example:
        >>> schema = parse_shex('''
        ...     PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        ...     <PersonShape> { foaf:name xsd:string }
        ... ''')
        >>> context = generate_jsonld_context(schema)
        >>> print(context)
        {'name': {'@id': 'http://xmlns.com/foaf/0.1/name'}, ...}
    """
    context: dict[str, Any] = {}

    # Add common type mapping
    context["type"] = {"@id": "@type", "@container": "@set"}

    # Process each shape
    for shape in schema.shapes:
        shape_context = _generate_shape_context(shape, schema.prefixes)

        # Add shape-specific context
        shape_name = _get_local_name(shape.id)
        context[shape_name] = {"@id": shape.id, "@context": shape_context}

        # Also add properties at top level for convenience
        for prop_name, prop_def in shape_context.items():
            if prop_name not in context:
                context[prop_name] = prop_def

    return context


def _get_local_name(iri: str) -> str:
    """Extract local name from an IRI."""
    name = iri.rsplit("#", 1)[-1]
    name = name.rsplit("/", 1)[-1]
    return name


def _generate_shape_context(shape: Shape, prefixes: dict[str, str]) -> dict[str, Any]:
    """Generate context entries for a shape's properties."""
    context: dict[str, Any] = {}

    # Always add type mapping
    context["type"] = {"@id": "@type", "@container": "@set"}

    # Extract properties from expression
    properties = _extract_properties(shape.expression)

    for prop in properties:
        prop_name = _get_local_name(prop.predicate)
        prop_context = _generate_property_context(prop)

        if prop_context:
            context[prop_name] = prop_context

    return context


def _extract_properties(
    expression: Union[EachOf, OneOf, TripleConstraint, None],
) -> list[TripleConstraint]:
    """Recursively extract all TripleConstraints from an expression."""
    if expression is None:
        return []

    if isinstance(expression, TripleConstraint):
        return [expression]

    if isinstance(expression, EachOf):
        props = []
        for expr in expression.expressions:
            props.extend(_extract_properties(expr))
        return props

    if isinstance(expression, OneOf):
        props = []
        for expr in expression.expressions:
            props.extend(_extract_properties(expr))
        return props

    return []


def _generate_property_context(prop: TripleConstraint) -> dict[str, Any]:
    """Generate JSON-LD context entry for a property."""
    context: dict[str, Any] = {"@id": prop.predicate}

    # Handle rdf:type specially
    if prop.predicate == RDF_TYPE:
        return {"@id": "@type", "@container": "@set"}

    # Determine @type based on value constraint
    if prop.value_expr:
        if isinstance(prop.value_expr, ShapeRef):
            # Reference to another shape - it's an IRI
            context["@type"] = "@id"

        elif isinstance(prop.value_expr, NodeConstraint):
            nc = prop.value_expr

            # Node kind determines @type
            if nc.node_kind in (NodeKind.IRI, NodeKind.NONLITERAL):
                context["@type"] = "@id"
            elif nc.node_kind == NodeKind.BNODE:
                context["@type"] = "@id"

            # Datatype
            if nc.datatype:
                context["@type"] = nc.datatype

            # Value set with IRIs
            if nc.values:
                # Check if values look like IRIs
                if all(_looks_like_iri(v) for v in nc.values):
                    context["@type"] = "@id"

    # Handle container for multi-valued properties
    if prop.cardinality in (Cardinality.STAR, Cardinality.PLUS):
        context["@container"] = "@set"

    return context


def _looks_like_iri(value: str) -> bool:
    """Check if a value looks like an IRI."""
    return value.startswith("http://") or value.startswith("https://") or ":" in value


def generate_context_file(schema: ShExSchema, variable_name: str = "context") -> str:
    """
    Generate Python source code for a JSON-LD context.

    Args:
        schema: Parsed ShEx schema
        variable_name: Name for the context variable

    Returns:
        Python source code as a string
    """
    import json

    context = generate_jsonld_context(schema)

    lines = [
        '"""',
        "Generated JSON-LD context from ShEx schema.",
        "",
        "This file was auto-generated by pyldo. Do not edit manually.",
        '"""',
        "",
        "from typing import Any",
        "",
        f"{variable_name}: dict[str, Any] = " + json.dumps(context, indent=4),
    ]

    return "\n".join(lines)
