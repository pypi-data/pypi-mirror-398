#!/usr/bin/env python3
"""Test programmatic use of the LinkML parser."""

from pyldo.converter import generate_python_types, linkml_to_shex, parse_linkml

# Define a LinkML schema as a string
yaml_schema = '''
id: https://example.org/recipes
name: recipe-schema
prefixes:
  schema: http://schema.org/

classes:
  Recipe:
    class_uri: schema:Recipe
    attributes:
      name:
        slot_uri: schema:name
        range: string
        required: true
      ingredients:
        slot_uri: schema:recipeIngredient
        range: string
        multivalued: true
      cook_time:
        slot_uri: schema:cookTime
        range: string
      author:
        slot_uri: schema:author
        range: Person
        
  Person:
    class_uri: schema:Person
    attributes:
      name:
        slot_uri: schema:name
        range: string
        required: true
      email:
        slot_uri: schema:email
        range: string
'''

# 1. Parse LinkML to internal schema representation
print('1. Parsing LinkML schema...')
schema = parse_linkml(yaml_schema)
print(f'   ✓ Parsed {len(schema.shapes)} shapes:')
for shape in schema.shapes:
    name = shape.id.split('#')[-1]
    print(f'     - {name}')

# 2. Convert to ShEx for debugging
print()
print('2. Converting to ShEx:')
shex = linkml_to_shex(yaml_schema)
print(shex)

# 3. Generate Python types
print('3. Generating Python types...')
python_code = generate_python_types(schema, 'recipe')
print('   ✓ Generated Python code (first 500 chars):')
print(python_code[:500])
print('   ...')

print()
print('✅ All programmatic APIs working!')
