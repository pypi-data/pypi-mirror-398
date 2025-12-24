from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import (
    Any,
    ClassVar,
    Dict,
    Mapping,
    Optional,
    Sequence,
    Union,
    TYPE_CHECKING,
)

from .base import Resource

MachineRef = Union["MachineState", str, Mapping[str, Any]]
ComponentIdRef = Union[int, str, Mapping[str, Any], "Qubit", "Coupler"]
ComponentTypeRef = Union[str, Mapping[str, Any], "Qubit", "Coupler"]


def _resolve_machine(machine: Optional[MachineRef]) -> Optional[str]:
    if machine is None:
        return None
    if isinstance(machine, str):
        return machine
    if isinstance(machine, Mapping):
        identifier = machine.get("id")
        if identifier is not None:
            return str(identifier)
    identifier = getattr(machine, "id", None)
    if identifier is None:
        raise ValueError("Machine reference must expose an 'id'.")
    return str(identifier)


def _resolve_component_number(component: Optional[ComponentIdRef]) -> Optional[int]:
    if component is None:
        return None
    if isinstance(component, int):
        return component
    if isinstance(component, str):
        component = component.strip()
        if component.isdigit():
            return int(component)
        raise ValueError(
            f"Component reference '{component}' is not a valid integer number."
        )
    if isinstance(component, Mapping):
        if "number" in component and component["number"] is not None:
            return int(component["number"])
    number = getattr(component, "number", None)
    if number is not None:
        return int(number)
    raise ValueError(
        "Component reference must provide a 'number' attribute or integer value."
    )


def _resolve_component_type(component: Optional[ComponentTypeRef]) -> Optional[str]:
    if component is None:
        return None
    if isinstance(component, str):
        normalized = component.strip().lower()
        if normalized not in {"qubit", "coupler"}:
            raise ValueError(
                f"Component type '{component}' not supported. "
                "Valid values: 'qubit', 'coupler'."
            )
        return normalized
    if isinstance(component, Mapping):
        candidate = component.get("component_type") or component.get("type")
        if candidate:
            return _resolve_component_type(candidate)
    type_attr = getattr(component, "component_type", None)
    if type_attr is not None:
        return _resolve_component_type(type_attr)
    class_name = component.__class__.__name__.lower()
    if "qubit" in class_name:
        return "qubit"
    if "coupler" in class_name:
        return "coupler"
    raise ValueError(
        "Component reference type could not be inferred. "
        "Provide 'component_?_type' explicitly."
    )


@dataclass
class Crosstalk(Resource):

    ENDPOINT: ClassVar[str] = "/machines/crosstalks/"
    WRITABLE_FIELDS: ClassVar[Sequence[str]] = (
        "number",
        "component_1_id",
        "component_1_type",
        "component_2_id",
        "component_2_type",
        "op_1",
        "op_2",
        "strength",
        "machine",
    )
    READ_ONLY_FIELDS: ClassVar[Sequence[str]] = ("id",)

    id: Optional[str] = None
    number: Optional[int] = None
    component_1_id: Optional[int] = None
    component_1_type: Optional[str] = None
    component_2_id: Optional[int] = None
    component_2_type: Optional[str] = None
    op_1: Optional[str] = None
    op_2: Optional[str] = None
    strength: Optional[float] = None
    machine: Optional[str] = None

    @classmethod
    def _normalize_payload(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        for key in cls.WRITABLE_FIELDS:
            if key not in data:
                continue
            value = data[key]
            if value is None:
                continue
            if key == "machine":
                payload[key] = _resolve_machine(value)
            elif key in ("component_1_id", "component_2_id"):
                payload[key] = _resolve_component_number(value)
            elif key in ("component_1_type", "component_2_type"):
                payload[key] = _resolve_component_type(value)
            else:
                payload[key] = value
        return payload

    @classmethod
    def _prepare_diff_field(cls, field: str, current_value: Any) -> Any:
        if field == "machine":
            return _resolve_machine(current_value)
        if field in ("component_1_id", "component_2_id"):
            return _resolve_component_number(current_value)
        if field in ("component_1_type", "component_2_type"):
            return _resolve_component_type(current_value)
        return current_value

    @classmethod
    def from_api(
        cls,
        data: Dict[str, Any],
        *,
        client: Optional[Any] = None,
    ) -> "Crosstalk":
        fields: Dict[str, Any] = {}
        for field in cls.WRITABLE_FIELDS:
            value = data.get(field)
            if field == "machine":
                fields[field] = _resolve_machine(value)
            elif field in ("component_1_id", "component_2_id"):
                fields[field] = _resolve_component_number(value)
            elif field in ("component_1_type", "component_2_type"):
                fields[field] = _resolve_component_type(value)
            else:
                fields[field] = value
        readonly = {field: data.get(field) for field in cls.READ_ONLY_FIELDS}
        instance = cls(
            **fields,
            **readonly,
            _client=cls._client_or_default(client),
        )
        instance._snapshot()
        return instance

    def _update_with_response(self, data: Dict[str, Any]) -> None:
        for field_name in (*self.WRITABLE_FIELDS, *self.READ_ONLY_FIELDS):
            if field_name not in data:
                continue
            value = deepcopy(data[field_name])
            if field_name == "machine":
                value = _resolve_machine(value)
            elif field_name in ("component_1_id", "component_2_id"):
                value = _resolve_component_number(value)
            elif field_name in ("component_1_type", "component_2_type"):
                value = _resolve_component_type(value)
            setattr(self, field_name, value)

    def _sync_to_machine_config(self) -> None:
        if not hasattr(self, "_bound_to_machine") or self._bound_to_machine is None:
            return
        if not hasattr(self, "_bound_config_key") or self._bound_config_key is None:
            return

        machine = self._bound_to_machine
        if machine.machine_config is None:
            machine.machine_config = {}
        if "crosstalks" not in machine.machine_config:
            machine.machine_config["crosstalks"] = {}

        original = (
            machine.machine_config["crosstalks"].get(self._bound_config_key, {}).copy()
        )
        config_data: Dict[str, Any] = original.copy()

        for field in (
            "component_1_id",
            "component_1_type",
            "component_2_id",
            "component_2_type",
            "op_1",
            "op_2",
            "strength",
        ):
            value = getattr(self, field, None)
            if value is None:
                continue
            if field.endswith("_id"):
                config_data[field] = _resolve_component_number(value)
            elif field.endswith("_type"):
                config_data[field] = _resolve_component_type(value)
            else:
                config_data[field] = deepcopy(value)

        key_number = int(self._bound_config_key)
        config_data["number"] = self.number if self.number is not None else key_number

        machine.machine_config["crosstalks"][self._bound_config_key] = config_data

    def __setattr__(self, name: str, value: Any) -> None:
        normalized_value = value
        if name == "machine" and value is not None:
            normalized_value = _resolve_machine(value)
        elif name in ("component_1_id", "component_2_id") and value is not None:
            normalized_value = _resolve_component_number(value)
        elif name in ("component_1_type", "component_2_type") and value is not None:
            normalized_value = _resolve_component_type(value)

        super().__setattr__(name, normalized_value)

        if name.startswith("_"):
            return
        if name in self.WRITABLE_FIELDS:
            try:
                if (
                    hasattr(self, "_bound_to_machine")
                    and self._bound_to_machine is not None
                ):
                    self._sync_to_machine_config()
            except AttributeError:
                pass
