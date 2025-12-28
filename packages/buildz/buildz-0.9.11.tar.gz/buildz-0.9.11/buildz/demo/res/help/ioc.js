{
    text= 
r"""
xf格式的ioc控制反转配置文件的文件读取和生成对象
预设的数据项(item_conf)格式:
    {items}
查看预设数据类型格式:
    python -m buildz ioc -h 类型 [--file=预设数据处理配置文件] [-f 预设数据处理配置文件]
查看配置文件书写格式:
    python -m buildz ioc +h,doc
比如:
    python -m buildz ioc -h val

测试执行ioc:
    python -m buildz ioc 文件夹路径 [-s 配置文件后缀，默认js] [-i 数据id，默认main]
例:
    python -m buildz ioc /root/test -i obj.test
""";
text.en= 
r"""
xf format ioc profile file's reading and object build
preset data item(item_conf)format:

{items}

to see preset data item format:
python -m buildz ioc -h type [--file="filepath contain deal func to deal item_conf"] [-f "same to --file"]

to see profile file write format:
python -m buildz ioc +h,doc
exp:
python -m buildz ioc -h val

test run ioc:
python -m buildz ioc dirpath [-s profile file suffix, default js] [-i "data id，default 'main'"]
exp:
python -m buildz ioc /root/test -i obj.test
""";
}