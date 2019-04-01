#include "Python.h"

static PyMethodDef SpamMethods[] = {
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


/* -------------------------------- */
#if PY_MAJOR_VERSION >= 3

#define GETSTATE(m) ((struct module_state*)PyModule_GetState(m))
#define INITERROR return NULL

struct module_state {
    PyObject *error;
};

static int myextension_traverse(PyObject *m, visitproc visit, void *arg) {
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int myextension_clear(PyObject *m) {
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}

static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "ext_falcon",
        NULL,
        sizeof(struct module_state),
        SpamMethods,
        NULL,
        myextension_traverse,
        myextension_clear,
        NULL
};

PyMODINIT_FUNC
PyInit_ext_falcon(void)
{
    PyObject *module;

    module = PyModule_Create(&moduledef);
    if (module == NULL) INITERROR;
    struct module_state *st = GETSTATE(module);
    st->error = PyErr_NewException("ext_falcon.Error", NULL, NULL);
    if (st->error == NULL) {
        Py_DECREF(module);
        INITERROR;
    }
    return module;
}

/* -------------------------------- */
#else

PyMODINIT_FUNC
initext_falcon(void)
{
    PyObject *m;

    m = Py_InitModule("ext_falcon", SpamMethods);
    if (m == NULL)
        return;
}

/* -------------------------------- */
#endif /* PY_MAJOR_VERSION */
