"""
ShEx Schema Parser

Parses ShEx (Shape Expressions) schemas into an intermediate representation
that can be used for generating Python types and JSON-LD contexts.

This module provides a clean Pythonic representation of ShEx schemas,
abstracting away the complexity of the underlying ShEx format.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union


class NodeKind(Enum):
    """Possible node kinds in RDF."""

    IRI = "iri"
    BNODE = "bnode"
    LITERAL = "literal"
    NONLITERAL = "nonliteral"


class Cardinality(Enum):
    """Cardinality constraints for properties."""

    ONE = "one"  # exactly 1 (default)
    OPTIONAL = "optional"  # 0 or 1 (?)
    PLUS = "plus"  # 1 or more (+)
    STAR = "star"  # 0 or more (*)


@dataclass
class NodeConstraint:
    """
    Constraints on RDF nodes.

    Equivalent to ShEx's NodeConstraint:
    - datatype: XSD datatype IRI (e.g., xsd:string, xsd:integer)
    - node_kind: iri, bnode, literal, nonliteral
    - values: allowed values (value set)
    - pattern: regex pattern for strings
    """

    datatype: Optional[str] = None
    node_kind: Optional[NodeKind] = None
    values: Optional[list[str]] = None
    pattern: Optional[str] = None
    flags: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_inclusive: Optional[float] = None
    max_inclusive: Optional[float] = None
    min_exclusive: Optional[float] = None
    max_exclusive: Optional[float] = None


@dataclass
class ShapeRef:
    """Reference to another shape by IRI."""

    shape_iri: str


@dataclass
class TripleConstraint:
    """
    Constraint on a single predicate-object pair.

    Equivalent to ShEx's TripleConstraint:
    - predicate: the RDF predicate IRI
    - value_expr: constraint on the object (NodeConstraint or shape reference)
    - cardinality: how many times this triple can appear
    - inverse: if True, this is an inverse triple constraint
    """

    predicate: str
    value_expr: Optional[Union["NodeConstraint", "ShapeRef"]] = None
    cardinality: Cardinality = Cardinality.ONE
    inverse: bool = False
    min_count: int = 1
    max_count: int = 1  # -1 means unbounded
    annotations: dict[str, str] = field(default_factory=dict)


@dataclass
class EachOf:
    """All constraints must be satisfied (AND)."""

    expressions: list[Union["TripleConstraint", "EachOf", "OneOf"]] = field(
        default_factory=list
    )


@dataclass
class OneOf:
    """At least one constraint must be satisfied (OR)."""

    expressions: list[Union["TripleConstraint", "EachOf", "OneOf"]] = field(
        default_factory=list
    )


@dataclass
class Shape:
    """
    A shape definition describing the expected structure of an RDF node.

    Equivalent to ShEx's Shape:
    - id: IRI identifying this shape
    - expression: the triple expression (constraints on outgoing triples)
    - closed: if True, no extra triples allowed
    - extra: predicates allowed beyond the expression
    - extends: shapes this shape extends (inheritance)
    """

    id: str
    expression: Optional[Union[EachOf, OneOf, TripleConstraint]] = None
    closed: bool = False
    extra: list[str] = field(default_factory=list)
    extends: list[str] = field(default_factory=list)
    annotations: dict[str, str] = field(default_factory=dict)


@dataclass
class ShExSchema:
    """
    Complete ShEx schema containing shape definitions.

    Equivalent to ShEx's Schema:
    - shapes: list of shape definitions
    - prefixes: prefix -> IRI mappings
    - base: base IRI for relative IRIs
    - start: default starting shape
    """

    shapes: list[Shape] = field(default_factory=list)
    prefixes: dict[str, str] = field(default_factory=dict)
    base: Optional[str] = None
    start: Optional[str] = None


# XSD datatype to Python type mapping
XSD_TYPE_MAP: dict[str, str] = {
    "http://www.w3.org/2001/XMLSchema#string": "str",
    "http://www.w3.org/2001/XMLSchema#normalizedString": "str",
    "http://www.w3.org/2001/XMLSchema#token": "str",
    "http://www.w3.org/2001/XMLSchema#language": "str",
    "http://www.w3.org/2001/XMLSchema#Name": "str",
    "http://www.w3.org/2001/XMLSchema#NCName": "str",
    "http://www.w3.org/2001/XMLSchema#ID": "str",
    "http://www.w3.org/2001/XMLSchema#IDREF": "str",
    "http://www.w3.org/2001/XMLSchema#IDREFS": "str",
    "http://www.w3.org/2001/XMLSchema#NMTOKEN": "str",
    "http://www.w3.org/2001/XMLSchema#NMTOKENS": "str",
    "http://www.w3.org/2001/XMLSchema#QName": "str",
    "http://www.w3.org/2001/XMLSchema#anyURI": "str",
    "http://www.w3.org/2001/XMLSchema#base64Binary": "bytes",
    "http://www.w3.org/2001/XMLSchema#hexBinary": "bytes",
    "http://www.w3.org/2001/XMLSchema#integer": "int",
    "http://www.w3.org/2001/XMLSchema#int": "int",
    "http://www.w3.org/2001/XMLSchema#long": "int",
    "http://www.w3.org/2001/XMLSchema#short": "int",
    "http://www.w3.org/2001/XMLSchema#byte": "int",
    "http://www.w3.org/2001/XMLSchema#nonNegativeInteger": "int",
    "http://www.w3.org/2001/XMLSchema#positiveInteger": "int",
    "http://www.w3.org/2001/XMLSchema#nonPositiveInteger": "int",
    "http://www.w3.org/2001/XMLSchema#negativeInteger": "int",
    "http://www.w3.org/2001/XMLSchema#unsignedInt": "int",
    "http://www.w3.org/2001/XMLSchema#unsignedLong": "int",
    "http://www.w3.org/2001/XMLSchema#unsignedShort": "int",
    "http://www.w3.org/2001/XMLSchema#unsignedByte": "int",
    "http://www.w3.org/2001/XMLSchema#decimal": "float",
    "http://www.w3.org/2001/XMLSchema#float": "float",
    "http://www.w3.org/2001/XMLSchema#double": "float",
    "http://www.w3.org/2001/XMLSchema#boolean": "bool",
    "http://www.w3.org/2001/XMLSchema#date": "str",  # Could use datetime.date
    "http://www.w3.org/2001/XMLSchema#dateTime": "str",  # Could use datetime.datetime
    "http://www.w3.org/2001/XMLSchema#time": "str",  # Could use datetime.time
    "http://www.w3.org/2001/XMLSchema#duration": "str",
    "http://www.w3.org/2001/XMLSchema#gDay": "str",
    "http://www.w3.org/2001/XMLSchema#gMonth": "str",
    "http://www.w3.org/2001/XMLSchema#gMonthDay": "str",
    "http://www.w3.org/2001/XMLSchema#gYear": "str",
    "http://www.w3.org/2001/XMLSchema#gYearMonth": "str",
}


def parse_shex(shex_source: str, base_iri: str = "http://example.org/") -> ShExSchema:
    """
    Parse a ShEx schema from source text.

    Args:
        shex_source: ShEx schema as a string (ShExC format)
        base_iri: Base IRI for resolving relative IRIs

    Returns:
        Parsed ShExSchema object

    Example:
        >>> shex = '''
        ... PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        ... PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        ...
        ... <PersonShape> {
        ...     foaf:name xsd:string ;
        ...     foaf:age xsd:integer ?
        ... }
        ... '''
        >>> schema = parse_shex(shex)
        >>> print(schema.shapes[0].id)
        http://example.org/PersonShape
    """
    try:
        from pyshexc.parser_impl import generate_shexj
    except ImportError as e:
        raise ImportError(
            "PyShExC is required for parsing ShEx. "
            "Install it with: pip install pyshexc"
        ) from e

    # Use pyshexc to parse ShExC to ShExJ
    try:
        schema_obj = generate_shexj.parse(shex_source)
    except Exception as e:
        raise ValueError(f"Failed to parse ShEx schema: {e}") from e

    # Convert ShExJ to our internal representation
    return _convert_shexj_schema(schema_obj, base_iri)


def _convert_shexj_schema(shexj_schema, base_iri: str) -> ShExSchema:
    """Convert a ShExJ Schema object to our ShExSchema."""
    schema = ShExSchema(base=base_iri)

    # Convert shapes
    if hasattr(shexj_schema, "shapes") and shexj_schema.shapes:
        for shape_decl in shexj_schema.shapes:
            converted = _convert_shape(shape_decl, schema.prefixes)
            if converted:
                schema.shapes.append(converted)

    # Set start shape if defined
    if hasattr(shexj_schema, "start") and shexj_schema.start:
        schema.start = str(shexj_schema.start)

    return schema


def _convert_shape(shape_decl, prefixes: dict[str, str]) -> Optional[Shape]:
    """Convert a ShExJ ShapeDecl or Shape to our Shape."""
    # Get the shape ID
    shape_id = str(shape_decl.id) if hasattr(shape_decl, "id") and shape_decl.id else None

    if not shape_id:
        return None

    shape = Shape(id=shape_id)

    # pyshexc returns Shape objects where the expression is directly on the object
    # The `expression` attribute contains the triple constraints (EachOf, OneOf, TripleConstraint)
    if hasattr(shape_decl, "expression") and shape_decl.expression:
        shape.expression = _convert_triple_expr(shape_decl.expression, prefixes)

    if hasattr(shape_decl, "closed") and shape_decl.closed:
        shape.closed = True
    if hasattr(shape_decl, "extra") and shape_decl.extra:
        shape.extra = [str(e) for e in shape_decl.extra]
    if hasattr(shape_decl, "extends") and shape_decl.extends:
        shape.extends = [str(e) for e in shape_decl.extends]

    return shape


def _convert_triple_expr(
    expr, prefixes: dict[str, str]
) -> Optional[Union[EachOf, OneOf, TripleConstraint]]:
    """Convert a ShExJ triple expression to our representation."""
    if not hasattr(expr, "type"):
        return None

    if expr.type == "EachOf":
        expressions = []
        if hasattr(expr, "expressions"):
            for sub_expr in expr.expressions:
                converted = _convert_triple_expr(sub_expr, prefixes)
                if converted:
                    expressions.append(converted)
        return EachOf(expressions=expressions)

    elif expr.type == "OneOf":
        expressions = []
        if hasattr(expr, "expressions"):
            for sub_expr in expr.expressions:
                converted = _convert_triple_expr(sub_expr, prefixes)
                if converted:
                    expressions.append(converted)
        return OneOf(expressions=expressions)

    elif expr.type == "TripleConstraint":
        predicate = str(expr.predicate) if hasattr(expr, "predicate") else ""

        # Determine cardinality from min/max
        # None means default (1), -1 means unbounded
        min_count = getattr(expr, "min", None)
        max_count = getattr(expr, "max", None)

        # Handle None values (defaults)
        if min_count is None:
            min_count = 1
        if max_count is None:
            max_count = 1

        # Determine cardinality enum
        if min_count == 0 and max_count == 1:
            cardinality = Cardinality.OPTIONAL  # ?
        elif min_count == 0 and max_count == -1:
            cardinality = Cardinality.STAR  # *
        elif min_count >= 1 and max_count == -1:
            cardinality = Cardinality.PLUS  # +
        else:
            cardinality = Cardinality.ONE  # exactly 1

        # Convert value expression
        value_expr = None
        if hasattr(expr, "valueExpr") and expr.valueExpr:
            value_expr = _convert_value_expr(expr.valueExpr, prefixes)

        # Check for inverse
        inverse = getattr(expr, "inverse", False) or False

        # Extract annotations
        annotations = {}
        if hasattr(expr, "annotations") and expr.annotations:
            for ann in expr.annotations:
                if hasattr(ann, "predicate") and hasattr(ann, "object"):
                    pred = str(ann.predicate)
                    obj = (
                        str(ann.object.value)
                        if hasattr(ann.object, "value")
                        else str(ann.object)
                    )
                    annotations[pred] = obj

        return TripleConstraint(
            predicate=predicate,
            value_expr=value_expr,
            cardinality=cardinality,
            inverse=inverse,
            min_count=min_count,
            max_count=max_count,
            annotations=annotations,
        )

    return None


def _convert_value_expr(
    value_expr, prefixes: dict[str, str]
) -> Optional[Union[NodeConstraint, ShapeRef]]:
    """Convert a ShExJ value expression to our representation."""
    # String reference to another shape
    if isinstance(value_expr, str):
        return ShapeRef(shape_iri=value_expr)

    if not hasattr(value_expr, "type"):
        return None

    if value_expr.type == "NodeConstraint":
        constraint = NodeConstraint()

        if hasattr(value_expr, "datatype") and value_expr.datatype:
            constraint.datatype = str(value_expr.datatype)

        if hasattr(value_expr, "nodeKind") and value_expr.nodeKind:
            kind_map = {
                "iri": NodeKind.IRI,
                "bnode": NodeKind.BNODE,
                "literal": NodeKind.LITERAL,
                "nonliteral": NodeKind.NONLITERAL,
            }
            constraint.node_kind = kind_map.get(value_expr.nodeKind)

        if hasattr(value_expr, "values") and value_expr.values:
            constraint.values = [
                str(v) if isinstance(v, str) else str(getattr(v, "value", v))
                for v in value_expr.values
            ]

        if hasattr(value_expr, "pattern") and value_expr.pattern:
            constraint.pattern = str(value_expr.pattern)

        if hasattr(value_expr, "flags") and value_expr.flags:
            constraint.flags = str(value_expr.flags)

        if hasattr(value_expr, "minlength"):
            constraint.min_length = value_expr.minlength
        if hasattr(value_expr, "maxlength"):
            constraint.max_length = value_expr.maxlength
        if hasattr(value_expr, "mininclusive"):
            constraint.min_inclusive = value_expr.mininclusive
        if hasattr(value_expr, "maxinclusive"):
            constraint.max_inclusive = value_expr.maxinclusive
        if hasattr(value_expr, "minexclusive"):
            constraint.min_exclusive = value_expr.minexclusive
        if hasattr(value_expr, "maxexclusive"):
            constraint.max_exclusive = value_expr.maxexclusive

        return constraint

    # Shape reference by type
    if value_expr.type in ("Shape", "ShapeDecl", "ShapeRef"):
        if hasattr(value_expr, "id"):
            return ShapeRef(shape_iri=str(value_expr.id))

    return None


def get_python_type(constraint: Optional[Union[NodeConstraint, ShapeRef]]) -> str:
    """
    Get the Python type annotation for a constraint.

    Args:
        constraint: Node constraint or shape reference

    Returns:
        Python type as a string (e.g., "str", "int", "PersonShape")
    """
    if constraint is None:
        return "str"  # Default to string

    if isinstance(constraint, ShapeRef):
        # Extract shape name from IRI
        shape_name = constraint.shape_iri.rsplit("#", 1)[-1]
        shape_name = shape_name.rsplit("/", 1)[-1]
        return shape_name

    if isinstance(constraint, NodeConstraint):
        if constraint.datatype:
            return XSD_TYPE_MAP.get(constraint.datatype, "str")
        if constraint.node_kind == NodeKind.IRI:
            return "str"  # IRI as string
        if constraint.node_kind == NodeKind.LITERAL:
            return "str"
        if constraint.values:
            # Value set - could generate Literal type
            return "str"
        return "str"

    return "str"
