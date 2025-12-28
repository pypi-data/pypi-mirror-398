
#include"list.h"
#include"../mg.h"
Item* ListDeal::build(Item* obj, Manager& mg) {
    ItemList& list = *(ItemList*)obj->val;
    int size = list.size();
    // if (size==0){
    //     obj->is_val=true;
    //     return obj;
    // }
    if (size>1){
        Item* it = list[1];
        if (it->type==BUILD_TYPE_KEYVAL)return NULL;
    }
    Item* rst = build_arr(list, obj->pos, mg);
    delete &list;
    delete obj;
    return rst;
}
Item* ListDeal::build_arr(ItemList& arr, Int2& arr_pos, Manager& mg){
    void* rst = mg.callback->create(TYPE_LIST, NULL,arr.size());
    for(Item* it:arr) {
        if (!it->is_val) {
            std::string err("error in list: item is not val: ");
            err+=it->str();
            throw Exp(err, it->pos);
        }
        mg.callback->list_add(rst, it->val);
        delete it;
    }
    return new Item(rst, arr_pos, TYPE_LIST, true);
}