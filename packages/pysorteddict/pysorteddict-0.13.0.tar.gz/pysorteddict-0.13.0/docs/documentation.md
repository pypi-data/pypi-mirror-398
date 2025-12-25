# Documentation

<details class="notice">

<summary>Documentation of older versions is available on GitHub.</summary>

▸ [0.12.1](https://github.com/tfpf/pysorteddict/blob/v0.12.1/docs/documentation.md)
▸ [0.12.0](https://github.com/tfpf/pysorteddict/blob/v0.12.0/docs/documentation.md)  
▸ [0.11.0](https://github.com/tfpf/pysorteddict/blob/v0.11.0/docs/documentation.md)  
▸ [0.10.0](https://github.com/tfpf/pysorteddict/blob/v0.10.0/docs/documentation.md)  
▸ [0.9.0](https://github.com/tfpf/pysorteddict/blob/v0.9.0/docs/documentation.md)  
▸ [0.8.2](https://github.com/tfpf/pysorteddict/blob/v0.8.2/docs/documentation.md)
▸ [0.8.1](https://github.com/tfpf/pysorteddict/blob/v0.8.1/docs/documentation.md)
▸ [0.8.0](https://github.com/tfpf/pysorteddict/blob/v0.8.0/docs/documentation.md)  
▸ [0.7.3](https://github.com/tfpf/pysorteddict/blob/v0.7.3/docs/documentation.md)
▸ [0.7.2](https://github.com/tfpf/pysorteddict/blob/v0.7.2/docs/documentation.md)
▸ [0.7.1](https://github.com/tfpf/pysorteddict/blob/v0.7.1/docs/documentation.md)
▸ [0.7.0](https://github.com/tfpf/pysorteddict/blob/v0.7.0/docs/documentation.md)  
▸ [0.6.0](https://github.com/tfpf/pysorteddict/blob/v0.6.0/docs/documentation.md)  
▸ [0.5.3](https://github.com/tfpf/pysorteddict/blob/v0.5.3/docs/documentation.md)
▸ [0.5.2](https://github.com/tfpf/pysorteddict/blob/v0.5.2/docs/documentation.md)
▸ [0.5.1](https://github.com/tfpf/pysorteddict/blob/v0.5.1/docs/documentation.md)
▸ [0.5.0](https://github.com/tfpf/pysorteddict/blob/v0.5.0/docs/documentation.md)  
▸ [0.4.6](https://github.com/tfpf/pysorteddict/blob/v0.4.6/docs/documentation.md)
▸ [0.4.5](https://github.com/tfpf/pysorteddict/blob/v0.4.5/docs/index.md)
▸ [0.4.4](https://github.com/tfpf/pysorteddict/blob/v0.4.4/docs/index.md)

</details>

## Sorted Dictionary

`SortedDict` is a sorted dictionary which wraps the C++ sorted dictionary type (`std::map`). It may be imported
explicitly:

```python
from pysorteddict import SortedDict
```

or implicitly using the wildcard (though this is not recommended).

```python
from pysorteddict import *
```

The following key types are always supported.

* `bytes`
* `float`
* `int`
* `str`

The following key types are supported if they are importable (which they should always be—failure to import them may be
a sign of a corrupt or damaged Python installation).

* `datetime.date`
* `datetime.timedelta`
* `decimal.Decimal`
* `fractions.Fraction`
* `ipaddress.IPv4Address`
* `ipaddress.IPv4Interface`
* `ipaddress.IPv4Network`
* `ipaddress.IPv6Address`,
* `ipaddress.IPv6Interface`
* `ipaddress.IPv6Network`
* `pathlib.PosixPath`
* `pathlib.PurePosixPath`
* `pathlib.PureWindowsPath`
* `pathlib.WindowsPath`
* `time.struct_time`
* `uuid.UUID`

<details class="warning">

<summary>Shadowing standard library modules providing these types may lead to undefined behaviour.</summary>

```python
from pathlib import Path
with Path(__file__).with_name("decimal.py").open("w") as writer:
    print("import math", file=writer)
    print('Decimal = type("Decimal", (float,), {"is_nan": lambda self: math.isnan(self)})', file=writer)
from pysorteddict import *
from decimal import Decimal
d = SortedDict()
d[Decimal(0)] = None
```

Here, the imported `Decimal` (which is actually `float` with an `is_nan` method defined) came from the newly created
`decimal.py` instead of the standard library module `decimal`. This will work. However, comparisons between two such
`Decimal`s can be made to error out (by overriding `Decimal.__eq__` and friends). Errors in the comparison function of
the underlying C++ `std::map` invoke undefined behaviour.

</details>

### Constructor

#### `SortedDict(*args, **kwargs) -> SortedDict`

Create an empty sorted dictionary. `args` and `kwargs` are ignored.

### Properties

#### `d.key_type: type | None`

The key type of the sorted dictionary `d`, or `None` if no key-value pairs have been inserted in it.

```python
from pysorteddict import *
d = SortedDict()
assert d.key_type is None
d[b"foo"] = ()
assert d.key_type is bytes
```

### Magic Methods

#### `repr(d)`

Return a human-readable representation of the sorted dictionary `d`.

#### `key in d`

Return whether `key` is present in the sorted dictionary `d`.

<details class="warning">

<summary>This method may raise exceptions.</summary>

If no key-value pairs have been inserted into `d` yet, raises `RuntimeError`.

```python
from pysorteddict import *
d = SortedDict()
"foo" in d
```

```text
Traceback (most recent call last):
  File "…", line 3, in <module>
    "foo" in d
RuntimeError: key type not set: insert at least one item first
```

Otherwise, if `type(key)` does not match the type of the first key inserted into `d`, raises `TypeError`.

```python
from pysorteddict import *
d = SortedDict()
d["foo"] = ("bar", "baz")
100 in d
```

```text
Traceback (most recent call last):
  File "…", line 4, in <module>
    100 in d
TypeError: got key 100 of type <class 'int'>, want key of type <class 'str'>
```

Otherwise, if `key` is not comparable with instances of its type, raises `ValueError`.

```python
from pysorteddict import *
d = SortedDict()
d[1.1] = ("racecar",)
float("nan") in d
```

```text
Traceback (most recent call last):
  File "…", line 4, in <module>
    float("nan") in d
ValueError: got bad key nan of type <class 'float'>
```

</details>

#### `len(d)`

Return the number of key-value pairs in the sorted dictionary `d`.

<details class="warning">

<summary>This method may raise exceptions.</summary>

If the number of key-value pairs in `d` exceeds `PY_SSIZE_T_MAX`, raises `OverflowError`.

```python
from pysorteddict import *
d = SortedDict()
for i in range(65000):
    d[i] = i
print(len(d))
```

```text
Traceback (most recent call last):
  File "…", line 5, in <module>
    print(len(d))
          ^^^^^^
OverflowError: sorted dictionary length is 65000 which exceeds PY_SSIZE_T_MAX = 32767
```

On a 64-bit operating system, `PY_SSIZE_T_MAX` will probably be 9223372036854775807, so this error should never occur.

</details>

#### `d[key]`

Return the value mapped to `key` in the sorted dictionary `d`.

<details class="warning">

<summary>This method may raise exceptions.</summary>

If no key-value pairs have been inserted into `d` yet, raises `RuntimeError`.

```python
from pysorteddict import *
d = SortedDict()
d["foo"]
```

```text
Traceback (most recent call last):
  File "…", line 3, in <module>
    d["foo"]
    ~^^^^^^^
RuntimeError: key type not set: insert at least one item first
```

Otherwise, if `type(key)` does not match the type of the first key inserted into `d`, raises `TypeError`.

```python
from pysorteddict import *
d = SortedDict()
d["foo"] = ("bar", "baz")
d[100]
```

```text
Traceback (most recent call last):
  File "…", line 4, in <module>
    d[100]
    ~^^^^^
TypeError: got key 100 of type <class 'int'>, want key of type <class 'str'>
```

Otherwise, if `key` is not comparable with instances of its type, raises `ValueError`.

```python
from pysorteddict import *
d = SortedDict()
d[1.1] = ("racecar",)
d[float("nan")]
```

```text
Traceback (most recent call last):
  File "…", line 4, in <module>
    d[float("nan")]
    ~^^^^^^^^^^^^^^
ValueError: got bad key nan of type <class 'float'>
```

Otherwise, if `key` is not present in `d`, raises `KeyError`.

```python
from pysorteddict import *
d = SortedDict()
d["foo"] = ("bar", "baz")
d["spam"]
```

```text
Traceback (most recent call last):
  File "…", line 4, in <module>
    d["spam"]
    ~^^^^^^^^
KeyError: 'spam'
```

</details>

#### `d[key] = value`

Map `value` to `key` in the sorted dictionary `d`, replacing the previously-mapped value (if any).

<details class="warning">

<summary>This method may raise exceptions.</summary>

If no key-value pairs have been inserted into `d` yet and `type(key)` isn't one of the supported key types, raises
`TypeError`.

```python
from pysorteddict import *
d = SortedDict()
d[["eggs"]] = None
```

```text
Traceback (most recent call last):
  File "…", line 3, in <module>
    d[["eggs"]] = None
    ~^^^^^^^^^^
TypeError: got key ['eggs'] of unsupported type <class 'list'>
```

Otherwise, if `type(key)` does not match the type of the first key inserted into `d`, raises `TypeError`.

```python
from pysorteddict import *
d = SortedDict()
d["foo"] = ("bar", "baz")
d[100] = "spam"
```

```text
Traceback (most recent call last):
  File "…", line 4, in <module>
    d[100] = "spam"
    ~^^^^^
TypeError: got key 100 of type <class 'int'>, want key of type <class 'str'>
```

Otherwise, if `key` is not comparable with instances of its type, raises `ValueError`.

```python
from pysorteddict import *
d = SortedDict()
d[1.1] = ("racecar",)
d[float("nan")] = {}
```

```text
Traceback (most recent call last):
  File "…", line 4, in <module>
    d[float("nan")] = {}
    ~^^^^^^^^^^^^^^
ValueError: got bad key nan of type <class 'float'>
```

</details>

#### `del d[key]`

Remove `key` and the value mapped to it from the sorted dictionary `d`.

<details class="warning">

<summary>This method may raise exceptions.</summary>

If no key-value pairs have been inserted into `d` yet, raises `RuntimeError`.

```python
from pysorteddict import *
d = SortedDict()
del d["foo"]
```

```text
Traceback (most recent call last):
  File "…", line 3, in <module>
    del d["foo"]
        ~^^^^^^^
RuntimeError: key type not set: insert at least one item first
```

Otherwise, if `type(key)` does not match the type of the first key inserted into `d`, raises `TypeError`.

```python
from pysorteddict import *
d = SortedDict()
d["foo"] = ("bar", "baz")
del d[100]
```

```text
Traceback (most recent call last):
  File "…", line 4, in <module>
    del d[100]
        ~^^^^^
TypeError: got key 100 of type <class 'int'>, want key of type <class 'str'>
```

Otherwise, if `key` is not comparable with instances of its type, raises `ValueError`.

```python
from pysorteddict import *
d = SortedDict()
d[1.1] = ("racecar",)
del d[float("nan")]
```

```text
Traceback (most recent call last):
  File "…", line 4, in <module>
    del d[float("nan")]
        ~^^^^^^^^^^^^^^
ValueError: got bad key nan of type <class 'float'>
```

Otherwise, if `key` is not present in `d`, raises `KeyError`.

```python
from pysorteddict import *
d = SortedDict()
d["foo"] = ("bar", "baz")
del d["spam"]
```

```text
Traceback (most recent call last):
  File "…", line 4, in <module>
    del d["spam"]
        ~^^^^^^^^
KeyError: 'spam'
```

Otherwise, if there exists a forward iterator over the items, keys or values of `d` pointing to `key` (meaning that
calling `next` on the iterator would return `(key, d[key])`, `key` or `d[key]` respectively), raises `RuntimeError`.

```python
from pysorteddict import *
d = SortedDict()
for i in range(5):
  d[i] = None
ii = iter(d.items())
ki = iter(d.keys())
vi = iter(d.values())
del d[0]
```

```text
Traceback (most recent call last):
  File "…", line 8, in <module>
    del d[0]
        ~^^^
RuntimeError: operation not permitted: key-value pair locked by 3 iterator(s)
```

Otherwise, if there exists a reverse iterator over the items, keys or values of `d` pointing to the key immediately
less than `key` (meaning that calling `next` on the iterator last returned `(key, d[key])`, `key` or `d[key]`
respectively), raises `RuntimeError`.

```python
from pysorteddict import *
d = SortedDict()
for i in range(5):
  d[i] = None
ii = reversed(d.items())
ki = reversed(d.keys())
vi = reversed(d.values())
assert (next(ii), next(ki), next(vi)) == ((4, None), 4, None)
del d[4]
```

```text
Traceback (most recent call last):
  File "…", line 9, in <module>
    del d[4]
        ~^^^
RuntimeError: operation not permitted: key-value pair locked by 3 iterator(s)
```

</details>

<details class="warning">

<summary>This method may behave differently with PyPy.</summary>

PyPy does not run the destructor of an object immediately after it becomes unreachable. Hence, prematurely-deleted
iterators will keep a key-value pair locked.

```python
import gc
from pysorteddict import *
d = SortedDict()
d["foo"] = "bar"
d["baz"] = 1
ii = iter(d.items())
ki = iter(d.keys())
vi = iter(d.values())
del ii, ki, vi
# gc.collect()
del d["baz"]
```

```text
Traceback (most recent call last):
  File "…", line 11, in <module>
    del d["baz"]
        ~^^^^^^^
RuntimeError: operation not permitted: key-value pair locked by 3 iterator(s)
```

Uncommenting the commented line runs any required destructors and makes this error go away.

</details>

#### `iter(d)`

Return a forward iterator over the keys in the sorted dictionary `d`. This is an efficient shorthand for
`iter(d.keys())`. Typical usage is to iterate directly over `d` instead of using this method.

```python
from pysorteddict import *
d = SortedDict()
d["foo"] = ()
d["bar"] = [100]
d["baz"] = 3.14
for key in d:
    print(key)
```

```text
bar
baz
foo
```

#### `reversed(d)`

Return a reverse iterator over the keys in the sorted dictionary `d`. This is an efficient shorthand for
`reversed(d.keys())`.

```python
from pysorteddict import *
d = SortedDict()
d["foo"] = ()
d["bar"] = [100]
d["baz"] = 3.14
for key in reversed(d):
    print(key)
```

```text
foo
baz
bar
```

### Other Methods

#### `d.clear()`

Remove all key-value pairs in the sorted dictionary `d`.

<details class="warning">

<summary>This method may raise exceptions.</summary>

If there exist unexhausted iterators over the items, keys or values of `d`, raises `RuntimeError`.

```python
from pysorteddict import *
d = SortedDict()
d["foo"] = "bar"
ii = iter(d.items())
ki = iter(d.keys())
vi = reversed(d.values())
d.clear()
```

```text
Traceback (most recent call last):
  File "…", line 7, in <module>
    d.clear()
RuntimeError: operation not permitted: sorted dictionary locked by 3 iterator(s)
```

</details>

<details class="warning">

<summary>This method may behave differently with PyPy.</summary>

PyPy does not run the destructor of an object immediately after it becomes unreachable. Hence, prematurely-deleted
iterators will keep a sorted dictionary locked.

```python
import gc
from pysorteddict import *
d = SortedDict()
d["foo"] = "bar"
ii = iter(d.items())
ki = iter(d.keys())
vi = reversed(d.values())
del ii, ki, vi
# gc.collect()
d.clear()
```

```text
Traceback (most recent call last):
  File "…", line 10, in <module>
    d.clear()
RuntimeError: operation not permitted: sorted dictionary locked by 3 iterator(s)
```

Uncommenting the commented line runs any required destructors and makes this error go away.

</details>

#### `d.copy() -> SortedDict`

Return a shallow copy of the sorted dictionary `d`.

#### `d.get(key: Any, default: Any = None, /) -> Any`

Return the value mapped to `key` in the sorted dictionary `d`, or `default` if `key` isn't in `d`.

```python
from pysorteddict import *
d = SortedDict()
d["foo"] = "bar"
assert d.get("foo") == "bar"
assert d.get("baz") is None
assert d.get("spam", "eggs") == "eggs"
```

<details class="warning">

<summary>This method may raise exceptions.</summary>

If no key-value pairs have been inserted into `d` yet, raises `RuntimeError`.

```python
from pysorteddict import *
d = SortedDict()
d.get("foo")
```

```text
Traceback (most recent call last):
  File "…", line 3, in <module>
    d.get("foo")
RuntimeError: key type not set: insert at least one item first
```

Otherwise, if `type(key)` does not match the type of the first key inserted into `d`, raises `TypeError`.

```python
from pysorteddict import *
d = SortedDict()
d["foo"] = ("bar", "baz")
d.get(100)
```

```text
Traceback (most recent call last):
  File "…", line 4, in <module>
    d.get(100)
TypeError: got key 100 of type <class 'int'>, want key of type <class 'str'>
```

Otherwise, if `key` is not comparable with instances of its type, raises `ValueError`.

```python
from pysorteddict import *
d = SortedDict()
d[1.1] = ("racecar",)
d.get(float("nan"))
```

```text
Traceback (most recent call last):
  File "…", line 4, in <module>
    d.get(float("nan"))
ValueError: got bad key nan of type <class 'float'>
```

</details>

#### `d.items() -> SortedDictItems`

Return a dynamic view on the items in the sorted dictionary `d`.

```python
from pysorteddict import *
d = SortedDict()
items = d.items()
d["foo"] = ()
print(items)
d["bar"] = [100]
print(items)
d["baz"] = 3.14
print(items)
```

```text
SortedDictItems([('foo', ())])
SortedDictItems([('bar', [100]), ('foo', ())])
SortedDictItems([('bar', [100]), ('baz', 3.14), ('foo', ())])
```

See [sorted dictionary views](#sorted-dictionary-views).

#### `d.keys() -> SortedDictKeys`

Return a dynamic view on the keys in the sorted dictionary `d`.

```python
from pysorteddict import *
d = SortedDict()
keys = d.keys()
d["foo"] = ()
print(keys)
d["bar"] = [100]
print(keys)
d["baz"] = 3.14
print(keys)
```

```text
SortedDictKeys(['foo'])
SortedDictKeys(['bar', 'foo'])
SortedDictKeys(['bar', 'baz', 'foo'])
```

See [sorted dictionary views](#sorted-dictionary-views).

#### `d.setdefault(key: Any, default: Any = None, /) -> Any`

Return [`d.get(key, default)`](#dgetkey-any-default-any--none----any), and map `default` to `key` if `key` isn't in the
sorted dictionary `d`.

```python
from pysorteddict import *
d = SortedDict()
d["foo"] = "bar"
assert d.setdefault("foo") == "bar"
assert d.setdefault("baz") is None
assert d["baz"] is None
assert d.setdefault("spam", "eggs") == "eggs"
assert d["spam"] == "eggs"
```

<details class="warning">

<summary>This method may raise exceptions.</summary>

If no key-value pairs have been inserted into `d` yet, raises `RuntimeError`.

```python
from pysorteddict import *
d = SortedDict()
d.setdefault("foo")
```

```text
Traceback (most recent call last):
  File "…", line 3, in <module>
    d.setdefault("foo")
RuntimeError: key type not set: insert at least one item first
```

Otherwise, if `type(key)` does not match the type of the first key inserted into `d`, raises `TypeError`.

```python
from pysorteddict import *
d = SortedDict()
d["foo"] = ("bar", "baz")
d.setdefault(100)
```

```text
Traceback (most recent call last):
  File "…", line 4, in <module>
    d.setdefault(100)
TypeError: got key 100 of type <class 'int'>, want key of type <class 'str'>
```

Otherwise, if `key` is not comparable with instances of its type, raises `ValueError`.

```python
from pysorteddict import *
d = SortedDict()
d[1.1] = ("racecar",)
d.setdefault(float("nan"))
```

```text
Traceback (most recent call last):
  File "…", line 4, in <module>
    d.setdefault(float("nan"))
ValueError: got bad key nan of type <class 'float'>
```

</details>

#### `d.values() -> SortedDictValues`

Return a dynamic view on the values in the sorted dictionary `d`.

```python
from pysorteddict import *
d = SortedDict()
values = d.values()
d["foo"] = ()
print(values)
d["bar"] = [100]
print(values)
d["baz"] = 3.14
print(values)
```

```text
SortedDictValues([()])
SortedDictValues([[100], ()])
SortedDictValues([[100], 3.14, ()])
```

See [sorted dictionary views](#sorted-dictionary-views).

## Sorted Dictionary Views

Sorted dictionary views are dynamic views on a sorted dictionary: they are immutable and cannot be used to mutate the
sorted dictionary, but always reflect its current state.

There are three view types:

* `SortedDictItems`, the return type of [`SortedDict.items`](#ditems---sorteddictitems);
* `SortedDictKeys`, the return type of [`SortedDict.keys`](#dkeys---sorteddictkeys); and
* `SortedDictValues`, the return type of [`SortedDict.values`](#dvalues---sorteddictvalues).

### Magic Methods

#### `repr(v)`

Return a human-readable representation of the sorted dictionary view `v`.

#### `len(v)`

Return the length of the sorted dictionary view `v`.

The behaviour is equivalent to that of [`len(d)`](#lend) where `d` is the underlying sorted dictionary.

#### `ob in v`

Return whether `ob` is present in the sorted dictionary view `v`.

If `v` is of type `SortedDictItems` and `ob` is not a two-element `tuple`, this expression evaluates to `False`. If
`ob` is a two-element `tuple`, the behaviour is equivalent to that of `ob[0] in d and d[ob[0]] == ob[1]`, where `d` is
the underlying sorted dictionary.

If `v` is of type `SortedDictKeys`, the behaviour is equivalent to that of [`ob in d`](#key-in-d), where, once again,
`d` is the underlying sorted dictionary.

Finally, if `v` is of type `SortedDictValues`, the behaviour is equivalent to that of `ob in l`, where `l` is a `list`
of the elements in `v` in the same order. (In other words, an element-by-element comparison is performed.)

#### `v[pos]` or `v[start:stop:step]`

Return the element at position `pos` or a `list` of elements in the slice denoted by `start`, `stop` and `step` in the
sorted dictionary view `v`.

The behaviour is equivalent to that of `l[pos]` or `l[start:stop:step]` respectively where `l` is a `list` of the
elements in `v` in the same order. In the second form, `start`, `stop` and `step` can be omitted, just
like when slicing a `list`.

```python
from pysorteddict import *
d = SortedDict()
items, keys, values = d.items(), d.keys(), d.values()
d["foo"] = ()
d["bar"] = [100]
d["baz"] = 3.14
d["spam"] = {}
d["eggs"] = ""
print(d)
print(keys[0], keys[2], values[4])
print(keys[:3])
print(items[1:])
print(values[-3:3])
print(items[-5:4:2])
print(keys[::-1])
```

```text
SortedDict({'bar': [100], 'baz': 3.14, 'eggs': '', 'foo': (), 'spam': {}})
bar eggs {}
['bar', 'baz', 'eggs']
[('baz', 3.14), ('eggs', ''), ('foo', ()), ('spam', {})]
['']
[('bar', [100]), ('eggs', '')]
['spam', 'foo', 'eggs', 'baz', 'bar']
```

#### `iter(v)`

Return a forward iterator over the sorted dictionary view `v`. Typical usage is to iterate directly over `v` instead of
using this method.

<details class="notice">

<summary>This method returns a mostly mutation-safe iterator.</summary>

A sorted dictionary can be modified while iterating over any of its views. (Whether this is good practice is a separate
question.)

```python
from pysorteddict import *
d = SortedDict()
d["foo"] = ()
d["bar"] = [100]
d["baz"] = 3.14
for key in d.keys():
    d[key] = "spam"
    d["a_" + key] = "eggs"
    if "foo" in d:
        del d["foo"]
print(d)
```

```text
SortedDict({'a_bar': 'eggs', 'a_baz': 'eggs', 'bar': 'spam', 'baz': 'spam'})
```

Some modifications are prohibited, however. See [`del d[key]`](#del-dkey) and [`d.clear()`](#dclear) for details.

</details>

#### `reversed(v)`

Return a reverse iterator over the sorted dictionary view `v`.

<details class="notice">

<summary>This method returns a mostly mutation-safe iterator.</summary>

As explained under [`iter(v)`](#iterv).

```python
from pysorteddict import *
d = SortedDict()
d["foo"] = ()
d["bar"] = [100]
d["baz"] = 3.14
for key in reversed(d.keys()):
    d[key] = "spam"
    d["z_" + key] = "eggs"
    if "bar" in d:
        del d["bar"]
print(d)
```

```text
SortedDict({'baz': 'spam', 'foo': 'spam', 'z_baz': 'eggs', 'z_foo': 'eggs'})
```

</details>
