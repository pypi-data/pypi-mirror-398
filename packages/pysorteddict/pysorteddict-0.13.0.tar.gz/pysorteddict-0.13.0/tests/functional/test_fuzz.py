import builtins
import datetime
import decimal
import ipaddress
import math
import pathlib
import random
import re
import string
import sys
import uuid
from importlib.metadata import version

import pytest

from pysorteddict import SortedDict

unsupported_types = {bytearray, complex, dict, Exception, frozenset, list, set, tuple, type}
# Needs to be ordered. See https://github.com/pytest-dev/pytest-xdist/issues/432.
supported_types = [
    bool, bytes, float, int, str,
    # The type of `Fraction` is `ABCMeta`, not `type`. The representation of
    # `struct_time` is different across Python versions. It will be a lot of
    # work to generalise these tests for these key types. Since there is no
    # custom code handling them, they are no different from `int` in that
    # regard. Exclude them from tests. Also, concrete paths cannot be
    # instantiated on an incompatible system, so let the library decide.
    datetime.date, decimal.Decimal, ipaddress.IPv4Address, ipaddress.IPv4Interface, ipaddress.IPv4Network,
    ipaddress.IPv6Address, ipaddress.IPv6Interface, ipaddress.IPv6Network, type(pathlib.Path()),
    type(pathlib.PurePath()), datetime.timedelta, uuid.UUID,
]  # fmt: skip
all_types = [*unsupported_types.union(supported_types)]


class TestFuzz:
    def _gen(self, key_type: type | None = None):
        match key_type := key_type or self._rg.choice((bytes, frozenset, int, list, set, tuple, str)):
            case builtins.bool:
                return bool(self._rg.getrandbits(1))
            case builtins.bytearray | builtins.frozenset | builtins.list | builtins.set | builtins.tuple:
                return key_type(self._gen(bytes))
            case builtins.complex:
                return self._gen(float) + self._gen(float) * 1j
            case builtins.bytes:
                return self._rg.randbytes(self._rg.randrange(16, 32))
            case builtins.dict:
                return {b: b for b in self._gen(bytes)}
            case builtins.Exception:
                return Exception()
            case builtins.int:
                return self._rg.randrange(1_000, 2_000)
            case builtins.float | decimal.Decimal:
                # I want a non-negligible repetition chance. Hence the kludge.
                return key_type(self._rg.choices([*range(1_000), "-inf", "inf", "nan"], [1] * 1_002 + [100])[0])
            case builtins.str:
                return "".join(self._rg.choices(string.ascii_lowercase, k=self._rg.randrange(20, 30)))
            case builtins.type:
                return self._rg.choice(all_types)
            case datetime.date:
                return datetime.date.fromordinal(self._gen(int))
            case ipaddress.IPv4Address | ipaddress.IPv4Interface | ipaddress.IPv4Network:
                return key_type(self._rg.randrange(2**32 - 1))
            case ipaddress.IPv6Address | ipaddress.IPv6Interface | ipaddress.IPv6Network:
                return key_type(self._rg.randrange(2**64 - 1))
            case pathlib.PosixPath | pathlib.PurePosixPath | pathlib.PureWindowsPath | pathlib.WindowsPath:
                return key_type(self._gen(str))
            case datetime.timedelta:
                return datetime.timedelta(self._gen(int))
            case uuid.UUID:
                return uuid.uuid4()
            case _:
                raise RuntimeError(key_type)

    @pytest.mark.parametrize(
        "key_type",
        (
            pytest.param(
                supported_type,
                marks=pytest.mark.skipif(
                    supported_type not in {float, str, decimal.Decimal} and "rc" in version("pysorteddict"),
                    reason="reduce running time of cibuildwheel GitHub Action for pre-releases",
                ),
            )
            for supported_type in supported_types
        ),
    )
    def test_fuzz(self, key_type: type):
        self._rg = random.Random(f"{__name__}-{key_type.__name__}")
        self.key_type = key_type
        self._test___new__()

        attrs = {*dir(SortedDict)}.difference((
            "__class__", "__dict__", "__dir__", "__doc__", "__eq__", "__format__", "__ge__", "__getattr__",
            "__getattribute__", "__getstate__", "__gt__", "__hash__", "__init__", "__init_subclass__", "__iter__",
            "__le__", "__len__", "__lt__", "__ne__", "__reduce__", "__reduce_ex__", "__repr__", "__reversed__",
            "__setattr__", "__sizeof__", "__str__", "__subclasshook__", "__weakref__", "_debug", "key_type",
        ))  # fmt: skip
        for attr in self._rg.choices([*attrs], k=16_000):
            getattr(self, f"_test_{attr}")()

            if self.is_sorted_dict_new:
                assert self.sorted_dict.key_type is None
            else:
                assert self.sorted_dict.key_type is self.key_type

            sorted_normal_dict = dict(sorted(self.normal_dict.items()))
            assert len(self.sorted_dict) == len(sorted_normal_dict)
            assert repr(self.sorted_dict) == f"SortedDict({sorted_normal_dict})"
            assert [*self.sorted_dict] == [*sorted_normal_dict]
            assert [*reversed(self.sorted_dict)] == [*reversed(sorted_normal_dict)]

        with pytest.raises(TypeError, match=r"^unhashable type: 'pysorteddict.SortedDict'$"):
            hash(self.sorted_dict)

    def _test___contains__(self):
        for container in (self.sorted_dict, self.sorted_dict_keys, self.sorted_dict_items):
            container_contains_items = container.__class__.__name__ == "SortedDictItems"
            for key_type in all_types:
                key = self._gen(key_type)
                query = (key, self._gen()) if container_contains_items else key
                if self.is_sorted_dict_new:
                    with pytest.raises(RuntimeError, match=r"^key type not set: insert at least one item first$"):
                        query in container  # noqa: B015
                    continue
                if key_type is not self.key_type:
                    with pytest.raises(
                        TypeError,
                        match=re.escape(f"got key {key!r} of type {key_type!r}, want key of type {self.key_type!r}"),
                    ):
                        query in container  # noqa: B015
                    continue
                if (key_type is float or key_type is decimal.Decimal) and math.isnan(key):
                    with pytest.raises(ValueError, match=re.escape(f"got bad key {key!r} of type {key_type!r}")):
                        query in container  # noqa: B015
                    continue
                items = self.normal_dict.items()
                if self.normal_dict:
                    query = self._rg.choice([*items])
                    query = query if container_contains_items else query[0]
                    assert query in container
                if container_contains_items:
                    assert (query in container) == (query in items)
                    assert [*query] not in container
                    assert () not in container
                else:
                    assert (query in container) == (query in self.normal_dict)

    def _test___delattr__(self):
        with pytest.raises(AttributeError):
            delattr(self.sorted_dict, "key_type")
        for attr in ("clear", "copy", "items", "keys", "values"):
            with pytest.raises(AttributeError):
                delattr(self.sorted_dict, attr)

    def _test___delitem__(self):
        for key_type in all_types:
            key = self._gen(key_type)
            if self.is_sorted_dict_new:
                with pytest.raises(RuntimeError, match=r"^key type not set: insert at least one item first$"):
                    del self.sorted_dict[key]
                continue
            if key_type is not self.key_type:
                with pytest.raises(
                    TypeError,
                    match=re.escape(f"got key {key!r} of type {key_type!r}, want key of type {self.key_type!r}"),
                ):
                    del self.sorted_dict[key]
                continue
            if (key_type is float or key_type is decimal.Decimal) and math.isnan(key):
                with pytest.raises(ValueError, match=re.escape(f"got bad key {key!r} of type {key_type!r}")):
                    del self.sorted_dict[key]
                continue
            if key not in self.normal_dict:
                with pytest.raises(KeyError, match=re.escape(repr(key))):
                    del self.sorted_dict[key]
                continue
            del self.normal_dict[key]
            del self.sorted_dict[key]

    def _test___getitem__(self):
        for key_type in all_types:
            key = self._gen(key_type)
            if self.is_sorted_dict_new:
                with pytest.raises(RuntimeError, match=r"^key type not set: insert at least one item first$"):
                    self.sorted_dict[key]
                continue
            if key_type is not self.key_type:
                with pytest.raises(
                    TypeError,
                    match=re.escape(f"got key {key!r} of type {key_type!r}, want key of type {self.key_type!r}"),
                ):
                    self.sorted_dict[key]
                continue
            if (key_type is float or key_type is decimal.Decimal) and math.isnan(key):
                with pytest.raises(ValueError, match=re.escape(f"got bad key {key!r} of type {key_type!r}")):
                    self.sorted_dict[key]
                continue
            if key not in self.normal_dict:
                with pytest.raises(KeyError, match=re.escape(repr(key))):
                    self.sorted_dict[key]
                continue
            assert self.sorted_dict[key] == self.normal_dict[key]

    def _test___new__(self):
        self.normal_dict = {}
        self.sorted_dict = SortedDict()
        self.sorted_dict_items = self.sorted_dict.items()
        self.sorted_dict_keys = self.sorted_dict.keys()
        self.sorted_dict_values = self.sorted_dict.values()
        self.is_sorted_dict_new = True

    def _test___setitem__(self):
        for key_type in all_types:
            key, value = self._gen(key_type), self._gen()
            if self.is_sorted_dict_new and key_type in unsupported_types:
                with pytest.raises(
                    TypeError,
                    match=re.escape(f"got key {key!r} of unsupported type {key_type!r}"),
                ):
                    self.sorted_dict[key] = value
                continue
            if not self.is_sorted_dict_new and key_type is not self.key_type:
                with pytest.raises(
                    TypeError,
                    match=re.escape(f"got key {key!r} of type {key_type!r}, want key of type {self.key_type!r}"),
                ):
                    self.sorted_dict[key] = value
                continue
            if (
                (key_type is float or key_type is decimal.Decimal)
                and math.isnan(key)
                and (self.is_sorted_dict_new or self.key_type is key_type)
            ):
                with pytest.raises(ValueError, match=re.escape(f"got bad key {key!r} of type {key_type!r}")):
                    self.sorted_dict[key] = value
                continue
            if key_type is self.key_type:
                self.normal_dict[key] = value
                self.sorted_dict[key] = value
                self.is_sorted_dict_new = False

    def _test_clear(self):
        self.normal_dict.clear()
        self.sorted_dict.clear()

    def _test_copy(self):
        self.sorted_dict = self.sorted_dict.copy()
        self.sorted_dict_items = self.sorted_dict.items()
        self.sorted_dict_keys = self.sorted_dict.keys()
        self.sorted_dict_values = self.sorted_dict.values()

    def _test_get(self):
        for key_type in all_types:
            key = self._gen(key_type)
            if self.is_sorted_dict_new:
                with pytest.raises(RuntimeError, match=r"^key type not set: insert at least one item first$"):
                    self.sorted_dict.get(key)
                continue
            if key_type is not self.key_type:
                with pytest.raises(
                    TypeError,
                    match=re.escape(f"got key {key!r} of type {key_type!r}, want key of type {self.key_type!r}"),
                ):
                    self.sorted_dict.get(key)
                continue
            if (key_type is float or key_type is decimal.Decimal) and math.isnan(key):
                with pytest.raises(ValueError, match=re.escape(f"got bad key {key!r} of type {key_type!r}")):
                    self.sorted_dict.get(key)
                continue
            assert self.sorted_dict.get(key) == self.normal_dict.get(key)
            value = self._gen()
            assert self.sorted_dict.get(key, value) == self.normal_dict.get(key, value)
            with pytest.raises(TypeError):
                self.sorted_dict.get()

    def _test_items(self):
        self._test_view("SortedDictItems", self.sorted_dict_items, sorted(self.normal_dict.items()))

    def _test_keys(self):
        self._test_view("SortedDictKeys", self.sorted_dict_keys, sorted(self.normal_dict.keys()))

    def _test_setdefault(self):
        for key_type in all_types:
            key = self._gen(key_type)
            if self.is_sorted_dict_new:
                with pytest.raises(RuntimeError, match=r"^key type not set: insert at least one item first$"):
                    self.sorted_dict.setdefault(key)
                continue
            if key_type is not self.key_type:
                with pytest.raises(
                    TypeError,
                    match=re.escape(f"got key {key!r} of type {key_type!r}, want key of type {self.key_type!r}"),
                ):
                    self.sorted_dict.setdefault(key)
                continue
            if (key_type is float or key_type is decimal.Decimal) and math.isnan(key):
                with pytest.raises(ValueError, match=re.escape(f"got bad key {key!r} of type {key_type!r}")):
                    self.sorted_dict.setdefault(key)
                continue
            assert self.sorted_dict.setdefault(key) == self.normal_dict.setdefault(key)
            default = self._gen()
            assert self.sorted_dict.setdefault(key, default) == self.normal_dict.setdefault(key, default)
            with pytest.raises(TypeError):
                self.sorted_dict.setdefault()

    def _test_values(self):
        self._test_view(
            "SortedDictValues", self.sorted_dict_values, [item[1] for item in sorted(self.normal_dict.items())]
        )

    def _test_view(self, name, view, view_as_list):
        view_as_list_len = len(view_as_list)
        view_as_list_len_ex = int(1.3 * view_as_list_len)
        assert repr(view) == f"{name}({view_as_list})"
        assert len(view) == view_as_list_len
        start = self._rg.randint(-view_as_list_len_ex, view_as_list_len_ex)
        stop = self._rg.randint(-view_as_list_len_ex, view_as_list_len_ex)
        for idx in [start, stop]:
            if -view_as_list_len <= idx < view_as_list_len:
                assert view[idx] == view_as_list[idx]
            else:
                with pytest.raises(
                    IndexError, match=rf"^got invalid index {idx} for view of length {view_as_list_len}$"
                ):
                    view[idx]
        with pytest.raises(IndexError, match=r"^cannot fit 'int' into an index-sized integer$"):
            view[sys.maxsize + 1]
        with pytest.raises(TypeError, match=rf"^got index 0.0 of type {float}, want index of type {int} or {slice}$"):
            view[0.0]
        step = self._rg.randint(-view_as_list_len_ex, view_as_list_len_ex)
        if step == 0:
            with pytest.raises(ValueError, match=r"^slice step cannot be zero$"):
                view[start:stop:step]
        else:
            assert view[start:stop:step] == view_as_list[start:stop:step]
            assert view[:stop:step] == view_as_list[:stop:step]
            assert view[start::step] == view_as_list[start::step]
            assert view[::step] == view_as_list[::step]
        assert view[start:stop] == view_as_list[start:stop]
        assert view[start:] == view_as_list[start:]
        assert view[:stop] == view_as_list[:stop]
        assert view[:] == view_as_list
        assert [*view] == view_as_list
        assert [*reversed(view)] == [*reversed(view_as_list)]
