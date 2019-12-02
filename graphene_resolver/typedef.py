# -*- coding=UTF-8 -*-
"""Mongoose-like schema.  """

from __future__ import annotations
import functools
import typing

import graphene

from . import processor
from . import types

REGISTRY: typing.Dict[
    str,
    typing.Type[graphene.types.unmountedtype.UnmountedType]
] = {
    'ID': graphene.ID,
    'Boolean': graphene.Boolean,
    'String': graphene.String,
    'Int': graphene.Int,
    'Float': graphene.Float,
    'Decimal': graphene.Decimal,
    'Time': graphene.Time,
    'Date': graphene.Date,
    'DateTime': graphene.DateTime,
    'Duration': types.Duration,
}

TYPENAME_PROCESSOR = processor.Processor()


@TYPENAME_PROCESSOR.register(-1)
def _resolve_type(value) -> dict:  # pylint:disable=unused-argument
    return {
        '__typename': None
    }


class Union(graphene.Union):
    class Meta:
        abstract = True

    @classmethod
    def resolve_type(cls, instance, info):
        ret = super().resolve_type(instance, info)
        if ret is not None:
            return ret

        if isinstance(instance, typing.Mapping) and '__typename' in instance:
            return info.schema.get_type(instance['__typename']).graphene_type
        return TYPENAME_PROCESSOR.process(value=instance)['__typename']


def dynamic_type(type_: typing.Any, *, registry=None) -> typing.Callable:
    """Get dynamic type function for given typename.

    Args:
        type_ (typing.Any): typename or type itself.
        registry (typing.Dict, optional): Graphene type registry. Defaults to None.

    Returns:
        typing.Callable: dynamic type function
    """
    registry = registry or REGISTRY

    def type_fn(type_, *_args, **_kwargs):
        if isinstance(type_, str):
            type_ = registry[type_]

        assert (isinstance(type_, (type, typing.Callable))), repr(type_)
        return type_

    return functools.partial(type_fn, type_)
