# pylint:disable=missing-docstring,invalid-name
import graphene

import graphene_resolver as resolver


def test_simple():
    class Foo(resolver.Resolver):
        schema = 'Int'

        def resolve(self, **kwargs):
            print({"parent": self.parent})
            return self.parent['bar']

    class Bar(resolver.Resolver):
        schema = {
            "args": {
                "bar": 'Int'
            },
            "type": {
                "foo": Foo
            },
        }

        def resolve(self, **kwargs):
            return kwargs

    class Query(graphene.ObjectType):
        bar = Bar.as_field()

    schema = graphene.Schema(query=Query)
    result = schema.execute('''\
{
    bar(bar: 42){
        foo
    }
}
''')
    assert not result.errors
    assert result.data == {"bar": {"foo": 42}}


def test_list():
    class FooValue(resolver.Resolver):
        schema = 'Int'

        def resolve(self, **kwargs):
            return self.parent['bar']

    class Foo(resolver.Resolver):
        schema = {'value': FooValue}

    class Bar(resolver.Resolver):
        schema = {
            "args": {
                "bar": 'Int'
            },
            "type": [Foo]
        }

        def resolve(self, **kwargs):
            return [kwargs, {'bar': 1}]

    class Query(graphene.ObjectType):
        bar = Bar.as_field()

    schema = graphene.Schema(query=Query)
    assert str(schema) == '''\
schema {
  query: Query
}

type Foo {
  value: Int
}

type Query {
  bar(bar: Int): [Foo]
}
'''
    result = schema.execute('''\
{
    bar(bar: 42){
        value
    }
}
''')
    assert not result.errors
    assert result.data == {"bar": [{'value': 42}, {'value': 1}]}
