package com.buildz.xf;
import java.util.List;
import java.util.Map;
public class Loader {
    public static LoaderJNI jni = new LoaderJNI();
    // 声明native方法
    public Object loads(String s)throws Exception{
        Object obj = jni.jloads(s);
        if (obj instanceof Exception)throw (Exception)obj;
        if ((obj instanceof List)&&((List)obj).size()==0){
            return "";
        }
        if ((obj instanceof List)&&((List)obj).size()==1){
            obj = ((List)obj).get(0);
        }
        return obj;
    }
    public Object loadx(String s)throws Exception{
        return loadx(s, true);
    }
    public Object loadx(String s, boolean spc)throws Exception{
        Object obj = jni.jloadx(s,spc);
        if (obj instanceof Exception)throw (Exception)obj;
        if ((obj instanceof Args)&&((Args)obj).size()==0){
            return "";
        }
        if ((obj instanceof Args)&&((Args)obj).size()==1&&((Args)obj).list.size()==1){
            obj = ((Args)obj).list.get(0);
        }
        return obj;
    }

}
