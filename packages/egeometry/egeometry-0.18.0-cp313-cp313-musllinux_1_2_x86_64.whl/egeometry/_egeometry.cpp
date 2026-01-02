
// generated from codegen/templates/_egeometry.cpp

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <structmember.h>

#include "_modulestate.hpp"

    #include "_dboundingbox2d.hpp"

    #include "_fboundingbox2d.hpp"

    #include "_iboundingbox2d.hpp"

#include "emath.h"


static PyMethodDef module_methods[] = {
    {0, 0, 0, 0}
};


static int
module_traverse(PyObject *self, visitproc visit, void *arg)
{
    ModuleState *state = (ModuleState *)PyModule_GetState(self);
    return ModuleState_traverse(state, visit, arg);
}


static int
module_clear(PyObject *self)
{
    ModuleState *state = (ModuleState *)PyModule_GetState(self);
    return ModuleState_clear(state);
}


static struct PyModuleDef module_PyModuleDef = {
    PyModuleDef_HEAD_INIT,
    "egeometry._egeometry",
    0,
    sizeof(ModuleState),
    module_methods,
    0,
    module_traverse,
    module_clear
};


PyMODINIT_FUNC
PyInit__egeometry()
{
    PyObject *module = PyModule_Create(&module_PyModuleDef);
    ModuleState *state = 0;
    if (!module){ goto error; }
    if (PyState_AddModule(module, &module_PyModuleDef) == -1){ goto error; }
    state = (ModuleState *)PyModule_GetState(module);
    state->emath_api = EMathApi_Get();
    if (state->emath_api == 0)
    {
        goto error;
    }

    {
        PyTypeObject *type = define_DBoundingBox2d_type(module);
        if (!type){ goto error; }
        Py_INCREF(type);
        state->DBoundingBox2d_PyTypeObject = type;
    }

    {
        PyTypeObject *type = define_FBoundingBox2d_type(module);
        if (!type){ goto error; }
        Py_INCREF(type);
        state->FBoundingBox2d_PyTypeObject = type;
    }

    {
        PyTypeObject *type = define_IBoundingBox2d_type(module);
        if (!type){ goto error; }
        Py_INCREF(type);
        state->IBoundingBox2d_PyTypeObject = type;
    }


    return module;
error:
    Py_CLEAR(module);
    return 0;
}


static PyObject *
get_module()
{
    PyObject *module = PyState_FindModule(&module_PyModuleDef);
    if (!module)
    {
        return PyErr_Format(PyExc_RuntimeError, "egeometry module not ready");
    }
    return module;
}
