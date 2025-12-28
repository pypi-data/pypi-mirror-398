#ifndef XF_LRVAL
#define XF_LRVAL
#include"lr.h"
#include<unordered_map>
struct LRValDeal:public LRDeal{
    std::unordered_map<std::string, int> types;
    std::unordered_map<std::string, int> bools;
    LRValDeal(const char* left, const char* right):LRDeal(left, right,false){}
    Item* build_arr(ItemList& arr, Int2& arr_pos, Manager& mg);
    void set_type(const char* key, int type){
        types[key] = type;
    }
    void set_bool(const char* key, int val){
        bools[key] = val;
    }
};
#endif