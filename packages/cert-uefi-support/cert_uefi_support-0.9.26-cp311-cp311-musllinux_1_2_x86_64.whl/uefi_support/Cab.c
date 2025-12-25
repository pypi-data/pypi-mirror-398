#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdbool.h>

#include "system.h"
#include "cab.h"

static PyObject * exc = NULL;
static PyObject * message_fn = NULL;

static bool check_for_method(PyObject * obj, const char * name)
{
  PyObject * method = PyObject_GetAttrString(obj, name);
  if (!method) {
    PyErr_Format(exc, "Stream does not have a %s method", name);
    return false;
  }
  if (!PyCallable_Check(method)) {
    PyErr_Format(exc, "Stream's %s method is not callable", name);
    return false;
  }
  return true;
}

static PyObject * pymspack_open(
  struct mspack_system *Py_UNUSED(self),
  PyObject *stream,
  int mode)
{
  if (!check_for_method(stream, "seek")
      || !check_for_method(stream, "tell")
      || (mode == MSPACK_SYS_OPEN_READ && !check_for_method(stream, "readinto"))
      || (mode != MSPACK_SYS_OPEN_READ && !check_for_method(stream, "write"))
      || (mode == MSPACK_SYS_OPEN_WRITE && !check_for_method(stream, "truncate")))
  {
    return NULL;
  }
  if (mode == MSPACK_SYS_OPEN_WRITE) {
    PyObject * rv = PyObject_CallMethod(stream, "truncate", "i", 0);
    if (rv == NULL) {
      return NULL;
    }
    Py_DECREF(rv);
  } else if (mode == MSPACK_SYS_OPEN_APPEND) {
    PyObject * rv = PyObject_CallMethod(stream, "seek", "ii", 0, 2);
    if (rv == NULL) {
      return NULL;
    }
    Py_DECREF(rv);
  } else if (mode == MSPACK_SYS_OPEN_READ) {
    PyObject * rv = PyObject_CallMethod(stream, "seek", "ii", 0, 0);
    if (rv == NULL) {
      return NULL;
    }
    Py_DECREF(rv);
  }
  Py_INCREF(stream);
  return stream;
}

static void pymspack_close(
  PyObject *stream)
{
}

static int pymspack_read(
  PyObject *stream,
  void * buffer,
  int bytes)
{
  PyObject *pybuf = PyMemoryView_FromMemory((char *)buffer, bytes, 0x200);
  PyObject *rv = PyObject_CallMethod(stream, "readinto", "O", pybuf);
  Py_DECREF(pybuf);
  if (rv == NULL) {
    PyErr_Clear();
    return -1;
  }
  if (rv == Py_None) {
    Py_DECREF(rv);
    return 0;
  }
  long val = PyLong_AsLong(rv);
  Py_DECREF(rv);
  if (val == -1) {
    PyErr_Clear();
  }
  return val;
}

static int pymspack_write(
  PyObject *stream,
  void * buffer,
  int bytes)
{
  PyObject *pybuf = PyMemoryView_FromMemory((char *)buffer, bytes, 0x100);
  PyObject *rv = PyObject_CallMethod(stream, "write", "O", pybuf);
  Py_DECREF(pybuf);
  if (rv == NULL) {
    PyErr_Clear();
    return -1;
  }
  if (rv == Py_None) {
    Py_DECREF(rv);
    return 0;
  }
  long val = PyLong_AsLong(rv);
  Py_DECREF(rv);
  if (val == -1) {
    PyErr_Clear();
  }
  return val;
}

static int pymspack_seek(
  PyObject *stream,
  off_t offset,
  int mode)
{
  PyObject *rv = PyObject_CallMethod(stream, "seek", "ni", offset, mode);
  if (rv == NULL) {
    return -1;
  }
  Py_DECREF(rv);
  return 0;
}

static off_t pymspack_tell(
  PyObject *stream)
{
  PyObject *rv = PyObject_CallMethod(stream, "tell", "");
  if (rv == NULL) {
    return -1;
  }
  off_t retval = PyLong_AsSsize_t(rv);
  Py_DECREF(rv);
  return retval;
}

static void pymspack_message(
  PyObject *stream,
  const char * format,
  ...)
{
  if (message_fn) {
    char c;
    va_list args;
    va_start(args, format);
    int size = PyOS_vsnprintf(&c, 1, format, args);
    char *buf = (char *)PyMem_Malloc(size + 1);
    if (buf == NULL) {
      return;
    }
    PyOS_vsnprintf(buf, size + 1, format, args);
    PyMem_Free(buf);
    PyObject *msg = PyUnicode_FromStringAndSize(buf, size);
    if (!msg) {
      return;
    }
    PyObject *rv = PyObject_CallFunctionObjArgs(message_fn, msg, NULL);
    Py_DECREF(msg);
    Py_XDECREF(rv);
  }
}

static void * pymspack_alloc(
  struct mspack_system *Py_UNUSED(self),
  size_t bytes)
{
  return PyMem_Malloc(bytes);
}

static void pymspack_free(
  void * ptr)
{
  PyMem_Free(ptr);
}

static void pymspack_copy(
  void *src,
  void *dest,
  size_t bytes)
{
  memcpy(dest, src, bytes);
}

static struct mspack_system pymspack_system = {
  (struct mspack_file * (*)(struct mspack_system *, const char *, int)) &pymspack_open,
  (void (*)(struct mspack_file *)) &pymspack_close,
  (int (*)(struct mspack_file *, void *, int)) &pymspack_read,
  (int (*)(struct mspack_file *, void *, int)) &pymspack_write,
  (int (*)(struct mspack_file *, off_t, int)) &pymspack_seek,
  (off_t (*)(struct mspack_file *)) &pymspack_tell,
  (void (*)(struct mspack_file *, const char *, ...)) &pymspack_message,
  &pymspack_alloc,
  &pymspack_free,
  &pymspack_copy,
  NULL
};

typedef struct {
  int code;
  const char * message;
} errcodes_t;

static errcodes_t mspack_errcodes[] = {
  { MSPACK_ERR_OK, "Success" },
  { MSPACK_ERR_ARGS, "Bad argument" },
  { MSPACK_ERR_OPEN, "Error opening file" },
  { MSPACK_ERR_READ, "Error reading file" },
  { MSPACK_ERR_WRITE, "Error writing file" },
  { MSPACK_ERR_SEEK, "Error seeking file" },
  { MSPACK_ERR_NOMEMORY, "Out of memory" },
  { MSPACK_ERR_SIGNATURE, "Bad signature in file" },
  { MSPACK_ERR_DATAFORMAT, "Bad or corrupt file format" },
  { MSPACK_ERR_CHECKSUM, "Bad checksum or CRC" },
  { MSPACK_ERR_CRUNCH, "Error during compression" },
  { MSPACK_ERR_DECRUNCH, "Error during decompression" },
  { 0, NULL}
};

PyObject *raise_mspack_error(int err)
{
  for (errcodes_t * code = mspack_errcodes; code->message; ++code) {
    if (err == code->code) {
      PyErr_SetString(exc, code->message);
      return NULL;
    }
  }
  return PyErr_Format(exc, "Unknown mspack error %i", err);
}

typedef struct {
  PyObject_HEAD
  struct mscab_decompressor * obj;
} PymscabDecompressor;

typedef struct {
  PyObject_HEAD
  PymscabDecompressor *parent;
  PyObject *stream;
  struct mscabd_cabinet * obj;
} PymscabCabinet;

typedef struct {
  PyObject_HEAD
  PymscabCabinet *parent;
  struct mscabd_file * obj;
} PymscabFile;

static PyObject * pymscab_decompressor_new(
  PyTypeObject *type, PyObject *args, PyObject *kwds);
static void pymscab_decompressor_dealloc(
  PymscabDecompressor *self);
static PyObject * pymscab_decompressor_open(
  PymscabDecompressor *self, PyObject *args);

static void pymscab_cabinet_dealloc(
  PymscabCabinet *self);
static PyObject *pymscab_cabinet_next(
  PymscabCabinet *self, PyObject *);
static PyObject *pymscab_cabinet_files(
  PymscabCabinet * self, PyObject *);

static void pymscab_file_dealloc(
  PymscabFile *self);
static PyObject *pymscab_file_next(
  PymscabFile *self, PyObject *);
static PyObject *pymscab_file_info(
  PymscabFile *self, void *);
static PyObject *pymscab_file_data(
  PymscabFile *self, PyObject *buffer);

static PyMethodDef PymscabDecompressorMethods[] = {
  {"open", (PyCFunction)pymscab_decompressor_open, METH_O,
   "Open a stream as a cab file"},
  {NULL, NULL, 0, NULL}
};

static PyTypeObject PymscabDecompressorType = {
  PyVarObject_HEAD_INIT(NULL, 0)
  .tp_name = "mscab.Decompressor",
  .tp_basicsize = sizeof(PymscabDecompressor),
  .tp_doc = "Decompressor for Microsoft CAB archives",
  .tp_new = pymscab_decompressor_new,
  .tp_dealloc = (destructor)pymscab_decompressor_dealloc,
  .tp_methods = PymscabDecompressorMethods,
};

static PyMethodDef PymscabCabinetMethods[] = {
  {"next", (PyCFunction)pymscab_cabinet_next, METH_NOARGS,
   "Return the next cabinet"},
  {"first_file", (PyCFunction)pymscab_cabinet_files, METH_NOARGS,
   "Return the first file in the cabinet"},
  {NULL, NULL, 0, NULL}
};

static PyTypeObject PymscabCabinetType = {
  PyVarObject_HEAD_INIT(NULL, 0)
  .tp_name = "mscab.Cabinet",
  .tp_basicsize = sizeof(PymscabCabinet),
  .tp_doc = "A Microsoft CAB file cabinet",
  .tp_dealloc = (destructor)pymscab_cabinet_dealloc,
  .tp_methods = PymscabCabinetMethods,
};

static PyMethodDef PymscabFileMethods[] = {
  {"next", (PyCFunction)pymscab_file_next, METH_NOARGS,
   "Return the next file"},
  {"data", (PyCFunction)pymscab_file_data, METH_O,
   "Read file data into BUFFER, returning BUFFER"},
  {NULL, NULL, 0, NULL}
};

static PyGetSetDef PymscabFileGetSetters[] = {
  {"info", (getter)pymscab_file_info, NULL, "File info", NULL},
  {NULL, NULL, NULL, NULL, NULL}
};

static PyTypeObject PymscabFileType = {
  PyVarObject_HEAD_INIT(NULL, 0)
  .tp_name = "mscab.File",
  .tp_basicsize = sizeof(PymscabFile),
  .tp_doc = "A file from a Microsoft CAB file",
  .tp_dealloc = (destructor)pymscab_file_dealloc,
  .tp_methods = PymscabFileMethods,
  .tp_getset = PymscabFileGetSetters,
};

static void pymscab_file_dealloc(
  PymscabFile * self)
{
  Py_DECREF(self->parent);
  Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject *pymscab_file_next(
  PymscabFile * self, PyObject *Py_UNUSED(args))
{
  if (self->obj->next) {
    PymscabFile *rv = PyObject_New(PymscabFile, &PymscabFileType);
    if (rv == NULL) { return NULL; }
    rv->obj = self->obj->next;
    rv->parent = self->parent;
    Py_INCREF(rv->parent);
    return (PyObject *)rv;
  }
  Py_RETURN_NONE;
}

static PyObject *pymscab_file_info(
  PymscabFile *self, void *Py_UNUSED(closure))
{
  return Py_BuildValue("sIi(ibbbbb)",
                       self->obj->filename,
                       self->obj->length,
                       self->obj->attribs,
                       self->obj->date_y,
                       self->obj->date_m,
                       self->obj->date_d,
                       self->obj->time_h,
                       self->obj->time_m,
                       self->obj->time_s);
}

static PyObject *pymscab_file_data(
  PymscabFile * self, PyObject *buffer)
{
  int rv = self->parent->parent->obj->extract(self->parent->parent->obj, self->obj,
                                              (const char *)buffer);
  if (PyErr_Occurred()) {
    return NULL;
  }
  if (rv) {
    return raise_mspack_error(rv);
  }
  Py_INCREF(buffer);
  return buffer;
}

static void pymscab_cabinet_dealloc(
  PymscabCabinet * self)
{
  self->parent->obj->close(self->parent->obj, self->obj);
  Py_DECREF((PyObject *)self->parent);
  Py_DECREF(self->stream);
  Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject *pymscab_cabinet_next(
  PymscabCabinet * self, PyObject *Py_UNUSED(args))
{
  if (self->obj->next) {
    PymscabCabinet *rv = PyObject_New(PymscabCabinet, &PymscabCabinetType);
    if (rv == NULL) { return NULL; }
    rv->obj = self->obj->next;
    rv->stream = self->stream;
    rv->parent = self->parent;
    Py_INCREF(rv->stream);
    Py_INCREF(rv->parent);
    return (PyObject *)rv;
  }
  Py_RETURN_NONE;
}

static PyObject *pymscab_cabinet_files(
  PymscabCabinet* self, PyObject *Py_UNUSED(args))
{
  if (self->obj->files) {
    PymscabFile *rv = PyObject_New(PymscabFile, &PymscabFileType);
    if (rv == NULL) { return NULL; }
    rv->obj = self->obj->files;
    rv->parent = self;
    Py_INCREF(rv->parent);
    return (PyObject *)rv;
  }
  Py_RETURN_NONE;
}

static PyObject * pymscab_decompressor_new(
  PyTypeObject *type, PyObject *args, PyObject *kwds)
{
  PymscabDecompressor *self;
  self = (PymscabDecompressor *)type->tp_alloc(type, 0);
  if (self == NULL) { return NULL; }
  self->obj = mspack_create_cab_decompressor(&pymspack_system);
  if (self->obj == NULL) { return NULL; }
  return (PyObject *)self;
}

static void pymscab_decompressor_dealloc(
  PymscabDecompressor *self)
{
  if (self->obj) {
    mspack_destroy_cab_decompressor(self->obj);
    self->obj = NULL;
  }
  Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject * pymscab_decompressor_open(
  PymscabDecompressor *self, PyObject *stream)
{
  struct mscabd_cabinet * cab = self->obj->open(self->obj, (const char *)stream);
  if (cab == NULL) {
    return raise_mspack_error(self->obj->last_error(self->obj));
  }
  PymscabCabinet *rv = PyObject_New(PymscabCabinet, &PymscabCabinetType);
  if (rv == NULL) {
    self->obj->close(self->obj, cab);
    return NULL;
  }
  rv->obj = cab;
  rv->parent = self;
  rv->stream = stream;
  Py_INCREF((PyObject *)rv->parent);
  Py_INCREF(rv->stream);
  return (PyObject *)rv;
}

static PyObject *set_message_function(
  PyObject *fn)
{
  Py_INCREF(fn);
  Py_XDECREF(message_fn);
  message_fn = fn;
  Py_RETURN_NONE;
}

static PyMethodDef Cab_Funcs[] = {
  {"set_message_function", (PyCFunction)set_message_function, METH_O,
  "Set the warning message callback"},
  {NULL, NULL, 0, NULL}
};

static PyModuleDef Cab_Module = {
  PyModuleDef_HEAD_INIT,
  .m_name = "mscab",
  .m_doc = "Decompressor for Microsoft CAB archives",
  .m_size = -1,
  .m_methods = Cab_Funcs,
};

PyMODINIT_FUNC
PyInit_Cab(void) {
  PyObject *module = PyModule_Create(&Cab_Module);
  if (exc == NULL) {
    exc = PyErr_NewException("Cab.Error", NULL, NULL);
    if (exc == NULL) {
      Py_DECREF(module);
      return NULL;
    }
  }
  PyModule_AddObject(module, "Error", exc);

  if (PyType_Ready(&PymscabDecompressorType) < 0) {
    Py_DECREF(module);
    return NULL;
  }
  PyModule_AddObject(module, "Decompressor", (PyObject *)&PymscabDecompressorType);

  if (PyType_Ready(&PymscabCabinetType) < 0) {
    Py_DECREF(module);
    return NULL;
  }
  PyModule_AddObject(module, "Cabinet", (PyObject *)&PymscabCabinetType);

  if (PyType_Ready(&PymscabFileType) < 0) {
    Py_DECREF(module);
    return NULL;
  }
  PyModule_AddObject(module, "File", (PyObject *)&PymscabFileType);

  return module;
}
