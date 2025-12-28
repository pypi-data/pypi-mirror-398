
#include"callback_demo.h"
static const char* s_types[10];
int init_s_types(){
    s_types[TYPE_BOOL] = "bool";
    s_types[TYPE_INT] = "int";
    s_types[TYPE_FLOAT] = "float";
    s_types[TYPE_LIST] = "list";
    s_types[TYPE_DICT] = "dict";
    s_types[TYPE_LISTDICT] = "list_dict";
    return 0;
}
int tmp = init_s_types();
bool Compare::operator()(const ptrTypeVal& a, const ptrTypeVal& b)const{
    return *a<*b;
}
    bool TypeVal::operator<(const TypeVal& tval)const{
        if (type!=tval.type){return type<tval.type;}
        switch(type){
            case TYPE_NULL:
                return false;
            case TYPE_INT:
            case TYPE_BOOL:
            case TYPE_FLOAT:
                return fval<tval.fval;
            case TYPE_STR:
                return s<tval.s;
                break;
        }
        printf("error key type:%s\n",s_types[type]);
        //std::cout<<"error key type:"<<s_types[type]<<std::endl;
        exit(0);
    }
    std::string TypeVal::str(){
        std::stringstream ss;
        switch(type){
            case TYPE_NULL:
                ss<<"null";
                break;
            case TYPE_INT:
                ss<<val;
                break;
            case TYPE_FLOAT:
                ss<<fval;
                break;
            case TYPE_BOOL:
                ss<<bl;
                break;
            case TYPE_STR:
                ss<<s;
                break;
            case TYPE_LIST:
                ss<<"[";
                for (TypeVal* it:list){
                    ss<<it->str()<<",";
                }
                ss<<"]";
                break;
            case TYPE_DICT:
                ss<<"{";
                for(const auto& pair:dict){
                    ss<<pair.first->str()<<":"<<pair.second->str()<<",";
                }
                ss<<"}";
                break;
            case TYPE_LISTDICT:
                ss<<"(";
                for (TypeVal* it:list){
                    ss<<it->str()<<",";
                }
                for(const auto& pair:dict){
                    ss<<pair.first->str()<<"="<<pair.second->str()<<",";
                }
                ss<<")";
                break;
        }
        //ss<<"<"<<s_types[type]<<">";
        return ss.str();
    }
    TypeVal::TypeVal(int type, void* val, int ival):type(type){
        const char* _s = (const char*) val;
        switch(type){
            case TYPE_NULL:
                break;
            case TYPE_BOOL_TRUE:
                bl = true;
                type = TYPE_BOOL;
                break;
            case TYPE_BOOL_FALSE:
                bl = false;
                type = TYPE_BOOL;
                break;
            case TYPE_BOOL:
                bl = ival!=0;
                break;
            case TYPE_INT:
                this->val = atoi(_s);
                break;
            case TYPE_FLOAT:
                this->fval = atof(_s);
                break;
            case TYPE_STR_TRANSLATE:
                type = TYPE_STR;
            case TYPE_STR:
                s=(const char*) val;
                break;
            case TYPE_LIST:
                if (ival>0){
                    list.reserve(ival);
                }
                break;
            case TYPE_DICT:
                if (ival>0){
                    //dict.reserve(size);
                }
                break;
            case TYPE_LISTDICT:
                break;
        }
    }
    void* CallbackDemo::create(int type, void* val, int ival){
        return new TypeVal(type, val, ival);
    }
    void CallbackDemo::dict_set(void* dict, void* key, void *val) {
        // TypeVal& map = *(TypeVal*) dict;
        // map.dict[(TypeVal*)key] = (TypeVal*)val;
    }
    void CallbackDemo::list_add(void* list, void* val){
        // TypeVal& arr = *(TypeVal*) list;
        // arr.list.push_back((TypeVal*)val);
    }
    void* CallbackDemo::exp(const char* s){
        //std::cout<<"exp: "<<s<<std::endl;
        printf("exp: %s\n", s);
        //exit(0);
        return NULL;
    }