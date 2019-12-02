
# pylint:disable=missing-docstring,invalid-name
import typing
import graphene

import graphene_resolver as resolver


def test_simple():

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
    result = schema.execute('''\
{
    foo{
      __typename
      ... on Foo0 {
        a
      }
    }
}
''')
    assert not result.errors
    assert result.data == {"foo": {"__typename": "Foo0", "a": 'a'}}


def test_multiple_use():

    class Foo(resolver.Resolver):
        schema = ({'a': 'String'}, {'b': 'Int'})

        def resolve(self, **kwargs):
            return {'__typename': 'Foo0', 'a': 'a'}

    class Bar(resolver.Resolver):
        schema = {'a': Foo}

        def resolve(self, **kwargs):
            return {'a': None}

    class Query(graphene.ObjectType):
        foo = Foo.as_field()
        bar = Bar.as_field()

    schema = graphene.Schema(query=Query)
    assert str(schema) == '''\
schema {
  query: Query
}

type Bar {
  a: Foo
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
  bar: Bar
}
'''
    result = schema.execute('''\
{
    foo{
      __typename
      ... on Foo0 {
        a
      }
    }
    bar{
        a {
            __typename
            ... on Foo0 {
                a
            }
        }
    }
}
''')
    assert not result.errors
    assert result.data == {"foo": {"__typename": "Foo0", "a": 'a'},
                           "bar": {"a": {"__typename": "Foo0", "a": 'a'}}}


def test_dynamic():
    class Bar(resolver.Resolver):
        schema = {'a': 'Foo'}

        def resolve(self, **kwargs):
            return {'a': {'__typename': 'Foo0', 'a': 'c'}}

    class Foo(resolver.Resolver):
        schema = ({'a': 'String'}, {'b': 'Int'})

        def resolve(self, **kwargs):
            return {'__typename': 'Foo0', 'a': 'a'}

    class Query(graphene.ObjectType):
        foo = Foo.as_field()
        bar = Bar.as_field()

    schema = graphene.Schema(query=Query)
    assert str(schema) == '''\
schema {
  query: Query
}

type Bar {
  a: Foo
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
  bar: Bar
}
'''
    result = schema.execute('''\
{
    foo{
      __typename
      ... on Foo0 {
        a
      }
    }
    bar{
        a {
            __typename
            ... on Foo0 {
                a
            }
        }
    }
}
''')
    assert not result.errors
    assert result.data == {"foo": {"__typename": "Foo0", "a": 'a'},
                           "bar": {"a": {"__typename": "Foo0", "a": 'c'}}}


def test_connection():

    class Foo(resolver.Resolver):
        schema = ({'a': 'String'}, {'b': 'Int'})

        def resolve(self, **kwargs):
            return {'__typename': 'Foo0', 'a': 'a'}

    class FooConnection(resolver.Resolver):
        schema = resolver.connection.get_type(Foo)

        def resolve(self, **kwargs):
            return resolver.connection.resolve([{'__typename': 'Foo0', 'a': 'c'}, {'__typename': 'Foo1', 'b': 1}], **kwargs)

    class Query(graphene.ObjectType):
        foo_set = FooConnection.as_field()

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

type FooConnection {
  edges: [FooEdge]
  nodes: [Foo]
  pageInfo: PageInfo!
  totalCount: Int!
}

type FooEdge {
  node: Foo
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

type Query {
  fooSet(after: String, before: String, first: Int, last: Int): FooConnection
}
'''
    result = schema.execute('''\
{
    fooSet{
        nodes {
            __typename
            ... on Foo0 {
                a
            }
        }
    }
}
''')
    assert not result.errors
    assert result.data == {"fooSet": {
        'nodes': [
            {"__typename": "Foo0", "a": 'c'},
            {"__typename": "Foo1", },
        ],
    }}


def test_with_typename_processor():

    @resolver.TYPENAME_PROCESSOR.register(0)
    def _resolve_type(value):
        if not isinstance(value, typing.Mapping):
            return None
        if 'a' in value:
            return {
                '__typename': 'Foo0'
            }
        if 'b' in value:
            return {
                '__typename': 'Foo1'
            }

    class Foo(resolver.Resolver):
        schema = ({'a': 'String'}, {'b': 'Int'})

        def resolve(self, **kwargs):
            return {'__typename': 'Foo0', 'a': 'a'}

    class FooConnection(resolver.Resolver):
        schema = resolver.connection.get_type(Foo)

        def resolve(self, **kwargs):
            return resolver.connection.resolve([{'a': 'c'}, {'b': 1}], **kwargs)

    class Query(graphene.ObjectType):
        foo_set = FooConnection.as_field()

    schema = graphene.Schema(query=Query)
    result = schema.execute('''\
{
    fooSet{
        nodes {
            __typename
            ... on Foo0 {
                a
            }
        }
    }
}
''')
    assert not result.errors
    assert result.data == {"fooSet": {
        'nodes': [
            {"__typename": "Foo0", "a": 'c'},
            {"__typename": "Foo1", },
        ],
    }}
