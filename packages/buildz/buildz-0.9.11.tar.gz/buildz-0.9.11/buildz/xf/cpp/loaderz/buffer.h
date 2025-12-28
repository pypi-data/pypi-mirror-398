#ifndef XF_BUFFER
#define XF_BUFFER
#include "base.h"
#include <cctype>
//#include <cstring>
struct Int2{
    int first,last;
    Int2(){}
    Int2(int a,int b):first(a),last(b){}
    Int2(const Int2& a){first=a.first;last=a.last;}
    void reset(int a, int b) { first=a; last=b; }
    void reset(Int2& a){first=a.first;last=a.last;}
    std::string str(){
        std::stringstream ss;
        ss<<"("<<first<<", "<<last<<")";
        return ss.str();
    }
};
struct BufferBase {
    int buffer_base;
    int read_base;
    BufferBase():buffer_base(0),read_base(0){}
    void pos(Int2& i2){i2.reset(buffer_base, buffer_base+size());}
    void offsets(Int2& i2){ i2.reset(buffer_base, read_base); }
    int clean2read(int size=1) { return clean(size); }
    // virtual
    virtual std::string pos2str(Int2& pos)=0;
    virtual char read_cache() =0;
    virtual bool check_read(const char* chars, int size)=0;
    virtual char read() = 0;
    virtual int clean(int read_size=0)=0;
    virtual int size()=0;
    virtual int full(char*& chars, bool strip=false)=0;
    virtual int rget(char* chars, int size=1)=0;
    virtual int get(char* chars, int size=1)=0;
    virtual bool check_rget(const char* chars, int size=1)=0;
    virtual bool check_get(const char* chars, int size=1)=0;
};
struct StrBuffer: public BufferBase {
    const char* str;
    int buffer_size;
    int str_size;
    StrBuffer(const char* str, int size):BufferBase(),str(str),buffer_size(0),str_size(size){}
    std::string pos2str(Int2& pos);
    char read_cache();
    bool check_read(const char* chars, int size);
    char read();
    int clean(int read_size=0);
    int size();
    int full(char*& chars, bool strip=false);
    int rget(char* chars, int size=1);
    int get(char* chars, int size=1);
    inline bool _check_get(const char* chars, int size=1, bool right=false);
    bool check_get(const char* chars, int size=1);
    bool check_rget(const char* chars, int size=1);
};
#endif