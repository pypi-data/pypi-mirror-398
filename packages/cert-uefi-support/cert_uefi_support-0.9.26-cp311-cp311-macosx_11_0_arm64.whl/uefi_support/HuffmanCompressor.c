#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "pch_format.h"

int unhuff(unsigned char *huff, unsigned char *out, int outlen, int flags, int version);

static PyObject * exc = NULL;

static PyObject *
Decode(PyObject *self, PyObject *args, PyObject *kwds)
{
  const unsigned char *src;
  Py_ssize_t size;
  unsigned int offset;
  int outlen;
  int flags;
  int version;
  int actual_outlen;
  PyObject *out;

  static char *kwd_names[] = {
    "data", "offset", "flags", "length", "version", NULL };

  if (!PyArg_ParseTupleAndKeywords(args, kwds, "y#Iiii", kwd_names, &src, &size, &offset,
                                   &flags, &outlen, &version))
  {
    return NULL;
  }

  if ((out = PyBytes_FromStringAndSize(NULL, (size_t)outlen)) == NULL) {
    return NULL;
  }

  actual_outlen = unhuff((unsigned char *)src + offset,
                         (unsigned char *)PyBytes_AS_STRING(out), outlen, flags, version);
  if (actual_outlen == outlen) {
    return out;
  }
  Py_DECREF(out);
  PyErr_SetString(exc, "Error decompressing data");
  return NULL;
}

static PyMethodDef HuffmanCompressor_Funcs[] = {
  {"HuffmanDecompress", (PyCFunction)Decode, METH_VARARGS | METH_KEYWORDS,
   "Decompress Huffman-encoded data"},
  {NULL, NULL, 0, NULL}
};

static struct PyModuleDef HuffmanCompressor_Module = {
  PyModuleDef_HEAD_INIT,
  "HuffmanCompressor",
  "Huffman (De)Compression Module",
  -1,
  HuffmanCompressor_Funcs
};

PyMODINIT_FUNC
PyInit_HuffmanCompressor(void) {
  PyObject *module = PyModule_Create(&HuffmanCompressor_Module);
  exc = PyErr_NewException("HuffmanCompressor.HuffmanException", NULL, NULL);
  if (exc == NULL) {
    Py_DECREF(module);
    return NULL;
  }
  PyModule_AddObject(module, "HuffmanException", exc);
  return module;
}
