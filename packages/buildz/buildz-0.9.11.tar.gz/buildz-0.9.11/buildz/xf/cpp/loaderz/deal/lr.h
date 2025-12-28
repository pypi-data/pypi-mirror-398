#ifndef XF_LR
#define XF_LR
#include"../base_deal.h"
struct LRDeal: public BaseDeal {
    byte bt_left;
    const char *left, *right;
    int ll, lr;
    bool mg_build;
    LRDeal(const char* left, const char* right, bool mg_build = true):left(left),right(right),mg_build(mg_build) {
        bt_left = left[0];
        ll = strlen(left);
        lr = strlen(right);
    }
    int label(){return bt_left;}
    bool deal(BufferBase& buffer, ItemList& rst, Manager& mg);
    virtual Item* build_arr(ItemList& arr, Int2& arr_pos, Manager& mg)=0;
};
#endif