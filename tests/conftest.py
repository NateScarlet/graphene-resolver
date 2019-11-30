import pytest
import graphene_resolver as resolver


_DEFAULT_TYPE_REGISTRY = dict(resolver.typedef.REGISTRY)


@pytest.fixture(autouse=True)
def _clear_registry():
    resolver.connection.REGISTRY.clear()
    resolver.typedef.REGISTRY.clear()
    resolver.typedef.REGISTRY.update(**_DEFAULT_TYPE_REGISTRY)
