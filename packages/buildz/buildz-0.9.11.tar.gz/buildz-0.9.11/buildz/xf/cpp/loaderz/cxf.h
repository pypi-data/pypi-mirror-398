
#ifdef __cplusplus
extern "C" {
#endif

typedef void* (*fptr_create)(int type, void* val, int ival);
typedef void (*fptr_dict_set)(void* dict, void* key, void *val);
typedef void (*fptr_list_add)(void* list, void* val);
typedef void* (*fptr_exp)(const char* s);

typedef void* (*mptr_create)(void* obj, int type, void* val, int ival);
typedef void (*mptr_dict_set)(void* obj, void* dict, void* key, void *val);
typedef void (*mptr_list_add)(void* obj, void* list, void* val);
typedef void* (*mptr_exp)(void* obj, const char* s);

void* loads(const char* s, void* callback);
void* loadx(const char* s, void* callback, bool spc=true);
void* loads_fcs(const char* s, fptr_create fc_create, fptr_dict_set fc_set, fptr_list_add fc_add, fptr_exp fc_exp);
void* loadx_fcs(const char* s, fptr_create fc_create, fptr_dict_set fc_set, fptr_list_add fc_add, fptr_exp fc_exp, bool spc=true);
void* loads_mtds(const char* s, void* obj, mptr_create fc_create, mptr_dict_set fc_set, mptr_list_add fc_add, mptr_exp fc_exp);
void* loadx_mtds(const char* s, void* obj, mptr_create fc_create, mptr_dict_set fc_set, mptr_list_add fc_add, mptr_exp fc_exp, bool spc=true);
#ifdef __cplusplus
}
#endif