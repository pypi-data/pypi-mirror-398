"""
Test demonstrating the pyldo data flow at each stage.

Run with: python tests/test_dataflow.py
"""

import json
import sys
from pathlib import Path

# Add src to path for local testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pyldo.converter import generate_jsonld_context, generate_python_types, parse_shex


def main():
    # ═══════════════════════════════════════════════════════════════════════
    # STAGE 0: Input - Raw ShEx Schema Text
    # ═══════════════════════════════════════════════════════════════════════
    shex_source = """
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

<PersonShape> {
    foaf:name xsd:string ;
    foaf:age xsd:integer ? ;
    foaf:knows @<PersonShape> *
}
"""

    print("=" * 70)
    print("STAGE 0: INPUT - Raw ShEx Schema Text")
    print("=" * 70)
    print(shex_source)

    # ═══════════════════════════════════════════════════════════════════════
    # STAGE 1: parse_shex() → ShExSchema dataclass
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("STAGE 1: parse_shex() → ShExSchema Object")
    print("=" * 70)

    schema = parse_shex(shex_source)

    print(f"\nShExSchema:")
    print(f"  base: {schema.base}")
    print(f"  start: {schema.start}")
    print(f"  prefixes: {schema.prefixes}")
    print(f"  shapes: {len(schema.shapes)} shape(s)")

    for shape in schema.shapes:
        print(f"\n  Shape:")
        print(f"    id: {shape.id}")
        print(f"    closed: {shape.closed}")
        print(f"    extra: {shape.extra}")
        print(f"    expression type: {type(shape.expression).__name__}")

        if shape.expression:
            print(f"    expression.expressions: {len(shape.expression.expressions)} constraint(s)")

            for i, tc in enumerate(shape.expression.expressions):
                print(f"\n    TripleConstraint #{i+1}:")
                print(f"      predicate: {tc.predicate}")
                print(f"      cardinality: {tc.cardinality}")
                print(f"      min_count: {tc.min_count}, max_count: {tc.max_count}")
                print(f"      value_expr type: {type(tc.value_expr).__name__ if tc.value_expr else None}")
                if tc.value_expr:
                    if hasattr(tc.value_expr, "datatype"):
                        print(f"      value_expr.datatype: {tc.value_expr.datatype}")
                    if hasattr(tc.value_expr, "shape_iri"):
                        print(f"      value_expr.shape_iri: {tc.value_expr.shape_iri}")

    # ═══════════════════════════════════════════════════════════════════════
    # STAGE 2: generate_python_types() → Python Source Code
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("STAGE 2: generate_python_types() → Python Source Code")
    print("=" * 70)

    python_code = generate_python_types(schema)
    print(python_code)

    # ═══════════════════════════════════════════════════════════════════════
    # STAGE 3: generate_jsonld_context() → JSON-LD Context Dict
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("STAGE 3: generate_jsonld_context() → JSON-LD Context")
    print("=" * 70)

    context = generate_jsonld_context(schema)
    print(json.dumps(context, indent=2))

    # ═══════════════════════════════════════════════════════════════════════
    # STAGE 4: Using the Generated Code
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("STAGE 4: Using the Generated Pydantic Model")
    print("=" * 70)

    # Execute the generated code to create the model class
    # We need to provide the imports that the generated code expects
    from typing import Optional

    from pydantic import BaseModel, Field

    exec_globals = {
        "Optional": Optional,
        "BaseModel": BaseModel,
        "Field": Field,
        "__annotations__": {},  # For forward references
    }
    exec(python_code, exec_globals)
    PersonShape = exec_globals["PersonShape"]
    PersonShape.model_rebuild()  # Rebuild for forward references

    # Create an instance
    person = PersonShape(
        **{"@id": "https://example.org/alice"},
        name="Alice",
        age=30,
        knows=[],
    )

    print(f"\nCreated PersonShape instance:")
    print(f"  id: {person.id}")
    print(f"  name: {person.name}")
    print(f"  age: {person.age}")
    print(f"  knows: {person.knows}")

    print(f"\nJSON output (by_alias=True for RDF predicates):")
    print(person.model_dump_json(indent=2, by_alias=True))

    # ═══════════════════════════════════════════════════════════════════════
    # Summary diagram
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("DATA FLOW SUMMARY")
    print("=" * 70)
    print("""
    ┌─────────────────────────────────────┐
    │  STAGE 0: ShEx Text (input)         │
    │  PREFIX foaf: <...>                 │
    │  <PersonShape> { foaf:name ... }    │
    └─────────────────┬───────────────────┘
                      │
                      ▼ parse_shex()
    ┌─────────────────────────────────────┐
    │  STAGE 1: ShExSchema (dataclass)    │
    │  - shapes: [Shape(...)]             │
    │  - Shape.expression: EachOf(...)    │
    │  - TripleConstraint(predicate=...)  │
    └─────────────────┬───────────────────┘
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
    generate_python_types()  generate_jsonld_context()
          │                       │
          ▼                       ▼
    ┌─────────────────┐   ┌─────────────────┐
    │ STAGE 2: Python │   │ STAGE 3: JSON-LD│
    │ class Person-   │   │ {"name": {      │
    │   Shape(Base-   │   │   "@id": "..."  │
    │   Model): ...   │   │ }}              │
    └────────┬────────┘   └─────────────────┘
             │
             ▼ exec() / import
    ┌─────────────────────────────────────┐
    │  STAGE 4: Pydantic Model Instance   │
    │  person = PersonShape(name="Alice") │
    │  person.model_dump_json()           │
    └─────────────────────────────────────┘
    """)


if __name__ == "__main__":
    main()
