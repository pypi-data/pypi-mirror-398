from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable


OnChangeCallback = Callable[..., None]


@dataclass(frozen=True)
class Actor:
    type: str  # 'user' | 'device' | 'system' | 'ai'
    user: "User" | None


@dataclass
class Zone:
    id: int
    name: str


@dataclass
class Category:
    id: int
    name: str


@dataclass
class Component:
    _simo: Any = field(repr=False)

    id: int = 0
    data: dict[str, Any] = field(default_factory=dict)
    name: str = ""
    icon: str | None = None
    base_type: str | None = None
    zone_id: int | None = None
    category_id: int | None = None
    gateway_id: int | None = None
    show_in_app: bool | None = None
    controller_uid: str | None = None

    last_change: float | None = None
    last_modified: float | None = None
    read_only: bool | None = None
    masters_only: bool | None = None
    slaves: list[int] = field(default_factory=list)
    app_widget: dict[str, Any] = field(default_factory=dict)
    info: Any = None

    value: Any = None
    value_units: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    alive: bool | None = None
    error_msg: str | None = None
    alarm_category: str | None = None
    arm_status: str | None = None
    controller_methods: list[str] = field(default_factory=list)
    battery_level: int | None = None

    _on_change: list[tuple[set[str], OnChangeCallback]] = field(default_factory=list, repr=False)
    _change_cond: threading.Condition = field(default_factory=threading.Condition, repr=False)
    _change_seq: int = field(default=0, repr=False)
    _last_dirty_fields: set[str] = field(default_factory=set, repr=False)

    def refresh(self) -> "Component":
        data = self._simo._rest.get_component(self.id)
        self._simo._store.upsert_component(data)
        return self

    # --- control ---------------------------------------------------------
    def call(self, method: str, *args: Any, **kwargs: Any) -> None:
        self._simo._call_component(self.id, method, args=list(args), kwargs=kwargs)

    def __getattr__(self, name: str):
        if name.startswith('_'):
            raise AttributeError(name)
        if name in (self.controller_methods or []):
            def _method(*args: Any, **kwargs: Any) -> None:
                self.call(name, *args, **kwargs)
            return _method
        raise AttributeError(name)

    def slave(self, instance_id: int):
        return SubComponent(parent=self, sub_id=int(instance_id))

    def send(self, value: Any) -> None:
        self.call("send", value)

    def turn_on(self) -> None:
        self.call("turn_on")

    def turn_off(self) -> None:
        self.call("turn_off")

    def toggle(self) -> None:
        self.call("toggle")

    def open(self) -> None:
        self.call("open")

    def close(self) -> None:
        self.call("close")

    # --- realtime --------------------------------------------------------
    def on_change(self, callback: OnChangeCallback, *, fields: list[str] | None = None) -> None:
        self._on_change.clear()
        if not callback:
            return
        watched = set(fields or ["value"])  # default most common
        self._on_change.append((watched, callback))

    def wait_for(
        self,
        *,
        fields: list[str] | None = None,
        timeout: float = 10.0,
    ) -> bool:
        """Block until a matching realtime update arrives.

        This never polls REST; it only waits for MQTT feed updates.

        Returns:
        - True if an update arrived within timeout.
        - False on timeout.
        """
        watched = set(fields or ["value"])
        deadline = time.monotonic() + float(timeout)
        with self._change_cond:
            start_seq = self._change_seq
            while True:
                if self._change_seq != start_seq and self._last_dirty_fields.intersection(watched):
                    return True
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                self._change_cond.wait(timeout=remaining)

    def _emit_change(self, dirty_fields: set[str], actor: Actor | None = None) -> None:
        with self._change_cond:
            self._last_dirty_fields = set(dirty_fields)
            self._change_seq += 1
            self._change_cond.notify_all()
        for watched, cb in list(self._on_change):
            if watched.intersection(dirty_fields):
                try:
                    import inspect
                    try:
                        no_args = len(inspect.getfullargspec(cb).args)
                        if inspect.ismethod(cb):
                            no_args -= 1
                    except Exception:
                        no_args = 1
                    if no_args <= 0:
                        cb()
                    elif no_args == 1:
                        cb(self)
                    else:
                        cb(self, actor)
                except Exception:
                    import traceback, sys
                    print('SIMO.io SDK: on_change callback failed:', file=sys.stderr)
                    print(traceback.format_exc(), file=sys.stderr)


@dataclass
class SubComponent:
    parent: Component
    sub_id: int

    def call(self, method: str, *args: Any, **kwargs: Any) -> None:
        self.parent._simo._call_component(
            self.parent.id,
            method,
            subcomponent_id=self.sub_id,
            args=list(args),
            kwargs=kwargs,
        )

    def __getattr__(self, name: str):
        if name.startswith('_'):
            raise AttributeError(name)
        if name in (self.parent.controller_methods or []):
            def _method(*args: Any, **kwargs: Any) -> None:
                self.call(name, *args, **kwargs)
            return _method
        raise AttributeError(name)

    def send(self, value: Any) -> None:
        self.call("send", value)

    def turn_on(self) -> None:
        self.call("turn_on")

    def turn_off(self) -> None:
        self.call("turn_off")

    def toggle(self) -> None:
        self.call("toggle")

    def open(self) -> None:
        self.call("open")

    def close(self) -> None:
        self.call("close")
@dataclass
class User:
    _simo: Any = field(repr=False)
    id: int = 0  # InstanceUser id

    data: dict[str, Any] = field(default_factory=dict)

    user_id: int | None = None
    email: str | None = None
    name: str | None = None

    role_id: int | None = None
    role_name: str | None = None
    role_is_owner: bool | None = None
    role_is_superuser: bool | None = None
    role_can_manage_users: bool | None = None
    role_is_person: bool | None = None

    is_active: bool | None = None
    at_home: bool | None = None
    last_seen: float | None = None
    last_seen_location: str | None = None
    last_seen_speed_kmh: float | None = None
    phone_on_charge: bool | None = None

    _on_change: list[tuple[set[str], OnChangeCallback]] = field(default_factory=list, repr=False)
    _change_cond: threading.Condition = field(default_factory=threading.Condition, repr=False)
    _change_seq: int = field(default=0, repr=False)
    _last_dirty_fields: set[str] = field(default_factory=set, repr=False)

    def __str__(self) -> str:
        if self.name:
            return str(self.name)
        if self.email:
            return str(self.email)
        return f"User {self.id}"

    def on_change(self, callback: OnChangeCallback, *, fields: list[str] | None = None) -> None:
        self._on_change.clear()
        if not callback:
            return
        watched = set(fields or ["at_home"])  # most common
        self._on_change.append((watched, callback))

    def wait_for(self, *, fields: list[str] | None = None, timeout: float = 10.0) -> bool:
        watched = set(fields or ["at_home"])
        deadline = time.monotonic() + float(timeout)
        with self._change_cond:
            start_seq = self._change_seq
            while True:
                if self._change_seq != start_seq and self._last_dirty_fields.intersection(watched):
                    return True
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                self._change_cond.wait(timeout=remaining)

    def _emit_change(self, dirty_fields: set[str]) -> None:
        with self._change_cond:
            self._last_dirty_fields = set(dirty_fields)
            self._change_seq += 1
            self._change_cond.notify_all()
        for watched, cb in list(self._on_change):
            if watched.intersection(dirty_fields):
                try:
                    import inspect
                    try:
                        no_args = len(inspect.getfullargspec(cb).args)
                        if inspect.ismethod(cb):
                            no_args -= 1
                    except Exception:
                        no_args = 1
                    if no_args <= 0:
                        cb()
                    else:
                        cb(self)
                except Exception:
                    import traceback, sys
                    print('SIMO.io SDK: user on_change callback failed:', file=sys.stderr)
                    print(traceback.format_exc(), file=sys.stderr)

    def notify(
        self,
        *,
        severity: str,
        title: str,
        body: str | None = None,
        component: "Component" | None = None,
    ) -> None:
        self._simo.notify(
            users=[self],
            severity=severity,
            title=title,
            body=body,
            component=component,
        )
