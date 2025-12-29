# PyLDO - Linked Data Objects for Python

[![PyPI version](https://badge.fury.io/py/pyldo.svg)](https://badge.fury.io/py/pyldo)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

PyLDO makes working with RDF data as easy as working with plain Python objects. It's the Python equivalent of the [JavaScript LDO library](https://ldo.js.org/) and designed for building [Solid](https://solidproject.org/) applications.

## Features

- **Seamless RDF to Python object mapping** - Work with RDF as Pydantic models
- **ShEx schema support** - Generate typed Python classes from ShEx shapes
- **Solid integration** - Full support for Solid Pods with DPoP authentication
- **Link traversal** - Automatically fetch linked resources across documents
- **Reactive updates** - Subscribe to data changes with SubscribableDataset
- **Type safe** - Full type hints and Pydantic v2 integration

## Installation

```bash
pip install pyldo
```

## Quick Start

### 1. Generate Python types from a ShEx schema

```bash
# Generate types from a ShEx schema file
pyldo generate profile.shex --output ./ldo/
```

This creates:
- `profile_types.py` - Pydantic models
- `profile_context.py` - JSON-LD context
- `profile_shapetypes.py` - ShapeType definitions

### 2. Use the generated types

```python
from pyldo import parse_rdf
from ldo.profile_types import ProfileShape

# Parse RDF data
dataset = parse_rdf('''
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    <#me> a foaf:Person ;
        foaf:name "Alice" ;
        foaf:knows <https://bob.example/profile#me> .
''', base_iri="https://alice.example/profile")

# Get a typed Python object
profile = dataset.using(ProfileShape).from_subject("#me")

print(profile.name)  # "Alice"

# Modify and serialize back to RDF
profile.name = "Alice Smith"
profile.sync_to_graph()
print(dataset.to_turtle())
```

### 3. Work with Solid Pods

```python
from pyldo import SolidClient, parse_rdf
from ldo.profile_types import ProfileShape

# Create a client (add auth for private data)
client = SolidClient()

# Fetch a profile from a Solid Pod
turtle = await client.get("https://alice.solidcommunity.net/profile/card")
dataset = parse_rdf(turtle, base_iri="https://alice.solidcommunity.net/profile/card")

profile = dataset.using(ProfileShape).from_subject("#me")
print(f"Hello, {profile.name}!")
```

## Core Concepts

### LdoDataset

The main entry point for working with RDF data:

```python
from pyldo import LdoDataset
from ldo.profile_types import PersonShape

dataset = LdoDataset()
dataset.parse_turtle(turtle_string)

# Query for typed objects
person = dataset.using(PersonShape).from_subject("https://example.com/#me")
```

### Transactions

Track changes and generate SPARQL updates:

```python
dataset.start_transaction()

profile.name = "New Name"
profile.sync_to_graph()

# Generate SPARQL UPDATE for the changes
sparql = dataset.to_sparql_update()
print(sparql)
# DELETE DATA { <#me> <http://xmlns.com/foaf/0.1/name> "Old Name" }
# INSERT DATA { <#me> <http://xmlns.com/foaf/0.1/name> "New Name" }

dataset.commit()
```

### SubscribableDataset

React to data changes:

```python
from pyldo import SubscribableDataset

dataset = SubscribableDataset()

# Subscribe to changes
def on_change(event):
    print(f"Data changed: {event.type}")

unsubscribe = dataset.subscribe(on_change)

# Subscribe to specific subjects
dataset.subscribe_to_subject(subject_uri, on_change)
```

### LinkQuery

Traverse links across multiple resources:

```python
from pyldo import LinkQuery, LdoDataset
from ldo.profile_shapetypes import PersonShapeType

dataset = LdoDataset()

query = LinkQuery(
    dataset=dataset,
    shape_type=PersonShapeType,
    starting_resource="https://alice.example/profile",
    starting_subject="https://alice.example/profile#me",
)

# Fetch profile and friends
result = await query.run({
    "name": True,
    "knows": {
        "name": True,  # Fetches linked profiles
    }
})
```

## CLI Commands

```bash
# Generate Python types from ShEx
pyldo generate schema.shex --output ./ldo/

# Show version
pyldo --version
```

## Integration Examples

### FastAPI

```python
from fastapi import FastAPI
from pyldo import parse_rdf, SolidClient
from ldo.profile_types import ProfileShape

app = FastAPI()
client = SolidClient()

@app.get("/profile/{webid:path}")
async def get_profile(webid: str):
    # pyldo models ARE Pydantic models - FastAPI serializes them!
    turtle = await client.get(webid)
    dataset = parse_rdf(turtle, base_iri=webid)
    profile = dataset.using(ProfileShape).from_subject(webid)
    return profile  # Automatic JSON serialization
```

### LangChain

```python
from langchain.tools import tool
from pyldo import parse_rdf, SolidClient
from ldo.profile_types import ProfileShape

client = SolidClient()

@tool
def read_solid_profile(webid: str) -> str:
    """Read a person's profile from their Solid Pod."""
    turtle = client.get_sync(webid)
    dataset = parse_rdf(turtle, base_iri=webid)
    profile = dataset.using(ProfileShape).from_subject(webid)
    return f"Name: {profile.name}"
```

## API Reference

### Parsing & Serialization

- `parse_rdf(data, format, base_iri)` - Parse RDF to LdoDataset
- `to_turtle(ldo)` - Serialize to Turtle
- `to_ntriples(ldo)` - Serialize to N-Triples
- `to_jsonld(ldo)` - Serialize to JSON-LD
- `to_sparql_update(ldo)` - Generate SPARQL UPDATE

### Transactions

- `start_transaction(ldo)` - Begin tracking changes
- `commit_transaction(ldo)` - Apply changes
- `rollback_transaction(ldo)` - Discard changes
- `transaction_changes(ldo)` - Get pending changes

### Language Support

- `languages_of(ldo, property)` - Get available languages
- `set_language_preferences(*langs)` - Set preferred languages

### Querying

- `match_subject(dataset, predicate, object)` - Find subjects
- `match_object(dataset, subject, predicate)` - Find objects

## Requirements

- Python 3.10+
- pydantic >= 2.0.0
- rdflib >= 7.0.0
- httpx >= 0.25.0

## License

MIT

## Credits

Inspired by the [JavaScript LDO library](https://github.com/o-development/ldo) by Jackson Morgan.
