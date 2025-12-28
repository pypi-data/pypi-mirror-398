
#include <jni.h>
#include <stdio.h>
#include "com_buildz_xf_LoaderJNI.h"
#include "loaderz/cxf.h"
#include "loaderz/base.h"
void* fc_create(void* obj, int type, void* val, int ival){
    JNIEnv* env = (JNIEnv*) obj;
    switch(type){
        case TYPE_NULL:
            return NULL;
        case TYPE_BOOL:
        {
            jclass booleanClass = env->FindClass("java/lang/Boolean");
            jmethodID constructor = env->GetMethodID(booleanClass, "<init>", "(Z)V");
            jobject result = env->NewObject(booleanClass, constructor, ival==1);
            env->DeleteLocalRef(booleanClass);
            return (void*)result;
        }
        case TYPE_INT:
        {
            long long lval = std::stoll((const char*) val);
            jclass longClass = env->FindClass("java/lang/Long");
            jmethodID constructor = env->GetMethodID(longClass, "<init>", "(J)V");
            jobject result = env->NewObject(longClass, constructor, lval);
            env->DeleteLocalRef(longClass);
            return (void*)result;
        }
        case TYPE_FLOAT:
        {
            double dval = std::stod((const char*) val);
            jclass doubleClass = env->FindClass("java/lang/Double");
            jmethodID constructor = env->GetMethodID(doubleClass, "<init>", "(D)V");
            jobject result = env->NewObject(doubleClass, constructor, dval);
            env->DeleteLocalRef(doubleClass);
            return (void*)result;
        }
        case TYPE_STR: {
            jstring sval = env->NewStringUTF((const char*) val);
            return (void*)sval;
        }
        case TYPE_LIST:{
            jclass mapClass = env->FindClass("java/util/ArrayList");
            jmethodID initMethod = env->GetMethodID(mapClass, "<init>", "()V");
            jobject hashMap = env->NewObject(mapClass, initMethod);
            env->DeleteLocalRef(mapClass);
            return (void*)hashMap;
        }
        case TYPE_DICT:{
            jclass mapClass = env->FindClass("java/util/HashMap");
            jmethodID initMethod = env->GetMethodID(mapClass, "<init>", "()V");
            jobject hashMap = env->NewObject(mapClass, initMethod);
            env->DeleteLocalRef(mapClass);
            return (void*)hashMap;
        }
        case TYPE_LISTDICT:{
            jclass mapClass = env->FindClass("com/buildz/xf/Args");
            jmethodID initMethod = env->GetMethodID(mapClass, "<init>", "()V");
            jobject hashMap = env->NewObject(mapClass, initMethod);
            env->DeleteLocalRef(mapClass);
            return (void*)hashMap;
        }
    }
    return NULL;
}
void fc_dict_set(void* obj, void* dict, void* key, void* val){
    JNIEnv* env = (JNIEnv*) obj;
    jclass mapClass = env->FindClass("java/util/Map");
    jmethodID putMethod = env->GetMethodID(mapClass, "put", 
        "(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;");
    env->CallObjectMethod((jobject)dict, putMethod, (jobject)key, (jobject)val);
    env->DeleteLocalRef((jobject)key);
    env->DeleteLocalRef((jobject)val);
    env->DeleteLocalRef(mapClass);
}
void fc_dict_setx(void* obj, void* dict, void* key, void* val){
    JNIEnv* env = (JNIEnv*) obj;
    jclass mapClass = env->FindClass("com/buildz/xf/Args");
    jmethodID putMethod = env->GetMethodID(mapClass, "put", 
        "(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;");
    env->CallObjectMethod((jobject)dict, putMethod, (jobject)key, (jobject)val);
    env->DeleteLocalRef((jobject)key);
    env->DeleteLocalRef((jobject)val);
    env->DeleteLocalRef(mapClass);
}
void fc_list_add(void* obj, void* list, void* val){
    JNIEnv* env = (JNIEnv*) obj;
    jclass mapClass = env->FindClass("java/util/List");
    jmethodID addMethod = env->GetMethodID(mapClass, "add", 
        "(Ljava/lang/Object;)Z");
    env->CallObjectMethod((jobject)list, addMethod, val);
    env->DeleteLocalRef((jobject)val);
    env->DeleteLocalRef(mapClass);
}
void fc_list_addx(void* obj, void* list, void* val){
    JNIEnv* env = (JNIEnv*) obj;
    jclass mapClass = env->FindClass("com/buildz/xf/Args");
    jmethodID addMethod = env->GetMethodID(mapClass, "add", 
        "(Ljava/lang/Object;)Z");
    env->CallObjectMethod((jobject)list, addMethod, val);
    env->DeleteLocalRef((jobject)val);
    env->DeleteLocalRef(mapClass);
}
void* fc_exp(void* obj, const char* s){
    JNIEnv* env = (JNIEnv*) obj;
    jstring str = env->NewStringUTF(s);
    jclass mapClass = env->FindClass("java/lang/Exception");
    jmethodID initMethod = env->GetMethodID(mapClass, "<init>", "(Ljava/lang/String;)V");
    jobject exp = env->NewObject(mapClass, initMethod, str);
    env->DeleteLocalRef(mapClass);
    return (void*)exp;
}
JNIEXPORT jobject JNICALL Java_com_buildz_xf_LoaderJNI_jloads
  (JNIEnv *env, jobject it, jstring s){
    return (jobject)loads_mtds(env->GetStringUTFChars(s, nullptr), (void*)env, fc_create, fc_dict_set, fc_list_add, fc_exp);
  }

JNIEXPORT jobject JNICALL Java_com_buildz_xf_LoaderJNI_jloadx
  (JNIEnv *env, jobject it, jstring s, jboolean spc){
    return (jobject)loadx_mtds(env->GetStringUTFChars(s, nullptr), (void*)env, fc_create, fc_dict_setx, fc_list_addx, fc_exp, spc);
  }