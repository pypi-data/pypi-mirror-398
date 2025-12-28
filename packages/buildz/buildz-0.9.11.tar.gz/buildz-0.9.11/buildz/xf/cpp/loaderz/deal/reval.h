#ifndef XF_REVAL
#define XF_REVAL
#include"../base_deal.h"
#include<regex>
struct ValDeal: public BaseDeal {
    std::regex pt;
    int val_type;
    int obj_type;
    int type(){return BUILD_TYPE_STR;}
    ValDeal(const char* pt, int val_type, int obj_type=-1):pt(pt),val_type(val_type),obj_type(obj_type){
        if (obj_type<0){
            this->obj_type = val_type;
        }
    }
    Item* build(Item* obj, Manager& mg){
        //if (val_type!=TYPE_INT){return NULL;}
        char* val = (char*)(obj->val);
        if (!std::regex_match(val, pt)){
            return NULL;
        }
        int ival = 0;
        int real_type = val_type;
        if (val_type==TYPE_BOOL_TRUE){
            real_type = TYPE_BOOL;
            ival = 1;
        }else if (val_type == TYPE_BOOL_FALSE){
            real_type = TYPE_BOOL;
            ival = 0;
        }
        void* rst = mg.callback->create(real_type, (void*)val, ival);
        //void* rst = fc(val, mg);
        delete val;
        obj->val = rst;
        obj->type = obj_type;
        obj->is_val = true;
        return obj;
    }
};
#endif