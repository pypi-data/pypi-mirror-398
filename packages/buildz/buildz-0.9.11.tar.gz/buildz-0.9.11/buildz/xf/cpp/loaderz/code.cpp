
#include<cstring>
int unicode_to_utf8(int code_point, char* s) {
    if (code_point<0)return 0;
    int i=0;
    if (code_point <= 0x7F) { // 1-byte sequence
        s[i++]=(char)code_point;
    } else if (code_point <= 0x7FF) { // 2-byte
        s[i++]=(char)(0xC0 | ((code_point >> 6) & 0x1F));
        s[i++]=(char)(0x80 | (code_point & 0x3F));
    } else if (code_point <= 0xFFFF) { // 3-byte
        s[i++]=(char)(0xE0 | ((code_point >> 12) & 0x0F));
        s[i++]=(char)(0x80 | ((code_point >> 6) & 0x3F));
        s[i++]=(char)(0x80 | (code_point & 0x3F));
    } else if (code_point <= 0x10FFFF) { // 4-byte
        s[i++]=(char)(0xF0 | ((code_point >> 18) & 0x07));
        s[i++]=(char)(0x80 | ((code_point >> 12) & 0x3F));
        s[i++]=(char)(0x80 | ((code_point >> 6) & 0x3F));
        s[i++]=(char)(0x80 | (code_point & 0x3F));
    } else { // illegal
        //throw;
    }
    return i;
}
int s2hex(const char* s, int size){
    int rst = 0;
    char c;
    for(int i=0;i<size;++i){
        c = s[i];
        if (c>='0'&&c<='9'){
            c -='0';
        }else if (c>='a'&&c<='f'){
            c-='a'-10;
        }else if (c>='A' && c<='F'){
            c-='A'-10;
        }else{
            return -1;
        }
        rst = (rst<<4)|c;
    }
    return rst;
}
char barr[256];
bool mark_init_barr = false;
inline void init_barr();
void init_barr(){
    if (mark_init_barr)return;
    for(int i=0;i<256;++i)barr[i]=-1;
    // barr['b'] = '\b';
    // barr['f'] = '\f';
    // barr['r'] = '\r';
    // barr['t'] = '\t';
    barr['\\'] = '\\';
    barr['\''] = '\'';
    barr['"'] = '"';
    barr['a'] = '\a';
    barr['b'] = '\b';
    barr['e'] = '\e';
    barr['f'] = '\f';
    barr['n'] = '\n';
    barr['p'] = '\p';
    barr['r'] = '\r';
    barr['t'] = '\t';
    //barr['u'] = '\u';
    barr['v'] = '\v';
}
char* do_translate(const char* s){
    init_barr();
    int i=0;
    int j = 0;
    int sz = strlen(s);
    char* rst = new char[sz+1];
    while (i<sz){
        char c = s[i++];
        if (c!='\\'){
            rst[j++]=c;
            continue;
        }
        char x = s[i++];
        if (x=='u'){
            int vhex = s2hex(s+i,4);
            int usz = unicode_to_utf8(vhex, rst+j);
            j+=usz;
            if (usz==0){
                rst[j++]=c;
                rst[j++]=x;
                for(int k=0;k<4;k++){
                    rst[j++]=s[i++];
                }
            }
            i+=4;
        } else {
            char vx = x;
            if (x>0){
                vx = barr[x];
            }
            if (vx<0){
                rst[j++]=c;
                rst[j++]=x;
            } else {
                rst[j++]=vx;
            }
        }
    }
    rst[j]=0;
    return rst;
}
