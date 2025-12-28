#include"mg.h"

    Manager& Manager::add(BaseDeal* deal) {
        int label = deal->label();
        if (label>=0) {
            deals[label].push_back(deal);
        }
        int type = deal->type();
        if (type>=0) {
            builds[type].push_back(deal);
        }
        return *this;
    }
    bool Manager::deal(BufferBase& buffer, ItemList& arr) {
        //char chars[2];
        //buffer.read(chars);
        byte c = buffer.read();
        if(c==0 && buffer.size()==0)return false;
        for(BaseDeal* deal:deals[c]) {
            if (deal->deal(buffer, arr, *this))return true;
        }
        for(BaseDeal* deal:deals[DEFAULT_DEAL]){
            if (deal->deal(buffer, arr, *this))return true;
        }
        return false;
    }
    Item* Manager::build(Item* obj) {
        if (obj->is_val){
            return obj;
        }
        int type = obj->type;
        Item* rst;
        for(BaseDeal* deal:builds[type]){
            rst = deal->build(obj, *this);
            if (rst)return rst;
        }
        std::stringstream ss;
        ss<<"unspt deal type:["<<obj->str()<<"]";
        std::string s = ss.str();
        throw Exp(s, obj->pos);
    }
    int Manager::build_arr(ItemList& arr, ItemList& outs) {
        for(Item* k:arr) {
            Item* _k = build(k);
            if (Item::is_null(_k))continue;
            outs.push_back(_k);
        }
        return 0;
    }
    void Manager::arr_pos(ItemList& arr, Int2& rst) {
        if (arr.size()==0){
            rst.reset(0,0);
            return;
        }
        rst.reset((*arr.front()).pos.first, (*arr.back()).pos.last);
    }
    void* Manager::_load(BufferBase& buffer, Callback* callback) {
        this->callback = callback;
        ItemList arr_items;
        arr_items.reserve(16);
        while(deal(buffer, arr_items));
        ItemList* arr = new ItemList();
        arr->reserve(arr_items.size());
        build_arr(arr_items, *arr);
        Int2 arr_pos;
        Manager::arr_pos(*arr, arr_pos);
        Item* obj = new Item(arr, arr_pos, BUILD_TYPE_LIST, false);
        obj = build(obj);
        void* val = obj->val;
        delete obj;
        return val;
    }
    void* Manager::load(BufferBase& buffer, Callback* callback) {
        try{
            return _load(buffer, callback);
        }catch(Exp& exp){
            return callback->exp(exp.deal(buffer).c_str());
            //return NULL;
        }
    }
    void* Manager::loads(const char* str, Callback* callback){
        StrBuffer buffer(str, strlen(str));
        return load(buffer, callback);
    }
    void Manager::release_deals(BaseDealList& deals, std::set<BaseDeal*>& rels) {
        for(BaseDeal* deal:deals) {
            auto find = rels.find(deal);
            if (find!=rels.end())continue;
            rels.insert(deal);
            delete deal;
        }
    }
    Manager::~Manager() {
        std::set<BaseDeal*> rels;
        for(int i=0;i<MG_MAX_SIZE;++i) {
            release_deals(deals[i], rels);
            release_deals(builds[i], rels);
        }
    }