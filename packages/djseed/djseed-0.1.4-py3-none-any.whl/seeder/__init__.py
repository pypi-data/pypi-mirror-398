# seeder/__init__.py
from .registry import registry


def seed_all(*args, **kwargs):
    from .base import seed_all as _seed_all

    return _seed_all(*args, **kwargs)


__all__ = ["seed_all", "registry"]
