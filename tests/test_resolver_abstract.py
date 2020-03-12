# pylint:disable=missing-docstring,invalid-name

import graphene

import graphene_resolver as resolver


def test_simple():
    class Resolver(resolver.Resolver, abstract=True):
        def get_custom_data(self):
            return 'foo'

    class Foo(Resolver):
        schema = {
            "args": {
                "key":  'String!',
                "value": 'String!',
            },
            "type": 'String!',
        }

        def resolve(self, **kwargs):
            return self.get_custom_data()

    class Query(graphene.ObjectType):
        foo = Foo.as_field()

    assert len(Query.foo.args) == 2
    schema = graphene.Schema(query=Query)
    result = schema.execute('''\
{
    foo(key: "k", value: "v")
}
''')
    assert not result.errors
    assert result.data == {"foo":  "foo"}
