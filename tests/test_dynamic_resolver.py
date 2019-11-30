# pylint:disable=missing-docstring,invalid-name,unused-variable

import typing

import graphene

import graphene_resolver as resolver


def test_simple():
    class FirstPet(resolver.Resolver):
        schema = 'Pet!'

        def resolve(self, **kwargs):
            return {
                'name': 'pet1',
                'age': 1
            }

    class Pet(resolver.Resolver):
        schema = {
            'name': 'String',
            'age': 'Int',
        }

    class Query(graphene.ObjectType):
        first_pet = FirstPet.as_field()

    schema = graphene.Schema(query=Query)
    assert str(schema) == '''\
schema {
  query: Query
}

type Pet {
  name: String
  age: Int
}

type Query {
  firstPet: Pet!
}
'''
    result = schema.execute('''\
{
    firstPet{
        name
        age
    }
}
''')
    assert not result.errors
    assert result.data == {
        "firstPet": {"name": 'pet1',
                     'age': 1}
    }


def test_node():
    pets = [dict(
        id=1,
        name='pet1',
        age=1,
    )]

    class FirstPet(resolver.Resolver):
        schema = 'Pet!'

        def resolve(self, **kwargs):
            return pets[0]

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
        first_pet = FirstPet.as_field()

    schema = graphene.Schema(query=Query)
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
  firstPet: Pet!
}
'''
    result = schema.execute('''\
{
    firstPet{
        name
        age
    }
}
''')
    assert not result.errors
    assert result.data == {
        "firstPet": {"name": 'pet1',
                     'age': 1}
    }
