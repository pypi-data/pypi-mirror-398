from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Optional,
    Sequence,
    Union,
    Mapping,
)

from .base import Resource

MachineRef = Union["MachineState", str]
QubitRef = Union["Qubit", int]


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


def _resolve_qubit_number(qubit: Optional[QubitRef]) -> Optional[int]:
    if qubit is None:
        return None
    if isinstance(qubit, int):
        return qubit
    number = getattr(qubit, "number", None)
    if number is None:
        raise ValueError("Qubit reference must expose a 'number'.")
    return number


@dataclass
class Qubit(Resource):

    ENDPOINT: ClassVar[str] = "/machines/qubits/"
    WRITABLE_FIELDS: ClassVar[Sequence[str]] = (
        "number",
        "model_type",
        "freq",
        "fmax",
        "fmin",
        "anharmonicity_max",
        "flux_bias",
        "num_lvl",
        "driving_freq",
        "detuning",
        "time_scales",
        "machine",
    )
    READ_ONLY_FIELDS: ClassVar[Sequence[str]] = ("id",)

    # Resource fields (from base class)
    id: Optional[str] = None

    # Qubit-specific fields
    number: Optional[int] = None
    model_type: Optional[str] = None
    freq: Optional[float] = None
    fmax: Optional[float] = None
    fmin: Optional[float] = None
    anharmonicity_max: Optional[float] = None
    flux_bias: Optional[float] = None
    num_lvl: Optional[int] = None
    driving_freq: Optional[float] = None
    detuning: Optional[float] = None
    time_scales: Optional[Dict[str, Any]] = field(default=None)
    machine: Optional[str] = None

    # Override base class methods
    @classmethod
    def _normalize_payload(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize payload with machine reference resolution."""
        payload: Dict[str, Any] = {}
        for key in cls.WRITABLE_FIELDS:
            if key not in data:
                continue
            value = data[key]
            if value is None:
                continue
            if key == "machine":
                payload[key] = _resolve_machine(value)
            else:
                payload[key] = value
        return payload

    @classmethod
    def _prepare_diff_field(cls, field: str, current_value: Any) -> Any:
        """Resolve machine reference in diff."""
        if field == "machine":
            return _resolve_machine(current_value)
        return current_value

    def _update_with_response(self, data: Dict[str, Any]) -> None:
        """Update with machine reference resolution."""
        for field_name in (*self.WRITABLE_FIELDS, *self.READ_ONLY_FIELDS):
            if field_name in data:
                value = deepcopy(data[field_name])
                if field_name == "machine":
                    self.machine = _resolve_machine(value)
                else:
                    setattr(self, field_name, value)

    def _sync_to_machine_config(self) -> None:
        """Sync this instance's state back to the bound machine's machine_config."""
        if not hasattr(self, "_bound_to_machine") or self._bound_to_machine is None:
            return
        if not hasattr(self, "_bound_config_key") or self._bound_config_key is None:
            return

        machine = self._bound_to_machine
        if machine.machine_config is None:
            machine.machine_config = {}
        if "qubits" not in machine.machine_config:
            machine.machine_config["qubits"] = {}

        original_config = (
            machine.machine_config["qubits"].get(self._bound_config_key, {}).copy()
        )

        expected_fields = (
            "number",
            "model_type",
            "freq",
            "fmax",
            "fmin",
            "anharmonicity_max",
            "flux_bias",
            "num_lvl",
            "driving_freq",
            "detuning",
            "time_scales",
        )

        config_data: Dict[str, Any] = {}

        for field in expected_fields:
            if field in original_config:
                original_value = original_config[field]
                if original_value is not None:
                    if isinstance(original_value, dict):
                        config_data[field] = deepcopy(original_value)
                    else:
                        config_data[field] = original_value

        for field in self.WRITABLE_FIELDS:
            if field == "machine" or field not in expected_fields:
                continue
            value = getattr(self, field, None)
            if value is not None:
                # Deep copy to avoid reference issues
                if isinstance(value, dict):
                    config_data[field] = deepcopy(value)
                else:
                    config_data[field] = value
            elif field == "time_scales":
                config_data.pop("time_scales", None)

        if "time_scales" in config_data and config_data["time_scales"] is None:
            config_data.pop("time_scales", None)

        key_as_int = int(self._bound_config_key)
        if self.number is not None:
            config_data["number"] = self.number
        else:
            config_data["number"] = key_as_int

        machine.machine_config["qubits"][self._bound_config_key] = config_data

    def __setattr__(self, name: str, value: Any) -> None:
        """Override to sync changes back to machine_config when bound."""
        super().__setattr__(name, value)
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
