#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <map>

#include "sorted_dict_keys_type.hh"
#include "sorted_dict_type.hh"
#include "sorted_dict_view_type.hh"

template<typename T>
static PyObject* iterator_to_object(T it)
{
    return Py_NewRef(it->first);  // 🆕
}

template<typename T>
PyObject* SortedDictKeysIterType<T>::New(PyTypeObject* type, SortedDictType* sd)
{
    return SortedDictViewIterType<T>::New(type, sd, iterator_to_object<T>);
}

int SortedDictKeysType::contains(PyObject* key)
{
    return this->sd->contains(key);
}

PyObject* SortedDictKeysType::New(PyTypeObject* type, SortedDictType* sd)
{
    return SortedDictViewType::New(type, sd, iterator_to_object<FwdIterType>, iterator_to_object<RevIterType>);
}

template struct SortedDictKeysIterType<FwdIterType>;
template struct SortedDictKeysIterType<RevIterType>;
