
#include "init.h"
#include "deal/next.h"
#include "deal/list.h"
#include "deal/reval.h"
#include "deal/spt.h"
#include "deal/kv.h"
#include "deal/dict.h"
#include "deal/str.h"
#include "deal/lrval.h"
#include "deal/listdict.h"
#include "cxf.h"
Item* Item::null = NULL;
void add_lrval(Manager& mg){
    LRValDeal* deal = new LRValDeal("<",">");
    deal->set_type("bool", TYPE_BOOL);
    deal->set_type("bl", TYPE_BOOL);
    deal->set_type("b", TYPE_BOOL);
    deal->set_type("int", TYPE_FLOAT);
    deal->set_type("i", TYPE_FLOAT);
    deal->set_type("float", TYPE_FLOAT);
    deal->set_type("f", TYPE_FLOAT);
    deal->set_type("null", TYPE_NULL);
    deal->set_type("nil", TYPE_NULL);
    deal->set_type("n", TYPE_NULL);
    deal->set_bool("0", 0);
    deal->set_bool("false", 0);
    deal->set_bool("False", 0);
    deal->set_bool("1", 1);
    deal->set_bool("true", 1);
    deal->set_bool("True", 1);
    mg.add(deal);
}
void add_reval(Manager& mg){
    mg.add(new ValDeal("^[\\+\\-]?\\d+$", TYPE_INT));
    mg.add(new ValDeal("^[\\+\\-]?\\d*\\.\\d+$", TYPE_FLOAT));
    mg.add(new ValDeal("^[\\+\\-]?\\d*(?:\\.\\d+)?e[\\+\\-]?\\d+$", TYPE_FLOAT));
    mg.add(new ValDeal("^null$", TYPE_NULL));
    mg.add(new ValDeal("^true$", TYPE_BOOL_TRUE));
    mg.add(new ValDeal("^false$", TYPE_BOOL_FALSE));
}
Loads::Loads(){
    mark_init = false;
}
void Loads::build(){
    if (mark_init)return;
    mark_init = true;
    mg.add(new KeyValDeal(":"));
    mg.add(new KeyValDeal("="));
    mg.add(new PrevSptDeal(",",true));
    mg.add(new PrevSptDeal(";",true));
    mg.add(new PrevSptDeal("\n",false));
    add_lrval(mg);
    mg.add(new ListDeal("[","]"));
    mg.add(new ListDeal("(",")"));
    mg.add(new DictDeal("{","}"));
    add_reval(mg);
    mg.add(new StrDeal("r'''","'''",false,false,false));
    mg.add(new StrDeal("r\"\"\"","\"\"\"",false,false,false));
    mg.add(new StrDeal("r'","'",true,false,false,true));
    mg.add(new StrDeal("r\"","\"",true,false,false));
    mg.add(new StrDeal("###","###",false,true));
    mg.add(new StrDeal("/*","*/",false,true));
    mg.add(new StrDeal("'''","'''",false,false,true));
    mg.add(new StrDeal("\"\"\"","\"\"\"",false,false,true));
    mg.add(new StrDeal("#","\n",true,true));
    mg.add(new StrDeal("//","\n",true,true));
    mg.add(new StrDeal("'","'",true,false,true));
    mg.add(new StrDeal("\"","\"",true,false,true));
    mg.add(new PrevNextDeal());
}
void Loads::buildx(bool spc){
    if (mark_init)return;
    mark_init = true;
    mg.add(new KeyValDeal(":"));
    mg.add(new KeyValDeal("="));
    mg.add(new PrevSptDeal(",",true));
    mg.add(new PrevSptDeal(";",true));
    mg.add(new PrevSptDeal("\n",false));
    if (spc)mg.add(new PrevSptDeal(" ",false));
    add_lrval(mg);
    mg.add(new ListDictDeal("[","]"));
    mg.add(new ListDictDeal("(",")"));
    mg.add(new ListDictDeal("{","}",true));
    add_reval(mg);
    mg.add(new StrDeal("r'''","'''",false,false,false));
    mg.add(new StrDeal("r\"\"\"","\"\"\"",false,false,false));
    mg.add(new StrDeal("r'","'",true,false,false,true));
    mg.add(new StrDeal("r\"","\"",true,false,false));
    mg.add(new StrDeal("###","###",false,true));
    mg.add(new StrDeal("/*","*/",false,true));
    mg.add(new StrDeal("'''","'''",false,false,true));
    mg.add(new StrDeal("\"\"\"","\"\"\"",false,false,true));
    mg.add(new StrDeal("#","\n",true,true));
    mg.add(new StrDeal("//","\n",true,true));
    mg.add(new StrDeal("'","'",true,false,true));
    mg.add(new StrDeal("\"","\"",true,false,true));
    mg.add(new PrevNextDeal());
}
Loads::~Loads(){
    //std::cout<<"release loads"<<std::endl;
    //printf("release loads\n");
}
struct FcCallback:public Callback{
    fptr_create fc_create; 
    fptr_dict_set fc_set; 
    fptr_list_add fc_add; 
    fptr_exp fc_exp;
    FcCallback(fptr_create fc_create, fptr_dict_set fc_set, fptr_list_add fc_add, fptr_exp fc_exp):
    fc_create(fc_create),fc_set(fc_set),fc_add(fc_add),fc_exp(fc_exp){}
    void* create(int type, void* val=NULL, int ival=0){
        return fc_create(type, val, ival);
    }
    void dict_set(void* dict, void* key, void *val){
        fc_set(dict, key, val);
    }
    void list_add(void* list, void* val){
        fc_add(list, val);
    }
    void* exp(const char* s){
        return fc_exp(s);
    }
};
static Loads obj_loads;
static Loads obj_loadx;
static Loads obj_loadx_spc;
void* loads(const char* s, void* callback){
    Callback* cb = (Callback*)callback;
    obj_loads.build();
    return obj_loads.loads(s, *cb);
}
void* loadx(const char* s, void* callback, bool spc){
    Callback* cb = (Callback*)callback;
    Loads* obj_ld = NULL;
    if(spc){
        obj_ld = &obj_loadx_spc;
    } else {
        obj_ld = &obj_loadx;
    }
    obj_ld->buildx(spc);
    return obj_ld->loads(s, *cb);
}
void* loads_fcs(const char* s, fptr_create fc_create, fptr_dict_set fc_set, fptr_list_add fc_add, fptr_exp fc_exp){
    FcCallback callback(fc_create, fc_set, fc_add, fc_exp);
    obj_loads.build();
    return obj_loads.loads(s, callback);
}
void* loadx_fcs(const char* s, fptr_create fc_create, fptr_dict_set fc_set, fptr_list_add fc_add, fptr_exp fc_exp, bool spc){
    FcCallback callback(fc_create, fc_set, fc_add, fc_exp);
    Loads* obj_ld = NULL;
    if(spc){
        obj_ld = &obj_loadx_spc;
    } else {
        obj_ld = &obj_loadx;
    }
    obj_ld->buildx(spc);
    return obj_ld->loads(s, callback);
}
struct MethodCallback:public Callback{
    mptr_create fc_create; 
    mptr_dict_set fc_set; 
    mptr_list_add fc_add; 
    mptr_exp fc_exp;
    void* obj;
    MethodCallback(void* obj, mptr_create fc_create, mptr_dict_set fc_set, mptr_list_add fc_add, mptr_exp fc_exp):obj(obj),
    fc_create(fc_create),fc_set(fc_set),fc_add(fc_add),fc_exp(fc_exp){}
    void* create(int type, void* val=NULL, int ival=0){
        return fc_create(obj, type, val, ival);
    }
    void dict_set(void* dict, void* key, void *val){
        fc_set(obj, dict, key, val);
    }
    void list_add(void* list, void* val){
        fc_add(obj, list, val);
    }
    void* exp(const char* s){
        return fc_exp(obj, s);
    }
};
void* loads_mtds(const char* s, void* obj, mptr_create fc_create, mptr_dict_set fc_set, mptr_list_add fc_add, mptr_exp fc_exp){
    MethodCallback callback(obj, fc_create, fc_set, fc_add, fc_exp);
    obj_loads.build();
    return obj_loads.loads(s, callback);
}
void* loadx_mtds(const char* s, void* obj, mptr_create fc_create, mptr_dict_set fc_set, mptr_list_add fc_add, mptr_exp fc_exp, bool spc){
    MethodCallback callback(obj, fc_create, fc_set, fc_add, fc_exp);
    Loads* obj_ld = NULL;
    if(spc){
        obj_ld = &obj_loadx_spc;
    } else {
        obj_ld = &obj_loadx;
    }
    obj_ld->buildx(spc);
    return obj_ld->loads(s, callback);
}