#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <map>

#include "sorted_dict_type.hh"
#include "sorted_dict_values_type.hh"
#include "sorted_dict_view_type.hh"

template<typename T>
static PyObject* iterator_to_object(T it)
{
    return Py_NewRef(it->second.value);  // 🆕
}

PyObject* SortedDictValuesType::New(PyTypeObject* type, SortedDictType* sd)
{
    return SortedDictViewType::New(type, sd, iterator_to_object<FwdIterType>, iterator_to_object<RevIterType>);
}

template struct SortedDictValuesIterType<FwdIterType>;
template struct SortedDictValuesIterType<RevIterType>;
