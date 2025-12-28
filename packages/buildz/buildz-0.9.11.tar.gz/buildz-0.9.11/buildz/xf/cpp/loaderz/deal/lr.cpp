
#include "lr.h"
#include"../mg.h"
bool LRDeal::deal(BufferBase& buffer, ItemList& rst, Manager& mg){
    if (!buffer.check_read(left, ll))return false;
    char* rm = NULL;
    Int2 rm_pos;
    int rm_size = buffer.full(rm, true);
    buffer.pos(rm_pos);
    buffer.clean2read(ll);
    //ItemList* arr = new ItemList();
    ItemList arr, mg_arr;
    arr.reserve(16);
    mg_arr.reserve(16);
    if (rm_size>0){
        arr.push_back(new Item(rm, rm_pos, BUILD_TYPE_STR, false));
    }
    Int2 arr_pos(rm_pos);
    while (!buffer.check_read(right, lr)){
        if (!mg.deal(buffer, arr)){
            buffer.pos(rm_pos);
            throw Exp("Error lr", rm_pos);
        }
    }
    rm=NULL;
    rm_size = buffer.full(rm,true);
    buffer.pos(rm_pos);
    buffer.clean2read(lr);
    arr_pos.last = rm_pos.last;
    if (rm_size>0){
        arr.push_back(new Item(rm, rm_pos, BUILD_TYPE_STR, false));
    }
    ItemList* ptr_arr = &arr;
    if (mg_build) {
        mg.build_arr(arr, mg_arr);
        ptr_arr = &mg_arr;
    }
    Item* obj = build_arr(*ptr_arr, arr_pos, mg);
    rst.push_back(obj);
    return true;
}