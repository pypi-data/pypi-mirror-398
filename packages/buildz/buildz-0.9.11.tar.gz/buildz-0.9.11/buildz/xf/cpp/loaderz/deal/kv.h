#ifndef XF_KEYVAL
#define XF_KEYVAL
#include"spt.h"

struct KeyValDeal:public PrevSptDeal{
    KeyValDeal(const char* spt):PrevSptDeal(spt,true,BUILD_TYPE_KEYVAL){}
    Item* build(Item* it, Manager&){return it;}
};
#endif