# simo-sdk

## Quick start

```python
from simo_sdk import SIMOClient

home = SIMOClient(
    url="https://hub.example.com",
    secret_key="YOUR_SIMO_IO_SECRET_KEY",
    instance="my-home",  # instance slug OR instance uid
)

light = home.components.filter(name="Main light", zone="Living Room")[0]
light.turn_on()
light.wait_for(fields=["value"], timeout=10)
print(light.value)

print(home.sun.is_night())

print(home.main_state.value)
print(home.weather.value)
```


## Install

```bash
pip install -e packages/simo-sdk
```


## SIMOClient

Type: `simo_sdk.client.SIMOClient`

```python
home = SIMOClient(url="https://hub.example.com", secret_key="...", instance="my-home")
```

Parameters:

- `url: str` – URL of your SIMO.io hub
- `secret_key: str` – your SIMO.io user secret key
- `instance: str` – instance slug or instance uid
- `verify_ssl: bool | str | None` – optional (LAN hubs with self-signed certs are supported automatically)

If MQTT is not reachable, the client keeps retrying in the background.

Attributes:

- `home.zones: simo_sdk.collections.Zones`
- `home.categories: simo_sdk.collections.Categories`
- `home.components: simo_sdk.collections.Components`
- `home.users: simo_sdk.collections.Users`
- `home.sun: simo_sdk.sun.LocalSun`
- `home.main_state: simo_sdk.models.Component | None`
- `home.weather: simo_sdk.models.Component | None`


## home.sun

Type: `simo_sdk.sun.LocalSun`

Use this for time-of-day logic (sunrise/sunset/night checks) in automations.

Methods:

- `now() -> datetime`
  - Current time in the instance timezone (if available).
- `is_night(localdatetime=None) -> bool`
  - `True` when current time is outside sunrise–sunset.
- `get_sunrise_time(localdatetime=None) -> datetime`
- `get_sunset_time(localdatetime=None) -> datetime`
- `seconds_to_sunrise(localdatetime=None) -> float`
- `seconds_to_sunset(localdatetime=None) -> float`

Examples:

```python
if home.sun.is_night():
    print("It's dark")

print("sunrise:", home.sun.get_sunrise_time(home.sun.now()))
print("sunset:", home.sun.get_sunset_time(home.sun.now()))
```


## home.main_state

Type: `simo_sdk.models.Component | None`

This is the SIMO.io "Main State" component (default name: "Main State").

It represents a single global state for the whole smart home and is meant to be used by automations as a shared context.

Common states include (by default):

- `morning`
- `day`
- `evening`
- `night`
- `sleep`
- `away`
- `vacation`

Usage:

```python
state = home.main_state.value if home.main_state else None
if state in ("away", "vacation"):
    print("Skip some automations")

# change state (use configured state slugs)
if home.main_state:
    home.main_state.send("sleep")
```


## home.weather

Type: `simo_sdk.models.Component | None`

This is the SIMO.io "Weather" component.

It provides current outdoor weather information for your instance location.
In automations it is typically used to check:

- temperature / feels_like
- wind
- rain/snow indicators
- general condition

Usage:

```python
if home.weather:
    w = home.weather.value or {}
    temp = (w.get("main") or {}).get("temp")
    feels = (w.get("main") or {}).get("feels_like")
    condition = ((w.get("weather") or [{}])[0] or {}).get("main")
    print(temp, feels, condition)
```

Typical `home.weather.value` shape (example):

```python
{
  "dt": 1766408550,
  "id": 597881,
  "cod": 200,
  "sys": {
    "id": 1880,
    "type": 1,
    "sunset": 1766411955,
    "country": "LT",
    "sunrise": 1766386119
  },
  "base": "stations",
  "main": {
    "temp": 4.33,
    "humidity": 88,
    "pressure": 1023,
    "temp_max": 4.33,
    "temp_min": 4.33,
    "sea_level": 1023,
    "feels_like": 2.45,
    "grnd_level": 1014
  },
  "name": "Kulautuva",
  "wind": {
    "deg": 304,
    "gust": 3.26,
    "speed": 2.13
  },
  "coord": {
    "lat": 54.9383,
    "lon": 23.6476
  },
  "clouds": {
    "all": 36
  },
  "weather": [
    {
      "id": 802,
      "icon": "03d",
      "main": "Clouds",
      "description": "scattered clouds"
    }
  ],
  "timezone": 7200,
  "visibility": 10000
}
```


## Zones

Zone type: `simo_sdk.models.Zone`

- `id: int`
- `name: str`

Lookup:

```python
zone_by_id = home.zones[12]
zone_by_name = home.zones["Kitchen"]
```


## Categories

Category type: `simo_sdk.models.Category`

- `id: int`
- `name: str`

Lookup:

```python
cat_by_id = home.categories[5]
cat_by_name = home.categories["Lights"]
```


## Components

### Get by id

```python
lamp = home.components[123]
```

### Filter

Type returned by `filter(...)`: `simo_sdk.collections.ComponentQuery` (iterable)

```python
# by name (substring match, case-insensitive)
items = home.components.filter(name="light")

# by base_type
items = home.components.filter(base_type="switch")

# by zone/category using name
items = home.components.filter(zone="Kitchen", category="Lights")

# by zone/category using objects
z = home.zones["Kitchen"]
c = home.categories["Lights"]
items = home.components.filter(zone=z, category=c)
```

Filter parameters:

- `name: str | None`
- `base_type: str | None`
- `zone: int | str | simo_sdk.models.Zone | None`
- `category: int | str | simo_sdk.models.Category | None`

### Order

```python
items = home.components.filter(zone="Kitchen")

# default ordering is by id
items = items.order_by()          # same as order_by("id")

# order by any field
items = items.order_by("name")
items = items.order_by("-last_change")

# multi-field ordering
items = items.order_by("zone_id", "name")
```


## Component

Component type: `simo_sdk.models.Component`

### Actions

```python
lamp.turn_on()
lamp.turn_off()
lamp.toggle()

blinds = home.components.filter(base_type="blinds")[0]
blinds.open()
blinds.close()

lamp.send(True)
lamp.call("set_volume", 30)
```

If the method exists on the component, you can call it directly:

```python
lamp.set_volume(30)
```

### Slave components

If your component has slave components (for example a multi-switch), you can control a slave like this:

```python
multi = home.components.filter(name="Kitchen switch")[0]
slave = multi.slave(multi.slaves[0])
slave.turn_on()
```

### Waiting for a state update

```python
lamp.turn_on()
lamp.wait_for(fields=["value"], timeout=10)
print(lamp.value)
```

### Reacting to changes

```python
def changed(c):
    print(c.name, c.value)

lamp.on_change(changed, fields=["value"])
```

You can also receive the actor:

```python
def changed(c, actor):
    if actor and actor.type == "user" and actor.user:
        print("changed by:", actor.user.name)
    else:
        print("changed by:", actor.type)

lamp.on_change(changed, fields=["value"])
```

### Refresh

```python
lamp.refresh()
print(lamp.value)
```

### Fields

These are exposed as attributes:

- `id: int`
- `name: str`
- `icon: str | None`
- `base_type: str | None`
- `zone_id: int | None`
- `category_id: int | None`
- `gateway_id: int | None`
- `show_in_app: bool | None`
- `controller_uid: str | None`
- `last_change: float | None`
- `last_modified: float | None`
- `read_only: bool | None`
- `slaves: list[int]`
- `info: Any`
- `value: Any`
- `value_units: str | None`
- `meta: dict`
- `config: dict`
- `alive: bool | None`
- `error_msg: str | None`
- `alarm_category: str | None`
- `arm_status: str | None`
- `battery_level: int | None`
- `controller_methods: list[str]`

Additional fields (including future SIMO.io fields) are always available here:

- `data: dict`


## Users

User type: `simo_sdk.models.User` (this represents an InstanceUser in SIMO.io)

### Current user

```python
me = home.users.me
print(me.name, me.at_home)
```

### Filter

```python
home_users = home.users.filter(is_active=True)
people_at_home = home.users.filter(at_home=True)
```

### Notify a user

```python
u = home.users.filter(name="Simon")[0]
u.notify(severity="warning", title="Hello", body="Test")
```

### Reacting to user changes

```python
def presence_changed(u):
    print(u.name, "at_home:", u.at_home)

home.users.me.on_change(presence_changed, fields=["at_home"])
```

### User fields

- `id: int` (InstanceUser id)
- `user_id: int | None` (global User id)
- `email: str | None`
- `name: str | None`
- `role_id: int | None`
- `role_name: str | None`
- `role_is_owner: bool | None`
- `role_is_superuser: bool | None`
- `role_can_manage_users: bool | None`
- `role_is_person: bool | None`
- `is_active: bool | None`
- `at_home: bool | None`
- `last_seen: float | None` (timestamp)
- `last_seen_location: str | None` ("lat,lon")
- `last_seen_speed_kmh: float | None`
- `phone_on_charge: bool | None`


## Actor

Actor type: `simo_sdk.models.Actor`

- `type: str` – one of: `user`, `device`, `system`, `ai`
- `user: simo_sdk.models.User | None`

Note: `actor.user` is only set when `actor.type == "user"`.
