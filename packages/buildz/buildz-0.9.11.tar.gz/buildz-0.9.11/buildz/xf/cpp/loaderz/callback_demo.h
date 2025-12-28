
#ifndef XF_CALLBACK_DEMO
#define XF_CALLBACK_DEMO
#include"base.h"
#include"callback.h"
struct TypeVal;
typedef TypeVal* ptrTypeVal;
struct Compare{
    bool operator()(const ptrTypeVal& a, const ptrTypeVal& b) const ;
};
struct TypeVal{
    std::string str();
    int type;
    union{
        int val;
        bool bl;
        float fval;
    };
    std::string s;
    std::map<TypeVal*, TypeVal*, Compare> dict;
    std::vector<TypeVal*> list;
    TypeVal(int type, void* val=NULL,int ival = 0);
    bool operator<(const TypeVal& tval)const;
    ~TypeVal(){}
};
struct CallbackDemo:public Callback{
    void* create(int type, void* val=NULL, int ival = 0);
    void dict_set(void* dict, void* key, void *val);
    void list_add(void* list, void* val);
    void* exp(const char* s);
};
#endif