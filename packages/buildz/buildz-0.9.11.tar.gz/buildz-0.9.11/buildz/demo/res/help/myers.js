{
text= 
r"""
文件比较（模仿git diff）:
    python -m buildz myers 操作 文件路径1 文件路径2 [step文件] [+e/t/s/ns]
    操作:
        diff: 计算文件1到文件2需要的步骤，保存到step文件
        update: 文件1根据step文件修改，保存到文件2
        count: 计算文件1到文件2的差异
    可选:
        +e: step文件字节保存（默认）
        +t: step文件字符串保存
        +s: 字符串做切分（默认）
        +ns: 字符串不做切分（更精准，但可能耗时很高）

比如:
    python -m buildz myers diff test.py curr_test.py step.dt

"""
text.en= 
r"""
file compare:
    python -m buildz myers opt file1 file2 [step_file] [+e/t/s/ns]
    opt:
        diff: calucate steps from file1 to fiel2, save into step_file
        update: update file1 by step_file, save into file2
        count: count differenct from file1 to file2
    options:
        +e: step_file save in bytes(default)
        +t: step_file save by string
        +s: cut string into pices(default)
        +ns: not cut string（more precise but maybe more step_file size）

exp:
    python -m buildz myers diff test.py curr_test.py step.dt

"""
}