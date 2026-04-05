"""pytest configuration: override settings for the unit test suite."""

import pytest


@pytest.fixture(autouse=True)
def use_locmem_cache(settings):
    """Replace Redis cache with an in-memory backend during tests.

    Unit tests must not depend on an external Redis server. Views that use the
    cache layer still exercise the full code path because the low-level cache
    API (cache.get / cache.set / cache.incr) is identical across backends.
    """
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "dicoevent-test-cache",
            "TIMEOUT": 300,
        }
    }
