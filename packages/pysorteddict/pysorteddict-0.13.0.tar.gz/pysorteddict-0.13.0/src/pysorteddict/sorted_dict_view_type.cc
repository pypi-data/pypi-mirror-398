#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <algorithm>
#include <map>

#include "sorted_dict_type.hh"
#include "sorted_dict_utils.hh"
#include "sorted_dict_view_type.hh"

/**
 * Do all the necessary bookkeeping required to start tracking the given
 * forward iterator of the underlying sorted dictionary.
 *
 * The caller should ensure that this method is called immediately after the
 * iterator member is updated.
 *
 * @param it Current value of the iterator member.
 */
template<>
void SortedDictViewIterType<FwdIterType>::track(FwdIterType it)
{
    if (it == this->sd->map->begin())
    {
        Py_INCREF(this->sd);
        ++this->sd->known_referrers;
        this->should_raise_stop_iteration = false;
    }
    if (it != this->sd->map->end())
    {
        ++it->second.known_referrers;
    }
    else
    {
        this->should_raise_stop_iteration = true;
        --this->sd->known_referrers;
        Py_DECREF(this->sd);
    }
}

/**
 * Do all the necessary bookkeeping required to start tracking the given
 * reverse iterator of the underlying sorted dictionary.
 *
 * The caller should ensure that this method is called immediately after the
 * iterator member is updated.
 *
 * @param it Current value of the iterator member.
 */
template<>
void SortedDictViewIterType<RevIterType>::track(RevIterType it)
{
    if (it == this->sd->map->rbegin())
    {
        Py_INCREF(this->sd);
        ++this->sd->known_referrers;
        this->should_raise_stop_iteration = false;
    }
    if (it != this->sd->map->rend())
    {
        FwdIterType it_base = it.base();
        if (it_base != this->sd->map->end())
        {
            ++it_base->second.known_referrers;
        }
    }
    else
    {
        this->should_raise_stop_iteration = true;
        --this->sd->known_referrers;
        Py_DECREF(this->sd);
    }
}

/**
 * Do all the necessary bookkeeping required to stop tracking the given forward
 * iterator of the underlying sorted dictionary.
 *
 * The caller should ensure that this method is called immediately after the
 * iterator member is updated.
 *
 * @param it Previous value of the iterator member.
 */
template<>
void SortedDictViewIterType<FwdIterType>::untrack(FwdIterType it)
{
    --it->second.known_referrers;
}

/**
 * Do all the necessary bookkeeping required to stop tracking the given reverse
 * iterator of the underlying sorted dictionary.
 *
 * The caller should ensure that this method is called immediately after the
 * iterator member is updated.
 *
 * @param it Previous value of the iterator member.
 */
template<>
void SortedDictViewIterType<RevIterType>::untrack(RevIterType it)
{
    FwdIterType it_base = it.base();
    if (it_base != this->sd->map->end())
    {
        --it_base->second.known_referrers;
    }
}

template<typename T>
void SortedDictViewIterType<T>::Delete(PyObject* self)
{
    SortedDictViewIterType<T>* sdvi = reinterpret_cast<SortedDictViewIterType<T>*>(self);
    if (!sdvi->should_raise_stop_iteration)
    {
        sdvi->untrack(sdvi->it);
        --sdvi->sd->known_referrers;
        Py_DECREF(sdvi->sd);
    }
    Py_TYPE(self)->tp_free(self);
}

template<typename T>
PyObject* SortedDictViewIterType<T>::next(void)
{
    if (this->should_raise_stop_iteration)
    {
        return nullptr;
    }

    // The 'next' key-value pair is the current one the iterator points to.
    T curr = this->it++;
    this->untrack(curr);
    this->track(this->it);
    return this->iterator_to_object(curr);
}

template<>
PyObject* SortedDictViewIterType<FwdIterType>::New(
    PyTypeObject* type, SortedDictType* sd, IteratorToObject<FwdIterType> forward_iterator_to_object
)
{
    PyObject* self = type->tp_alloc(type, 0);  // 🆕
    if (self == nullptr)
    {
        return nullptr;
    }

    SortedDictViewIterType<FwdIterType>* sdvi = reinterpret_cast<SortedDictViewIterType<FwdIterType>*>(self);
    sdvi->sd = sd;
    sdvi->it = sdvi->sd->map->begin();
    sdvi->track(sdvi->it);
    sdvi->iterator_to_object = forward_iterator_to_object;
    return self;
}

template<>
PyObject* SortedDictViewIterType<RevIterType>::New(
    PyTypeObject* type, SortedDictType* sd, IteratorToObject<RevIterType> reverse_iterator_to_object
)
{
    PyObject* self = type->tp_alloc(type, 0);  // 🆕
    if (self == nullptr)
    {
        return nullptr;
    }

    SortedDictViewIterType<RevIterType>* sdvi = reinterpret_cast<SortedDictViewIterType<RevIterType>*>(self);
    sdvi->sd = sd;
    sdvi->it = sdvi->sd->map->rbegin();
    sdvi->track(sdvi->it);
    sdvi->iterator_to_object = reverse_iterator_to_object;
    return self;
}

PyObject* SortedDictViewType::getitem(Py_ssize_t position)
{
    Py_ssize_t sz = this->sd->len();
    if (sz == -1)
    {
        return nullptr;
    }
    Py_ssize_t positive_position = position >= 0 ? position : position + sz;
    if (positive_position < 0 || sz <= positive_position)
    {
        PyErr_Format(PyExc_IndexError, "got invalid index %zd for view of length %zd", position, sz);
        return nullptr;
    }
    FwdIterType it;
    if (positive_position <= sz / 2)
    {
        it = this->sd->map->begin();
        std::advance(it, positive_position);
    }
    else
    {
        it = this->sd->map->end();
        std::advance(it, positive_position - sz);
    }
    return this->forward_iterator_to_object(it);
}

PyObject* SortedDictViewType::getitem(Py_ssize_t start, Py_ssize_t stop, Py_ssize_t step)
{
    Py_ssize_t sz = this->sd->len();
    if (sz == -1)
    {
        return nullptr;
    }
    Py_ssize_t slice_len = PySlice_AdjustIndices(sz, &start, &stop, step);
    PyObject* lst = PyList_New(slice_len);  // 🆕
    if (slice_len == 0)
    {
        return lst;
    }

    FwdIterType it;
    if ((step > 0 && start <= sz - stop) || (step < 0 && sz - 1 - start < stop + 1))
    {
        if (step > 0)
        {
            it = this->sd->map->begin();
            std::advance(it, start);
        }
        else
        {
            it = this->sd->map->end();
            std::advance(it, start - sz);
        }
        for (Py_ssize_t i = 0;; ++i)
        {
            PyList_SET_ITEM(lst, i, this->forward_iterator_to_object(it));
            if (i == slice_len - 1)
            {
                break;
            }
            std::advance(it, step);
        }
    }
    else
    {
        start += (slice_len - 1) * step;
        if (step > 0)
        {
            it = this->sd->map->end();
            std::advance(it, start - sz);
        }
        else
        {
            it = this->sd->map->begin();
            std::advance(it, start);
        }
        for (Py_ssize_t i = slice_len - 1;; --i)
        {
            PyList_SET_ITEM(lst, i, this->forward_iterator_to_object(it));
            if (i == 0)
            {
                break;
            }
            std::advance(it, -step);
        }
    }
    return lst;
}

void SortedDictViewType::Delete(PyObject* self)
{
    SortedDictViewType* sdv = reinterpret_cast<SortedDictViewType*>(self);
    Py_DECREF(sdv->sd);
    Py_TYPE(self)->tp_free(self);
}

PyObject* SortedDictViewType::repr(PyObject* ob)
{
    PyObjectWrapper ob_list(PySequence_List(ob));  // 🆕
    if (ob_list == nullptr)
    {
        return nullptr;
    }
    // The full name contains the package name, which is fixed. Remove it.
    // Hacky, but shouldn't break.
    return PyUnicode_FromFormat("%s(%R)", Py_TYPE(ob)->tp_name + 13, ob_list.get());
}

Py_ssize_t SortedDictViewType::len(void)
{
    return this->sd->len();
}

PyObject* SortedDictViewType::getitem(PyObject* idx)
{
    if (PyIndex_Check(idx))
    {
        Py_ssize_t position = PyNumber_AsSsize_t(idx, PyExc_IndexError);
        if (position == -1 && PyErr_Occurred() != nullptr)
        {
            return nullptr;
        }
        return this->getitem(position);
    }

    if (PySlice_Check(idx))
    {
        Py_ssize_t start, stop, step;
        if (PySlice_Unpack(idx, &start, &stop, &step) != 0)
        {
            return nullptr;
        }
        return this->getitem(start, stop, step);
    }

    PyErr_Format(
        PyExc_TypeError, "got index %R of type %R, want index of type %R or %R", idx, Py_TYPE(idx), &PyLong_Type,
        &PySlice_Type
    );
    return nullptr;
}

PyObject* SortedDictViewType::iter(PyTypeObject* type)
{
    return SortedDictViewIterType<FwdIterType>::New(type, this->sd, this->forward_iterator_to_object);
}

PyObject* SortedDictViewType::reversed(PyTypeObject* type)
{
    return SortedDictViewIterType<RevIterType>::New(type, this->sd, this->reverse_iterator_to_object);
}

PyObject* SortedDictViewType::New(
    PyTypeObject* type, SortedDictType* sd, IteratorToObject<FwdIterType> forward_iterator_to_object,
    IteratorToObject<RevIterType> reverse_iterator_to_object
)
{
    PyObject* self = type->tp_alloc(type, 0);  // 🆕
    if (self == nullptr)
    {
        return nullptr;
    }

    SortedDictViewType* sdv = reinterpret_cast<SortedDictViewType*>(self);
    sdv->sd = sd;
    Py_INCREF(sdv->sd);
    sdv->forward_iterator_to_object = forward_iterator_to_object;
    sdv->reverse_iterator_to_object = reverse_iterator_to_object;
    return self;
}

template struct SortedDictViewIterType<FwdIterType>;
template struct SortedDictViewIterType<RevIterType>;
