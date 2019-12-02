# -*- coding=UTF-8 -*-
"""Mongoose-like schema.  """
# pylint:disable=unused-import

from __future__ import annotations
import dataclasses
import enum
import typing

import graphene
import phrases_case

from . import typedef
from . import processor


class SpecialType(enum.Enum):
    """Indicate special type syntax used in schema.  """

    MAPPING = enum.auto()
    LIST = enum.auto()
    ENUM = enum.auto()
    UNION = enum.auto()


CONFIG_PROCESSOR = processor.Processor()


@CONFIG_PROCESSOR.register(100)
def _process_resolver_config(type_def, config):
    from . import resolver
    if not (isinstance(type_def, type)
            and issubclass(type_def, resolver.Resolver)):
        return None
    _resolver: typing.Type[resolver.Resolver] = type_def
    # merge schema
    config['name'] = _resolver._schema.name
    config['type'] = _resolver.as_type()
    config['args'].update(**_resolver._schema.args)
    config['interfaces'] += _resolver._schema.interfaces
    config.setdefault('required', _resolver._schema.required)

    _parent_resolver = config.get('resolver')

    def resolve_fn(parent, info, **kwargs):
        if _parent_resolver:
            parent = _parent_resolver(parent, info, **kwargs)
        return _resolver._schema.resolver(parent, info, **kwargs)
    config.setdefault('resolver', resolve_fn)
    config.setdefault('description', _resolver._schema.description)
    config.setdefault('deprecation_reason',
                      _resolver._schema.deprecation_reason)
    child_definition = _resolver._schema.child_definition
    return dict(
        config=config,
        child_definition=child_definition
    )


@CONFIG_PROCESSOR.register(90)
def _process_str_type_def(type_def, config):
    if not isinstance(type_def, str):
        return None
    if type_def[-1] == '!':
        config.setdefault('required', True)
        type_def = type_def[:-1]
    config['type'] = type_def
    return dict(
        config=config
    )


@CONFIG_PROCESSOR.register(80)
def _process_mapping_type_def(type_def, config):
    if not isinstance(type_def, typing.Mapping):
        return None
    config['type'] = SpecialType.MAPPING
    return dict(
        config=config,
        child_definition=type_def
    )


@CONFIG_PROCESSOR.register(70)
def _process_empty_iterable_type_def(type_def, config):
    if isinstance(type_def, typing.Iterable) and len(type_def) == 0:
        raise ValueError('Can not use empty iterable as type.')


@CONFIG_PROCESSOR.register(60)
def _process_list_type_def(type_def, config):
    if not (isinstance(type_def, typing.Iterable) and len(type_def) == 1):
        return None
    config['type'] = SpecialType.LIST
    return dict(
        config=config,
        child_definition=type_def[0]
    )


@CONFIG_PROCESSOR.register(50)
def _process_enum_type_def(type_def, config):
    if not(isinstance(type_def, typing.Iterable)
            and all(isinstance(i, (str, tuple)) for i in type_def)):
        return None
    config['type'] = SpecialType.ENUM
    return dict(
        config=config,
        child_definition=type_def
    )


@CONFIG_PROCESSOR.register(40)
def _process_union_type_def(type_def, config):
    if not isinstance(type_def, typing.Iterable):
        return None
    config['type'] = SpecialType.UNION
    return dict(
        config=config,
        child_definition=type_def
    )


@CONFIG_PROCESSOR.register(-1)
def _process_type_type_def(type_def, config):
    config['type'] = type_def
    return dict(
        config=config,
    )


@dataclasses.dataclass
class EnumFieldDefinition:
    value: str
    description: typing.Optional[str]

    @classmethod
    def parse(cls, v) -> EnumFieldDefinition:
        """Parse schema for enum

        Args:
            v (typing.Any): schema item

        Returns:
            EnumFieldDefinition: Parsing result
        """
        if isinstance(v, str):
            return cls(value=v, description=None)
        elif isinstance(v, tuple) and len(v) == 2:
            return cls(value=v[0], description=v[1])
        raise ValueError(
            f'Enum field should be a str or 2-value tuple, got {v}')


@dataclasses.dataclass
class FieldDefinition:
    """A mongoose-like schema for resolver field.  """

    # Options:
    args: typing.Mapping
    type: typing.Type
    required: bool
    name: str
    interfaces: typing.Tuple[typing.Type[graphene.Interface], ...]
    description: typing.Optional[str]
    deprecation_reason: typing.Optional[str]
    resolver: typing.Optional[typing.Callable]
    default: typing.Any

    # Parse results:
    child_definition: typing.Any

    @classmethod
    def parse(cls, v: typing.Any, *, default: typing.Dict = None) -> FieldDefinition:
        """Parse a mongoose like schema

        Args:
            v (typing.Any): schema item

        Returns:
            SchemaDefinition: Parsing result
        """
        from . import resolver

        assert v is not None, 'schema is None'
        config = default or {}
        child_definition = None
        is_full_config = (
            isinstance(v, typing.Mapping)
            and 'type' in v
            and not (  # Handle `type` as mapping key.
                isinstance(v['type'], typing.Mapping)
                and 'type' in v['type']
                and not isinstance(v['type']['type'], typing.Mapping)))

        type_def = v
        if is_full_config:
            config.update(**v)
            type_def = v['type']
        if 'name' not in config:
            raise ValueError(f'Not specified field name in: {v}')
        # Convert args
        config.setdefault('args', {})
        if config['args']:
            config['args'] = {
                k: (cls
                    .parse(
                        v,
                        default={
                            'name': phrases_case.camel(f'{config["name"]}_{k}')
                        })
                    .mount(as_=graphene.Argument))
                for k, v in config['args'].items()
            }
        # Convert interfaces
        config.setdefault('interfaces', ())
        config['interfaces'] = tuple(
            i.as_interface() if (isinstance(i, type) and issubclass(i, resolver.Resolver)) else i
            for i in config['interfaces']
        )

        result = CONFIG_PROCESSOR.process(config=config, type_def=type_def)
        config = result['config']
        child_definition = result.get('child_definition')

        config.setdefault('required', False)
        config.setdefault('description', None)
        config.setdefault('deprecation_reason', None)
        config.setdefault('resolver', None)
        config.setdefault('default', None)

        return cls(
            type=config['type'],
            required=config['required'],
            name=config['name'],
            description=config['description'],
            deprecation_reason=config['deprecation_reason'],
            args=config['args'],
            interfaces=config['interfaces'],
            resolver=config['resolver'],
            default=config['default'],
            child_definition=child_definition,
        )

    def _get_options(self, target: typing.Type):
        allowed_options = ()
        if not isinstance(target, type):
            pass

        allowed_options_by_type = [
            (graphene.Argument,
             ('required', 'default_value', 'description', )),
            (graphene.Field,
             ('args', 'resolver', 'required', 'default_value',
              'description', 'deprecation_reason', )),
            (graphene.InputField,
             ('required', 'default_value', 'description', 'deprecation_reason',)),
        ]
        for classinfo, options in allowed_options_by_type:
            if issubclass(target, classinfo):
                allowed_options += options

        options = dict(
            name=self.name,
            required=self.required,
            description=self.description,
            deprecation_reason=self.deprecation_reason,
            args=self.args,
            resolver=self.resolver,
            default_value=self.default,
        )

        return {k: v for k, v in options.items() if k in allowed_options}

    def as_type(
            self,
            *,
            mapping_bases: typing.Tuple[typing.Type] = (graphene.ObjectType,),
            registry=None
    ) -> graphene.types.unmountedtype.UnmountedType:
        """Convert schema to graphene unmounted type instance with options set.

        Args:
            is_input (bool, optional): Whether is input field. Defaults to False.
            registry (typing.Dict, optional): Graphene type registry. Defaults to None.

        Returns:
            graphene.types.unmountedtype.UnmountedType: result
        """
        registry = registry or typedef.REGISTRY

        namespace = self.name
        is_input = graphene.InputObjectType in mapping_bases

        options = self._get_options(
            graphene.Argument if is_input else graphene.Field)
        ret = None
        # Mapping
        if self.type is SpecialType.MAPPING:
            assert self.child_definition
            _type: typing.Type = type(
                namespace,
                mapping_bases,
                {
                    **{
                        k: (self.parse(
                            v,
                            default={
                                'name': phrases_case.camel(f'{namespace}_{k}')}
                        ).mount(as_=graphene.InputField if is_input else graphene.Field))
                        for k, v in self.child_definition.items()
                    },
                    **dict(
                        Meta=dict(
                            name=self.name,
                            interfaces=self.interfaces,
                            description=self.description,
                        )
                    )
                })
            registry[namespace] = _type
            ret = _type
        # Iterable
        elif self.type is SpecialType.LIST:
            assert self.child_definition
            _item_schema = self.parse(
                self.child_definition,
                default={'name': namespace}
            )
            _item_type = _item_schema.as_type(mapping_bases=mapping_bases)
            if _item_schema.required:
                # `required` option for list item not work,
                # so non-null structure is required.
                _item_type = graphene.NonNull(_item_type)
            ret = graphene.List(
                _item_type,
                **options
            )
        elif self.type is SpecialType.ENUM:
            assert self.child_definition
            _enum_defs = [EnumFieldDefinition.parse(i)
                          for i in self.child_definition]
            _enum = enum.Enum(  # type: ignore
                namespace, {i.value: i.value for i in _enum_defs})

            def _get_description(v):
                if v is None:
                    return self.description
                return next(i for i in _enum_defs if i.value == v.value).description
            ret = graphene.Enum.from_enum(
                _enum,
                description=_get_description
            )
        elif self.type is SpecialType.UNION:
            assert self.child_definition

            def _dynamic():
                if not isinstance(registry[namespace], type):
                    _types = [FieldDefinition.parse(i, default={'name': f'{namespace}{index}'}).as_type()
                              for index, i in enumerate(self.child_definition)]
                    _types = [i() if callable(i) and not isinstance(i, type) else i
                              for i in _types]
                    registry[namespace] = type(namespace, (typedef.Union,), dict(
                        Meta=dict(
                            types=_types,
                            description=self.description,
                        )
                    ))
                return registry[namespace]
            ret = _dynamic
            registry[namespace] = ret

        # Unmounted type.
        elif (isinstance(self.type, type)
              and issubclass(self.type, graphene.types.unmountedtype.UnmountedType)):
            ret = self.type(**options)
        # Dynamic
        elif isinstance(self.type, str):
            ret = typedef.dynamic_type(self.type)
        # As-is
        else:
            ret = self.type
        return ret

    def mount(
            self,
            *,
            as_: typing.Type,
            type_: graphene.types.unmountedtype.UnmountedType = None,
            registry=None
    ):
        """Mount schema as a graphene mounted type instance.

        Args:
            as_ (typing.Type): Target type
            type_ (graphene.types.unmountedtype.UnmountedType, optional):
                Override unmmounted type. Defaults to None.
            registry (typing.Mapping, optional): Graphene type registry. Defaults to None.

        Returns:
            Mounted type instance.
        """

        is_input = (
            isinstance(as_, type)
            and issubclass(
                as_,
                (graphene.Argument, graphene.InputField, graphene.InputObjectType)))
        mapping_bases = (graphene.InputObjectType,
                         ) if is_input else (graphene.ObjectType,)
        type_ = type_ or self.as_type(
            mapping_bases=mapping_bases, registry=registry)

        if isinstance(type_, graphene.types.unmountedtype.UnmountedType):
            return type_.mount_as(as_)
        return as_(type=type_, **self._get_options(as_))
