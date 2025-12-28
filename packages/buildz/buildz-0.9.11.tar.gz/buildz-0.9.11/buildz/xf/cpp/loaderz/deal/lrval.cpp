
#include"lrval.h"
#include"../mg.h"
#include<unordered_map>
Item* LRValDeal::build_arr(ItemList& arr, Int2& arr_pos, Manager& mg){
    if(arr.size()!=3){
        std::stringstream errs;
        errs<<"error in lrval:"<<arr.size();;
        throw Exp(errs.str(), arr_pos);
    }
    Item* lrtype = arr[0];
    Item* lrval = arr[2];
    if(lrtype->type!=BUILD_TYPE_STR||lrval->type!=BUILD_TYPE_STR){
        std::stringstream errs;
        errs<<"error in lrval: type="<<lrtype->str()<<", val="<<lrval->str();
        throw Exp(errs.str(), arr_pos);
    }
    char* chars = (char*)lrtype->val;
    int ival = 0;
    int real_type;
    if (types.find(chars)==types.end()){
        std::stringstream errs;
        errs<<"error in lrval types:"<<chars;
        throw Exp(errs.str(), arr_pos);
    }
    real_type = types[chars];
    chars = (char*)lrval->val;
    if (real_type==TYPE_BOOL){
        if (bools.find(chars)==bools.end()){
            std::stringstream errs;
            errs<<"error in lrval bools:"<<chars;
            throw Exp(errs.str(), arr_pos);
        }
        ival = bools[chars];
    }
    void* rst = mg.callback->create(real_type, chars, ival);
    delete (char*) arr[0]->val;
    delete (char*) arr[2]->val;
    delete arr[0];
    delete arr[1];
    delete arr[2];
    return new Item(rst, arr_pos, real_type, true);
}