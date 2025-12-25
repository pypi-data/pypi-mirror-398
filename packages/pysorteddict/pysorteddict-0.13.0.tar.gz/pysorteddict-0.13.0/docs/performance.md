# Performance

The table below describes the environment the performance benchmarks were run in.

| Component                      | Specification                              |
| :----------------------------: | :----------------------------------------: |
| CPU                            | Intel Core i9-12900H                       |
| CPU Frequency Scaling Governor | powersave                                  |
| RAM                            | 16 GiB DDR4                                |
| Kernel                         | Linux 6.1.0 (64-bit)                       |
| Operating System               | Debian 12 "bookworm"                       |
| Operating System Libraries     | GNU C Library 2.36, GNU C++ Library 12.2.0 |
| Python Interpreter             | CPython 3.11.2                             |
| Python Interpreter Libraries   | Jupyter 1.1.1, pysorteddict 0.12.1         |

The key type chosen was `float`, since it is easy to generate floating-point numbers uniformly distributed in the unit
interval. Comparing two `float`s is straightforward (as opposed to comparing, say, two `str`s—if their lengths are
different, they may introduce noise in the benchmarks). Before every benchmark, the random number generator was seeded
with _π_, a nothing-up-my-sleeve number.

There is an extra step required when using `float` keys: the check for NaN. Hence, the performance will be marginally
worse than if `int` keys were used.

<div class="notice">
The performance benchmarking code is in a Jupyter notebook in the GitHub repository. It contains everything required to
run the benchmarks.
</div>

## Overview

The average execution times of some expressions are tabulated against the lengths of the sorted dictionaries used.

| Expression                       | &emsp;10<sup>2</sup>&emsp; | &emsp;10<sup>3</sup>&emsp; | &emsp;10<sup>4</sup>&emsp; | &emsp;10<sup>5</sup>&emsp; | &emsp;10<sup>6</sup>&emsp; | &emsp;10<sup>7</sup>&emsp; |
| :------------------------------: | :------------------------: | :------------------------: | :------------------------: | :------------------------: | :------------------------: | :------------------------: |
| `0.00 in d`                      | 36.8 ns                    | 49.6 ns                    | 65.0 ns                    | 83.0 ns                    | 93.2 ns                    | 105 ns                     |
| `0.33 in d`                      | 46.3 ns                    | 60.5 ns                    | 67.4 ns                    | 82.9 ns                    | 98.7 ns                    | 112 ns                     |
| `0.67 in d`                      | 40.4 ns                    | 57.0 ns                    | 67.6 ns                    | 77.1 ns                    | 97.2 ns                    | 113 ns                     |
| `1.00 in d`                      | 31.7 ns                    | 58.9 ns                    | 62.9 ns                    | 82.3 ns                    | 90.4 ns                    | 111 ns                     |
| `set_del(d, keys_33)`            | 4.10 μs                    | 5.08 μs                    | 6.06 μs                    | 6.96 μs                    | 8.02 μs                    | 9.89 μs                    |
| `set_del(d, keys_67)`            | 8.50 μs                    | 10.3 μs                    | 12.7 μs                    | 15.9 μs                    | 21.7 μs                    | 31.5 μs                    |
| `set_del(d, keys_100)`           | 13.0 μs                    | 16.1 μs                    | 22.6 μs                    | 30.2 μs                    | 42.6 μs                    | 62.8 μs                    |
| `for _ in d: pass`               | 857 ns                     | 8.73 μs                    | 132 μs                     | 2.65 ms                    | 117 ms                     | 1.32 s                     |
| `for _ in reversed(d): pass`     | 1.12 μs                    | 11.6 μs                    | 160 μs                     | 3.02 ms                    | 119 ms                     | 1.40 s                     |

## Details

### Membership Check

The numbers 0.00, 0.33, 0.67 and 1.00 are spaced equally in the range spanned by the keys, but are absent in the sorted
dictionaries constructed using the seeded random number generator described above. Hence, a search for them in any of
those sorted dictionaries will not terminate permaturely.

```{image} _static/images/perf-contains-light.svg
:align: center
:class: only-light
:width: 100%
```

```{image} _static/images/perf-contains-dark.svg
:align: center
:class: only-dark
:width: 100%
```

### Insertion and Deletion

Inserting or deleting an item into or from a sorted dictionary changes its length. Hence, benchmarks which only insert
or only delete items cannot be said to have been performed on a sorted dictionary of a particular length. Therefore,
the strategy chosen was:

* generate a `list` of random `float`s;
* insert all of them into the sorted dictionary; and
* delete all of them from the sorted dictionary in order of insertion.

Only the last two steps (defined in a function `set_del`) were timed. After these, ideally, the sorted dictionary
should return to the original state, allowing it to be used for the next round of timing. In practice, it is likely to
be in a different state because of rebalancing operations. But that change of state can be assumed to simulate the
real-world effects of insertions and deletions, so this is a sound strategy.

This benchmark was repeated for three different lengths of the `list` of random `float`s: 33, 67 and 100.

```{image} _static/images/perf-setitem-light.svg
:align: center
:class: only-light
:width: 100%
```

```{image} _static/images/perf-setitem-dark.svg
:align: center
:class: only-dark
:width: 100%
```

### Iteration

```{image} _static/images/perf-iter-light.svg
:align: center
:class: only-light
:width: 100%
```

```{image} _static/images/perf-iter-dark.svg
:align: center
:class: only-dark
:width: 100%
```
