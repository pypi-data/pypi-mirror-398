from __future__ import annotations

import atexit
import os
import threading
import time
from typing import Any

from .collections import Categories, Components, Users, Zones
from .exceptions import BootstrapError
from .mqtt import MqttClient, MqttConfig
from .rest import RestClient
from .store import Store
from .sun import LocalSun


class SIMOClient:
    """SIMO.io client for controlling a smart home."""

    _instances: dict[tuple[str, str, str], "SIMOClient"] = {}

    def __new__(cls, *, url: str, secret_key: str, instance: str):
        key = (url.rstrip("/"), secret_key, instance)
        existing = cls._instances.get(key)
        if existing is not None:
            return existing
        obj = super().__new__(cls)
        cls._instances[key] = obj
        return obj

    def __init__(
        self,
        *,
        url: str,
        secret_key: str,
        instance: str,
        verify_ssl: bool | str | None = None,
    ):
        if getattr(self, "_initialized", False):
            return

        self._rest = RestClient(
            base_url=url,
            secret_key=secret_key,
            instance_slug=None,
            verify_ssl=verify_ssl,
        )
        whoami = self._rest.whoami(instance=instance)

        selected = whoami.get("selected_instance") or {}
        mqtt_info = whoami.get("mqtt") or {}
        user_info = whoami.get("user") or {}

        try:
            self._user_id = int(user_info["id"])
            self._user_email = str(user_info["email"])
            self._instance_slug = str(selected["slug"])
            self._instance_uid = str(selected["uid"])
        except Exception as e:
            raise BootstrapError(f"Invalid whoami response: {e}") from e

        self._rest.instance_slug = self._instance_slug

        self._mqtt = MqttClient(
            MqttConfig(
                host=str(mqtt_info.get("host") or ""),
                port=int(mqtt_info.get("port") or 1883),
                tls=bool(mqtt_info.get("tls") or False),
                verify_ssl=False if self._rest.verify_ssl is False else True,
                transport=str(mqtt_info.get('transport') or 'tcp'),
                path=str(mqtt_info.get('path') or '/mqtt/'),
                username=self._user_email,
                password=secret_key,
            )
        )
        self._mqtt.add_feed_handler(self._on_feed_event)
        self._mqtt_loop_started = False
        self._debug_events = os.environ.get('SIMO_SDK_DEBUG_EVENTS', '').strip().lower() in (
            '1', 'true', 'yes', 'on'
        )
        self._users_refresh_lock = threading.Lock()
        self._users_last_refresh = 0.0
        self._users_base_cache: dict[int, dict[str, Any]] | None = None
        self._users_base_cache_ts = 0.0

        self._store = Store(simo=self)
        self.zones = Zones(self._store.zones)
        self.categories = Categories(self._store.categories)
        self.components = Components(self._store, self.zones, self.categories)
        self.users = Users(self._store, current_user_id=self._user_id)

        # Initial load.
        self._sync()

        # Common helpers.
        settings = self._rest.get_settings()
        self.sun = LocalSun(
            location=settings.get("location"),
            timezone_name=settings.get("timezone"),
        )
        self.main_state = self._get_component_or_none(settings.get("main_state"))
        self.weather = self._get_component_or_none(settings.get("weather"))

        # Live updates.
        self._mqtt_warned = False
        self._mqtt_connected_logged = False
        self._start_mqtt_loop()

        atexit.register(self._mqtt.disconnect)
        self._initialized = True

    def _get_component_or_none(self, component_id) -> Any:
        try:
            component_id = int(component_id)
        except Exception:
            return None
        if component_id <= 0:
            return None
        try:
            return self.components[component_id]
        except Exception:
            try:
                data = self._rest.get_component(component_id)
            except Exception:
                return None
            self._store.upsert_component(data)
            try:
                return self.components[component_id]
            except Exception:
                return None

    def _sync(self) -> None:
        for z in self._rest.list_zones():
            self._store.upsert_zone(z)
        for c in self._rest.list_categories():
            self._store.upsert_category(c)
        for comp in self._rest.list_components():
            self._store.upsert_component(comp)

        for iu in self._rest.list_instance_users():
            self._store.upsert_user(iu)

        # Fill missing name/email from global users list (some hubs may emit
        # InstanceUser events without duplicating user identity fields).
        missing_identity = [
            u for u in self._store.users.values()
            if u.user_id is not None and (not u.email or not u.name)
        ]
        if missing_identity:
            users_map: dict[int, dict[str, Any]] = {}
            for u in self._rest.list_users():
                try:
                    uid = int(u.get('id'))
                except Exception:
                    continue
                users_map[uid] = u

            for iu in missing_identity:
                try:
                    base = users_map.get(int(iu.user_id))
                except Exception:
                    base = None
                if not base:
                    continue
                if not iu.email:
                    iu.email = base.get('email')
                if not iu.name:
                    iu.name = base.get('name')

    def _refresh_users_if_needed(self, *, min_interval_s: float = 2.0) -> None:
        now = time.time()
        if now - self._users_last_refresh < min_interval_s:
            return
        with self._users_refresh_lock:
            now = time.time()
            if now - self._users_last_refresh < min_interval_s:
                return
            self._users_last_refresh = now
            for iu in self._rest.list_instance_users():
                self._store.upsert_user(iu)

    def _ensure_user_identity(self, iu) -> None:
        if not iu or not getattr(iu, 'user_id', None):
            return
        if iu.email and iu.name:
            return

        now = time.time()
        if self._users_base_cache is None or now - self._users_base_cache_ts > 30:
            users_map: dict[int, dict[str, Any]] = {}
            for u in self._rest.list_users():
                try:
                    uid = int(u.get('id'))
                except Exception:
                    continue
                users_map[uid] = u
            self._users_base_cache = users_map
            self._users_base_cache_ts = now

        base = self._users_base_cache.get(int(iu.user_id)) if self._users_base_cache else None
        if not base:
            return
        if not iu.email:
            iu.email = base.get('email')
        if not iu.name:
            iu.name = base.get('name')

    def _connect_mqtt_once(self) -> None:
        self._mqtt.connect()
        self._mqtt.subscribe_control_responses(user_id=self._user_id)
        self._mqtt.subscribe_feed(user_id=self._user_id, instance_uid=self._instance_uid)

    def _start_mqtt_loop(self) -> None:
        if self._mqtt_loop_started:
            return
        self._mqtt_loop_started = True
        try:
            self._connect_mqtt_once()
            self._mqtt_loop_started = False
            return
        except Exception as e:
            if not self._mqtt_warned:
                self._mqtt_warned = True
                print(f"SIMO.io SDK: MQTT connection failed, retrying... ({e})")

        def _loop():
            try:
                while True:
                    if self._mqtt.is_connected:
                        if self._mqtt_warned and not self._mqtt_connected_logged:
                            self._mqtt_connected_logged = True
                            print("SIMO.io SDK: MQTT connected")
                        return
                    try:
                        self._connect_mqtt_once()
                    except Exception:
                        time.sleep(2)
                        continue
            finally:
                self._mqtt_loop_started = False

        threading.Thread(target=_loop, daemon=True).start()

    def _call_component(
        self,
        component_id: int,
        method: str,
        *,
        subcomponent_id: int | None = None,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> None:
        if self._mqtt.is_connected:
            self._mqtt.call_component_method(
                user_id=self._user_id,
                instance_uid=self._instance_uid,
                component_id=int(component_id),
                subcomponent_id=subcomponent_id,
                method=method,
                args=args,
                kwargs=kwargs,
            )
            return

        # Ensure MQTT eventually connects in the background.
        # This is a no-op if already connected or a loop is running.
        self._start_mqtt_loop()

        self._rest.call_component_method(
            component_id=int(component_id),
            method=method,
            subcomponent_id=subcomponent_id,
            args=args,
            kwargs=kwargs,
        )

    def notify(
        self,
        *,
        users: list[Any],
        severity: str,
        title: str,
        body: str | None = None,
        component: Any | None = None,
    ) -> None:
        instance_user_ids = []
        for u in users:
            try:
                instance_user_ids.append(int(u.id))
            except Exception:
                continue
        component_id = None
        if component is not None:
            try:
                component_id = int(component.id)
            except Exception:
                component_id = None
        self._rest.send_notification(
            severity=severity,
            title=title,
            body=body,
            component_id=component_id,
            instance_user_ids=instance_user_ids,
        )

    def _on_feed_event(self, event) -> None:
        if event.instance_uid != self._instance_uid:
            return

        if event.model == "Component":
            comp = self._store.upsert_component({"id": event.obj_id, **dict(event.payload)})
            dirty = set((event.payload.get("dirty_fields") or {}).keys())
            if dirty:
                payload = dict(event.payload or {})
                actor_type = payload.get('actor_type')
                actor_iuser_id = payload.get('actor_instance_user_id')
                actor_user_id = payload.get('actor_user_id')

                if not actor_type and actor_iuser_id is not None:
                    actor_type = 'user'
                actor_type = str(actor_type or 'system')

                actor_user = None
                if actor_type == 'user':
                    if actor_user_id is not None:
                        try:
                            actor_user_id_int = int(actor_user_id)
                        except Exception:
                            actor_user_id_int = None
                    else:
                        actor_user_id_int = None

                    if actor_iuser_id is not None:
                        try:
                            actor_user = self.users[int(actor_iuser_id)]
                        except Exception:
                            actor_user = None
                    if actor_user is None and actor_iuser_id is not None:
                        try:
                            self._refresh_users_if_needed()
                            actor_user = self.users[int(actor_iuser_id)]
                        except Exception:
                            actor_user = None

                    if actor_user is None and actor_user_id_int is not None:
                        for u in self._store.users.values():
                            if u.user_id == actor_user_id_int:
                                actor_user = u
                                break

                    if actor_user is not None and actor_user_id_int is not None and actor_user.user_id is None:
                        actor_user.user_id = actor_user_id_int
                    self._ensure_user_identity(actor_user)

                if actor_type != 'user':
                    actor_user = None

                from .models import Actor
                actor = Actor(type=actor_type, user=actor_user)

                if self._debug_events:
                    print(
                        "SIMO.io SDK DEBUG event:",
                        "model=Component",
                        f"id={event.obj_id}",
                        f"dirty={sorted(dirty)}",
                        f"actor_type={payload.get('actor_type')}",
                        f"actor_instance_user_id={payload.get('actor_instance_user_id')}",
                        f"actor_user_id={payload.get('actor_user_id')}",
                        f"actor_resolved={actor.type}:{getattr(actor.user, 'id', None)}",
                    )

                comp._emit_change(dirty, actor)

        if event.model == 'InstanceUser':
            iu = self._store.upsert_user({"id": event.obj_id, **dict(event.payload)})
            dirty = set((event.payload.get('dirty_fields') or {}).keys())
            if dirty:
                iu._emit_change(dirty)
