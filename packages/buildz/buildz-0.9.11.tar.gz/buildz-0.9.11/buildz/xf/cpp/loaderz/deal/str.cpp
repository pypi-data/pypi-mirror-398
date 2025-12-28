#include"str.h"
#include"../mg.h"
#include"../code.h"
Item* StrDeal::build(Item* obj, Manager& mg){
    char* s = (char*)obj->val;
    void* c_s = mg.callback->create(build_type, s);
    delete s;
    obj->val = c_s;
    obj->is_val = true;
    return obj;
}
bool StrDeal::deal(BufferBase& buffer, ItemList& rst, Manager& mg){
    if (!buffer.check_read(left, ll))return false;
    char* rm = NULL;
    Int2 rm_pos;
    int rm_size = buffer.full(rm, true);
    buffer.pos(rm_pos);
    buffer.clean2read(ll);
    //ItemList* arr = new ItemList();
    // ItemList arr, mg_arr;
    // arr.reserve(16);
    // mg_arr.reserve(16);
    if (rm_size>0){
        if (!note){
            std::stringstream errs;
            errs<<"unexcept char before string: "<<rm;
            throw Exp(errs.str(), rm_pos);
        } else {
            rst.push_back(new Item(rm, rm_pos, BUILD_TYPE_STR, false));
        }
    }
    bool do_judge = true;
    bool mark_l2 = false;
    int count_et = 0;
    //char chars[2];
    char ch;
    Int2 pos;
    int read_size;
    while(true){
        if (do_judge&&buffer.check_rget(right, lr)) {
            break;
        }
        //read_size = buffer.read_cache(chars);
        ch = buffer.read_cache();
        if (ch==0){
            if (single_line && note)break;
            buffer.pos(pos);
            throw Exp("unexcept string end while reading str", pos);
        }
        if (do_judge && ch=='\n'){
            ++count_et;
        }
        do_judge =true;
        if (ch=='\\'){
            mark_l2 = true;
            do_judge = false;
            ch = buffer.read_cache();
            if (ch==0){
                buffer.pos(pos);
                throw Exp("unexcept string end while reading str", pos);
            }
        }
    }
    buffer.pos(pos);
    pos.last-=lr;
    count_et -= et_in_right;
    if (single_line && count_et>0){
        throw Exp("contain enter in single line string", pos);
    }
    if (note){
        buffer.clean();
        return true;
    }
    char* data = NULL;
    read_size = buffer.full(data, false);
    data[read_size-1]=0;
    buffer.clean();
    int build_type = TYPE_STR;
    if (translate&&mark_l2) {
        char* tdata = do_translate(data);
        delete data;
        data=tdata;
        //build_type = TYPE_STR_TRANSLATE;
    }
    void* real_obj = mg.callback->create(build_type, data);
    delete data;
    rst.push_back(new Item(real_obj, pos, TYPE_STR, true));
    return true;
}
