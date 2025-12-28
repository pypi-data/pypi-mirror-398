# Schema Query API - Python SDK

Use the schema query endpoints to inspect field definitions without fetching entire collection objects. This is ideal for AI assistants, code generators, or documentation tooling.

## Single Collection Schema

```python
schema = pb.collections.get_schema("articles")

print(schema["name"], schema["type"])
for field in schema["fields"]:
    print(field["name"], field["type"], field.get("required"))
```

## All Schemas

```python
all_schemas = pb.collections.get_all_schemas()
for collection in all_schemas["collections"]:
    print(collection["name"], len(collection["fields"]))
```

## Typical Workflow

1. Fetch `get_all_schemas()` during startup.
2. Cache the response locally (it changes infrequently).
3. Feed the structure to your AI prompt or code generation logic.

## Metadata

Each field entry includes:

- `name`
- `type`
- `required`
- `system`
- `hidden`

This is enough to build type hints or form builders without downloading the full collection definition.
