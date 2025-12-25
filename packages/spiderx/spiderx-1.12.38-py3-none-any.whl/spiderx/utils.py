# encoding: utf-8
from wmi import WMI
from hashlib import md5
from uuid import uuid1
import re
def 获取_机器码(加密字符串=None,类型=1):
    c=WMI()
    info={}
    主板=c.Win32_BaseBoard()[0]
    if 类型==1:    #绑定主板
        info['主板型号'] = 主板.Product.strip()
        info['主板UUID'] = 主板.qualifiers['UUID'].strip()
    elif 类型==2:  #绑定主板+网卡
        info['主板型号'] = 主板.Product.strip()
        info['主板UUID'] = 主板.qualifiers['UUID'].strip()
        info['网卡地址']=str(uuid1()).split('-')[-1].strip()
    if 加密字符串:
        info['加密字符串'] = str(加密字符串)
    return md5(str(info).encode("utf-8")).hexdigest()
def 获取_电脑信息():
    c=WMI()
    dic = {'cpu': c.Win32_Processor(),
           '硬盘': c.Win32_DiskDrive(),
           '主板': c.Win32_BaseBoard(),
           'bios': c.Win32_BIOS(),
           '电池': c.Win32_Battery(),
           '网卡': c.Win32_NetworkAdapter()
           }
    dic_new = {}
    for k, v in dic.items():
        dic_new[k] = []
        for x in v:
            dic_new[k].append(dict(re.findall('(\w+) = (.*?);', str(x))))
    return dic_new


