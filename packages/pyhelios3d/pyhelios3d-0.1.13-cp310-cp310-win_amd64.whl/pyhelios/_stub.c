/*
 * Minimal stub extension to signal that PyHelios contains platform-specific binaries.
 * This ensures setuptools creates platform-specific wheels instead of universal wheels.
 * The actual functionality is provided by the bundled native libraries.
 */

#include <Python.h>

static PyObject *
stub_info(PyObject *self, PyObject *args)
{
    return PyUnicode_FromString("PyHelios platform-specific wheel marker");
}

static PyMethodDef StubMethods[] = {
    {"info", stub_info, METH_NOARGS, "Get stub extension info"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef stubmodule = {
    PyModuleDef_HEAD_INIT,
    "_stub",
    "Platform-specific wheel marker for PyHelios",
    -1,
    StubMethods
};

PyMODINIT_FUNC
PyInit__stub(void)
{
    return PyModule_Create(&stubmodule);
}