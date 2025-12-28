#ifndef XF_SPT
#define XF_SPT
#include"../base_deal.h"

struct PrevSptDeal:public BaseDeal{
    const char* spt;
    bool allow_empty;
    int build_type;
    int l_spt;
    byte bt_spt;
    PrevSptDeal(const char* spt, bool allow_empty=false, int type=BUILD_TYPE_SPT):spt(spt),allow_empty(allow_empty),build_type(type){
        l_spt = strlen(spt);
        bt_spt = spt[0];
    }
    int label(){return bt_spt;}
    int type(){return build_type;}
    Item* build(Item* it, Manager&);
    bool deal(BufferBase& buffer, ItemList& rst, Manager& mg);
    
};
#endif