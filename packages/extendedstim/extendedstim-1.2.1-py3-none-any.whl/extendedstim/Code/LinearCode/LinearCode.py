"""""
模块作用：定义经典线性码基础结构与常用属性 (秩、逻辑位、码字、对偶等)。
"""""
from functools import cached_property
import galois
import numpy as np
from extendedstim.tools.GaloisTools import mip_distance_caculator


class LinearCode:
    __slots__=['check_matrix','number_bit','number_checker']
    GF=galois.GF(2)

    #%%  CHAPTER：构造方法
    def __init__(self,check_matrix:np.ndarray|galois.GF(2))->None:
        """""
        input.check_matrix：01或GF(2)校验矩阵 (m,n)
        """""

        ##  SECTION：----数据预处理----
        assert isinstance(check_matrix, np.ndarray) or isinstance(check_matrix, list), "check_matrix必须是01数组"

        ##  SECTION：----根据校验矩阵构造对象----
        self.check_matrix = self.GF(np.array(check_matrix,dtype=int))
        self.number_bit=len(check_matrix[0])
        self.number_checker=len(check_matrix)

    #%%  CHAPTER：===属性方法===
    ##  SECTION：----计算秩----
    @property
    def rank(self)->int:
        """""
        output：int，校验矩阵行空间秩
        """""
        return np.linalg.matrix_rank(self.check_matrix)

    ##  SECTION：----计算距离----
    @property
    def distance(self)->int:
        """""
        output：int，占位实现（返回1）
        """""
        return mip_distance_caculator(self.check_matrix,self.codewords)

    ##  SECTION：----计算逻辑位数目----
    @property
    def logical_number(self)->int:
        """""
        output：n - rank
        """""
        return self.number_bit-self.rank

    ##  SECTION：----计算码字---
    @property
    def codewords(self)->galois.GF(2):
        """""
        output：GF(2)矩阵，零空间基（所有码字的生成集合）
        """""
        return self.check_matrix.null_space()

    ##  SECTION：----计算对偶码----
    @property
    def dual(self)->'LinearCode':
        """""
        output：LinearCode，对偶码（当前校验矩阵零空间为新校验矩阵）
        """""
        return LinearCode(self.check_matrix.null_space())

    ##  SECTION：----判断是否dual-containing----
    @cached_property
    def is_dual_containing(self)->bool:
        """""
        output：bool，H H^T = 0 判定自对偶包含结构
        """""
        return np.all(self.check_matrix @ self.check_matrix.T == 0)
