#! /usr/bin/env python3

from pysorteddict import SortedDict

sorted_dict = SortedDict()
sorted_dict["honestly"] = "weight"
sorted_dict["gain is"] = 31.692
sorted_dict["times"] = "easier than"
sorted_dict["losing"] = ["weight"]

assert sorted_dict.key_type is str

for key, value in sorted_dict.items():
    print(key, "->", value)
