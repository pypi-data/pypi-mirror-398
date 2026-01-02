from __future__ import annotations  # for self references in return types
from collections import abc
from typing import TypeVar, Generic, Optional, Mapping, Iterable, Tuple, Union, Dict, overload, Iterator, Any

# Adapted from: https://github.com/DeveloperRSquared/case-insensitive-dict/blob/main/case_insensitive_dict/case_insensitive_dict.py

KT = TypeVar('KT')  # pylint: disable=invalid-name
VT = TypeVar('VT')  # pylint: disable=invalid-name
MutableMapping = abc.MutableMapping[KT, VT]  # pylint: disable=unsubscriptable-object

class CaseInsensitiveDict(MutableMapping, Generic[KT, VT]):
    @overload
    def __init__(self, data: Optional[Mapping[KT, VT]] = None) -> None:
        ...

    @overload
    def __init__(self, data: Optional[Iterable[Tuple[KT, VT]]] = None) -> None:
        ...

    def __init__(self, data: Optional[Union[Mapping[KT, VT], Iterable[Tuple[KT, VT]]]] = None) -> None:
        # Mapping from lowercased key to tuple of (actual key, value)
        self._data: Dict[KT, Tuple[KT, VT]] = {}
        if data is None:
            data = {}
        self.update(data)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({dict(self.items())!r})'

    @staticmethod
    def _convert_key(key: KT) -> KT:
        if isinstance(key, str):
            return key.lower()  # type: ignore[return-value]
        return key

    def _get_key_value(self, key: KT) -> Tuple[KT, VT]:
        try:
            return self._data[self._convert_key(key=key)]
        except KeyError:
            raise KeyError(f"Key: {key!r} not found.") from None

    def __setitem__(self, key: KT, value: VT) -> None:
        self._data[self._convert_key(key=key)] = (key, value)

    def __getitem__(self, key: KT) -> VT:
        return self._get_key_value(key=key)[1]

    def __delitem__(self, key: KT) -> None:
        del self._data[self._convert_key(key=key)]

    def __iter__(self) -> Iterator[KT]:
        return (key for key, _ in self._data.values())

    def __len__(self) -> int:
        return len(self._data)

    def lower_items(self) -> Iterator[Tuple[KT, VT]]:
        return ((key, val[1]) for key, val in self._data.items())

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, abc.Mapping):
            return False
        other_dict = CaseInsensitiveDict[Any, Any](data=other)
        return dict(self.lower_items()) == dict(other_dict.lower_items())

    def copy(self) -> CaseInsensitiveDict[KT, VT]:
        return CaseInsensitiveDict(data=dict(self._data.values()))

    def getkey(self, key: KT) -> KT:
        return self._get_key_value(key=key)[0]

    @classmethod
    def fromkeys(cls, iterable: Iterable[KT], value: VT) -> CaseInsensitiveDict[KT, VT]:
        return cls([(key, value) for key in iterable])
