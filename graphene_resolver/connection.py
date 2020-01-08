"""Relay compatible connection resolver.  """

import re
import typing

import graphene
from graphql_relay.connection import arrayconnection
import lazy_object_proxy as lazy

from . import resolver
from . import schema as schema_

REGISTRY: typing.Dict[str, typing.Type] = {}


def _get_node_name(node: typing.Union[resolver.Resolver, str, typing.Any]) -> str:
    if isinstance(node, str):
        return node
    if (isinstance(node, type)
            and issubclass(node, resolver.Resolver)):
        node_name = schema_.FieldDefinition.parse(
            node.schema, default={'name': node.__name__}).name
    else:
        node_name = schema_.FieldDefinition.parse(node).name
    return node_name


def build_schema(
        node: typing.Union[resolver.Resolver, str, typing.Any],
        *,
        name: str = None,) -> dict:
    """Build a github-like connection resolver schema.
    see at https://developer.github.com/v4/explorer/

    Args:
        node (typing.Union[resolver.Resolver, str, typing.Any]): Node resolver or schema.
        name (str, optional): Override default connection name,
            required when node name is not defined.

    Returns:
        dict: dict for Resolver schema.
    """

    name = name or f'{_get_node_name(node)}Connection'
    edge_name = f"{re.sub('Connection$', '', name)}Edge"

    return dict(
        name=name,
        description=f"The connection type for {re.sub('Connection$', '', name)}.",
        args=dict(
            after={
                'type': 'String',
                'description': ('Returns the elements in the list '
                                'that come after the specified cursor.')
            },
            before={
                'type': 'String',
                'description': ('Returns the elements in the list '
                                'that come before the specified cursor.')
            },
            first={
                'type': 'Int',
                'description': 'Returns the first _n_ elements from the list.'
            },
            last={
                'type': 'Int',
                'description': 'Returns the last _n_ elements from the list.'
            },
        ),
        type={
            'edges': {
                'type': [{
                    'name': edge_name,
                    'type': {
                        'node': {
                            'type': node,
                            'description': 'The item at the end of the edge.',
                        },
                        'cursor': {
                            'type': 'String!',
                            'description': 'A cursor for use in pagination.'
                        },
                    },
                }],
                'description': 'A list of edges.'
            },
            'nodes': {
                'type': [node],
                'description': 'A list of nodes.'
            },
            'pageInfo': {
                'type': graphene.relay.PageInfo,
                'required': True,
                'description': 'Information to aid in pagination.',
            },
            'totalCount': {
                'type': 'Int!',
                'description': 'Identifies the total count of items in the connection.',
            },
        }
    )


def get_type(
        node: typing.Union[resolver.Resolver, str, typing.Any],
        *,
        name: str = None,
) -> resolver.Resolver:
    """Get connection resolver from registry.
    one will be created with `build_schema` if not found in registry.

    Args:
        node (typing.Union[resolver.Resolver, str, typing.Any]): Node resolver or schema.
        name (str, optional): Override default connection name,
            required when node name is not defined.

    Returns:
        resolver.Resolver: Created connection resolver, same name will returns same resolver.
    """

    name = name or f'{_get_node_name(node)}Connection'

    if name in REGISTRY:
        return REGISTRY[name]

    REGISTRY[name] = type(
        name, (resolver.Resolver,),
        dict(schema=build_schema(node, name=name))
    )

    return REGISTRY[name]


def _get_lazy_wrapped(v):
    if not isinstance(v, lazy.Proxy):
        return v
    return _get_lazy_wrapped(v.__wrapped__)


def patch_lazy_default_resolver() -> None:
    """Patch graphene default resolver to support lazy object proxy.  """

    default_resolver = graphene.types.resolver.get_default_resolver()

    def _lazy_patched_default_resolver(*args, **kwargs):
        ret = default_resolver(*args, **kwargs)
        ret = _get_lazy_wrapped(ret)
        return ret

    if default_resolver.__name__ == _lazy_patched_default_resolver.__name__:
        # Already patched
        return
    graphene.types.resolver.set_default_resolver(
        _lazy_patched_default_resolver)


patch_lazy_default_resolver()


def resolve(
        iterable,
        length: int = None,
        *,
        first: int = None,
        last: int = None,
        after: str = None,
        before: str = None,
        **_,
) -> dict:
    """Resolve iterable to connection

    Args:
        iterable (typing.Iterable): value
        length (int, Optional): defaults to `len(iterable)`,
            iterable length.

    Returns:
        dict: Connection data.
    """
    def _get_length():
        if length is None:
            return len(iterable)
        return length
    _len = lazy.Proxy(_get_length)

    after_index = arrayconnection.get_offset_with_default(after, -1) + 1
    before_index = arrayconnection.get_offset_with_default(before, None)

    def _get_start_index() -> typing.Optional[int]:
        ret = after_index
        if isinstance(last, int):
            ret = max((_len
                       if end_index is None
                       else end_index) - last, ret)
        return ret

    def _get_end_index() -> typing.Optional[int]:
        ret = before_index
        if isinstance(first, int):
            ret = (min(after_index + first, ret)
                   if ret is not None
                   else after_index + first)
        return ret

    start_index = lazy.Proxy(_get_start_index)
    end_index = lazy.Proxy(_get_end_index)

    def _get_nodes():
        # lazy proxy None can not use as None index.
        return iterable[start_index.__wrapped__:end_index.__wrapped__]

    nodes = lazy.Proxy(_get_nodes)
    edges = lazy.Proxy(lambda: [
        dict(
            node=node,
            cursor=arrayconnection.offset_to_cursor(start_index + i)
        )
        for i, node in enumerate(nodes)
    ])

    def _get_start_cursor():
        end = end_index.__wrapped__
        start = start_index.__wrapped__
        if end is not None and end <= start:
            return None
        return arrayconnection.offset_to_cursor(start)

    def _get_end_cursor():
        if not edges:
            return None
        return edges[-1]['cursor']

    return dict(
        nodes=nodes,
        edges=edges,
        pageInfo=dict(
            start_cursor=lazy.Proxy(_get_start_cursor),
            end_cursor=lazy.Proxy(_get_end_cursor),
            has_previous_page=lazy.Proxy(lambda: isinstance(
                last, int) and start_index > (after_index + 1 if after else 0)),
            has_next_page=lazy.Proxy(lambda: isinstance(first, int) and end_index < (
                before_index if before else _len))
        ),
        totalCount=_len,
    )
