Union
================


Iterable in schema that length greater than 1 and not match :doc:`/enum` definition
will be parsed as union type.

Default name from current path and index.

Return value for union field should be mapping that contains ``__typename`` key.
``__typename`` value should be typename of one possible type.
Returns a graphene object type instance should also work but not tested.

You can returns any value with ``TYPENAME_PROCESSOR``:

.. code:: python

  import graphene_resolver as resolver

  class CustomDict(dict):
    pass

  @resolver.TYPENAME_PROCESSOR.register(10) # 10 is process weight, higher first.
  def _resolve_type(value):
      if isinstance(value, CustomDict):
          return {
            '__typename': 'CustomDictObjectType'
          }
