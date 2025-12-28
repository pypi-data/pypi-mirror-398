# GraphQL queries with the Python SDK

Use `pb.graphql.query()` to call `/api/graphql` with your current auth token. It returns a dict with `data`, `errors`, and `extensions`.

> Authentication: the GraphQL endpoint is **superuser-only**. Authenticate as a superuser before calling GraphQL, e.g. `pb.collection("_superusers").auth_with_password(email, password)`.

## Single-table query

```python
query = """
  query ActiveUsers($limit: Int!) {
    records(collection: "users", perPage: $limit, filter: "status = true") {
      items { id data }
    }
  }
"""

response = pb.graphql.query(query, variables={"limit": 5})
print(response["data"])
```

## Multi-table join via expands

```python
query = """
  query PostsWithAuthors {
    records(
      collection: "posts",
      expand: ["author", "author.profile"],
      sort: "-created"
    ) {
      items {
        id
        data  # expanded relations live under data.expand
      }
    }
  }
"""

response = pb.graphql.query(query)
```

## Conditional query with variables

```python
query = """
  query FilteredOrders($minTotal: Float!, $state: String!) {
    records(
      collection: "orders",
      filter: "total >= $minTotal && status = $state",
      sort: "created"
    ) {
      items { id data }
    }
  }
"""

result = pb.graphql.query(
  query,
  variables={"minTotal": 100, "state": "paid"},
)
```

Use the `filter`, `sort`, `page`, `perPage`, and `expand` arguments to mirror REST list behavior while keeping query logic in GraphQL.

## Create a record

```python
mutation = """
  mutation CreatePost($data: JSON!) {
    createRecord(collection: "posts", data: $data, expand: ["author"]) {
      id
      data
    }
  }
"""

payload = {"title": "Hello", "author": "USER_ID"}
created = pb.graphql.query(mutation, variables={"data": payload})
```

## Update a record

```python
mutation = """
  mutation UpdatePost($id: ID!, $data: JSON!) {
    updateRecord(collection: "posts", id: $id, data: $data) {
      id
      data
    }
  }
"""

pb.graphql.query(
  mutation,
  variables={
    "id": "POST_ID",
    "data": {"title": "Updated title"},
  },
)
```

## Delete a record

```python
mutation = """
  mutation DeletePost($id: ID!) {
    deleteRecord(collection: "posts", id: $id)
  }
"""

pb.graphql.query(mutation, variables={"id": "POST_ID"})
```
