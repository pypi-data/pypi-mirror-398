# Repository

[Explore the repository on GitHub.](https://github.com/tfpf/pysorteddict)

Related components are grouped into directories.

## `docs/`

Code for the static website you are viewing right now.

## `src/pysorteddict/`

Core logic.

### `sorted_dict_type.cc`

Implementation of the Python `SortedDict` type.

### `sorted_dict_view_type.cc`

Implementation of views over `SortedDict` objects—superclasses of `SortedDictItems`, `SortedDictItemsIter`,
`SortedDictKeys`,  `SortedDictKeysIter`, `SortedDictValues` and `SortedDictValuesIter`.

### `sorted_dict_items_type.cc`

Implementation of the Python `SortedDictItems` and `SortedDictItemsIter` types. Exposed to users only indirectly via
`SortedDict.items`.

### `sorted_dict_keys_type.cc`

Implementation of the Python `SortedDictKeys` and `SortedDictKeysIter` types. Exposed to users only indirectly via
`SortedDict.keys`.

### `sorted_dict_values_type.cc`

Implementation of the Python `SortedDictValues` and `SortedDictValuesIter` types. Exposed to users only indirectly via
`SortedDict.values`.

### `sorted_dict_module.cc`

Implementation of the Python `pysorteddict` module. Glue between Python methods and C++ methods.

### `sorted_dict_utils.hh`

Miscellanies for ease of development.

## `tests/functional/`

Functional (behavioural) tests.

### `test_fuzz.py`

Randomised tests which cover most scenarios.

### `test_keys_iter.py`

Tests for `SortedDictKeysIter`.

### `test_uncommon_errors.py`

Tests for errors not expected to occur during regular usage.

## `tests/performance/`

Performance tests.

### `performance.ipynb`

Tests to benchmark the performance of some methods.
