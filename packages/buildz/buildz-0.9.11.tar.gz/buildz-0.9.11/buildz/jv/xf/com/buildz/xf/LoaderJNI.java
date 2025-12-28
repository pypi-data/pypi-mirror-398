package com.buildz.xf;
import java.util.List;
import java.util.Map;
public class LoaderJNI {
    // 声明native方法
    public native Object jloads(String s);
    public native Object jloadx(String s, boolean spc);
    // 加载动态链接库
    static {
        System.loadLibrary("./jxf");
    }

}
