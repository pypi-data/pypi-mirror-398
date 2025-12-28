"""""
模块作用：提供常用的类型判断工具函数。
"""""
import numpy as np


#%%  CHAPTER：===判断是否整数或整型===
def isinteger(num):
    """""
    input.num：任意对象
    output：bool，True表示是整数类型（含内置int/float和numpy整型）
    influence：用于对参数进行整数性检查
    """""
    return isinstance(num, (int, float,np.int8,np.int16,np.int32, np.int64))

#%%  CHAPTER：===判断是否序列(list/tuple/ndarray/range)===
def islist(num):
    """""
    input.num：任意对象
    output：bool，True表示是列表/元组/ndarray/range之一
    influence：用于区分单值与序列输入
    """""
    return isinstance(num, (list, tuple, np.ndarray,range))

#%%  CHAPTER：===判断是否浮点数===
def isfloat(num):
    """""
    input.num：任意对象
    output：bool，True表示是float或numpy浮点类型
    influence：用于浮点参数校验
    """""
    return isinstance(num, (float, np.float32, np.float64,np.float128,np.float256))


#%%  CHAPTER：===判断是否实数（整数或浮点）===
def isreal(num):
    """""
    input.num：任意对象
    output：bool，True表示属于实数范围（整数或浮点）
    influence：数值计算前的实数性检查
    """""
    return isinteger(num) or isfloat(num)

#%%  CHAPTER：===判断是否复数（含整数和浮点）===
def iscomplex(num):
    """""
    input.num：任意对象
    output：bool，True表示是复数或其numpy对应类型，或是整数/浮点
    influence：用于复数相关算符或系数的输入检查
    """""
    return isinteger(num) or isfloat(num) or isinstance(num, (complex, np.complex64, np.complex128, np.complex256, np.complex512))

#%%  CHAPTER：===判断可迭代对象内部的元素是否为某一类型===
def iter_isinstance(num,check_type):
    """""
    input.num：可迭代对象（如列表、元组、ndarray等）
    input.check_type：bool，是否检查元素类型（默认True）
    output：bool，True表示所有元素均为整数或整型浮点
    """""
    if check_type==isinteger or check_type==isfloat or check_type==iscomplex or check_type==isreal:
        return all(check_type(i) for i in num)
    else:
        return all(isinstance(i,check_type) for i in num)
