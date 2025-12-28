#ifndef XF_LISTDICT
#define XF_LISTDICT
#include"lr.h"
struct ListDictDeal:public LRDeal{
    bool deal_build;
    ListDictDeal(const char* left, const char* right, bool deal_build = false):LRDeal(left, right),deal_build(deal_build){}
    int type(){if(deal_build)return BUILD_TYPE_LIST;else return -1;}
    Item* build(Item* obj, Manager& mg);
    Item* build_arr(ItemList& arr, Int2& arr_pos, Manager& mg);
};
#endif