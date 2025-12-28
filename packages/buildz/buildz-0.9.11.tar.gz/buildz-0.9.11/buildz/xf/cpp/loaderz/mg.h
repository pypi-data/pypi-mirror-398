#ifndef XF_MANAGER
#define XF_MANAGER

//#include <unordered_map>
#include "base_deal.h"
#include "base.h"
#include "exp.h"
#include "item.h"
#include "callback.h"
typedef std::vector<BaseDeal*> BaseDealList;
#define MG_MAX_SIZE 256
struct Manager{
    BaseDealList deals[MG_MAX_SIZE];
    BaseDealList builds[MG_MAX_SIZE];
    Callback* callback;
    Manager(){
    }
    Manager& add(BaseDeal* deal);
    bool deal(BufferBase& buffer, ItemList& arr);
    Item* build(Item* obj);
    int build_arr(ItemList& arr, ItemList& outs);
    static void arr_pos(ItemList& arr, Int2& rst);
    void* _load(BufferBase& buffer, Callback* callback) ;
    void* load(BufferBase& buffer, Callback* callback);
    void* loads(const char* str, Callback* callback);
    inline void release_deals(BaseDealList& deals, std::set<BaseDeal*>& rels);
    ~Manager();
};

#endif