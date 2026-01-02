
// generated from codegen/templates/_boundingbox2d.hpp

#ifndef EGEOMETRY_FBOUNDINGBOX2D_HPP
#define EGEOMETRY_FBOUNDINGBOX2D_HPP

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "structmember.h"

#include <glm/glm.hpp>

#include "_fboundingbox2dtype.hpp"
#include "_modulestate.hpp"


static PyObject *
FBoundingBox2d__new__(PyTypeObject *cls, PyObject *args, PyObject *kwds)
{
    ModuleState *module_state = get_module_state();
    if (!module_state){ return 0; }
    auto get_vector_ptr = module_state->emath_api->FVector2_GetValuePointer;

    PyTypeObject *vector_2_cls = module_state->emath_api->FVector2_GetType();

    PyObject *py_position = 0;
    PyObject *py_size = 0;
    FBoundingBox2d *self = 0;

    auto arg_count = PyTuple_GET_SIZE(args);
    auto kwarg_count = PyDict_Size(kwds);
    PyErr_Clear();

    if (arg_count == 2 && kwarg_count <= 0)
    {
        if (PyObject_TypeCheck(PyTuple_GET_ITEM(args, 0), vector_2_cls) == 0)
        {
            PyErr_SetString(
                PyExc_TypeError,
                "expected FVector2 for position argument"
            );
            return 0;
        }
        py_size = PyTuple_GET_ITEM(args, 1);
        auto size = (FBoundingBox2dGlmVector *)get_vector_ptr(py_size);
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
        auto position = FBoundingBox2dGlmVector(0);
        auto extent = position;
        {
            PyObject *py_shapes_iter = PyObject_GetIter(py_shapes);
            if (!py_shapes_iter){ return 0; }
            {
                PyObject *py_shape;
                bool is_first_item = true;
                while((py_shape = PyIter_Next(py_shapes_iter)))
                {
                    FBoundingBox2dGlmVector shape_position;
                    FBoundingBox2dGlmVector shape_extent;
                    if (PyObject_TypeCheck(py_shape, vector_2_cls) != 0)
                    {
                        auto result = get_vector_ptr(py_shape);
                        if (!result)
                        {
                            Py_DECREF(py_shape);
                            Py_DECREF(py_shapes_iter);
                            return 0;
                        }
                        shape_position = *(FBoundingBox2dGlmVector *)result;
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
                        auto result = get_vector_ptr(((FBoundingBox2d*)py_shape_bb)->py_position);
                        if (!result)
                        {
                            Py_DECREF(py_shape_bb);
                            Py_DECREF(py_shape);
                            Py_DECREF(py_shapes_iter);
                            return 0;
                        }
                        shape_position = *(FBoundingBox2dGlmVector *)result;
                        result = get_vector_ptr(((FBoundingBox2d*)py_shape_bb)->py_size);
                        if (!result)
                        {
                            Py_DECREF(py_shape_bb);
                            Py_DECREF(py_shape);
                            Py_DECREF(py_shapes_iter);
                            return 0;
                        }
                        shape_extent = shape_position + *(FBoundingBox2dGlmVector *)result;
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
        auto create_vector = module_state->emath_api->FVector2_Create;
        py_position = create_vector((float*)&position);
        if (!py_position){ return 0; }
        auto size = extent - position;
        py_size = create_vector((float*)&size);
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

    self = (FBoundingBox2d*)cls->tp_alloc(cls, 0);
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
        "FBoundingBox2d expects 2 positional arguments (position and size) or shapes keyword "
        "argument"
    );
    return 0;
}

static void
FBoundingBox2d__dealloc__(FBoundingBox2d *self)
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
FBoundingBox2d__hash__(FBoundingBox2d *self)
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
FBoundingBox2d__repr__(FBoundingBox2d *self)
{
    return PyUnicode_FromFormat(
        "<FBoundingBox2d position=%S size=%S>",
        self->py_position,
        self->py_size
    );
}


static PyObject *
FBoundingBox2d__richcmp__(FBoundingBox2d *self, FBoundingBox2d *other, int op)
{
    ModuleState *module_state = get_module_state();
    if (!module_state){ return 0; }
    auto cls = module_state->FBoundingBox2d_PyTypeObject;

    if (PyObject_TypeCheck((PyObject *)other, cls) == 0)
    {
        Py_RETURN_NOTIMPLEMENTED;
    }

    auto get_vector_ptr = module_state->emath_api->FVector2_GetValuePointer;
    auto self_pos = (FBoundingBox2dGlmVector *)get_vector_ptr(self->py_position);
    if (!self_pos){ return 0; }
    auto other_pos = (FBoundingBox2dGlmVector *)get_vector_ptr(other->py_position);
    if (!other_pos){ return 0; }
    auto self_size = (FBoundingBox2dGlmVector *)get_vector_ptr(self->py_size);
    if (!self_size){ return 0; }
    auto other_size = (FBoundingBox2dGlmVector *)get_vector_ptr(other->py_size);
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
FBoundingBox2d_clip(FBoundingBox2d *self, FBoundingBox2d *other)
{
    ModuleState *module_state = get_module_state();
    if (!module_state){ return 0; }
    auto cls = module_state->FBoundingBox2d_PyTypeObject;

    if (PyObject_TypeCheck((PyObject *)other, cls) == 0)
    {
        PyErr_SetObject(PyExc_TypeError, (PyObject *)other);
        return 0;
    }

    auto get_vector_ptr = module_state->emath_api->FVector2_GetValuePointer;

    auto self_position = (FBoundingBox2dGlmVector *)get_vector_ptr(self->py_position);
    if (!self_position){ return 0; }
    auto self_size = (FBoundingBox2dGlmVector *)get_vector_ptr(self->py_size);
    if (!self_size){ return 0; }
    auto self_extent = *self_position + *self_size;

    auto other_position = (FBoundingBox2dGlmVector *)get_vector_ptr(((FBoundingBox2d *)other)->py_position);
    if (!other_position){ return 0; }
    auto other_size = (FBoundingBox2dGlmVector *)get_vector_ptr(((FBoundingBox2d *)other)->py_size);
    if (!other_size){ return 0; }
    auto other_extent = *other_position + *other_size;

    auto result_position = FBoundingBox2dGlmVector(
        self_position->x > other_position->x ? self_position->x : other_position->x,
        self_position->y > other_position->y ? self_position->y : other_position->y
    );
    auto result_extent = FBoundingBox2dGlmVector(
        self_extent.x < other_extent.x ? self_extent.x : other_extent.x,
        self_extent.y < other_extent.y ? self_extent.y : other_extent.y
    );
    auto result_size = result_extent - result_position;
    if (result_size.x < 0 || result_size.y < 0)
    {
        result_size = FBoundingBox2dGlmVector(0);
    }

    auto create_vector_2 = module_state->emath_api->FVector2_Create;
    auto py_position = create_vector_2((float*)&result_position);
    if (!py_position){ return 0; }
    auto py_size = create_vector_2((float*)&result_size);
    if (!py_size)
    {
        Py_DECREF(py_position);
        return 0;
    }

    auto result = (FBoundingBox2d*)cls->tp_alloc(cls, 0);
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
    FBoundingBox2d__matmul__(PyObject *left, FBoundingBox2d *right)
    {
        ModuleState *module_state = get_module_state();
        if (!module_state){ return 0; }

        auto get_matrix_ptr = module_state->emath_api->FMatrix4x4_GetValuePointer;
        auto transform = (glm::tmat4x4<float, glm::defaultp> *)get_matrix_ptr(left);
        if (!transform){ Py_RETURN_NOTIMPLEMENTED; }

        auto get_vector_ptr = module_state->emath_api->FVector2_GetValuePointer;
        auto position = (FBoundingBox2dGlmVector *)get_vector_ptr(right->py_position);
        if (!position){ return 0; }
        auto size = (FBoundingBox2dGlmVector *)get_vector_ptr(right->py_size);
        if (!size){ return 0; }

        auto top_left = FBoundingBox2dGlmVector4(position->x, position->y, 0, 1);
        auto top_right = FBoundingBox2dGlmVector4(position->x + size->x, position->y, 0, 1);
        auto bottom_right = FBoundingBox2dGlmVector4(position->x + size->x, position->y + size->y, 0, 1);
        auto bottom_left = FBoundingBox2dGlmVector4(position->x, position->y + size->y, 0, 1);

        FBoundingBox2dGlmVector4 *points[] = {
            &top_left,
            &top_right,
            &bottom_right,
            &bottom_left
        };
        for (size_t i = 0; i < 4; i++)
        {
            auto point = points[i];
            (*point) = *transform * *point;
        }

        auto result_position = FBoundingBox2dGlmVector(top_left.x, top_left.y);
        auto result_extent = result_position;

        for (size_t i = 1; i < 4; i++)
        {
            auto point = points[i];
            if (result_position.x > point->x)
            {
                result_position.x = point->x;
            }
            if (result_position.y > point->y)
            {
                result_position.y = point->y;
            }
            if (result_extent.x < point->x)
            {
                result_extent.x = point->x;
            }
            if (result_extent.y < point->y)
            {
                result_extent.y = point->y;
            }
        }
        auto result_size = result_extent - result_position;

        auto create_vector_2 = module_state->emath_api->FVector2_Create;
        auto py_position = create_vector_2((float*)&result_position);
        if (!py_position){ return 0; }
        auto py_size = create_vector_2((float*)&result_size);
        if (!py_size)
        {
            Py_DECREF(py_position);
            return 0;
        }

        auto cls = module_state->FBoundingBox2d_PyTypeObject;
        auto result = (FBoundingBox2d*)cls->tp_alloc(cls, 0);
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
FBoundingBox2d_overlaps_f_vector_2(FBoundingBox2d *self, PyObject *py_other)
{
    ModuleState *module_state = get_module_state();
    if (!module_state){ return 0; }
    auto get_vector_ptr = module_state->emath_api->FVector2_GetValuePointer;

    auto other = (FBoundingBox2dGlmVector *)get_vector_ptr(py_other);
    if (!other){ return 0; }

    auto position = (FBoundingBox2dGlmVector *)get_vector_ptr(self->py_position);
    if (!position){ return 0; }
    if (other->x < position->x || other->y < position->y)
    {
        Py_RETURN_FALSE;
    }

    auto size = (FBoundingBox2dGlmVector *)get_vector_ptr(self->py_size);
    if (!size){ return 0; }
    auto extent = *position + *size;
    if (other->x >= extent.x || other->y >= extent.y)
    {
        Py_RETURN_FALSE;
    }

    Py_RETURN_TRUE;
}

static PyObject *
FBoundingBox2d_overlaps(FBoundingBox2d *self, PyObject *other)
{
    ModuleState *module_state = get_module_state();
    if (!module_state){ return 0; }
    auto vector_2_cls = module_state->emath_api->FVector2_GetType();
    if (PyObject_TypeCheck(other, vector_2_cls) == 0)
    {
        auto other_overlaps = PyObject_GetAttrString(other, "overlaps_f_bounding_box_2d");
        if (!other_overlaps)
        {
            PyErr_SetObject(PyExc_TypeError, other);
            return 0;
        }
        return PyObject_CallOneArg(other_overlaps, (PyObject *)self);
    }
    return FBoundingBox2d_overlaps_f_vector_2(self, other);
}

static PyObject *
FBoundingBox2d_overlaps_f_bounding_box_2d(FBoundingBox2d *self, PyObject *other)
{
    ModuleState *module_state = get_module_state();
    if (!module_state){ return 0; }
    auto cls = module_state->FBoundingBox2d_PyTypeObject;

    if (PyObject_TypeCheck(other, cls) == 0)
    {
        PyErr_SetObject(PyExc_TypeError, other);
        return 0;
    }

    auto get_vector_ptr = module_state->emath_api->FVector2_GetValuePointer;

    auto self_position = (FBoundingBox2dGlmVector *)get_vector_ptr(self->py_position);
    if (!self_position){ return 0; }
    auto self_size = (FBoundingBox2dGlmVector *)get_vector_ptr(self->py_size);
    if (!self_size){ return 0; }
    auto self_extent = *self_position + *self_size;

    auto other_position = (FBoundingBox2dGlmVector *)get_vector_ptr(((FBoundingBox2d *)other)->py_position);
    if (!other_position){ return 0; }
    auto other_size = (FBoundingBox2dGlmVector *)get_vector_ptr(((FBoundingBox2d *)other)->py_size);
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
FBoundingBox2d_overlaps_f_reverse_lookup(FBoundingBox2d *self, PyObject *other)
{
    return PyObject_CallMethod(other, "overlaps_f_bounding_box_2d", "O", self);
}

static PyObject *
FBoundingBox2d_translate(FBoundingBox2d *self, PyObject *py_translation)
{
    ModuleState *module_state = get_module_state();
    if (!module_state){ return 0; }
    auto cls = module_state->FBoundingBox2d_PyTypeObject;
    auto get_vector_ptr = module_state->emath_api->FVector2_GetValuePointer;

    auto translation = (FBoundingBox2dGlmVector *)get_vector_ptr(py_translation);
    if (!translation){ return 0; }

    auto position = (FBoundingBox2dGlmVector *)get_vector_ptr(self->py_position);

    auto new_position = *position + *translation;

    auto py_new_position = module_state->emath_api->FVector2_Create((float*)&new_position);
    if (!py_new_position){ return 0; }

    auto result = (FBoundingBox2d*)cls->tp_alloc(cls, 0);
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
FBoundingBox2d_to_d(FBoundingBox2d *self, void *)
{
    ModuleState *module_state = get_module_state();
    if (!module_state){ return 0; }
    auto get_vector_ptr = module_state->emath_api->FVector2_GetValuePointer;

    auto position = (FBoundingBox2dGlmVector *)get_vector_ptr(self->py_position);
    if (!position){ return 0; }
    auto size = (FBoundingBox2dGlmVector *)get_vector_ptr(self->py_size);
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
    auto result = (FBoundingBox2d*)to_cls->tp_alloc(to_cls, 0);
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
FBoundingBox2d_to_i(FBoundingBox2d *self, void *)
{
    ModuleState *module_state = get_module_state();
    if (!module_state){ return 0; }
    auto get_vector_ptr = module_state->emath_api->FVector2_GetValuePointer;

    auto position = (FBoundingBox2dGlmVector *)get_vector_ptr(self->py_position);
    if (!position){ return 0; }
    auto size = (FBoundingBox2dGlmVector *)get_vector_ptr(self->py_size);
    if (!size){ return 0; }

    auto to_position = glm::vec<2, int, glm::defaultp>(*position);
    auto to_size = glm::vec<2, int, glm::defaultp>(*size);

    auto create_to_vector = module_state->emath_api->IVector2_Create;
    auto py_to_position = create_to_vector((int*)&to_position);
    if (!py_to_position){ return 0; }
    auto py_to_size = create_to_vector((int*)&to_size);
    if (!py_to_size)
    {
        Py_DECREF(py_to_position);
        return 0;
    }

    auto to_cls = module_state->IBoundingBox2d_PyTypeObject;
    auto result = (FBoundingBox2d*)to_cls->tp_alloc(to_cls, 0);
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


static PyMethodDef FBoundingBox2d_PyMethodDef[] = {
    {"clip", (PyCFunction)FBoundingBox2d_clip, METH_O, 0},
    {"overlaps", (PyCFunction)FBoundingBox2d_overlaps, METH_O, 0},
    {"overlaps_f_vector_2", (PyCFunction)FBoundingBox2d_overlaps_f_vector_2, METH_O, 0},
    {"overlaps_f_bounding_box_2d", (PyCFunction)FBoundingBox2d_overlaps_f_bounding_box_2d, METH_O, 0},
    {"overlaps_f_circle", (PyCFunction)FBoundingBox2d_overlaps_f_reverse_lookup, METH_O, 0},
    {"overlaps_f_rectangle", (PyCFunction)FBoundingBox2d_overlaps_f_reverse_lookup, METH_O, 0},
    {"overlaps_f_triangle_2d", (PyCFunction)FBoundingBox2d_overlaps_f_reverse_lookup, METH_O, 0},
    {"translate", (PyCFunction)FBoundingBox2d_translate, METH_O, 0},

    {"to_d", (PyCFunction)FBoundingBox2d_to_d, METH_NOARGS, 0},

    {"to_i", (PyCFunction)FBoundingBox2d_to_i, METH_NOARGS, 0},

    {0, 0, 0, 0}
};

static PyMemberDef FBoundingBox2d_PyMemberDef[] = {
    {"__weaklistoffset__", T_PYSSIZET, offsetof(FBoundingBox2d, weakreflist), READONLY},
    {"position", T_OBJECT_EX, offsetof(FBoundingBox2d, py_position), READONLY},
    {"size", T_OBJECT_EX, offsetof(FBoundingBox2d, py_size), READONLY},
    {0, 0, 0, 0, 0},
};

static PyObject *
FBoundingBox2d_bounding_box(FBoundingBox2d *self, void *)
{
    Py_INCREF(self);
    return (PyObject *)self;
}

static PyObject *
FBoundingBox2d_extent(FBoundingBox2d *self, void *)
{
    auto module_state = get_module_state();
    if (!module_state){ return 0; }

    EMathApi_GetFVector2ValuePointer get_vector_ptr = module_state->emath_api->FVector2_GetValuePointer;

    FBoundingBox2dGlmVector *position = (FBoundingBox2dGlmVector *)get_vector_ptr(self->py_position);
    if (!position){ return 0; }
    FBoundingBox2dGlmVector *size = (FBoundingBox2dGlmVector *)get_vector_ptr(self->py_size);
    if (!size){ return 0; }

    FBoundingBox2dGlmVector extent = *position + *size;

    return module_state->emath_api->FVector2_Create((float *)&extent);
}

static PyObject *
FBoundingBox2d_points(FBoundingBox2d *self, void *)
{
    auto module_state = get_module_state();
    if (!module_state){ return 0; }

    auto get_vector_ptr = module_state->emath_api->FVector2_GetValuePointer;
    auto create_vector = module_state->emath_api->FVector2_Create;

    FBoundingBox2dGlmVector *position = (FBoundingBox2dGlmVector *)get_vector_ptr(self->py_position);
    if (!position){ return 0; }
    FBoundingBox2dGlmVector *size = (FBoundingBox2dGlmVector *)get_vector_ptr(self->py_size);
    if (!size){ return 0; }

    auto top_right = FBoundingBox2dGlmVector4(position->x + size->x, position->y, 0, 1);
    auto bottom_right = FBoundingBox2dGlmVector4(position->x + size->x, position->y + size->y, 0, 1);
    auto bottom_left = FBoundingBox2dGlmVector4(position->x, position->y + size->y, 0, 1);

    PyObject *py_result = PyTuple_New(4);
    if (!py_result){ return 0; }

    Py_INCREF(self->py_position);
    PyTuple_SET_ITEM(py_result, 0, self->py_position);

    auto py_top_right = create_vector((float*)&top_right);
    if (!py_top_right)
    {
        Py_DECREF(py_result);
        return 0;
    }
    PyTuple_SET_ITEM(py_result, 1, py_top_right);

    auto py_bottom_right = create_vector((float*)&bottom_right);
    if (!py_bottom_right)
    {
        Py_DECREF(py_result);
        return 0;
    }
    PyTuple_SET_ITEM(py_result, 2, py_bottom_right);

    auto py_bottom_left = create_vector((float*)&bottom_left);
    if (!py_bottom_left)
    {
        Py_DECREF(py_result);
        return 0;
    }
    PyTuple_SET_ITEM(py_result, 3, py_bottom_left);

    return py_result;
}

static PyGetSetDef FBoundingBox2d_PyGetSetDef[] = {
    {"bounding_box", (getter)FBoundingBox2d_bounding_box, 0, 0, 0},
    {"extent", (getter)FBoundingBox2d_extent, 0, 0, 0},
    {"points", (getter)FBoundingBox2d_points, 0, 0, 0},
    {0, 0, 0, 0, 0}
};

static PyType_Slot FBoundingBox2d_PyType_Slots [] = {
    {Py_tp_new, (void*)FBoundingBox2d__new__},
    {Py_tp_dealloc, (void*)FBoundingBox2d__dealloc__},
    {Py_tp_hash, (void*)FBoundingBox2d__hash__},
    {Py_tp_repr, (void*)FBoundingBox2d__repr__},
    {Py_tp_richcompare, (void*)FBoundingBox2d__richcmp__},

        {Py_nb_matrix_multiply, (void*)FBoundingBox2d__matmul__},

    {Py_tp_members, (void*)FBoundingBox2d_PyMemberDef},
    {Py_tp_getset, (void*)FBoundingBox2d_PyGetSetDef},
    {Py_tp_methods, (void*)FBoundingBox2d_PyMethodDef},
    {0, 0},
};

static PyType_Spec FBoundingBox2d_PyTypeSpec = {
    "egeometry.FBoundingBox2d",
    sizeof(FBoundingBox2d),
    0,
    Py_TPFLAGS_DEFAULT,
    FBoundingBox2d_PyType_Slots
};

static PyTypeObject *
define_FBoundingBox2d_type(PyObject *module)
{
    PyTypeObject *type = (PyTypeObject *)PyType_FromModuleAndSpec(
        module,
        &FBoundingBox2d_PyTypeSpec,
        0
    );
    if (!type){ return 0; }
    // Note:
    // Unlike other functions that steal references, PyModule_AddObject() only
    // decrements the reference count of value on success.
    if (PyModule_AddObject(module, "FBoundingBox2d", (PyObject *)type) < 0)
    {
        Py_DECREF(type);
        return 0;
    }
    return type;
}

#endif
