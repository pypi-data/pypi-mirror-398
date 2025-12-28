#ifndef XF_STR
#define XF_STR
#include"lr.h"
struct StrDeal:public LRDeal{
    bool single_line, note, translate, deal_build;
    int et_in_right;
    int build_type;
    StrDeal(const char* left, const char* right, bool single_line=false, bool note=false, bool translate=false,bool deal_build=false):LRDeal(left, right),single_line(single_line), note(note), translate(translate), deal_build(deal_build){
        if(translate){
            build_type = TYPE_STR_TRANSLATE;
        } else {
            build_type = TYPE_STR;
        }
        et_in_right=0;
        for(int i=0;i<lr;++i){
            if (right[i]=='\n')++et_in_right;
        }
    }
    int type(){if (deal_build)return BUILD_TYPE_STR;else return -1;}
    Item* build(Item* obj, Manager& mg);
    bool deal(BufferBase& buffer, ItemList& rst, Manager& mg);
    Item* build_arr(ItemList& arr, Int2& arr_pos, Manager& mg){return NULL;}

};
#endif