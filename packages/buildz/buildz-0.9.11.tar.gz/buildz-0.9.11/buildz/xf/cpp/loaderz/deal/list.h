#ifndef XF_LIST
#define XF_LIST
#include"lr.h"
struct ListDeal:public LRDeal{
    ListDeal(const char* left, const char* right):LRDeal(left, right){}
    int type(){return BUILD_TYPE_LIST;}
    Item* build(Item* obj, Manager& mg);
    Item* build_arr(ItemList& arr, Int2& arr_pos, Manager& mg);
};
#endif