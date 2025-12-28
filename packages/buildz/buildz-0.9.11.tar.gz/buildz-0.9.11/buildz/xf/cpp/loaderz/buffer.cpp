
#include "buffer.h"
#include <cctype>
    std::string StrBuffer::pos2str(Int2& pos){
        int size = pos.last-pos.first;
        char chars[size+1];
        std::memcpy(chars, str+pos.first, size);
        chars[size]=0;
        return std::string(chars);
    }
    // int StrBuffer::read(char* chars, int size){
    //     size = std::min(size, str_size+1-read_base);
    //     std::memcpy(chars, str+read_base, size);
    //     chars[size]=0;
    //     return size;
    // }
    // int StrBuffer::read_cache(char* chars, int size){
    //     size = read(chars, size);
    //     buffer_size+=size;
    //     read_base+=size;
    //     return size;
    // }
    char StrBuffer::read(){
        return str[read_base];
    }
    char StrBuffer::read_cache(){
        char c = read();
        if (c==0)return c;
        buffer_size++;
        read_base++;
        return c;
    }
    bool StrBuffer::check_read(const char* chars, int size){
        if (size>(str_size-read_base))return false;
        for(int i=0;i<size;++i){
            if (chars[i]!=str[read_base+i])return false;
        }
        return true;
    }
    int StrBuffer::clean(int read_size){
        read_base+=read_size;
        buffer_base=read_base;
        buffer_size=0;
        return 0;
    }
    int StrBuffer::size(){return buffer_size;}
    int StrBuffer::full(char*& chars, bool strip) {
        int base = buffer_base;
        int last = buffer_base+buffer_size;
        if (strip){
            while(base<last&&std::isspace(str[base]))++base;
            while(last>base&&std::isspace(str[last-1]))--last;
        }
        int size = last-base;
        if (size>0){
            if (chars==NULL){
                chars = new char[size+1];
            }
            std::memcpy(chars, str+base,size);
            chars[size]=0;
        }
        return size;
    }
    int StrBuffer::rget(char* chars, int size){
        size = std::min(size, buffer_size);
        std::memcpy(chars, str+(buffer_base+buffer_size-size), size);
        return size;
    }
    int StrBuffer::get(char* chars, int size){
        size = std::min(size, buffer_size);
        std::memcpy(chars, str+buffer_base, size);
        return size;
    }
    bool StrBuffer::_check_get(const char* chars, int size, bool right){
        if (buffer_size<size)return false;
        int base = buffer_base;
        if (right)base += buffer_size-size;
        for(int i=0;i<size;++i){
            if (chars[i]!=str[base+i])return false;
        }
        return true;
    }
    bool StrBuffer::check_get(const char* chars, int size){
        return _check_get(chars, size);
    }
    bool StrBuffer::check_rget(const char* chars, int size){
        return _check_get(chars, size, true);
    }