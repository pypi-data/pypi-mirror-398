from __future__ import annotations

import ipaddress
import warnings
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from urllib3.exceptions import InsecureRequestWarning

from .exceptions import RestError


def _default_verify_ssl(base_url: str) -> bool:
    try:
        parsed = urlparse(base_url)
    except Exception:
        return True

    if (parsed.scheme or '').lower() != 'https':
        return True

    host = (parsed.hostname or '').strip().lower()
    if not host:
        return True

    if host in ('localhost', '127.0.0.1', '::1'):
        return False

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return not (host.endswith('.local') or host.endswith('.lan'))
    return not (ip.is_private or ip.is_loopback or ip.is_link_local)


@dataclass
class RestClient:
    base_url: str
    secret_key: str
    instance_slug: str | None = None
    timeout: float = 30.0
    user_agent: str = 'SIMO.io-SDK/0.2'
    verify_ssl: bool | str | None = None

    def __post_init__(self) -> None:
        self._session = requests.Session()
        if self.verify_ssl is None:
            self.verify_ssl = _default_verify_ssl(self.base_url)
        if self.verify_ssl is False:
            warnings.filterwarnings('ignore', category=InsecureRequestWarning)
        self._session.headers.update(
            {
                'Secret': self.secret_key,
                'User-Agent': self.user_agent,
                'Accept': 'application/json',
            }
        )

    def _require_instance_slug(self) -> str:
        if not self.instance_slug:
            raise RestError('instance is required')
        return self.instance_slug

    def _api_base(self) -> str:
        slug = self._require_instance_slug().strip('/')
        return urljoin(self.base_url.rstrip('/') + '/', f'api/{slug}/')

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = urljoin(self._api_base(), path.lstrip('/'))
        timeout = kwargs.pop('timeout', self.timeout)
        try:
            resp = self._session.request(
                method=method,
                url=url,
                timeout=timeout,
                verify=self.verify_ssl,
                **kwargs,
            )
        except requests.RequestException as e:
            raise RestError(str(e)) from e

        if resp.status_code >= 400:
            raise RestError(f'HTTP {resp.status_code}: {resp.text}')
        if not resp.content:
            return None
        try:
            return resp.json()
        except Exception:
            return resp.text

    def _request_root(self, method: str, path: str, **kwargs: Any) -> Any:
        url = urljoin(self.base_url.rstrip('/') + '/', path.lstrip('/'))
        timeout = kwargs.pop('timeout', self.timeout)
        try:
            resp = self._session.request(
                method=method,
                url=url,
                timeout=timeout,
                verify=self.verify_ssl,
                **kwargs,
            )
        except requests.RequestException as e:
            raise RestError(str(e)) from e

        if resp.status_code >= 400:
            raise RestError(f'HTTP {resp.status_code}: {resp.text}')
        if not resp.content:
            return None
        try:
            return resp.json()
        except Exception:
            return resp.text

    def get(self, path: str, **kwargs: Any) -> Any:
        return self._request('GET', path, **kwargs)

    def post(self, path: str, json: Any | None = None, **kwargs: Any) -> Any:
        return self._request('POST', path, json=json, **kwargs)

    def whoami(self, *, instance: str | None = None) -> dict[str, Any]:
        params = {}
        if instance:
            params['instance'] = instance
        data = self._request_root('GET', 'users/whoami/', params=params)
        if not isinstance(data, dict):
            raise RestError('Unexpected response for whoami')
        return data

    def get_settings(self) -> dict[str, Any]:
        data = self.get('core/settings/')
        if not isinstance(data, dict):
            raise RestError('Unexpected response for core/settings')
        return data

    @staticmethod
    def _unwrap_list(data: Any, *, label: str) -> list[dict[str, Any]]:
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if isinstance(data, dict) and isinstance(data.get('results'), list):
            return [x for x in data['results'] if isinstance(x, dict)]
        raise RestError(f'Unexpected response for {label}')

    def list_zones(self) -> list[dict[str, Any]]:
        return self._unwrap_list(self.get('core/zones/'), label='core/zones')

    def list_categories(self) -> list[dict[str, Any]]:
        return self._unwrap_list(self.get('core/categories/'), label='core/categories')

    def list_components(self) -> list[dict[str, Any]]:
        return self._unwrap_list(self.get('core/components/'), label='core/components')

    def list_instance_users(self) -> list[dict[str, Any]]:
        return self._unwrap_list(self.get('users/instance-users/'), label='users/instance-users')

    def list_users(self) -> list[dict[str, Any]]:
        return self._unwrap_list(self.get('users/users/'), label='users/users')

    def send_notification(
        self,
        *,
        severity: str,
        title: str,
        body: str | None = None,
        component_id: int | None = None,
        instance_user_ids: list[int] | None = None,
    ) -> Any:
        payload: dict[str, Any] = {
            'severity': severity,
            'title': title,
            'body': body,
            'instance_user_ids': instance_user_ids or [],
        }
        if component_id is not None:
            payload['component_id'] = int(component_id)
        return self.post('notifications/send/', json=payload)

    def get_component(self, component_id: int) -> dict[str, Any]:
        data = self.get(f'core/components/{int(component_id)}/')
        if not isinstance(data, dict):
            raise RestError('Unexpected response for core/components/<id>')
        return data

    def call_component_method(
        self,
        component_id: int,
        method: str,
        *,
        subcomponent_id: int | None = None,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        if not method or method.startswith('_'):
            raise RestError('Invalid method name')
        if args is not None and kwargs is not None and args and kwargs:
            raise RestError('Provide either args or kwargs (not both)')

        if kwargs is not None and kwargs:
            payload: dict[str, Any] = {method: kwargs}
        else:
            payload = {method: args or []}

        if subcomponent_id is not None:
            payload = {**payload, 'id': int(subcomponent_id)}
            return self.post(f'core/components/{int(component_id)}/subcomponent/', json=payload)
        return self.post(f'core/components/{int(component_id)}/controller/', json=payload)
