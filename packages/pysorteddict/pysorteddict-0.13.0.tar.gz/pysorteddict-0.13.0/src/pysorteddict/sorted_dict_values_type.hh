#ifndef SORTED_DICT_VALUES_TYPE_HH_
#define SORTED_DICT_VALUES_TYPE_HH_

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "sorted_dict_view_type.hh"

template<typename T>
struct SortedDictValuesIterType : public SortedDictViewIterType<T>
{
};

struct SortedDictValuesType : public SortedDictViewType
{
public:
    static PyObject* New(PyTypeObject*, SortedDictType*);
};

#endif
