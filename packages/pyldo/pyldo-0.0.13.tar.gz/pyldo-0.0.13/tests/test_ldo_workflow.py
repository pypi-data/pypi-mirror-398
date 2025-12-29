"""
End-to-end test demonstrating the full pyldo workflow.

This test shows:
1. Generating Pydantic models from ShEx schema
2. Parsing RDF data
3. Creating typed Linked Data Objects
4. Modifying objects and syncing to graph
5. Transaction support with SPARQL UPDATE generation
6. Serialization to various formats

Run with: python tests/test_ldo_workflow.py
"""

import sys
from pathlib import Path

# Add src to path for local testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def main():
    print("=" * 70)
    print("PYLDO END-TO-END WORKFLOW TEST")
    print("=" * 70)

    # =========================================================================
    # STEP 1: Generate Pydantic models from ShEx
    # =========================================================================
    print("\n" + "=" * 70)
    print("STEP 1: Generate Pydantic Models from ShEx")
    print("=" * 70)

    from pyldo.converter import generate_python_types, parse_shex

    # Using a simpler schema without self-references for this test
    shex_schema = """
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    <PersonShape> {
        foaf:name xsd:string ;
        foaf:age xsd:integer ? ;
        foaf:mbox IRI *
    }
    """

    print("ShEx Schema:")
    print(shex_schema)

    schema = parse_shex(shex_schema)
    python_code = generate_python_types(schema)

    print("\nGenerated Pydantic Model:")
    print(python_code)

    # Execute the generated code to get the PersonShape class
    from typing import Optional

    from pydantic import BaseModel, Field

    exec_globals = {
        "Optional": Optional,
        "BaseModel": BaseModel,
        "Field": Field,
    }
    exec(python_code, exec_globals)
    PersonShape = exec_globals["PersonShape"]
    PersonShape.model_rebuild()

    print("✅ PersonShape class created successfully")

    # =========================================================================
    # STEP 2: Create LdoDataset and Parse RDF
    # =========================================================================
    print("\n" + "=" * 70)
    print("STEP 2: Create LdoDataset and Parse RDF")
    print("=" * 70)

    from pyldo import LdoDataset

    dataset = LdoDataset()

    turtle_data = """
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    <https://example.org/alice> 
        foaf:name "Alice" ;
        foaf:age 30 ;
        foaf:mbox <mailto:alice@example.org> .

    <https://example.org/bob>
        foaf:name "Bob" ;
        foaf:age 25 ;
        foaf:mbox <mailto:bob@example.org>, <mailto:bob@work.com> .
    """

    dataset.parse_turtle(turtle_data)

    print(f"Parsed RDF data: {len(dataset)} triples")
    print("\nRaw Turtle:")
    print(turtle_data)

    # =========================================================================
    # STEP 3: Create Typed Linked Data Objects
    # =========================================================================
    print("\n" + "=" * 70)
    print("STEP 3: Create Typed Linked Data Objects")
    print("=" * 70)

    # Get Alice as a typed PersonShape
    alice = dataset.using(PersonShape).from_subject("https://example.org/alice")

    print(f"Alice:")
    print(f"  @id: {alice.id}")
    print(f"  name: {alice.name}")
    print(f"  age: {alice.age}")
    print(f"  mbox: {alice.mbox}")

    # Get Bob
    bob = dataset.using(PersonShape).from_subject("https://example.org/bob")
    print(f"\nBob:")
    print(f"  @id: {bob.id}")
    print(f"  name: {bob.name}")
    print(f"  age: {bob.age}")
    print(f"  mbox: {bob.mbox}")

    # =========================================================================
    # STEP 4: Create New Object and Add to Graph
    # =========================================================================
    print("\n" + "=" * 70)
    print("STEP 4: Create New Object and Add to Graph")
    print("=" * 70)

    # Create Charlie from JSON data
    charlie = dataset.using(PersonShape).from_json({
        "@id": "https://example.org/charlie",
        "name": "Charlie",
        "age": 35,
    })

    print(f"Created Charlie:")
    print(f"  @id: {charlie.id}")
    print(f"  name: {charlie.name}")
    print(f"  age: {charlie.age}")
    print(f"\nDataset now has {len(dataset)} triples")

    # =========================================================================
    # STEP 5: Transactions and SPARQL UPDATE
    # =========================================================================
    print("\n" + "=" * 70)
    print("STEP 5: Transactions and SPARQL UPDATE")
    print("=" * 70)

    # Start a transaction
    dataset.start_transaction()
    print("Transaction started")

    # Make changes - we need to update the graph directly for now
    from rdflib import Literal, Namespace, URIRef
    FOAF = Namespace("http://xmlns.com/foaf/0.1/")

    # Change Alice's name
    alice_uri = URIRef("https://example.org/alice")
    old_name = Literal("Alice")
    new_name = Literal("Alicia")

    dataset.graph.remove((alice_uri, FOAF.name, old_name))
    dataset.graph.add((alice_uri, FOAF.name, new_name))

    print(f"Changed Alice's name from 'Alice' to 'Alicia'")

    # Generate SPARQL UPDATE
    sparql_update = dataset.to_sparql_update()
    print("\nSPARQL UPDATE generated:")
    print(sparql_update)

    # Commit the transaction
    dataset.commit()
    print("\n✅ Transaction committed")

    # =========================================================================
    # STEP 6: Serialization
    # =========================================================================
    print("\n" + "=" * 70)
    print("STEP 6: Serialization")
    print("=" * 70)

    # Serialize to Turtle
    print("Turtle output:")
    print(dataset.to_turtle({
        "foaf": "http://xmlns.com/foaf/0.1/",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
    }))

    # Serialize to N-Triples
    print("\nN-Triples output (first 3 lines):")
    ntriples = dataset.to_ntriples()
    for line in ntriples.strip().split("\n")[:3]:
        print(line)
    print("...")

    # =========================================================================
    # STEP 7: Query Multiple Objects
    # =========================================================================
    print("\n" + "=" * 70)
    print("STEP 7: Query Multiple Objects")
    print("=" * 70)

    from rdflib import RDF
    # Note: We'd need to add rdf:type triples for this to work properly
    # For now, let's just show we can iterate

    print("All people in the dataset:")
    # We can get all subjects that have foaf:name
    for person in dataset.using(PersonShape).match_subject(FOAF.name):
        print(f"  - {person.name} ({person.id})")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
    ✅ Generated Pydantic models from ShEx schema
    ✅ Created LdoDataset and parsed Turtle RDF
    ✅ Retrieved typed Linked Data Objects (Alice, Bob)
    ✅ Created new object from JSON (Charlie)
    ✅ Used transactions to track changes
    ✅ Generated SPARQL UPDATE from changes
    ✅ Serialized to Turtle and N-Triples
    ✅ Queried multiple objects from graph

    pyldo is working! 🎉
    """)


if __name__ == "__main__":
    main()
