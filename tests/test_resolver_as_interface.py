# pylint:disable=missing-docstring,invalid-name
import graphene

import graphene_resolver as resolver


def test_simple():
    class IBarBar(resolver.Resolver):
        schema = 'String'

        def resolve(self, **kwargs):
            return self.parent['bar']

    class IBar(resolver.Resolver):
        schema = {
            'bar': IBarBar
        }

    class Foo(resolver.Resolver):
        schema = {
            'args': {
                'bar': "String"
            },
            'type': {
                'ok': 'Int!'
            },
            'interfaces': (IBar,)
        }

        def resolve(self, **kwargs):
            return {
                **kwargs,
                'ok': 1
            }

    class Query(graphene.ObjectType):
        foo = Foo.as_field()
    schema = graphene.Schema(query=Query)
    assert str(schema) == '''\
schema {
  query: Query
}

type Foo implements IBar {
  bar: String
  ok: Int!
}

interface IBar {
  bar: String
}

type Query {
  foo(bar: String): Foo
}
'''

    result = schema.execute('''\
{
    foo(bar: "abc"){
        ok
        bar
    }
}
''')
    assert not result.errors
    assert result.data == {
        'foo': {
            'ok': 1,
            'bar': "abc",
        }
    }
