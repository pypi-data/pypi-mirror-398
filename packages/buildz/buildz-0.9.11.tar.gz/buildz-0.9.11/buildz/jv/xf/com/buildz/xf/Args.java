package com.buildz.xf;
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;

public class Args{
    public String toString(){
        return "<args list="+list.toString()+", map="+map.toString()+">";
    }
    public List list = new ArrayList();
    public Map map = new HashMap();
    public Args(){}
    public boolean add(Object obj){
        return list.add(obj);
    }
    public Object put(Object key, Object val){
        return map.put(key, val);
    }
    public int size(){
        return list.size()+map.size();
    }
}