
// generated from codegen/templates/_boundingbox2dtype.hpp

#ifndef EGEOMETRY_FBoundingBox2d_TYPE_HPP
#define EGEOMETRY_FBoundingBox2d_TYPE_HPP

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <glm/glm.hpp>

typedef glm::vec<2, float, glm::defaultp> FBoundingBox2dGlmVector;
typedef glm::vec<4, float, glm::defaultp> FBoundingBox2dGlmVector4;

struct FBoundingBox2d
{
    PyObject_HEAD
    PyObject *weakreflist;
    PyObject *py_position;
    PyObject *py_size;
};

#endif
