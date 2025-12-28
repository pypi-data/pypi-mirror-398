#ifndef XF_ITEM
#define XF_ITEM
#include "base.h"
#include "buffer.h"
struct Item{
    void* val;
    Int2 pos;
    int type;
    bool is_val;
    void* others;
    Item(void* val, Int2& pos, int type=-1, bool is_val = false, void* others=NULL):val(val),pos(pos),type(type),is_val(is_val),others(others){}
    std::string str(){
        std::stringstream ss;
        ss<<"<Item val = "<<val<<", type = "<<type<<", is_val = "<<is_val<<", pos = "<<pos.str()<<", others = "<<others<<">";
        return ss.str();
    }
    static Item* null;
    static bool is_null(Item* it) {
        return it==null;
    }
    static Item* get_null(){
        if (null==NULL){
            Int2 pos(0,0);
            null = new Item(NULL,pos);
        }
        return null;
    }
    ~Item(){}
};
typedef std::vector<Item*> ItemList;
#endif