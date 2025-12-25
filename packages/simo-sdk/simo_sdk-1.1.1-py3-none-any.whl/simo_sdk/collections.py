from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import Category, Component, Zone, User


class ComponentQuery:
    def __init__(self, items: list[Component]):
        self._items = list(items)

    def __iter__(self):
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, idx):
        return self._items[idx]

    def order_by(self, *fields: str):
        items = list(self._items)
        if not fields:
            fields = ("id",)

        def key_for(field: str):
            reverse = False
            if field.startswith("-"):
                reverse = True
                field = field[1:]

            def _get(obj: Component):
                v = getattr(obj, field, None)
                # Keep sort stable when values are None.
                return (v is None, v)

            return _get, reverse

        # Apply multi-field ordering like Django: last key first.
        for f in reversed(fields):
            getter, rev = key_for(f)
            items.sort(key=getter, reverse=rev)
        return ComponentQuery(items)


class UserQuery:
    def __init__(self, items: list[User]):
        self._items = list(items)

    def __iter__(self):
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, idx):
        return self._items[idx]

    def order_by(self, *fields: str):
        items = list(self._items)
        if not fields:
            fields = ("id",)

        def key_for(field: str):
            reverse = False
            if field.startswith("-"):
                reverse = True
                field = field[1:]

            def _get(obj: User):
                v = getattr(obj, field, None)
                return (v is None, v)

            return _get, reverse

        for f in reversed(fields):
            getter, rev = key_for(f)
            items.sort(key=getter, reverse=rev)
        return UserQuery(items)


@dataclass
class Zones:
    _by_id: dict[int, Zone]

    def __getitem__(self, key: int | str) -> Zone:
        if isinstance(key, int):
            return self._by_id[key]
        key_lower = key.strip().lower()
        for z in self._by_id.values():
            if z.name.strip().lower() == key_lower:
                return z
        raise KeyError(key)

    def all(self) -> list[Zone]:
        return list(self._by_id.values())


@dataclass
class Categories:
    _by_id: dict[int, Category]

    def __getitem__(self, key: int | str) -> Category:
        if isinstance(key, int):
            return self._by_id[key]
        key_lower = key.strip().lower()
        for c in self._by_id.values():
            if c.name.strip().lower() == key_lower:
                return c
        raise KeyError(key)

    def all(self) -> list[Category]:
        return list(self._by_id.values())


class Components:
    def __init__(self, store, zones: Zones, categories: Categories):
        self._store = store
        self._zones = zones
        self._categories = categories

    def __getitem__(self, component_id: int) -> Component:
        return self._store.components[int(component_id)]

    def filter(
        self,
        *,
        name: str | None = None,
        base_type: str | None = None,
        zone: int | str | Zone | None = None,
        category: int | str | Category | None = None,
    ) -> ComponentQuery:
        zone_id = None
        if zone is not None:
            if isinstance(zone, Zone):
                zone_id = zone.id
            elif isinstance(zone, int):
                zone_id = zone
            else:
                zone_id = self._zones[zone].id

        category_id = None
        if category is not None:
            if isinstance(category, Category):
                category_id = category.id
            elif isinstance(category, int):
                category_id = category
            else:
                category_id = self._categories[category].id

        name_norm = name.strip().lower() if name else None

        out: list[Component] = []
        for c in self._store.components.values():
            if name_norm and name_norm not in c.name.strip().lower():
                continue
            if base_type and (c.base_type != base_type):
                continue
            if zone_id is not None and c.zone_id != zone_id:
                continue
            if category_id is not None and c.category_id != category_id:
                continue
            out.append(c)
        out.sort(key=lambda x: x.id)
        return ComponentQuery(out)


class Users:
    def __init__(self, store, *, current_user_id: int):
        self._store = store
        self._current_user_id = int(current_user_id)

    @property
    def me(self) -> User:
        for u in self._store.users.values():
            if u.user_id == self._current_user_id:
                return u
        raise KeyError('me')

    def __getitem__(self, instance_user_id: int) -> User:
        return self._store.users[int(instance_user_id)]

    def filter(
        self,
        *,
        name: str | None = None,
        email: str | None = None,
        is_active: bool | None = None,
        at_home: bool | None = None,
    ) -> UserQuery:
        name_norm = name.strip().lower() if name else None
        email_norm = email.strip().lower() if email else None

        out: list[User] = []
        for u in self._store.users.values():
            if name_norm and (not u.name or name_norm not in u.name.strip().lower()):
                continue
            if email_norm and (not u.email or u.email.strip().lower() != email_norm):
                continue
            if is_active is not None and u.is_active != is_active:
                continue
            if at_home is not None and u.at_home != at_home:
                continue
            out.append(u)
        out.sort(key=lambda x: x.id)
        return UserQuery(out)
