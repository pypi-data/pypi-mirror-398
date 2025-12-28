
#ifdef __cplusplus
extern "C" {
#endif
#include"Python.h"
typedef PyObject* (*pfptr_create)(int type, void* val, int ival);
typedef void (*pfptr_dict_set)(PyObject* dict, PyObject* key, PyObject *val);
typedef void (*pfptr_list_add)(PyObject* list, PyObject* val);
typedef PyObject* (*pfptr_exp)(const char* s);

PyObject* ploads_fcs(const char* s, pfptr_create fc_create, pfptr_dict_set fc_set, pfptr_list_add fc_add, pfptr_exp fc_exp);
PyObject* ploadx_fcs(const char* s, pfptr_create fc_create, pfptr_dict_set fc_set, pfptr_list_add fc_add, pfptr_exp fc_exp, bool spc);
#ifdef __cplusplus
}
#endif
