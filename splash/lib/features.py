from re import compile
from typing import Any, TypeVar, Optional

_T = TypeVar('_T')

_flag_name_pattern = compile(r'^[A-Z0-9_]+$')

class Feature(object):
    _name: str
    _enabled: bool
    _description: Optional[str]
    _value: Any

    def __init__(self, name: str, enabled: bool, description: Optional[str] = None, value: Any = None):
        self._name = name
        self._enabled = enabled
        self._description = description
        self._value = value

    def __bool__(self) -> bool:
        return self.enabled

    def __str__(self):
        return f'{self._name}={self._enabled}'

    def __repr__(self):
        return f'{self._name}={self._enabled}'

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

    def toggle(self) -> bool:
        self._enabled = not self._enabled

        return self.enabled

    @property
    def name(self) -> str:
        return self._name

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def description(self) -> str:
        return self._description

    def get_value(self) -> _T:
        return self._value

    def set_value(self, value: _T) -> None:
        self._value = value

_FEATURES: dict[str, Feature] = {}

def create_feature_flag(name: str, enabled: bool, *, description: Optional[str] = None, value: Any = None) -> Feature:
    name = convert_to_flag_name(name)
    if name in _FEATURES:
        raise Exception(f'Feature already exists: {name}')

    feature = Feature(name, enabled, description, value)
    _FEATURES[name] = feature

    return _FEATURES[name]

def get_feature(name: str) -> Optional[Feature]:
    name = convert_to_flag_name(name)
    if name not in _FEATURES:
        return None

    return _FEATURES[name]

def get_all_features() -> list[Feature]:
    return [feature for feature in _FEATURES.values()]

def get_enabled_features() -> list[Feature]:
    return [feature for feature in get_all_features() if feature.enabled]

def get_disabled_features() -> list[Feature]:
    return [feature for feature in get_all_features() if not feature.enabled]

def convert_to_flag_name(name: str) -> str:
    if not _flag_name_pattern.match(name):
        return _to_screaming_snake_case(name)

    return name

def _to_screaming_snake_case(input_string: str):
    cleaned_string = ''.join(c.upper() if c.isalnum() else '_' for c in input_string)
    cleaned_string = cleaned_string.strip('_')
    cleaned_string = '_'.join(filter(None, cleaned_string.split('_')))

    return cleaned_string
