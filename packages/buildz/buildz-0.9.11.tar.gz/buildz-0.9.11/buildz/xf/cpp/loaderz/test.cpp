#include<stdio.h>
#include<stdlib.h>
#include<string>
//#include<iostream>
#include "init.h"
#include"cxf.h"
#include "callback_demo.h"
#include<regex>
void* testloads(const char* str){
    CallbackDemo callback;
    Loads loads;
    loads.build();
    TypeVal* rst;
    try{
        rst = (TypeVal*)loads.loads(str, callback);
    }catch(std::exception& exp) {
        //std::cout<<"exp: "<<exp.what()<<std::endl;
        return (void*)1;
    }
    //std::cout<<"done loads"<<std::endl<<rst->str()<<std::endl;
    return NULL;

}
// int mainx(){
//     const char* str = "[-1e-1,1,2,3],1,2,3,{1=2,3=4,c=-123,null=xyz,hello=world,null=test},asdf,null,<bx, 0 >";
//     Loads loads;
//     loads.build();
//     CallbackDemo callback;
//     TypeVal* rst;
//     std::cout<<"start loads"<<std::endl;
//     try{
//         rst = (TypeVal*)loads.loads(str, callback);
//     }catch(std::exception& exp) {
//         std::cout<<"exp: "<<exp.what()<<std::endl;
//         return -1;
//     }
//     std::cout<<"done loads"<<std::endl<<rst->str()<<std::endl;
//     return 0;
// }

// g++ test.cpp -o test && ./test

// cls && g++ test.cpp -o test && test