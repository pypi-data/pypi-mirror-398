"""
Schema Converter - transforms ShEx and LinkML schemas to Python types and JSON-LD contexts.

This is the Python equivalent of @ldo/schema-converter-shex from the JS LDO package.
It takes a ShEx or LinkML schema and generates:
  1. Python Pydantic models for type-safe data access
  2. JSON-LD context dictionaries for RDF serialization/deserialization

ShEx Example:
    >>> from pyldo.converter import parse_shex, generate_python_types, generate_jsonld_context
    >>> 
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
    >>> python_code = generate_python_types(schema)
    >>> context = generate_jsonld_context(schema)

LinkML Example:
    >>> from pyldo.converter import parse_linkml, generate_python_types
    >>> 
    >>> linkml = '''
    ... prefixes:
    ...   foaf: http://xmlns.com/foaf/0.1/
    ... classes:
    ...   Person:
    ...     attributes:
    ...       name:
    ...         slot_uri: foaf:name
    ...         range: string
    ...       age:
    ...         slot_uri: foaf:age
    ...         range: integer
    ...         required: false
    ... '''
    >>> schema = parse_linkml(linkml)
    >>> python_code = generate_python_types(schema)
"""

from .context_generator import generate_jsonld_context
from .linkml_parser import linkml_to_shex, parse_linkml
from .shapetype_generator import (
    generate_schema_file,
    generate_shapetypes_file,
)
from .shex_parser import ShExSchema, parse_shex
from .type_generator import generate_python_types

__all__ = [
    # ShEx
    "parse_shex",
    "ShExSchema",
    # LinkML
    "parse_linkml",
    "linkml_to_shex",
    # Generators (work with both)
    "generate_python_types",
    "generate_jsonld_context",
    "generate_shapetypes_file",
    "generate_schema_file",
]
