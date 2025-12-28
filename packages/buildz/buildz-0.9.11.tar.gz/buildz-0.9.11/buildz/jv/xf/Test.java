
import com.buildz.xf.Loader;
public class Test {
    public static void main(String[] args) throws Exception{
        Loader jni = new Loader();
        Object rst;
        rst = jni.loads("a,b,c,{},[1,2,3,(4,5,6),{7=8,9=0},'asdf\\n']");
        System.out.println("rst:"+rst);
        rst = jni.loadx("(a,b,c=0) x y");
        System.out.println("rst:"+rst);
        rst = jni.loadx("(a,b,c=0) x y", false);
        System.out.println("rst:"+rst);
    }
}