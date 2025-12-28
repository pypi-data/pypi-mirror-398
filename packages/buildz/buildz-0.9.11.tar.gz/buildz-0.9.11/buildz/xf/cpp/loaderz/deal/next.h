#ifndef XF_NEXT
#define XF_NEXT
#include"../base_deal.h"

struct PrevNextDeal:public BaseDeal{
    int label(){return DEFAULT_DEAL;}
    bool deal(BufferBase& buffer, ItemList& rst, Manager& mg);
    
};
#endif