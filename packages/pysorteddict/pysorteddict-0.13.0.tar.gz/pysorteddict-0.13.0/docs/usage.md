# Usage

All keys in a sorted dictionary must be of the same type, which is determined when the first key-value pair is inserted
into it. The values, though, can be of any type.

```python
from pysorteddict import SortedDict

sorted_dict = SortedDict()
sorted_dict["honestly"] = "weight"
sorted_dict["gain is"] = 31.692
sorted_dict["times"] = "easier than"
sorted_dict["losing"] = ["weight"]

assert sorted_dict.key_type is str

for key, value in sorted_dict.items():
    print(key, "->", value)
```

The above Python script will output the keys in ascending order.

```text
gain is -> 31.692
honestly -> weight
losing -> ['weight']
times -> easier than
```
