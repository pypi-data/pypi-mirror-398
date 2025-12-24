from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Sequence,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from ..client import HttpClient

from .._utils import ensure_iterable_of_dicts, unwrap_api_payload
from ..client import HttpClient


@dataclass
class Resource(ABC):

    ENDPOINT: ClassVar[str]
    WRITABLE_FIELDS: ClassVar[Sequence[str]]
    READ_ONLY_FIELDS: ClassVar[Sequence[str]] = ("id",)

    id: Optional[str] = None
    _client: HttpClient = field(default=None, repr=False, compare=False)
    _original: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def _client_or_default(cls, client: Optional[HttpClient]) -> HttpClient:
        """Get the client instance or default singleton."""
        return client or HttpClient.instance()

    @classmethod
    @abstractmethod
    def _normalize_payload(cls, data: Dict[str, Any]) -> Dict[str, Any]:

        payload: Dict[str, Any] = {}
        for key in cls.WRITABLE_FIELDS:
            if key in data and data[key] is not None:
                payload[key] = data[key]
        return payload

    @classmethod
    def _normalize_list_response(cls, items: Any) -> List[Dict[str, Any]]:

        return ensure_iterable_of_dicts(items)

    @classmethod
    def _prepare_diff_field(cls, field: str, current_value: Any) -> Any:
        return current_value

    def _prepare_post_payload(self) -> Dict[str, Any]:
        return self._normalize_payload(self._current_state())

    def _prepare_patch_payload(self, diff: Dict[str, Any]) -> Dict[str, Any]:
        return diff

    def _update_with_response(self, data: Dict[str, Any]) -> None:
        for field_name in (*self.WRITABLE_FIELDS, *self.READ_ONLY_FIELDS):
            if field_name in data:
                setattr(self, field_name, deepcopy(data[field_name]))

    @classmethod
    def list(
        cls,
        *,
        client: Optional[HttpClient] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> List["Resource"]:

        http = cls._client_or_default(client)
        payload = http.get(cls.ENDPOINT, params=params)
        items = unwrap_api_payload(payload)
        resource_dicts = cls._normalize_list_response(items)
        return [cls.from_api(item, client=http) for item in resource_dicts]

    @classmethod
    def get(
        cls,
        resource_id: str,
        *,
        client: Optional[HttpClient] = None,
    ) -> "Resource":

        http = cls._client_or_default(client)
        payload = http.get(f"{cls.ENDPOINT}{resource_id}/")
        data = unwrap_api_payload(payload)
        if not isinstance(data, dict):
            raise ValueError(f"Unexpected payload returned for {cls.__name__}.get()")
        return cls.from_api(data, client=http)

    @classmethod
    def create(
        cls,
        *,
        client: Optional[HttpClient] = None,
        **attributes: Any,
    ) -> "Resource":

        http = cls._client_or_default(client)
        payload = cls._normalize_payload(attributes)
        response = http.post(cls.ENDPOINT, json=payload)
        data = unwrap_api_payload(response)
        if not isinstance(data, dict):
            raise ValueError(f"Unexpected payload returned for {cls.__name__}.create()")
        return cls.from_api(data, client=http)

    @classmethod
    def from_api(
        cls,
        data: Dict[str, Any],
        *,
        client: Optional[HttpClient] = None,
    ) -> "Resource":

        fields = {field: data.get(field) for field in cls.WRITABLE_FIELDS}
        readonly = {field: data.get(field) for field in cls.READ_ONLY_FIELDS}
        instance = cls(
            **fields,
            **readonly,
            _client=cls._client_or_default(client),
        )
        instance._snapshot()
        return instance

    def _snapshot(self) -> None:
        self._original = self._current_state()

    def _current_state(self) -> Dict[str, Any]:
        data = {
            field: deepcopy(getattr(self, field))
            for field in (*self.WRITABLE_FIELDS, *self.READ_ONLY_FIELDS)
        }
        return data

    def _diff(self) -> Dict[str, Any]:
        current = self._current_state()
        diff: Dict[str, Any] = {}
        for field in self.WRITABLE_FIELDS:
            original_value = self._original.get(field)
            current_value = current.get(field)
            if original_value != current_value:
                diff[field] = self._prepare_diff_field(field, current_value)
        return diff

    @staticmethod
    def _values_equal(lhs: Any, rhs: Any) -> bool:
        return lhs == rhs

    def save(self) -> "Resource":

        if self._client is None:
            self._client = HttpClient.instance()

        if self.id is None:
            payload = self._prepare_post_payload()
            response = self._client.post(self.ENDPOINT, json=payload)
        else:
            diff = self._diff()
            if not diff:
                return self
            payload = self._prepare_patch_payload(diff)
            response = self._client.patch(f"{self.ENDPOINT}{self.id}/", json=payload)

        data = unwrap_api_payload(response)
        if not isinstance(data, dict):
            raise ValueError(
                f"Unexpected payload returned by {self.__class__.__name__}.save()"
            )

        self._update_with_response(data)
        self._snapshot()
        return self

    def refresh(self) -> "Resource":

        if self.id is None:
            raise ValueError(
                f"Cannot refresh a {self.__class__.__name__} without an id."
            )
        if self._client is None:
            self._client = HttpClient.instance()

        response = self._client.get(f"{self.ENDPOINT}{self.id}/")
        data = unwrap_api_payload(response)
        if not isinstance(data, dict):
            raise ValueError(
                f"Unexpected payload returned by {self.__class__.__name__}.refresh()"
            )

        self._update_with_response(data)
        self._snapshot()
        return self

    def delete(self) -> None:

        if self.id is None:
            raise ValueError(
                f"Cannot delete a {self.__class__.__name__} without an id."
            )
        if self._client is None:
            self._client = HttpClient.instance()

        self._client.delete(f"{self.ENDPOINT}{self.id}/")
