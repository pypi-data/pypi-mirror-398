{
text= 
r"""在json格式基础上加了些其他东西，让配置写起来更简单：
    1，字符串可以不用引号括起来，程序判断字段不是整数，小数，布尔型等类型后，当字段是字符串
    2，可以写注释，//,#,/**/, ###...###，其中/*note*/和###note###是多行注释
    3，分号;和逗号,和换行\n等价，等于号=和冒号:等价，括号()和中括号[]等价
    4，加了python的字符串书写方式："...", '...', r"..."，r'...', r'''...'''
    5，输出格式化
    6，可配置化(但没太多注释)

运行以下命令会打印文件格式化后的样式:
    python -m buildz xf 文件名

比如:
    python -m buildz xf {default}

"""
text.en= 
r"""add something base on json format, make it eaisier to write profile file:
    1, string can write without ' or ", codes will regard item as string if not in int, float, boolean, list, map, ... format
    2, can write note on file, support note type: //note1 #note2 /*note3*/ ###note4###, /*note*/ and ###note### support multi-line notes
    3, ';' and '\n' used equal to ',' in json, '=' used equal to ':', '()' used equals to '[]'
    4, string can write like python format: "string1", 'string2', r"string3", r'string4', '''multi-line string1''', r'''multi-line string2'''
    5, codes to make format output string on data
    6, configurable(but has few notes on code)

output format string on input file:
    python -m buildz xf filepath

exp:
    python -m buildz xf {default}

"""
}