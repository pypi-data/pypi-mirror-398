
#ifndef XF_CALLBACK
#define XF_CALLBACK
#include"base.h"
struct Callback{
    virtual void* create(int type, void* val=NULL, int ival=0)=0;
    virtual void dict_set(void* dict, void* key, void *val)=0;
    virtual void list_add(void* list, void* val)=0;
    virtual void* exp(const char* s)=0;
};
#endif