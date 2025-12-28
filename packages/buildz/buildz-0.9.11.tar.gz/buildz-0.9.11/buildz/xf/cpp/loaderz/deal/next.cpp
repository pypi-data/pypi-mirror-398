
#include"next.h"
#include"../mg.h"
    bool PrevNextDeal::deal(BufferBase& buffer, ItemList& rst, Manager& mg){
        //char s[2];
        //int size = buffer.read_cache(s, 1);
        char c = buffer.read_cache();
        if (c==0){
            //size = buffer.size();
            char* rm = NULL;
            int size = buffer.full(rm,true);
            if (size==0){
                return false;
            }
            Int2 pos;
            buffer.pos(pos);
            buffer.clean();
            Item* item = new Item(rm, pos, BUILD_TYPE_STR, false);
            rst.push_back(item);
            return true;
        }
        return true;
    }
    