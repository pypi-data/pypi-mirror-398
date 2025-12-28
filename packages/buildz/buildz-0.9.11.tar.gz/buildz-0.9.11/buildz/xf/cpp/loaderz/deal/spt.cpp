
#include"spt.h"
#include"../mg.h"
    Item* PrevSptDeal::build(Item* it, Manager&){
        delete it;
        return Item::get_null();
    }
    bool PrevSptDeal::deal(BufferBase& buffer, ItemList& rst, Manager& mg){
        if (!buffer.check_read(spt, l_spt))return false;
        Int2 spt_pos(buffer.read_base, buffer.read_base+l_spt);
        char* rm = NULL;
        int rm_size = buffer.full(rm, true);
        Int2 rm_pos;
        buffer.pos(rm_pos);
        buffer.clean2read(l_spt);
        Item* it = new Item((void*)spt, spt_pos, build_type, false);
        if (rm_size==0){
            if (!allow_empty||(rst.size()>0 && rst.back()->is_val)){
                rst.push_back(it);
                return true;
            }
        }
        Item* obj = new Item(rm, rm_pos, BUILD_TYPE_STR, false);
        rst.push_back(obj);
        rst.push_back(it);
        return true;
    }