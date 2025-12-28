#include"pc.h"
#include"cxf.h"
PyObject* ploads_fcs(const char* s, pfptr_create fc_create, pfptr_dict_set fc_set, pfptr_list_add fc_add, pfptr_exp fc_exp){
	return (PyObject*)loads_fcs(s, (fptr_create)fc_create,(fptr_dict_set)fc_set, (fptr_list_add)fc_add, (fptr_exp)fc_exp);
}
PyObject* ploadx_fcs(const char* s, pfptr_create fc_create, pfptr_dict_set fc_set, pfptr_list_add fc_add, pfptr_exp fc_exp, bool spc){
	return (PyObject*)loadx_fcs(s, (fptr_create)fc_create,(fptr_dict_set)fc_set, (fptr_list_add)fc_add, (fptr_exp)fc_exp, spc);
}
