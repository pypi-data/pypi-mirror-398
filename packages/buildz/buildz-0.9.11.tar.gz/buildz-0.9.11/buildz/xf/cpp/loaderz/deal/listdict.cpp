
#include"listdict.h"
#include"../mg.h"
Item* ListDictDeal::build(Item* obj, Manager& mg) {
    ItemList& list = *(ItemList*)obj->val;
    Item* rst = build_arr(list, obj->pos, mg);
    delete &list;
    delete obj;
    return rst;
}
Item* ListDictDeal::build_arr(ItemList& arr, Int2& arr_pos, Manager& mg){
    int size = arr.size();
    void* rst = mg.callback->create(TYPE_LISTDICT, NULL,size);
    int i=0;
    std::stringstream errs;
    while (i<size){
        Item* obj = arr[i];
        Item* opt = NULL;
        if (i+1<size){
            opt = arr[i+1];
        }
        if (opt!=NULL&&opt->type==BUILD_TYPE_KEYVAL){
            if(i+2>=size){
                errs<<"u f in listdict:"<<size;
                throw Exp(errs.str(), arr_pos);
            }
            Item* val = arr[i+2];
            mg.callback->dict_set(rst, obj->val, val->val);
            i+=3;
            delete opt;
            delete val;
        } else {
            mg.callback->list_add(rst, obj->val);
            ++i;
        }
        delete obj;
    }
    return new Item(rst, arr_pos, TYPE_LISTDICT, true);
}