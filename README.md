# Graphene resolvers

[![build status](https://github.com/NateScarlet/graphene-resolver/workflows/Python%20package/badge.svg)](https://github.com/NateScarlet/graphene-resolver/actions)
[![version](https://img.shields.io/pypi/v/graphene-resolver)](https://pypi.org/project/graphene-resolver/)
![python version](https://img.shields.io/pypi/pyversions/graphene-resolver)
![wheel](https://img.shields.io/pypi/wheel/graphene-resolver)
![maintenance](https://img.shields.io/maintenance/yes/2019)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org)

Using mongoose-like schema to write apollo-like resolver.

## Install

`pip install graphene-resolver`

## Usage

simple example:

```python
import graphene
import graphene_resolver as resolver

class Foo(resolver.Resolver):
    schema = {
        "args": {
            "key":  'String!',
            "value": 'String!',
        },
        "type": 'String!',
    }

    def resolve(self, **kwargs):
        self.parent # parent field
        self.info # resolve info
        self.context # resolve context
        return kwargs['value']

class Query(graphene.ObjectType):
    foo = Foo.as_field()
```

```graphql
{
  foo(key: "k", value: "v")
}
```

```json
{ "foo": "v" }
```

relay node:

```python
pets = [dict(
    id=1,
    name='pet1',
    age=1,
)]
class Pet(resolver.Resolver):
    schema = {
        'type': {
            'name': 'String',
            'age': 'Int',
        },
        'interfaces': (graphene.Node,)
    }

    def get_node(self, id_):
        return next(i for i in pets if i['id'] == int(id_))

    def validate(self, value):
        return (
            isinstance(value, typing.Mapping)
            and isinstance(value.get('name'), str)
            and isinstance(value.get('age'), int)
        )
class Query(graphene.ObjectType):
    node = graphene.Node.Field()

schema = graphene.Schema(query=Query, types=[Pet.as_type()])
```

```graphql
{
  node(id: "UGV0OjE=") {
    id
    __typename
    ... on Pet {
      name
      age
    }
  }
}
```

```json
{ "node": { "id": "UGV0OjE=", "__typename": "Pet", "name": "pet1", "age": 1 } }
```

relay connection:

```python
class Item(resolver.Resolver):
    schema = {'name': 'String!'}

class Items(resolver.Resolver):
    schema = resolver.connection.get_type(Item)

    def resolve(self, **kwargs):
        return resolver.connection.resolve([{'name': 'a'}, {'name': 'b'}], **kwargs)
```

```graphql
{
  items {
    edges {
      node {
        name
      }
      cursor
    }
    pageInfo {
      total
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
    }
  }
}
```

```json
{
  "items": {
    "edges": [
      { "node": { "name": "a" }, "cursor": "YXJyYXljb25uZWN0aW9uOjA=" },
      { "node": { "name": "b" }, "cursor": "YXJyYXljb25uZWN0aW9uOjE=" }
    ],
    "pageInfo": {
      "total": 2,
      "hasNextPage": false,
      "hasPreviousPage": false,
      "startCursor": "YXJyYXljb25uZWN0aW9uOjA=",
      "endCursor": "YXJyYXljb25uZWN0aW9uOjE="
    }
  }
}
```

enum:

```python

    class Foo(resolver.Resolver):
        schema = ('a', 'b')

        def resolve(self, **kwargs):
            return 'a'

    class Query(graphene.ObjectType):
        foo = Foo.as_field()

    schema = graphene.Schema(query=Query)
    assert str(schema) == '''\
schema {
  query: Query
}

enum Foo {
  a
  b
}

type Query {
  foo: Foo
}
'''
```

enum with description:

```python

    class Foo(resolver.Resolver):
        schema = {
            'type': [('a', 'this is a'), ('b', 'this is b'), 'c'],
            'description': 'A enum',
        }

        def resolve(self, **kwargs):
            return 'a'

    class Query(graphene.ObjectType):
        foo = Foo.as_field()

    schema = graphene.Schema(query=Query)
    enum_type = schema.get_type('Foo')
    assert enum_type.description == 'A enum'
    assert enum_type.get_value('a').value == 'a'
    assert enum_type.get_value('a').description == 'this is a'
    assert enum_type.get_value('b').value == 'b'
    assert enum_type.get_value('b').description == 'this is b'
    assert enum_type.get_value('c').value == 'c'
    assert enum_type.get_value('c').description is None
```

union:

```python
    class Foo(resolver.Resolver):
        schema = ({'a': 'String'}, {'b': 'Int'})

        def resolve(self, **kwargs):
            return {'__typename': 'Foo0', 'a': 'a'}

    class Query(graphene.ObjectType):
        foo = Foo.as_field()

    schema = graphene.Schema(query=Query)
    assert str(schema) == '''\
schema {
  query: Query
}

union Foo = Foo0 | Foo1

type Foo0 {
  a: String
}

type Foo1 {
  b: Int
}

type Query {
  foo: Foo
}
'''
```

```graphql
{
  foo {
    __typename
    ... on Foo0 {
      a
    }
  }
}
```

```json
{ "foo": { "__typename": "Foo0", "a": "a" } }
```

complicated example:

```python
class Foo(resolver.Resolver):
    _input_schema = {
        "type": {"type": 'String'},
        "data": [
            {
                "type":
                {
                    "key": {
                        "type": 'String',
                        "required": True,
                        "description": "<description>",
                    },
                    "value": 'Int',
                    "extra": {
                        "type": ['String!'],
                        "deprecation_reason": "<deprecated>"
                    },
                },
                "required": True
            },
        ],
    }
    schema = {
        "args": {
            "input": _input_schema
        },
        "type": _input_schema,
        "description": "description",
        "deprecation_reason": None
    }

    def resolve(self, **kwargs):
        return kwargs['input']
```

```graphql
{
  foo(
    input: { type: "type", data: [{ key: "key", value: 42, extra: ["extra"] }] }
  ) {
    type
    data {
      key
      value
      extra
    }
  }
}
```

```json
{
  "foo": {
    "type": "type",
    "data": [{ "key": "key", "value": 42, "extra": ["extra"] }]
  }
}
```
