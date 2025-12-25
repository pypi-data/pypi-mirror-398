from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import Category, Component, Zone, User


@dataclass
class Store:
    simo: Any
    zones: dict[int, Zone] = field(default_factory=dict)
    categories: dict[int, Category] = field(default_factory=dict)
    components: dict[int, Component] = field(default_factory=dict)
    users: dict[int, User] = field(default_factory=dict)

    def upsert_zone(self, data: dict[str, Any]) -> Zone:
        zone_id = int(data.get("id"))
        zone = self.zones.get(zone_id) or Zone(id=zone_id, name=str(data.get("name") or ""))
        zone.name = str(data.get("name") or zone.name)
        self.zones[zone_id] = zone
        return zone

    def upsert_category(self, data: dict[str, Any]) -> Category:
        cat_id = int(data.get("id"))
        cat = self.categories.get(cat_id) or Category(id=cat_id, name=str(data.get("name") or ""))
        cat.name = str(data.get("name") or cat.name)
        self.categories[cat_id] = cat
        return cat

    def upsert_component(self, data: dict[str, Any]) -> Component:
        incoming = dict(data or {})
        for k in ("timestamp", "dirty_fields", "obj_ct_pk", "obj_pk"):
            incoming.pop(k, None)

        comp_id = int(incoming.get("id"))
        comp = self.components.get(comp_id)
        if not comp:
            comp = Component(_simo=self.simo, id=comp_id)
            self.components[comp_id] = comp

        comp.data.update(incoming)

        if "name" in incoming:
            comp.name = str(incoming.get("name") or "")
        if "icon" in incoming:
            comp.icon = incoming.get("icon")
        if "base_type" in incoming:
            comp.base_type = incoming.get("base_type")
        if "gateway" in incoming:
            try:
                comp.gateway_id = int(incoming.get("gateway")) if incoming.get("gateway") is not None else None
            except Exception:
                pass
        if "zone" in incoming:
            comp.zone_id = int(incoming.get("zone")) if incoming.get("zone") is not None else None
        if "category" in incoming:
            comp.category_id = int(incoming.get("category")) if incoming.get("category") is not None else None
        if "show_in_app" in incoming:
            comp.show_in_app = incoming.get("show_in_app")
        if "controller_uid" in incoming:
            comp.controller_uid = incoming.get("controller_uid")

        if "last_change" in incoming:
            comp.last_change = incoming.get("last_change")
        if "last_modified" in incoming:
            comp.last_modified = incoming.get("last_modified")
        if "read_only" in incoming:
            comp.read_only = incoming.get("read_only")
        if "masters_only" in incoming:
            comp.masters_only = incoming.get("masters_only")
        if "slaves" in incoming and isinstance(incoming.get("slaves"), list):
            try:
                comp.slaves = [int(x) for x in incoming.get("slaves")]
            except Exception:
                pass
        if "app_widget" in incoming and isinstance(incoming.get("app_widget"), dict):
            comp.app_widget = incoming.get("app_widget")
        if "info" in incoming:
            comp.info = incoming.get("info")

        if "value" in incoming:
            comp.value = incoming.get("value")
        if "value_units" in incoming:
            comp.value_units = incoming.get("value_units")
        if "meta" in incoming and isinstance(incoming.get("meta"), dict):
            comp.meta = incoming.get("meta")
        if "config" in incoming and isinstance(incoming.get("config"), dict):
            comp.config = incoming.get("config")
        if "alive" in incoming:
            comp.alive = incoming.get("alive")
        if "error_msg" in incoming:
            comp.error_msg = incoming.get("error_msg")
        if "alarm_category" in incoming:
            comp.alarm_category = incoming.get("alarm_category")
        if "arm_status" in incoming:
            comp.arm_status = incoming.get("arm_status")
        if "controller_methods" in incoming and isinstance(incoming.get("controller_methods"), list):
            comp.controller_methods = [str(m) for m in incoming.get("controller_methods")]
        if "battery_level" in incoming:
            try:
                comp.battery_level = int(incoming.get("battery_level")) if incoming.get("battery_level") is not None else None
            except Exception:
                pass

        return comp

    def upsert_user(self, data: dict[str, Any]) -> User:
        incoming = dict(data or {})
        for k in ('timestamp', 'dirty_fields', 'obj_ct_pk', 'obj_pk'):
            incoming.pop(k, None)

        iu_id = int(incoming.get('id'))
        user = self.users.get(iu_id)
        if not user:
            user = User(_simo=self.simo, id=iu_id)
            self.users[iu_id] = user

        user.data.update(incoming)

        # REST endpoint returns flat fields; MQTT InstanceUser events can be
        # partial and/or use nested structures.
        if 'user_id' in incoming:
            user.user_id = incoming.get('user_id')
        if 'email' in incoming:
            user.email = incoming.get('email')
        if 'name' in incoming:
            user.name = incoming.get('name')

        nested_user = incoming.get('user')
        if isinstance(nested_user, int):
            if user.user_id is None:
                user.user_id = nested_user
        elif isinstance(nested_user, dict):
            if user.user_id is None and 'id' in nested_user:
                user.user_id = nested_user.get('id')
            if user.email is None and 'email' in nested_user:
                user.email = nested_user.get('email')
            if user.name is None and 'name' in nested_user:
                user.name = nested_user.get('name')

        if 'role_id' in incoming:
            user.role_id = incoming.get('role_id')
        if 'role_name' in incoming:
            user.role_name = incoming.get('role_name')
        if 'role_is_owner' in incoming:
            user.role_is_owner = incoming.get('role_is_owner')
        if 'role_is_superuser' in incoming:
            user.role_is_superuser = incoming.get('role_is_superuser')
        if 'role_can_manage_users' in incoming:
            user.role_can_manage_users = incoming.get('role_can_manage_users')
        if 'role_is_person' in incoming:
            user.role_is_person = incoming.get('role_is_person')

        nested_role = incoming.get('role')
        if isinstance(nested_role, int):
            if user.role_id is None:
                user.role_id = nested_role
        elif isinstance(nested_role, dict):
            if user.role_id is None and 'id' in nested_role:
                user.role_id = nested_role.get('id')
            if user.role_name is None and 'name' in nested_role:
                user.role_name = nested_role.get('name')
            if user.role_is_owner is None and 'is_owner' in nested_role:
                user.role_is_owner = nested_role.get('is_owner')
            if user.role_is_superuser is None and 'is_superuser' in nested_role:
                user.role_is_superuser = nested_role.get('is_superuser')
            if user.role_can_manage_users is None and 'can_manage_users' in nested_role:
                user.role_can_manage_users = nested_role.get('can_manage_users')
            if user.role_is_person is None and 'is_person' in nested_role:
                user.role_is_person = nested_role.get('is_person')

        if 'is_active' in incoming:
            user.is_active = incoming.get('is_active')
        if 'at_home' in incoming:
            user.at_home = incoming.get('at_home')
        if 'last_seen' in incoming:
            user.last_seen = incoming.get('last_seen')
        if 'last_seen_location' in incoming:
            user.last_seen_location = incoming.get('last_seen_location')
        if 'last_seen_speed_kmh' in incoming:
            user.last_seen_speed_kmh = incoming.get('last_seen_speed_kmh')
        if 'phone_on_charge' in incoming:
            user.phone_on_charge = incoming.get('phone_on_charge')

        return user
