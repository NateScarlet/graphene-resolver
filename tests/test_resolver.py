# pylint:disable=missing-docstring,invalid-name
import typing

import graphene

import graphene_resolver as resolver


def test_simple():
    class Foo(resolver.Resolver):
        schema = {
            "args": {
                "key":  'String!',
                "value": 'String!',
            },
            "type": 'String!',
        }

        def resolve(self, **kwargs):
            return kwargs['value']

    class Query(graphene.ObjectType):
        foo = Foo.as_field()

    assert len(Query.foo.args) == 2
    print(dict(args=Query.foo.args['key'].type))
    schema = graphene.Schema(query=Query)
    result = schema.execute('''\
{
    foo(key: "k", value: "v")
}
''')
    assert not result.errors
    assert result.data == {"foo":  "v"}


def test_object():
    class Foo(resolver.Resolver):
        schema = {
            "ok": {
                "type": 'Int',
                "required": True,
            },
        }

        def resolve(self, **kwargs):
            return {"ok": 1}

    class Query(graphene.ObjectType):
        foo = Foo.as_field()

    schema = graphene.Schema(query=Query)
    result = schema.execute('''\
{
    foo{
        ok
    }
}
''')
    assert not result.errors
    assert result.data == {"foo": {"ok": 1}}


def test_enum():
    class State(graphene.Enum):
        A = 1

    class Foo(resolver.Resolver):
        schema = {
            'args': {
                'value': {
                    'type': State,
                    'required': True
                },
            },
            'type': State
        }

        def resolve(self, **kwargs):
            return kwargs['value']

    class Query(graphene.ObjectType):
        foo = Foo.as_field()

    schema = graphene.Schema(query=Query)
    result = schema.execute('''\
{
    foo(value: A)
}
''')
    assert not result.errors
    assert result.data == {"foo": "A"}


def test_complicated():
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

    class Query(graphene.ObjectType):
        foo = Foo.as_field()

    schema = graphene.Schema(query=Query)
    assert str(schema) == '''\
schema {
  query: Query
}

type Foo {
  type: String
  data: [FooData!]
}

type FooData {
  key: String!
  value: Int
  extra: [String!] @deprecated(reason: "<deprecated>")
}

input FooInput {
  type: String
  data: [FooInputData!]
}

input FooInputData {
  key: String!
  value: Int
  extra: [String!]
}

type Query {
  foo(input: FooInput): Foo
}
'''
    result = schema.execute('''\
{
    foo(input: {type: "type", data: [{key: "key", value: 42, extra: ["extra"]}]}){
        type
        data{
            key
            value
            extra
        }
    }
}
''')
    assert not result.errors
    assert result.data == {
        "foo": {"type": "type",
                "data": [{"key": "key", "value": 42, "extra": ["extra"]}]}}


def test_interface():
    pets = [dict(
        id=1,
        name='pet1',
        age=1,
    )]

    class Foo(resolver.Resolver):
        schema = {
            'type': {
                'name': 'String',
                'age': 'Int',
            },
            'interfaces': (graphene.Node,)
        }

        def resolve(self, **kwargs):
            return pets[0]

    class Query(graphene.ObjectType):
        foo = Foo.as_field()

    schema = graphene.Schema(query=Query)
    assert str(schema) == '''\
schema {
  query: Query
}

type Foo implements Node {
  id: ID!
  name: String
  age: Int
}

interface Node {
  id: ID!
}

type Query {
  foo: Foo
}
'''
    result = schema.execute('''\
{
    foo{
        id
        name
        age
    }
}
''')
    assert not result.errors
    assert result.data == {
        "foo": {"id": "Rm9vOjE=",
                "name": 'pet1',
                'age': 1}
    }


def test_node():
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
    assert str(schema) == '''\
schema {
  query: Query
}

interface Node {
  id: ID!
}

type Pet implements Node {
  id: ID!
  name: String
  age: Int
}

type Query {
  node(id: ID!): Node
}
'''
    result = schema.execute('''\
{
    node(id: "UGV0OjE="){
        id
        __typename
        ... on Pet {
            name
            age
        }
    }
}
''')
    assert not result.errors
    assert result.data == {
        "node": {"id": "UGV0OjE=",
                 "__typename": "Pet",
                 "name": 'pet1',
                 'age': 1}
    }


def test_list():
    class Foo(resolver.Resolver):
        schema = {
            'args': {
                'input': ['ID!']
            },
            'type': ['ID!'],
            'required': True
        }

        def resolve(self, **kwargs):
            return kwargs.get('input', [])

    class Query(graphene.ObjectType):
        foo = Foo.as_field()

    schema = graphene.Schema(query=Query)
    assert str(schema) == '''\
schema {
  query: Query
}

type Query {
  foo(input: [ID!]): [ID!]!
}
'''
    result = schema.execute('''\
{
    foo(input: "UGV0OjE=")
}
''')
    assert not result.errors
    assert result.data == {'foo': ["UGV0OjE="]}


def test_default():
    class Foo(resolver.Resolver):
        schema = {
            'args': {
                'input': {
                    'type': 'Int',
                    'default': 42,
                },
            },
            'type': 'Int!',
        }

        def resolve(self, **kwargs):
            return kwargs['input']

    class Query(graphene.ObjectType):
        foo = Foo.as_field()

    schema = graphene.Schema(query=Query)
    assert str(schema) == '''\
schema {
  query: Query
}

type Query {
  foo(input: Int = 42): Int!
}
'''
    result = schema.execute('''\
{
    foo
}
''')
    assert not result.errors
    assert result.data == {'foo': 42}
