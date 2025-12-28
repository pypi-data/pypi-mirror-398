
#include"dict.h"
#include"../mg.h"
#include<iostream>
Item* DictDeal::build(Item* obj, Manager& mg) {
    ItemList& list = *(ItemList*)obj->val;
    int size = list.size();
    if (size%3!=0)return NULL;
    if (size>0&&list[1]->type!=BUILD_TYPE_KEYVAL)return NULL;
    Item* rst = build_arr(list, obj->pos, mg);
    delete &list;
    delete obj;
    return rst;
}
Item* DictDeal::build_arr(ItemList& arr, Int2& arr_pos, Manager& mg){
    int size = arr.size();
    if (size%3!=0){
        std::stringstream errs;
        errs<<"u f in map: "<<arr.size();
        // for(int i=0;i<size;i++){
        //     std::cout<<"index:"<<i<<":"<<arr[i]->str()<<std::endl;
        // }
        throw Exp(errs.str(), arr_pos);
    }
    void* rst = mg.callback->create(TYPE_DICT, NULL, (size/3));
    for(int i=0;i<size;i+=3){
        Item* k = arr[i];
        Item* opt = arr[i+1];
        Item* v = arr[i+2];
        if (opt->type!=BUILD_TYPE_KEYVAL){
            std::stringstream errs;
            errs<<"u f opt in map: "<<opt->str();
            throw Exp(errs.str(), opt->pos);
        }
        mg.callback->dict_set(rst, k->val, v->val);
        delete k;
        delete v;
        delete opt;
    }
    return new Item(rst, arr_pos, TYPE_DICT, true);
}