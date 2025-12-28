

#ifndef XF_BASE
#define XF_BASE
#include<string>
#include<sstream>
#include<stdio.h>
//#include<iostream>
#include<cstring>
#include<stdlib.h>
#include <vector>
#include <exception>
#include <set>
#include <algorithm>
#include <map>

#define DEFAULT_DEAL 0
typedef unsigned char byte;

#define BUILD_TYPE_LIST 1
#define BUILD_TYPE_STR 2
#define BUILD_TYPE_KEYVAL 3
#define BUILD_TYPE_SPT 4

#define TYPE_NULL 0
#define TYPE_BOOL 1
#define TYPE_BOOL_TRUE 101
#define TYPE_BOOL_FALSE 102
#define TYPE_INT 2
#define TYPE_FLOAT 3
#define TYPE_STR 4
#define TYPE_STR_TRANSLATE 401
#define TYPE_LIST 5
#define TYPE_DICT 6
#define TYPE_LISTDICT 7
#endif