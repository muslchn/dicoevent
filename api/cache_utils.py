"""Cache helpers with namespace versioning for safe invalidation."""

from __future__ import annotations

import hashlib
from typing import Any

from django.core.cache import cache

CACHE_VERSION_PREFIX = "cache-version"


def _version_key(namespace: str) -> str:
    return f"{CACHE_VERSION_PREFIX}:{namespace}"


def _get_namespace_version(namespace: str) -> int:
    key = _version_key(namespace)
    current = cache.get(key)
    if current is None:
        cache.set(key, 1, timeout=None)
        return 1
    return int(current)


def build_cache_key(namespace: str, request, scope: str) -> str:
    version = _get_namespace_version(namespace)
    user_id = getattr(request.user, "id", "anon") or "anon"
    full_path = request.get_full_path()
    base = f"{request.method}:{user_id}:{scope}:{full_path}"
    digest = hashlib.sha256(base.encode("utf-8")).hexdigest()
    return f"{namespace}:v{version}:{digest}"


def invalidate_cache_namespace(namespace: str) -> None:
    key = _version_key(namespace)
    if cache.get(key) is None:
        cache.set(key, 2, timeout=None)
        return
    try:
        cache.incr(key)
    except ValueError:
        # Cache backend without incr support: reset to a new version.
        cache.set(key, _get_namespace_version(namespace) + 1, timeout=None)


def get_cached_payload(cache_key: str) -> Any:
    return cache.get(cache_key)


def set_cached_payload(cache_key: str, payload: Any, timeout: int) -> None:
    cache.set(cache_key, payload, timeout=timeout)
