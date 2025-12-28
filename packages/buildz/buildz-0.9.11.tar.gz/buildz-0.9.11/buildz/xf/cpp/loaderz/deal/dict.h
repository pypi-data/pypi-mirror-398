#ifndef XF_DICT
#define XF_DICT
#include"lr.h"
struct DictDeal:public LRDeal{
    DictDeal(const char* left, const char* right):LRDeal(left, right){}
    int type(){return BUILD_TYPE_LIST;}
    Item* build(Item* obj, Manager& mg);
    Item* build_arr(ItemList& arr, Int2& arr_pos, Manager& mg);
};
#endif