
// generated from codegen/templates/_boundingbox2dtype.hpp

#ifndef EGEOMETRY_IBoundingBox2d_TYPE_HPP
#define EGEOMETRY_IBoundingBox2d_TYPE_HPP

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <glm/glm.hpp>

typedef glm::vec<2, int, glm::defaultp> IBoundingBox2dGlmVector;
typedef glm::vec<4, int, glm::defaultp> IBoundingBox2dGlmVector4;

struct IBoundingBox2d
{
    PyObject_HEAD
    PyObject *weakreflist;
    PyObject *py_position;
    PyObject *py_size;
};

#endif
