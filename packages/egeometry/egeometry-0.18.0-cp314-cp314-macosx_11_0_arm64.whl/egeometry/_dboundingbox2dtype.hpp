
// generated from codegen/templates/_boundingbox2dtype.hpp

#ifndef EGEOMETRY_DBoundingBox2d_TYPE_HPP
#define EGEOMETRY_DBoundingBox2d_TYPE_HPP

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <glm/glm.hpp>

typedef glm::vec<2, double, glm::defaultp> DBoundingBox2dGlmVector;
typedef glm::vec<4, double, glm::defaultp> DBoundingBox2dGlmVector4;

struct DBoundingBox2d
{
    PyObject_HEAD
    PyObject *weakreflist;
    PyObject *py_position;
    PyObject *py_size;
};

#endif
