from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import (
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
QubitNumberRef = Union["Qubit", int]


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


def _extract_machine(data: Mapping[str, Any]) -> Optional[str]:
    if "machine" in data and data["machine"] is not None:
        return _resolve_machine(data["machine"])
    if "machine_id" in data and data["machine_id"] is not None:
        return str(data["machine_id"])
    return None


def _resolve_qubit_number(qubit: Optional[QubitNumberRef]) -> Optional[int]:
    if qubit is None:
        return None
    if isinstance(qubit, int):
        return qubit
    if isinstance(qubit, Mapping):
        if "number" in qubit and qubit["number"] is not None:
            return int(qubit["number"])
    number = getattr(qubit, "number", None)
    if number is None:
        raise ValueError("Qubit reference must expose a 'number'.")
    return number


def _extract_qubit_number(data: Mapping[str, Any], key: str) -> Optional[int]:
    candidate = data.get(key)
    if candidate is not None:
        return _resolve_qubit_number(candidate)
    alt_key = f"{key}_id"
    if alt_key in data and data[alt_key] is not None:
        return int(data[alt_key])
    return None


@dataclass
class Coupler(Resource):

    ENDPOINT: ClassVar[str] = "/machines/couplers/"
    WRITABLE_FIELDS: ClassVar[Sequence[str]] = (
        "number",
        "model_type",
        "fmin",
        "fmax",
        "anharmonicity_max",
        "flux_bias",
        "num_lvl",
        "op_1",
        "op_2",
        "qubit_1",
        "qubit_2",
        "g12_zero_flux",
        "g1c_zero_flux",
        "g2c_zero_flux",
        "cz_dc_total_simulated",
        "cz_dc_total_expected",
        "cz_dc_incoherent_simulated",
        "cz_dc_incoherent_expected",
        "cz_dc_coherent_simulated",
        "cz_dc_coherent_expected",
        "iswap_dc_total_simulated",
        "iswap_dc_total_expected",
        "iswap_dc_incoherent_simulated",
        "iswap_dc_incoherent_expected",
        "iswap_dc_coherent_simulated",
        "iswap_dc_coherent_expected",
        "machine",
    )
    READ_ONLY_FIELDS: ClassVar[Sequence[str]] = ("id",)

    id: Optional[str] = None
    number: Optional[int] = None
    model_type: Optional[str] = None
    fmin: Optional[float] = None
    fmax: Optional[float] = None
    anharmonicity_max: Optional[float] = None
    flux_bias: Optional[float] = None
    num_lvl: Optional[int] = None
    op_1: Optional[str] = None
    op_2: Optional[str] = None
    qubit_1: Optional[int] = None
    qubit_2: Optional[int] = None
    g12_zero_flux: Optional[float] = None
    g1c_zero_flux: Optional[float] = None
    g2c_zero_flux: Optional[float] = None
    cz_dc_total_simulated: Optional[float] = None
    cz_dc_total_expected: Optional[float] = None
    cz_dc_incoherent_simulated: Optional[float] = None
    cz_dc_incoherent_expected: Optional[float] = None
    cz_dc_coherent_simulated: Optional[float] = None
    cz_dc_coherent_expected: Optional[float] = None
    iswap_dc_total_simulated: Optional[float] = None
    iswap_dc_total_expected: Optional[float] = None
    iswap_dc_incoherent_simulated: Optional[float] = None
    iswap_dc_incoherent_expected: Optional[float] = None
    iswap_dc_coherent_simulated: Optional[float] = None
    iswap_dc_coherent_expected: Optional[float] = None
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
            elif key in ("qubit_1", "qubit_2"):
                payload[key] = _resolve_qubit_number(value)
            else:
                payload[key] = value
        return payload

    @classmethod
    def _prepare_diff_field(cls, field: str, current_value: Any) -> Any:
        if field == "machine":
            return _resolve_machine(current_value)
        elif field in ("qubit_1", "qubit_2"):
            return _resolve_qubit_number(current_value)
        return current_value

    def _diff(self) -> Dict[str, Any]:
        diff = super()._diff()
        if "qubit_1" not in diff and self.qubit_1 is not None:
            diff["qubit_1"] = _resolve_qubit_number(self.qubit_1)
        if "qubit_2" not in diff and self.qubit_2 is not None:
            diff["qubit_2"] = _resolve_qubit_number(self.qubit_2)
        return diff

    @classmethod
    def from_api(
        cls,
        data: Dict[str, Any],
        *,
        client: Optional[Any] = None,
    ) -> "Coupler":
        fields: Dict[str, Any] = {}
        for field in cls.WRITABLE_FIELDS:
            if field == "machine":
                fields[field] = _extract_machine(data)
            elif field in ("qubit_1", "qubit_2"):
                fields[field] = _extract_qubit_number(data, field)
            else:
                fields[field] = data.get(field)

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
            if field_name in data:
                value = deepcopy(data[field_name])
                if field_name == "machine":
                    self.machine = _extract_machine(data)
                elif field_name in ("qubit_1", "qubit_2"):
                    setattr(self, field_name, _extract_qubit_number(data, field_name))
                else:
                    setattr(self, field_name, value)

    def _sync_to_machine_config(self) -> None:
        if not hasattr(self, "_bound_to_machine") or self._bound_to_machine is None:
            return
        if not hasattr(self, "_bound_config_key") or self._bound_config_key is None:
            return

        machine = self._bound_to_machine
        if machine.machine_config is None:
            machine.machine_config = {}
        if "couplers" not in machine.machine_config:
            machine.machine_config["couplers"] = {}

        original_config = (
            machine.machine_config["couplers"].get(self._bound_config_key, {}).copy()
        )

        config_data: Dict[str, Any] = original_config.copy()

        for field in self.WRITABLE_FIELDS:
            if field == "machine":
                continue
            value = getattr(self, field, None)
            if value is not None:
                if field in ("qubit_1", "qubit_2"):
                    config_data[field] = _resolve_qubit_number(value)
                elif isinstance(value, dict):
                    config_data[field] = deepcopy(value)
                else:
                    config_data[field] = value

        config_data["number"] = self.number

        if "qubit_1" not in config_data and self.qubit_1 is not None:
            config_data["qubit_1"] = _resolve_qubit_number(self.qubit_1)
        if "qubit_2" not in config_data and self.qubit_2 is not None:
            config_data["qubit_2"] = _resolve_qubit_number(self.qubit_2)

        machine.machine_config["couplers"][self._bound_config_key] = config_data

    def __setattr__(self, name: str, value: Any) -> None:
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
