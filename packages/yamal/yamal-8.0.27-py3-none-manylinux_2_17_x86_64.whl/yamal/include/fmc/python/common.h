/******************************************************************************

    COPYRIGHT (c) 2024 by Featuremine Corporation.
    This software has been provided pursuant to a License Agreement
    containing restrictions on its use. This software contains valuable
    trade secrets and proprietary information of Featuremine Corporation
    and is protected by law. It may not be copied or distributed in any
    form or medium, disclosed to third parties, reverse engineered or used
    in any manner not provided for in said License Agreement except with
    the prior written authorization from Featuremine Corporation.

 *****************************************************************************/

#include <Python.h>

#define ADD_PY_CLASS(C, N, MOD)                                                \
  if (PyType_Ready(&C) < 0)                                                    \
    return NULL;                                                               \
  Py_INCREF(&C);                                                               \
  PyModule_AddObject(MOD, N, (PyObject *)&C)
