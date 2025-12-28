/*
 * signum.cpp
 * A robust, branchless implementation of the universal sign function for Python.
 * Version: 1.0.0
 * Released: December 25, 2025 (Christmas Edition)
 * Author: Alexandru Colesnicov
 * License: MIT
 */

#include <Python.h>

static PyObject *
signum_sign(PyObject *module, PyObject *x)
{
    /* Check for numeric NaN */
    double d = PyFloat_AsDouble(x);
    if (Py_IS_NAN(d)) return PyFloat_FromDouble(Py_NAN);
    /* If it is something special, we will try comparisons */
    if (PyErr_Occurred()) PyErr_Clear();

    PyObject *zero = PyLong_FromLong(0);
    if (!zero) return NULL; /* Memory Error? */

    int gt = PyObject_RichCompareBool(x, zero, Py_GT) + 1; /* 2: True; 1: False; 0: Error */
    int lt = PyObject_RichCompareBool(x, zero, Py_LT) + 1;
    int res = gt - lt; /* Result, if nothing special */
    int eq = PyObject_RichCompareBool(x, zero, Py_EQ) + 1; /* Used only to process NaN and errors */

    Py_DECREF(zero); /* Not used anymore */

    /* gt, lt, eq can be 0, 1, 2; let them be digits in the ternary number system */
    /* code = 9*gt+3*lt+eq is the value of the number written in the ternary system
       with these digits, with possible decimal values from 0 to 26;
       0 means that all three comparisons returned Error (quite possible for inappropriate type);
	   26 means that all were True (extremely strange, the argument is > 0, and < 0, and == 0) */
    /* We also use 9 = 8+1, 3 = 4-1, and replace multiplication by 8 and 4 with shift */
    int code = (gt << 3) + (lt << 2) + eq + res;
    /* (gt<<3) = 8*gt; (lt<<2) = 4*gt; code = 8*gt + 4*lt + eq + (gt-lt) = 9*gt+3*lt+eq */

    switch (code) {
        case 13: { /* 111₃ ->  8+4+1+0: possible NaN     (False, False, False) */
            int self_eq = PyObject_RichCompareBool(x, x, Py_EQ);
            switch (self_eq) {
                case -1: return NULL; /* Error in __eq__, we keep current Python error */
                case  0: return PyFloat_FromDouble(Py_NAN); /* NaN: not equal to itself */
                default: goto error; /* Not a NaN: equals to itself; not comparable to 0 */
            }
		}
        case 14:   /* 112₃ ->  8+4+2+0: x == 0 (res= 0)  (False, False, True ) */
        case 16:   /* 121₃ ->  8+8+1-1: x <  0 (res=-1)  (False, True,  False) */
        case 22:   /* 211₃ -> 16+4+1+1: x >  0 (res= 1)  (True,  False, False) */
            return PyLong_FromLong((long)res);
        default:  /* No more valid cases */
            goto error;
    }

error:
    if (PyErr_Occurred()) {
        PyObject *type, *value, *traceback;
        /* Extract the current error */
        PyErr_Fetch(&type, &value, &traceback);
        PyErr_NormalizeException(&type, &value, &traceback);

        /* Prepare the argument details */
        PyObject *repr = PyObject_Repr(x);
        const char *type_name = Py_TYPE(x)->tp_name;

        /* Prepare the old error as string */
        PyObject *old_msg = PyObject_Str(value);
        const char *old_msg_str = old_msg ? PyUnicode_AsUTF8(old_msg) : "unknown error";

        /* Format the new message */
        PyErr_Format(PyExc_TypeError,
            "signum.sign: invalid argument `%.160s` (type '%.80s'). "
            "Inner error: %.320s",
            repr ? PyUnicode_AsUTF8(repr) : "???",
            type_name,
            old_msg_str);

        /* Clean memory */
        Py_XDECREF(repr);
        Py_XDECREF(old_msg);
        Py_XDECREF(type);
        Py_XDECREF(value);
        Py_XDECREF(traceback);
    }
    else {
        PyObject *repr = PyObject_Repr(x);
        const char *type_name = Py_TYPE(x)->tp_name;

        if (repr) {
            PyErr_Format(PyExc_TypeError,
                "signum.sign: invalid argument `%.160s`. "
                "Type '%.80s' does not support order comparisons (>, <, ==) "
                "or NaN detection.",
                PyUnicode_AsUTF8(repr),
                type_name);
            Py_DECREF(repr);
        }
        else {
            PyErr_Format(PyExc_TypeError,
                "signum.sign: invalid argument of type '%.80s', "
                "which does not support order comparisons (>, <, ==) and printing.",
                type_name);
        }
    }
    return NULL;
}

/* --- FORMALITIES --- */

/* List of implemented methods */
static PyMethodDef SignumMethods[] = {
    {"sign", (PyCFunction)signum_sign, METH_O, "Return the sign of x: -1, 0, 1, or NaN."},
    {NULL, NULL, 0, NULL} /* Stop-string */
};

/* Module description */
static struct PyModuleDef signummodule = {
    PyModuleDef_HEAD_INIT,
    "signum",  /* Module name for import */
    "Fast signum implementation with ternary logic.",
    -1,
    SignumMethods
};

/* Module initialization */
PyMODINIT_FUNC PyInit_signum(void) {
    return PyModule_Create(&signummodule);
}
