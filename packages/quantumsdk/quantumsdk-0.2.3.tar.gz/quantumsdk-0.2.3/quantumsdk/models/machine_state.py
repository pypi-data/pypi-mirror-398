from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import (
    Any,
    ClassVar,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from .qubit import Qubit
    from .coupler import Coupler
    from .crosstalk import Crosstalk

from .._utils import normalize_numbered_mapping
from .base import Resource


def _prepare_machine_config(config: Any) -> Optional[Dict[str, Dict[str, Any]]]:
    if config is None:
        return None
    if not isinstance(config, dict):
        raise ValueError("machine_config must be provided as a dict.")

    normalized: Dict[str, Any] = {}

    for key, value in config.items():
        if key in ("qubits", "couplers", "crosstalks"):
            normalized_section = normalize_numbered_mapping(value)
            if normalized_section is not None:
                renumbered_section = _renumber_sequential(normalized_section)
                normalized[key] = renumbered_section
        else:
            normalized[key] = value

    return normalized


def _renumber_sequential(items: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    if not items:
        return {}

    forbidden_fields = {"id", "machine", "number"}

    sorted_items = sorted(
        items.items(), key=lambda x: int(x[0]) if x[0].isdigit() else float("inf")
    )

    renumbered: Dict[str, Dict[str, Any]] = {}
    for new_index, (old_key, item_data) in enumerate(sorted_items):
        new_key = str(new_index)
        item_copy = deepcopy(item_data)

        for field in forbidden_fields:
            item_copy.pop(field, None)

        filtered_item: Dict[str, Any] = {}
        for key, value in item_copy.items():
            if value is not None:
                filtered_item[key] = value

        renumbered[new_key] = filtered_item

    return renumbered


class NumberedResourceDict:

    def __init__(
        self,
        machine: "MachineState",
        resource_type: str,  # "qubits", "couplers", or "crosstalks"
    ) -> None:
        self._machine = machine
        self._resource_type = resource_type
        self._cache: Dict[int, Any] = {}

    def _get_config_dict(self) -> Dict[str, Dict[str, Any]]:
        if self._machine.machine_config is None:
            self._machine.machine_config = {}
        config = self._machine.machine_config
        if self._resource_type not in config:
            config[self._resource_type] = {}
        return config[self._resource_type]

    def __getitem__(self, number: int) -> Any:
        if not isinstance(number, int):
            raise TypeError(f"Resource number must be an integer, got {type(number)}")

        if number in self._cache:
            return self._cache[number]

        config_dict = self._get_config_dict()
        number_str = str(number)

        if number_str not in config_dict:
            raise KeyError(
                f"{self._resource_type[:-1].capitalize()} with number {number} not found. "
                f"Available numbers: {list(config_dict.keys())}"
            )

        data = config_dict[number_str].copy()
        data["number"] = number
        data["machine"] = self._machine.id

        if self._resource_type == "qubits":
            from .qubit import Qubit

            instance = Qubit.from_api(data, client=self._machine._client)
        elif self._resource_type == "couplers":
            from .coupler import Coupler

            instance = Coupler.from_api(data, client=self._machine._client)
        elif self._resource_type == "crosstalks":
            from .crosstalk import Crosstalk

            instance = Crosstalk.from_api(data, client=self._machine._client)
        else:
            raise ValueError(f"Unknown resource type: {self._resource_type}")

        instance._bound_to_machine = self._machine
        instance._bound_config_key = number_str

        self._cache[number] = instance

        return instance

    def __setitem__(self, number: int, value: Any) -> None:
        if not isinstance(number, int):
            raise TypeError(f"Resource number must be an integer, got {type(number)}")

        config_dict = self._get_config_dict()
        number_str = str(number)

        if isinstance(value, dict):
            value["number"] = number
            config_dict[number_str] = value
        else:
            data = value._current_state() if hasattr(value, "_current_state") else {}
            data["number"] = number
            config_dict[number_str] = data

        if number in self._cache:
            del self._cache[number]

    def __delitem__(self, number: int) -> None:
        if not isinstance(number, int):
            raise TypeError(f"Resource number must be an integer, got {type(number)}")

        config_dict = self._get_config_dict()
        number_str = str(number)

        if number_str not in config_dict:
            raise KeyError(
                f"{self._resource_type[:-1].capitalize()} with number {number} not found"
            )

        del config_dict[number_str]

        if number in self._cache:
            del self._cache[number]

    def __contains__(self, number: int) -> bool:
        """Check if a resource with the given number exists."""
        if not isinstance(number, int):
            return False
        config_dict = self._get_config_dict()
        return str(number) in config_dict

    def __iter__(self):
        """Iterate over resource numbers."""
        config_dict = self._get_config_dict()
        return (int(k) for k in config_dict.keys())

    def __len__(self) -> int:
        """Return the number of resources."""
        config_dict = self._get_config_dict()
        return len(config_dict)

    def keys(self):
        """Return resource numbers."""
        return iter(self)

    def values(self):
        """Return resource instances."""
        return (self[k] for k in self)

    def items(self):
        """Return (number, instance) pairs."""
        return ((k, self[k]) for k in self)

    def clear_cache(self) -> None:
        """Clear the instance cache (useful after refresh)."""
        self._cache.clear()


@dataclass
class MachineState(Resource):

    ENDPOINT: ClassVar[str] = "/machines/machine_state/"
    WRITABLE_FIELDS: ClassVar[Sequence[str]] = (
        "title",
        "machine",
        "machine_type",
        "modality",
        "control_electronics",
        "virtual_mode",
        "provider",
        "device",
        "type",
        "clock_time",
        "machine_config",
        "solver",
    )
    READ_ONLY_FIELDS: ClassVar[Sequence[str]] = (
        "id",
        "user",
        "created_at",
        "updated_at",
    )

    id: Optional[str] = None

    title: Optional[str] = None
    machine: Optional[str] = None
    machine_type: Optional[str] = None
    modality: Optional[str] = None
    control_electronics: Optional[str] = None
    virtual_mode: Optional[str] = None
    provider: Optional[str] = None
    device: Optional[str] = None
    type: Optional[str] = None
    clock_time: Optional[float] = None
    machine_config: Optional[Dict[str, Any]] = field(default=None)
    solver: Optional[Dict[str, Any]] = field(default=None)
    user: Optional[Dict[str, Any]] = field(default=None)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # MachineState-specific internal fields
    _qubits_dict: Optional[NumberedResourceDict] = field(
        default=None, repr=False, compare=False
    )
    _couplers_dict: Optional[NumberedResourceDict] = field(
        default=None, repr=False, compare=False
    )
    _crosstalks_dict: Optional[NumberedResourceDict] = field(
        default=None, repr=False, compare=False
    )

    @classmethod
    def _normalize_payload(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            key: value
            for key, value in data.items()
            if value is not None and key in cls.WRITABLE_FIELDS
        }
        machine_config = payload.get("machine_config")
        if machine_config is not None:
            payload["machine_config"] = _prepare_machine_config(machine_config)
        return payload

    @classmethod
    def _normalize_list_response(cls, items: Any) -> List[Dict[str, Any]]:
        if items is None:
            return []
        elif isinstance(items, dict):
            return [items]
        elif isinstance(items, Iterable) and not isinstance(items, (str, bytes)):
            result = []
            for item in items:
                if not isinstance(item, dict):
                    raise ValueError(
                        "Unexpected item type in MachineState.list() payload; "
                        f"expected dict, received {type(item)!r}."
                    )
                result.append(item)
            return result
        else:
            raise ValueError(
                "Unexpected payload structure returned for MachineState.list(); "
                f"received type {type(items)!r}."
            )

    @classmethod
    def _prepare_diff_field(cls, field: str, current_value: Any) -> Any:
        if field == "machine_config" and current_value is not None:
            return _prepare_machine_config(current_value)
        return current_value

    def _prepare_post_payload(self) -> Dict[str, Any]:
        payload = self._normalize_payload(self._current_state())
        import json as json_module

        print(f"[DEBUG] POST {self.ENDPOINT}")
        print(f"[DEBUG] Request payload: {json_module.dumps(payload, indent=2)}")
        return payload

    def _prepare_patch_payload(self, diff: Dict[str, Any]) -> Dict[str, Any]:
        import json as json_module

        print(f"[DEBUG] PATCH {self.ENDPOINT}{self.id}/")
        print(f"[DEBUG] Request payload (diff): {json_module.dumps(diff, indent=2)}")
        return diff

    def _update_with_response(self, data: Dict[str, Any]) -> None:
        super()._update_with_response(data)
        if self._qubits_dict is not None:
            self._qubits_dict.clear_cache()
        if self._couplers_dict is not None:
            self._couplers_dict.clear_cache()
        if self._crosstalks_dict is not None:
            self._crosstalks_dict.clear_cache()

    @property
    def qubits(self) -> NumberedResourceDict:
        if self._qubits_dict is None:
            self._qubits_dict = NumberedResourceDict(self, "qubits")
        return self._qubits_dict

    @property
    def couplers(self) -> NumberedResourceDict:
        if self._couplers_dict is None:
            self._couplers_dict = NumberedResourceDict(self, "couplers")
        return self._couplers_dict

    @property
    def crosstalks(self) -> NumberedResourceDict:
        """Access crosstalk entries by number: machine.crosstalks[0].strength = 1e-3"""
        if self._crosstalks_dict is None:
            self._crosstalks_dict = NumberedResourceDict(self, "crosstalks")
        return self._crosstalks_dict
