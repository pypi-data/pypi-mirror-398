from typing import Literal, overload
from nexo.enums.environment import OptEnvironment
from nexo.types.string import ListOfStrs, OptStr
from .enums import CacheOrigin, CacheLayer


@overload
def build_cache_namespace(
    *ext: str,
    environment: OptEnvironment = None,
    base: OptStr = None,
    origin: Literal[CacheOrigin.SERVICE],
    layer: CacheLayer,
    sep: str = ":",
) -> str: ...
@overload
def build_cache_namespace(
    *ext: str,
    environment: OptEnvironment = None,
    base: OptStr = None,
    client: str,
    origin: Literal[CacheOrigin.CLIENT],
    layer: CacheLayer,
    sep: str = ":",
) -> str: ...
def build_cache_namespace(
    *ext: str,
    environment: OptEnvironment = None,
    base: OptStr = None,
    client: OptStr = None,
    origin: CacheOrigin,
    layer: CacheLayer,
    sep: str = ":",
) -> str:
    slugs: ListOfStrs = []
    if environment is not None:
        slugs.append(environment.value)
    if base is not None:
        slugs.append(base)
    slugs.extend([origin, layer])
    if client is not None:
        slugs.append(client)
    slugs.extend(ext)
    return sep.join(slugs)


def build_cache_key(*ext: str, namespace: str, sep: str = ":"):
    return sep.join([namespace, *ext])
