#ifndef XF_INIT
#define XF_INIT

#include "mg.h"
struct Loads{
    Manager mg;
    bool mark_init;
    Loads();
    void build();
    void buildx(bool spc=true);
    void* loads(const char* s, Callback& callback){
        return mg.loads(s, &callback);
    }
    ~Loads();
};
#endif