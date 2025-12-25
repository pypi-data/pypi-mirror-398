/** @file
Efi Compressor

Copyright (c) 2009 - 2022, Intel Corporation. All rights reserved.<BR>
SPDX-License-Identifier: BSD-2-Clause-Patent

**/

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <Decompress.h>

// Static assertion
typedef char _assert_UINT32_is_int[2*!!(sizeof(int) == sizeof(UINT32))-1];

// EfiCompressor Exception
static PyObject * exc = NULL;


/*
 UefiDecompress(data_buffer, size, original_size)
*/
STATIC
PyObject*
UefiDecompress(
  PyObject    *Self,
  PyObject    *Args
  )
{
  PyObject      *Retval;
  Py_ssize_t    SrcDataSize;
  UINT32        DstDataSize;
  UINTN         Status;
  UINT8         *SrcBuf;
  UINT8         *DstBuf;

  Status = PyArg_ParseTuple(
            Args,
            "y#",
            &SrcBuf,
            &SrcDataSize
            );
  if (Status == 0) {
    return NULL;
  }

  Retval = NULL;
  DstBuf = NULL;
  Status = Extract((VOID *)SrcBuf, SrcDataSize, (VOID **)&DstBuf, &DstDataSize, 1);
  if (Status != EFI_SUCCESS) {
    PyErr_SetString(exc, "Failed to decompress\n");
    goto ERROR;
  }

  Retval = Py_BuildValue("y#", DstBuf, DstDataSize);

ERROR:
  if (DstBuf != NULL) {
    free(DstBuf);
  }
  return Retval;
}


STATIC
PyObject*
FrameworkDecompress(
  PyObject    *Self,
  PyObject    *Args
  )
{
  PyObject      *Retval;
  Py_ssize_t    SrcDataSize;
  UINT32        DstDataSize;
  UINTN         Status;
  UINT8         *SrcBuf;
  UINT8         *DstBuf;

  Status = PyArg_ParseTuple(
            Args,
            "y#",
            &SrcBuf,
            &SrcDataSize
            );
  if (Status == 0) {
    return NULL;
  }

  Retval = NULL;
  DstBuf = NULL;
  Status = Extract((VOID *)SrcBuf, SrcDataSize, (VOID **)&DstBuf, &DstDataSize, 2);
  if (Status != EFI_SUCCESS) {
    PyErr_SetString(exc, "Failed to decompress\n");
    goto ERROR;
  }

  Retval = Py_BuildValue("y#", DstBuf, DstDataSize);

ERROR:
  if (DstBuf != NULL) {
    free(DstBuf);
  }
  return Retval;
}


STATIC
PyObject*
UefiCompress(
  PyObject    *Self,
  PyObject    *Args
  )
{
  return NULL;
}


STATIC
PyObject*
FrameworkCompress(
  PyObject    *Self,
  PyObject    *Args
  )
{
  return NULL;
}

STATIC INT8 DecompressDocs[] = "Decompress(): Decompress data using UEFI standard algorithm\n";
STATIC INT8 CompressDocs[] = "Compress(): Compress data using UEFI standard algorithm\n";

STATIC PyMethodDef EfiCompressor_Funcs[] = {
  {"UefiDecompress", UefiDecompress, METH_VARARGS, (char *)DecompressDocs},
  {"UefiCompress", UefiCompress, METH_VARARGS, (char *)CompressDocs},
  {"FrameworkDecompress", FrameworkDecompress, METH_VARARGS, (char *)DecompressDocs},
  {"FrameworkCompress", FrameworkCompress, METH_VARARGS, (char *)CompressDocs},
  {NULL, NULL, 0, NULL}
};

STATIC struct PyModuleDef EfiCompressor_Module = {
  PyModuleDef_HEAD_INIT,
  "EfiCompressor",
  "EFI Compression Algorithm Extension Module",
  -1,
  EfiCompressor_Funcs
};

PyMODINIT_FUNC
PyInit_EfiCompressor(VOID) {
  PyObject *module = PyModule_Create(&EfiCompressor_Module);
  exc = PyErr_NewException("EfiCompressor.EfiException", NULL, NULL);
  if (exc == NULL) {
    Py_DECREF(module);
    return NULL;
  }
  PyModule_AddObject(module, "EfiException", exc);
  return module;
}
