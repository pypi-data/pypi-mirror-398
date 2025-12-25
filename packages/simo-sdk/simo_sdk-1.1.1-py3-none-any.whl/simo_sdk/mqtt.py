from __future__ import annotations

import json
import ssl
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable

import paho.mqtt.client as mqtt

from .exceptions import MqttError
from .types import FeedEvent


FeedHandler = Callable[[FeedEvent], None]


@dataclass
class MqttConfig:
    host: str
    port: int = 1883
    username: str | None = None
    password: str | None = None
    tls: bool = False
    verify_ssl: bool | None = None
    transport: str = 'tcp'  # 'tcp' | 'websockets'
    path: str = '/mqtt/'
    keepalive: int = 60
    client_id: str | None = None


class MqttClient:
    def __init__(self, config: MqttConfig):
        self.config = config
        self._client = mqtt.Client(
            client_id=config.client_id or "simo-sdk-" + uuid.uuid4().hex,
            transport=config.transport,
        )
        if config.username is not None:
            self._client.username_pw_set(config.username, config.password or "")
        if config.transport == 'websockets':
            try:
                self._client.ws_set_options(path=config.path)
            except Exception:
                pass
        if config.tls:
            if config.verify_ssl is False:
                self._client.tls_set(cert_reqs=ssl.CERT_NONE)
                try:
                    self._client.tls_insecure_set(True)
                except Exception:
                    pass
            else:
                self._client.tls_set()

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect
        try:
            self._client.reconnect_delay_set(min_delay=1, max_delay=30)
        except Exception:
            pass

        self._connected = threading.Event()
        self._stop = threading.Event()
        self._reconnect_lock = threading.Lock()
        self._reconnect_in_progress = False
        self._loop_started = False

        self._feed_handlers: list[FeedHandler] = []
        self._resp_lock = threading.Lock()
        self._pending: dict[str, dict[str, Any]] = {}
        self._pending_events: dict[str, threading.Event] = {}

        self._subs: list[tuple[str, int]] = []

    @property
    def is_connected(self) -> bool:
        return self._connected.is_set()

    def set_credentials(self, *, username: str, password: str) -> None:
        self.config.username = username
        self.config.password = password
        self._client.username_pw_set(username, password)

    # --- lifecycle -------------------------------------------------------
    def connect(self) -> None:
        try:
            self._client.connect(self.config.host, self.config.port, keepalive=self.config.keepalive)
        except Exception as e:
            raise MqttError(str(e)) from e
        if not self._loop_started:
            self._client.loop_start()
            self._loop_started = True
        if not self._connected.wait(timeout=10):
            raise MqttError("MQTT connect timeout")

    def disconnect(self) -> None:
        self._stop.set()
        self._connected.clear()
        try:
            self._client.loop_stop()
        except Exception:
            pass
        try:
            self._client.disconnect()
        except Exception:
            pass
        self._loop_started = False

    def add_feed_handler(self, handler: FeedHandler) -> None:
        self._feed_handlers.append(handler)

    # --- subscriptions ---------------------------------------------------
    def subscribe_feed(self, *, user_id: int, instance_uid: str) -> None:
        topic = f"SIMO/user/{int(user_id)}/feed/{instance_uid}/#"
        self._subscribe(topic, qos=0)

    def subscribe_control_responses(self, *, user_id: int) -> None:
        topic = f"SIMO/user/{int(user_id)}/control-resp/#"
        self._subscribe(topic, qos=0)

    def _subscribe(self, topic: str, qos: int) -> None:
        self._client.subscribe(topic, qos=qos)
        self._subs.append((topic, qos))

    # --- control ---------------------------------------------------------
    def call_component_method(
        self,
        *,
        user_id: int,
        instance_uid: str,
        component_id: int,
        subcomponent_id: int | None = None,
        method: str,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
        timeout: float = 10.0,
    ) -> Any:
        if not method or method.startswith("_"):
            raise MqttError("Invalid method name")
        request_id = uuid.uuid4().hex
        topic = f"SIMO/user/{int(user_id)}/control/{instance_uid}/Component/{int(component_id)}"
        payload = {
            "request_id": request_id,
            "method": method,
            "args": args or [],
            "kwargs": kwargs or {},
        }
        if subcomponent_id is not None:
            payload["subcomponent_id"] = int(subcomponent_id)

        ev = threading.Event()
        with self._resp_lock:
            self._pending_events[request_id] = ev
        self._client.publish(topic, json.dumps(payload), qos=0, retain=False)

        if not ev.wait(timeout=timeout):
            with self._resp_lock:
                self._pending_events.pop(request_id, None)
                self._pending.pop(request_id, None)
            raise MqttError("Control request timeout")

        with self._resp_lock:
            resp = self._pending.pop(request_id, None)
            self._pending_events.pop(request_id, None)
        if not isinstance(resp, dict):
            raise MqttError("Bad control response")
        if not resp.get("ok"):
            raise MqttError(resp.get("error") or "Control error")
        return resp.get("result")

    # --- mqtt callbacks --------------------------------------------------
    def _on_connect(self, client, userdata, flags, rc):
        self._connected.set()
        # Re-subscribe after reconnect
        for topic, qos in self._subs:
            try:
                client.subscribe(topic, qos=qos)
            except Exception:
                pass

    def _on_disconnect(self, client, userdata, rc):
        # rc != 0 means unexpected disconnect; paho will retry.
        if rc != 0:
            self._connected.clear()
            self._maybe_reconnect_async()

    def _maybe_reconnect_async(self) -> None:
        if self._stop.is_set():
            return
        with self._reconnect_lock:
            if self._reconnect_in_progress:
                return
            self._reconnect_in_progress = True

        def _loop():
            try:
                delay = 1.0
                while not self._stop.is_set():
                    try:
                        self._client.reconnect()
                        # on_connect will set _connected
                        return
                    except Exception:
                        time.sleep(delay)
                        delay = min(delay * 1.7, 30.0)
            finally:
                with self._reconnect_lock:
                    self._reconnect_in_progress = False

        threading.Thread(target=_loop, daemon=True).start()

    def _on_message(self, client, userdata, msg):
        topic = msg.topic or ""

        if "/control-resp/" in topic:
            self._handle_control_resp(topic, msg.payload)
            return
        if "/feed/" in topic:
            self._handle_feed(topic, msg.payload)
            return

    def _handle_control_resp(self, topic: str, payload_bytes: bytes) -> None:
        parts = topic.split("/")
        # SIMO/user/<user-id>/control-resp/<request_id>
        if len(parts) < 5:
            return
        request_id = parts[4]
        try:
            payload = json.loads(payload_bytes or b"{}")
        except Exception:
            payload = {"ok": False, "error": "Invalid JSON"}
        with self._resp_lock:
            self._pending[request_id] = payload
            ev = self._pending_events.get(request_id)
        if ev:
            ev.set()

    def _handle_feed(self, topic: str, payload_bytes: bytes) -> None:
        parts = topic.split("/")
        # SIMO/user/<user-id>/feed/<instance-uid>/<Model>/<id>
        if len(parts) < 7:
            return
        instance_uid = parts[4]
        model = parts[5]
        try:
            obj_id = int(parts[6])
        except Exception:
            return
        try:
            payload = json.loads(payload_bytes or b"{}")
        except Exception:
            return

        event = FeedEvent(model=model, obj_id=obj_id, instance_uid=instance_uid, payload=payload)
        for handler in list(self._feed_handlers):
            try:
                handler(event)
            except Exception:
                pass
