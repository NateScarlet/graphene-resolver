Connection
====================

Use ``get_connection`` to quick create relay compatible github-like connection resolver.

same name will returns same resolver, base on `CONNECTION_REGISTRY`.

.. code:: python

  import graphene
  import graphene_resolver as resolver
  from django.db import models

  class Item(resolver.Resolver):
      schema = {'name': 'String!'}

  class Items(resolver.Resolver):
      schema = resolver.connection.get_type(Item)

      def resolve(self, **kwargs):
          return resolver.connection.resolve([{'name': 'a'}, {'name': 'b'}], **kwargs)

  class Query(graphene.ObjectType):
      items = Items.as_field()
