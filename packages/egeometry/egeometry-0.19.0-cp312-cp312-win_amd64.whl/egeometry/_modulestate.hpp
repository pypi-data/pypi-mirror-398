
// generated from codegen/templates/_modulestate.hpp

#ifndef EGEOMETRY_MODULESTATE_HPP
#define EGEOMETRY_MODULESTATE_HPP

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "_module.hpp"
#include "emath.h"

struct ModuleState
{
    EMathApi *emath_api;

    PyTypeObject *DBoundingBox2d_PyTypeObject;

    PyTypeObject *FBoundingBox2d_PyTypeObject;

    PyTypeObject *IBoundingBox2d_PyTypeObject;

};


static int
ModuleState_traverse(
    ModuleState *self,
    visitproc visit,
    void *arg
)
{

    Py_VISIT(self->DBoundingBox2d_PyTypeObject);

    Py_VISIT(self->FBoundingBox2d_PyTypeObject);

    Py_VISIT(self->IBoundingBox2d_PyTypeObject);

    return 0;
}


static int
ModuleState_clear(ModuleState *self)
{
    if (self->emath_api)
    {
        EMathApi_Release();
        PyErr_Clear();
        self->emath_api = 0;
    }

    Py_CLEAR(self->DBoundingBox2d_PyTypeObject);

    Py_CLEAR(self->FBoundingBox2d_PyTypeObject);

    Py_CLEAR(self->IBoundingBox2d_PyTypeObject);

    return 0;
}


static ModuleState *
get_module_state()
{
    PyObject *module = get_module();
    if (!module){ return 0; }
    return (ModuleState *)PyModule_GetState(module);
}

#endif
