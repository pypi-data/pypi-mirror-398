#coding=utf-8

__version__="0.7.2"

# 小号多
__author__ = "Zzz, emails: 1174534295@qq.com, 1309458652@qq.com"
__doc__ = '''
使用此代码库发现bug或者有需求需要开发都可联系(QQ或邮箱联系，QQ就是邮箱号)
buildz.xf: 简化的json
buildz.xz: 简化对dict和list的读写
buildz.ioc, buildz.iocz: ioc注入
buildz.netz: 网络相关，包括ssl证书生成，正反向代理，端口映射，抓包
buildz.db: SQL脚本处理工具，基于其他SQL处理库做了使用简化
buildz.html: html文本处理
buildz.gpuz: 机器学习用内存做显存的模型缓存，目前只写了基于pytorch的工具，测试卷积和注意力的效果还行
buildz.fz: 文件处理
buildz.auto: 自动化测试
buildz.logz: 简单的日志工具
buildz.pyz: 简化python系统相关调用
buildz.base: 简化python类代码编写
buildz.pathz: 简化文件路径相关的代码编写 
'''

from .argx import fetch as args
from .base import Base, WBase,Args