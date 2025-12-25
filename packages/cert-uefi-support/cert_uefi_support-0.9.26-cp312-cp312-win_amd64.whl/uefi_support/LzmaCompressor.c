#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "Alloc.h"
#include "7zFile.h"
#include "7zVersion.h"
#include "LzmaDec.h"
#include "LzmaEnc.h"
#include "Bra.h"

#define LZMA_HEADER_SIZE (LZMA_PROPS_SIZE + 8)

typedef enum {
  NoConverter,
  X86Converter,
  MaxConverter
} CONVERTER_TYPE;

static void *pyalloc_7z(ISzAllocPtr p, size_t size) {
  return PyMem_RawMalloc(size);
}

static void pyfree_7z(ISzAllocPtr p, void *addr) {
  PyMem_RawFree(addr);
}

struct ISzAlloc py_alloc = {
  pyalloc_7z,
  pyfree_7z
};

static PyObject * exc = NULL;

static uint64_t maxlen = (uint64_t)1 << 30; // 1GB

static PyObject *
Decode(PyObject *self, PyObject *args)
{
  const unsigned char *src;
  Py_ssize_t  src_size;
  uint64_t    dest_size = 0;
  size_t      dest_size_l;
  size_t      src_data_size;
  PyObject   *dest = NULL;
  ELzmaStatus status;
  int         i;
  SRes        result;

  if (!PyArg_ParseTuple(args, "y#", &src, &src_size)) {
    return NULL;
  }

  if (src_size < LZMA_HEADER_SIZE) {
    PyErr_SetString(exc, "Buffer has too few bytes to be LZMA compressed");
    return NULL;
  }

  for (i = 0; i < 8; i++) {
    dest_size += ((uint64_t)src[LZMA_PROPS_SIZE + i]) << (i * 8);
  }

  if (((Py_ssize_t)dest_size) < 0) {
    PyErr_SetString(exc, "Interpreted negative size from LZMA size data");
    return NULL;
  }
  if (dest_size > maxlen) {
    PyErr_SetString(exc, "Too large decompressed size in LZMA header");
    return NULL;
  }

  dest_size_l = dest_size;
  if ((dest = PyBytes_FromStringAndSize(NULL, dest_size_l)) == NULL) {
    return NULL;
  }

  src_data_size = src_size - LZMA_HEADER_SIZE;
  result = LzmaDecode((Byte *)PyBytes_AS_STRING(dest), &dest_size_l,
                      (Byte *)src + LZMA_HEADER_SIZE, &src_data_size,
                      (Byte *)src, LZMA_PROPS_SIZE, LZMA_FINISH_END,
                      &status, &py_alloc);

  if (result == SZ_OK) {
    if (dest_size_l == dest_size) {
      return Py_BuildValue("Ny#", dest, src, LZMA_PROPS_SIZE);
    } else {
      PyErr_SetString(exc, "Decompressed size did not match advertised size");
    }
  } else {
    PyErr_SetString(exc, "Error decompressing data");
  }

  Py_DECREF(dest);
  return NULL;
}

static PyMethodDef LzmaCompressor_Funcs[] = {
  {"LzmaDecompress", Decode, METH_VARARGS, "Decompress LZMA-encoded data"},
  {NULL, NULL, 0, NULL}
};

static struct PyModuleDef LzmaCompressor_Module = {
  PyModuleDef_HEAD_INIT,
  "LzmaCompressor",
  "LZMA (De)Compression Module",
  -1,
  LzmaCompressor_Funcs
};

PyMODINIT_FUNC
PyInit_LzmaCompressor(void) {
  PyObject *module = PyModule_Create(&LzmaCompressor_Module);
  exc = PyErr_NewException("LzmaCompressor.LzmaException", NULL, NULL);
  if (exc == NULL) {
    Py_DECREF(module);
    return NULL;
  }
  PyModule_AddObject(module, "LzmaException", exc);
  return module;
}
