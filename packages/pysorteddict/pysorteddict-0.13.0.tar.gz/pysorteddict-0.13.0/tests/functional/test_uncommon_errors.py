import pytest

from pysorteddict import SortedDict


def test_key_repr_error():
    sorted_dict = SortedDict()
    sorted_dict[2**15000] = 0
    with pytest.raises(ValueError, match="Exceeds the limit"):
        str(sorted_dict)


def test_value_repr_error():
    sorted_dict = SortedDict()
    sorted_dict[0] = 2**15000
    with pytest.raises(ValueError, match="Exceeds the limit"):
        str(sorted_dict)
