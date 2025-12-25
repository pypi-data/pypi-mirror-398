#!/usr/bin/env python3

'''
@Author: xxlin
@LastEditors: xxlin
@Date: 2019-04-10 13:27:58
@LastEditTime: 2019-04-10 17:46:40
'''

from typing import Any
from ..core.datatype import AttribDict

# dirmap paths
paths: AttribDict[str, str] = AttribDict()

# object to store original command line options
cmdLineOptions: AttribDict[str, Any] = AttribDict()

# object to share within function and classes command
# line options and settings
conf: AttribDict[str, Any] = AttribDict()

# object to control engine 
th: AttribDict[str, Any] = AttribDict()

#创建payloads字典对象存储payloads
payloads: AttribDict[str, Any] = AttribDict()
#URL相似度检查使用的集合
payloads.similar_urls_set = set()

#创建tasks字典对象存储tasks
tasks: AttribDict[str, list[str]] = AttribDict()

#创建进度条对象存储进度
bar: AttribDict[str, Any] = AttribDict()