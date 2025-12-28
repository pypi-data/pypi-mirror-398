#ifndef XF_EXP
#define XF_EXP
#include <exception>
#include "buffer.h"
#include<string>
//#include<iostream>
struct Exp:public std::exception{
    Int2 pos;
    std::string msg;
    Exp(const char* msg, Int2 pos):pos(pos){
        this->msg = msg;
        this->msg += ", [OFFSET]: "+pos.str();
    }
    // Exp(std::string& msg, Int2& pos):Exp(msg.c_str(), pos){}
    Exp(std::string msg, Int2 pos):Exp(msg.c_str(), pos){

    }
    std::string deal(BufferBase& buffer){
        std::string s = buffer.pos2str(pos);
        s = msg+" [CONTENT]: '"+s+"'";
        return s;
        //throw std::runtime_error(s);
    }
};
#endif