{
text= 
r"""
文件查找，运行:
    python -m buildz search 文件夹路径
    可选参数:
        -f 文件路径正则
        --file=文件路径正则
        -c 文件内容正则
        --content=文件内容正则
        -o 输出文件
        --output=输出文件
        -d 最深路径
        --depth=最深路径
        -s/+s 展示内容查询
        -p 展示查询内容前多少字
        --prev=展示查询内容前多少字
        -a 展示查询内容前多少字
        --aft=展示查询内容后多少字
        

比如:
    python -m buildz search {default} -f ".*\.js" -c "ioc" -d 3

"""
text.en= 
r"""
file search, run by:
    python -m buildz search dirpath
    options:
        -f "regex on filepath"
        --file="regex on filepath"
        -c "regex on file content"
        --content="regex on file content"
        -o "output filepath"
        --output="output filepath"
        -d "max-depth"
        --depth="max-depth"

exp:
    python -m buildz search {default} -f ".*\.js" -c "ioc" -d 3

"""
}