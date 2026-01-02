
// generated from codegen/templates/_boundingbox2d.hpp

#ifndef EGEOMETRY_IBOUNDINGBOX2D_HPP
#define EGEOMETRY_IBOUNDINGBOX2D_HPP

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "structmember.h"

#include <glm/glm.hpp>

#include "_iboundingbox2dtype.hpp"
#include "_modulestate.hpp"


static PyObject *
IBoundingBox2d__new__(PyTypeObject *cls, PyObject *args, PyObject *kwds)
{
    ModuleState *module_state = get_module_state();
    if (!module_state){ return 0; }
    auto get_vector_ptr = module_state->emath_api->IVector2_GetValuePointer;

    PyTypeObject *vector_2_cls = module_state->emath_api->IVector2_GetType();

    PyObject *py_position = 0;
    PyObject *py_size = 0;
    IBoundingBox2d *self = 0;

    auto arg_count = PyTuple_GET_SIZE(args);
    auto kwarg_count = PyDict_Size(kwds);
    PyErr_Clear();

    if (arg_count == 2 && kwarg_count <= 0)
    {
        if (PyObject_TypeCheck(PyTuple_GET_ITEM(args, 0), vector_2_cls) == 0)
        {
            PyErr_SetString(
                PyExc_TypeError,
                "expected IVector2 for position argument"
            );
            return 0;
        }
        py_size = PyTuple_GET_ITEM(args, 1);
        auto size = (IBoundingBox2dGlmVector *)get_vector_ptr(py_size);
        if (size->x < 0 || size->y < 0)
        {
            PyErr_SetString(
                PyExc_ValueError,
                "each size dimension must be >= 0"
            );
            return 0;
        }
        py_position = PyTuple_GET_ITEM(args, 0);
        Py_INCREF(py_position);
        Py_INCREF(py_size);
    }
    else if (arg_count == 0 && kwarg_count == 1)
    {
        PyObject *py_shapes = PyDict_GetItemString(kwds, "shapes");
        if (!py_shapes){ goto invalid_args; }
        auto position = IBoundingBox2dGlmVector(0);
        auto extent = position;
        {
            PyObject *py_shapes_iter = PyObject_GetIter(py_shapes);
            if (!py_shapes_iter){ return 0; }
            {
                PyObject *py_shape;
                bool is_first_item = true;
                while((py_shape = PyIter_Next(py_shapes_iter)))
                {
                    IBoundingBox2dGlmVector shape_position;
                    IBoundingBox2dGlmVector shape_extent;
                    if (PyObject_TypeCheck(py_shape, vector_2_cls) != 0)
                    {
                        auto result = get_vector_ptr(py_shape);
                        if (!result)
                        {
                            Py_DECREF(py_shape);
                            Py_DECREF(py_shapes_iter);
                            return 0;
                        }
                        shape_position = *(IBoundingBox2dGlmVector *)result;
                        shape_extent = shape_position;
                    }
                    else
                    {
                        PyObject *py_shape_bb = PyObject_GetAttrString(py_shape, "bounding_box");
                        if (!py_shape_bb)
                        {
                            Py_DECREF(py_shape);
                            Py_DECREF(py_shapes_iter);
                            return 0;
                        }
                        if (PyObject_TypeCheck(py_shape_bb, cls) == 0)
                        {
                            Py_DECREF(py_shape_bb);
                            Py_DECREF(py_shape);
                            Py_DECREF(py_shapes_iter);
                            return 0;
                        }
                        auto result = get_vector_ptr(((IBoundingBox2d*)py_shape_bb)->py_position);
                        if (!result)
                        {
                            Py_DECREF(py_shape_bb);
                            Py_DECREF(py_shape);
                            Py_DECREF(py_shapes_iter);
                            return 0;
                        }
                        shape_position = *(IBoundingBox2dGlmVector *)result;
                        result = get_vector_ptr(((IBoundingBox2d*)py_shape_bb)->py_size);
                        if (!result)
                        {
                            Py_DECREF(py_shape_bb);
                            Py_DECREF(py_shape);
                            Py_DECREF(py_shapes_iter);
                            return 0;
                        }
                        shape_extent = shape_position + *(IBoundingBox2dGlmVector *)result;
                        Py_DECREF(py_shape_bb);
                    }
                    Py_DECREF(py_shape);
                    if (is_first_item)
                    {
                        is_first_item = false;
                        position = shape_position;
                        extent = shape_extent;
                    }
                    else
                    {
                        if (position.x > shape_position.x)
                        {
                            position.x = shape_position.x;
                        }
                        if (position.y > shape_position.y)
                        {
                            position.y = shape_position.y;
                        }
                        if (extent.x < shape_extent.x)
                        {
                            extent.x = shape_extent.x;
                        }
                        if (extent.y < shape_extent.y)
                        {
                            extent.y = shape_extent.y;
                        }
                    }
                }
                if (PyErr_Occurred())
                {
                    Py_DECREF(py_shapes_iter);
                    return 0;
                }
            }
            Py_DECREF(py_shapes_iter);
        }
        auto create_vector = module_state->emath_api->IVector2_Create;
        py_position = create_vector((int*)&position);
        if (!py_position){ return 0; }
        auto size = extent - position;
        py_size = create_vector((int*)&size);
        if (!py_size)
        {
            Py_DECREF(py_position);
            return 0;
        }
    }
    else
    {
        goto invalid_args;
    }

    self = (IBoundingBox2d*)cls->tp_alloc(cls, 0);
    if (!self)
    {
        Py_DECREF(py_position);
        Py_DECREF(py_size);
        return 0;
    }
    self->py_position = py_position;
    self->py_size = py_size;
    return (PyObject *)self;

invalid_args:
    PyErr_SetString(
        PyExc_TypeError,
        "IBoundingBox2d expects 2 positional arguments (position and size) or shapes keyword "
        "argument"
    );
    return 0;
}

static void
IBoundingBox2d__dealloc__(IBoundingBox2d *self)
{
    if (self->weakreflist)
    {
        PyObject_ClearWeakRefs((PyObject *)self);
    }

    Py_DECREF(self->py_position);
    Py_DECREF(self->py_size);

    PyTypeObject *type = Py_TYPE(self);
    type->tp_free(self);
    Py_DECREF(type);
}

// this is roughly copied from how python hashes tuples in 3.11
#if SIZEOF_PY_UHASH_T > 4
#define _HASH_XXPRIME_1 ((Py_uhash_t)11400714785074694791ULL)
#define _HASH_XXPRIME_2 ((Py_uhash_t)14029467366897019727ULL)
#define _HASH_XXPRIME_5 ((Py_uhash_t)2870177450012600261ULL)
#define _HASH_XXROTATE(x) ((x << 31) | (x >> 33))  /* Rotate left 31 bits */
#else
#define _HASH_XXPRIME_1 ((Py_uhash_t)2654435761UL)
#define _HASH_XXPRIME_2 ((Py_uhash_t)2246822519UL)
#define _HASH_XXPRIME_5 ((Py_uhash_t)374761393UL)
#define _HASH_XXROTATE(x) ((x << 13) | (x >> 19))  /* Rotate left 13 bits */
#endif
static Py_hash_t
IBoundingBox2d__hash__(IBoundingBox2d *self)
{
    Py_hash_t hashes[2];
    hashes[0] = PyObject_Hash(self->py_position);
    if (hashes[0] == -1){ return -1; }
    hashes[1] = PyObject_Hash(self->py_size);
    if (hashes[1] == -1){ return -1; }

    Py_ssize_t len = 2;
    Py_uhash_t acc = _HASH_XXPRIME_5;
    for (Py_ssize_t i = 0; i < len; i++)
    {
        acc += hashes[i] * _HASH_XXPRIME_2;
        acc = _HASH_XXROTATE(acc);
        acc *= _HASH_XXPRIME_1;
    }
    acc += len ^ (_HASH_XXPRIME_5 ^ 3527539UL);

    if (acc == (Py_uhash_t)-1) {
        return 1546275796;
    }
    return acc;
}

static PyObject *
IBoundingBox2d__repr__(IBoundingBox2d *self)
{
    return PyUnicode_FromFormat(
        "<IBoundingBox2d position=%S size=%S>",
        self->py_position,
        self->py_size
    );
}


static PyObject *
IBoundingBox2d__richcmp__(IBoundingBox2d *self, IBoundingBox2d *other, int op)
{
    ModuleState *module_state = get_module_state();
    if (!module_state){ return 0; }
    auto cls = module_state->IBoundingBox2d_PyTypeObject;

    if (PyObject_TypeCheck((PyObject *)other, cls) == 0)
    {
        Py_RETURN_NOTIMPLEMENTED;
    }

    auto get_vector_ptr = module_state->emath_api->IVector2_GetValuePointer;
    auto self_pos = (IBoundingBox2dGlmVector *)get_vector_ptr(self->py_position);
    if (!self_pos){ return 0; }
    auto other_pos = (IBoundingBox2dGlmVector *)get_vector_ptr(other->py_position);
    if (!other_pos){ return 0; }
    auto self_size = (IBoundingBox2dGlmVector *)get_vector_ptr(self->py_size);
    if (!self_size){ return 0; }
    auto other_size = (IBoundingBox2dGlmVector *)get_vector_ptr(other->py_size);
    if (!other_size){ return 0; }

    switch(op)
    {
        case Py_EQ:
        {
            if ((*self_pos) == (*other_pos) && (*self_size) == (*other_size))
            {
                Py_RETURN_TRUE;
            }
            else
            {
                Py_RETURN_FALSE;
            }
        }
        case Py_NE:
        {
            if ((*self_pos) != (*other_pos) || (*self_size) != (*other_size))
            {
                Py_RETURN_TRUE;
            }
            else
            {
                Py_RETURN_FALSE;
            }
        }
    }
    Py_RETURN_NOTIMPLEMENTED;
}

static PyObject *
IBoundingBox2d_clip(IBoundingBox2d *self, IBoundingBox2d *other)
{
    ModuleState *module_state = get_module_state();
    if (!module_state){ return 0; }
    auto cls = module_state->IBoundingBox2d_PyTypeObject;

    if (PyObject_TypeCheck((PyObject *)other, cls) == 0)
    {
        PyErr_SetObject(PyExc_TypeError, (PyObject *)other);
        return 0;
    }

    auto get_vector_ptr = module_state->emath_api->IVector2_GetValuePointer;

    auto self_position = (IBoundingBox2dGlmVector *)get_vector_ptr(self->py_position);
    if (!self_position){ return 0; }
    auto self_size = (IBoundingBox2dGlmVector *)get_vector_ptr(self->py_size);
    if (!self_size){ return 0; }
    auto self_extent = *self_position + *self_size;

    auto other_position = (IBoundingBox2dGlmVector *)get_vector_ptr(((IBoundingBox2d *)other)->py_position);
    if (!other_position){ return 0; }
    auto other_size = (IBoundingBox2dGlmVector *)get_vector_ptr(((IBoundingBox2d *)other)->py_size);
    if (!other_size){ return 0; }
    auto other_extent = *other_position + *other_size;

    auto result_position = IBoundingBox2dGlmVector(
        self_position->x > other_position->x ? self_position->x : other_position->x,
        self_position->y > other_position->y ? self_position->y : other_position->y
    );
    auto result_extent = IBoundingBox2dGlmVector(
        self_extent.x < other_extent.x ? self_extent.x : other_extent.x,
        self_extent.y < other_extent.y ? self_extent.y : other_extent.y
    );
    auto result_size = result_extent - result_position;
    if (result_size.x < 0 || result_size.y < 0)
    {
        result_size = IBoundingBox2dGlmVector(0);
    }

    auto create_vector_2 = module_state->emath_api->IVector2_Create;
    auto py_position = create_vector_2((int*)&result_position);
    if (!py_position){ return 0; }
    auto py_size = create_vector_2((int*)&result_size);
    if (!py_size)
    {
        Py_DECREF(py_position);
        return 0;
    }

    auto result = (IBoundingBox2d*)cls->tp_alloc(cls, 0);
    if (!result)
    {
        Py_DECREF(py_position);
        Py_DECREF(py_size);
        return 0;
    }
    result->py_position = py_position;
    result->py_size = py_size;
    return (PyObject *)result;
}



static PyObject *
IBoundingBox2d_overlaps_i_vector_2(IBoundingBox2d *self, PyObject *py_other)
{
    ModuleState *module_state = get_module_state();
    if (!module_state){ return 0; }
    auto get_vector_ptr = module_state->emath_api->IVector2_GetValuePointer;

    auto other = (IBoundingBox2dGlmVector *)get_vector_ptr(py_other);
    if (!other){ return 0; }

    auto position = (IBoundingBox2dGlmVector *)get_vector_ptr(self->py_position);
    if (!position){ return 0; }
    if (other->x < position->x || other->y < position->y)
    {
        Py_RETURN_FALSE;
    }

    auto size = (IBoundingBox2dGlmVector *)get_vector_ptr(self->py_size);
    if (!size){ return 0; }
    auto extent = *position + *size;
    if (other->x >= extent.x || other->y >= extent.y)
    {
        Py_RETURN_FALSE;
    }

    Py_RETURN_TRUE;
}

static PyObject *
IBoundingBox2d_overlaps(IBoundingBox2d *self, PyObject *other)
{
    ModuleState *module_state = get_module_state();
    if (!module_state){ return 0; }
    auto vector_2_cls = module_state->emath_api->IVector2_GetType();
    if (PyObject_TypeCheck(other, vector_2_cls) == 0)
    {
        auto other_overlaps = PyObject_GetAttrString(other, "overlaps_i_bounding_box_2d");
        if (!other_overlaps)
        {
            PyErr_SetObject(PyExc_TypeError, other);
            return 0;
        }
        return PyObject_CallOneArg(other_overlaps, (PyObject *)self);
    }
    return IBoundingBox2d_overlaps_i_vector_2(self, other);
}

static PyObject *
IBoundingBox2d_overlaps_i_bounding_box_2d(IBoundingBox2d *self, PyObject *other)
{
    ModuleState *module_state = get_module_state();
    if (!module_state){ return 0; }
    auto cls = module_state->IBoundingBox2d_PyTypeObject;

    if (PyObject_TypeCheck(other, cls) == 0)
    {
        PyErr_SetObject(PyExc_TypeError, other);
        return 0;
    }

    auto get_vector_ptr = module_state->emath_api->IVector2_GetValuePointer;

    auto self_position = (IBoundingBox2dGlmVector *)get_vector_ptr(self->py_position);
    if (!self_position){ return 0; }
    auto self_size = (IBoundingBox2dGlmVector *)get_vector_ptr(self->py_size);
    if (!self_size){ return 0; }
    auto self_extent = *self_position + *self_size;

    auto other_position = (IBoundingBox2dGlmVector *)get_vector_ptr(((IBoundingBox2d *)other)->py_position);
    if (!other_position){ return 0; }
    auto other_size = (IBoundingBox2dGlmVector *)get_vector_ptr(((IBoundingBox2d *)other)->py_size);
    if (!other_size){ return 0; }
    auto other_extent = *other_position + *other_size;

    if (
        self_position->x >= other_extent.x ||
        self_extent.x <= other_position->x ||
        self_position->y >= other_extent.y ||
        self_extent.y <= other_position->y
    )
    {
        Py_RETURN_FALSE;
    }
    Py_RETURN_TRUE;
}

static PyObject *
IBoundingBox2d_overlaps_i_reverse_lookup(IBoundingBox2d *self, PyObject *other)
{
    return PyObject_CallMethod(other, "overlaps_i_bounding_box_2d", "O", self);
}

static PyObject *
IBoundingBox2d_translate(IBoundingBox2d *self, PyObject *py_translation)
{
    ModuleState *module_state = get_module_state();
    if (!module_state){ return 0; }
    auto cls = module_state->IBoundingBox2d_PyTypeObject;
    auto get_vector_ptr = module_state->emath_api->IVector2_GetValuePointer;

    auto translation = (IBoundingBox2dGlmVector *)get_vector_ptr(py_translation);
    if (!translation){ return 0; }

    auto position = (IBoundingBox2dGlmVector *)get_vector_ptr(self->py_position);

    auto new_position = *position + *translation;

    auto py_new_position = module_state->emath_api->IVector2_Create((int*)&new_position);
    if (!py_new_position){ return 0; }

    auto result = (IBoundingBox2d*)cls->tp_alloc(cls, 0);
    if (!result)
    {
        Py_DECREF(py_new_position);
        return 0;
    }
    Py_INCREF(self->py_size);
    result->py_position = py_new_position;
    result->py_size = self->py_size;
    return (PyObject *)result;
}


static PyObject *
IBoundingBox2d_to_d(IBoundingBox2d *self, void *)
{
    ModuleState *module_state = get_module_state();
    if (!module_state){ return 0; }
    auto get_vector_ptr = module_state->emath_api->IVector2_GetValuePointer;

    auto position = (IBoundingBox2dGlmVector *)get_vector_ptr(self->py_position);
    if (!position){ return 0; }
    auto size = (IBoundingBox2dGlmVector *)get_vector_ptr(self->py_size);
    if (!size){ return 0; }

    auto to_position = glm::vec<2, double, glm::defaultp>(*position);
    auto to_size = glm::vec<2, double, glm::defaultp>(*size);

    auto create_to_vector = module_state->emath_api->DVector2_Create;
    auto py_to_position = create_to_vector((double*)&to_position);
    if (!py_to_position){ return 0; }
    auto py_to_size = create_to_vector((double*)&to_size);
    if (!py_to_size)
    {
        Py_DECREF(py_to_position);
        return 0;
    }

    auto to_cls = module_state->DBoundingBox2d_PyTypeObject;
    auto result = (IBoundingBox2d*)to_cls->tp_alloc(to_cls, 0);
    if (!result)
    {
        Py_DECREF(py_to_position);
        Py_DECREF(py_to_size);
        return 0;
    }
    result->py_position = py_to_position;
    result->py_size = py_to_size;
    return (PyObject *)result;
}

static PyObject *
IBoundingBox2d_to_f(IBoundingBox2d *self, void *)
{
    ModuleState *module_state = get_module_state();
    if (!module_state){ return 0; }
    auto get_vector_ptr = module_state->emath_api->IVector2_GetValuePointer;

    auto position = (IBoundingBox2dGlmVector *)get_vector_ptr(self->py_position);
    if (!position){ return 0; }
    auto size = (IBoundingBox2dGlmVector *)get_vector_ptr(self->py_size);
    if (!size){ return 0; }

    auto to_position = glm::vec<2, float, glm::defaultp>(*position);
    auto to_size = glm::vec<2, float, glm::defaultp>(*size);

    auto create_to_vector = module_state->emath_api->FVector2_Create;
    auto py_to_position = create_to_vector((float*)&to_position);
    if (!py_to_position){ return 0; }
    auto py_to_size = create_to_vector((float*)&to_size);
    if (!py_to_size)
    {
        Py_DECREF(py_to_position);
        return 0;
    }

    auto to_cls = module_state->FBoundingBox2d_PyTypeObject;
    auto result = (IBoundingBox2d*)to_cls->tp_alloc(to_cls, 0);
    if (!result)
    {
        Py_DECREF(py_to_position);
        Py_DECREF(py_to_size);
        return 0;
    }
    result->py_position = py_to_position;
    result->py_size = py_to_size;
    return (PyObject *)result;
}


static PyMethodDef IBoundingBox2d_PyMethodDef[] = {
    {"clip", (PyCFunction)IBoundingBox2d_clip, METH_O, 0},
    {"overlaps", (PyCFunction)IBoundingBox2d_overlaps, METH_O, 0},
    {"overlaps_i_vector_2", (PyCFunction)IBoundingBox2d_overlaps_i_vector_2, METH_O, 0},
    {"overlaps_i_bounding_box_2d", (PyCFunction)IBoundingBox2d_overlaps_i_bounding_box_2d, METH_O, 0},
    {"overlaps_i_circle", (PyCFunction)IBoundingBox2d_overlaps_i_reverse_lookup, METH_O, 0},
    {"overlaps_i_rectangle", (PyCFunction)IBoundingBox2d_overlaps_i_reverse_lookup, METH_O, 0},
    {"overlaps_i_triangle_2d", (PyCFunction)IBoundingBox2d_overlaps_i_reverse_lookup, METH_O, 0},
    {"translate", (PyCFunction)IBoundingBox2d_translate, METH_O, 0},

    {"to_d", (PyCFunction)IBoundingBox2d_to_d, METH_NOARGS, 0},

    {"to_f", (PyCFunction)IBoundingBox2d_to_f, METH_NOARGS, 0},

    {0, 0, 0, 0}
};

static PyMemberDef IBoundingBox2d_PyMemberDef[] = {
    {"__weaklistoffset__", T_PYSSIZET, offsetof(IBoundingBox2d, weakreflist), READONLY},
    {"position", T_OBJECT_EX, offsetof(IBoundingBox2d, py_position), READONLY},
    {"size", T_OBJECT_EX, offsetof(IBoundingBox2d, py_size), READONLY},
    {0, 0, 0, 0, 0},
};

static PyObject *
IBoundingBox2d_bounding_box(IBoundingBox2d *self, void *)
{
    Py_INCREF(self);
    return (PyObject *)self;
}

static PyObject *
IBoundingBox2d_extent(IBoundingBox2d *self, void *)
{
    auto module_state = get_module_state();
    if (!module_state){ return 0; }

    EMathApi_GetIVector2ValuePointer get_vector_ptr = module_state->emath_api->IVector2_GetValuePointer;

    IBoundingBox2dGlmVector *position = (IBoundingBox2dGlmVector *)get_vector_ptr(self->py_position);
    if (!position){ return 0; }
    IBoundingBox2dGlmVector *size = (IBoundingBox2dGlmVector *)get_vector_ptr(self->py_size);
    if (!size){ return 0; }

    IBoundingBox2dGlmVector extent = *position + *size;

    return module_state->emath_api->IVector2_Create((int *)&extent);
}

static PyObject *
IBoundingBox2d_points(IBoundingBox2d *self, void *)
{
    auto module_state = get_module_state();
    if (!module_state){ return 0; }

    auto get_vector_ptr = module_state->emath_api->IVector2_GetValuePointer;
    auto create_vector = module_state->emath_api->IVector2_Create;

    IBoundingBox2dGlmVector *position = (IBoundingBox2dGlmVector *)get_vector_ptr(self->py_position);
    if (!position){ return 0; }
    IBoundingBox2dGlmVector *size = (IBoundingBox2dGlmVector *)get_vector_ptr(self->py_size);
    if (!size){ return 0; }

    auto top_right = IBoundingBox2dGlmVector4(position->x + size->x, position->y, 0, 1);
    auto bottom_right = IBoundingBox2dGlmVector4(position->x + size->x, position->y + size->y, 0, 1);
    auto bottom_left = IBoundingBox2dGlmVector4(position->x, position->y + size->y, 0, 1);

    PyObject *py_result = PyTuple_New(4);
    if (!py_result){ return 0; }

    Py_INCREF(self->py_position);
    PyTuple_SET_ITEM(py_result, 0, self->py_position);

    auto py_top_right = create_vector((int*)&top_right);
    if (!py_top_right)
    {
        Py_DECREF(py_result);
        return 0;
    }
    PyTuple_SET_ITEM(py_result, 1, py_top_right);

    auto py_bottom_right = create_vector((int*)&bottom_right);
    if (!py_bottom_right)
    {
        Py_DECREF(py_result);
        return 0;
    }
    PyTuple_SET_ITEM(py_result, 2, py_bottom_right);

    auto py_bottom_left = create_vector((int*)&bottom_left);
    if (!py_bottom_left)
    {
        Py_DECREF(py_result);
        return 0;
    }
    PyTuple_SET_ITEM(py_result, 3, py_bottom_left);

    return py_result;
}

static PyGetSetDef IBoundingBox2d_PyGetSetDef[] = {
    {"bounding_box", (getter)IBoundingBox2d_bounding_box, 0, 0, 0},
    {"extent", (getter)IBoundingBox2d_extent, 0, 0, 0},
    {"points", (getter)IBoundingBox2d_points, 0, 0, 0},
    {0, 0, 0, 0, 0}
};

static PyType_Slot IBoundingBox2d_PyType_Slots [] = {
    {Py_tp_new, (void*)IBoundingBox2d__new__},
    {Py_tp_dealloc, (void*)IBoundingBox2d__dealloc__},
    {Py_tp_hash, (void*)IBoundingBox2d__hash__},
    {Py_tp_repr, (void*)IBoundingBox2d__repr__},
    {Py_tp_richcompare, (void*)IBoundingBox2d__richcmp__},

    {Py_tp_members, (void*)IBoundingBox2d_PyMemberDef},
    {Py_tp_getset, (void*)IBoundingBox2d_PyGetSetDef},
    {Py_tp_methods, (void*)IBoundingBox2d_PyMethodDef},
    {0, 0},
};

static PyType_Spec IBoundingBox2d_PyTypeSpec = {
    "egeometry.IBoundingBox2d",
    sizeof(IBoundingBox2d),
    0,
    Py_TPFLAGS_DEFAULT,
    IBoundingBox2d_PyType_Slots
};

static PyTypeObject *
define_IBoundingBox2d_type(PyObject *module)
{
    PyTypeObject *type = (PyTypeObject *)PyType_FromModuleAndSpec(
        module,
        &IBoundingBox2d_PyTypeSpec,
        0
    );
    if (!type){ return 0; }
    // Note:
    // Unlike other functions that steal references, PyModule_AddObject() only
    // decrements the reference count of value on success.
    if (PyModule_AddObject(module, "IBoundingBox2d", (PyObject *)type) < 0)
    {
        Py_DECREF(type);
        return 0;
    }
    return type;
}

#endif
