#ifndef XF_BASE_DEAL
#define XF_BASE_DEAL
#include"base.h"
#include "buffer.h"
#include"item.h"
#include <cctype>
struct Manager;
struct BaseDeal{
    virtual bool deal(BufferBase& buffer, ItemList& rst, Manager& mg){return false;}
    // if do build, do delete obj
    virtual Item* build(Item* obj, Manager& mg) {return NULL;}
    virtual int label(){return -1;}
    virtual int type(){return -1;}
    virtual void regist(Manager& mg){}
    virtual ~BaseDeal(){}
};

// std::string strip(const std::string &inpt)
// {
//     auto start_it = inpt.begin();
//     auto end_it = inpt.rbegin();
//     while (std::isspace(*start_it))
//         ++start_it;
//     while (std::isspace(*end_it))
//         ++end_it;
//     return std::string(start_it, end_it.base());
// }
#endif