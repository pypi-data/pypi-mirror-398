"""""
模块作用：定义量子码抽象基类，统一校验矩阵、逻辑位、距离、逻辑算符等接口。
"""""
import copy
from abc import ABC, abstractmethod
import numpy as np
from extendedstim.Physics.Operator import Operator
from extendedstim.tools.TypingTools import isinteger


class QuantumCode(ABC):

    #%%  CHAPTER：===构造方法===
    def __init__(self,generators:list|np.ndarray,physical_number:int):
        """""
        input.generators：稳定子/检验子算符列表
        input.physical_number：物理比特/费米子数目
        """""

        ##  检查输入合法性
        assert isinteger(physical_number)
        assert physical_number>0
        assert isinstance(generators, list) or isinstance(generators, np.ndarray)

        ##  赋值使用
        self.generators=[]
        for generator in generators:
            assert isinstance(generator, Operator)
            self.generators.append(generator)
        self.physical_number=physical_number
        self.checker_number=len(self.generators)

    #%%  CHAPTER：===属性方法===
    ##  SECTION：----求校验矩阵----
    @property
    def check_matrix(self):
        """""
        output：GF(2)矩阵，按占据向量堆叠得到 (m,2n)
        """""
        matrix=Operator.get_matrix(self.generators, self.physical_number)
        return matrix

    ##  SECTION：----求校验矩阵的秩----
    @property
    def rank(self):
        """""
        output：int，rank(check_matrix)
        """""
        return np.linalg.matrix_rank(self.check_matrix)

    ##  SECTION：----求logical number----
    @property
    def logical_number(self):
        """""
        output：int = physical_number - rank
        """""
        return self.physical_number-self.rank

    ##  SECTION：----求码距----
    @property
    @abstractmethod
    def distance(self):
        """""
        output：int，最小非平凡逻辑算符权重
        """""
        pass

    ##  SECTION：----求逻辑算符----
    @property
    @abstractmethod
    def logical_operators(self):
        """""
        output：算符数组/列表，成对或成组的独立逻辑算符
        """""
        pass

    #%%  CHAPTER：===对象方法===
    ##  SECTION：----修改索引----
    def index_map(self, index_map,physical_number):
        """""
        input.index_map：列表或数组，给出新索引映射
        output：无（原地修改生成元的索引）
        """""
        for generator in self.generators:
            generator.index_map(index_map)
        self.physical_number=physical_number

    ##  SECTION：----复制代码----
    def copy(self):
        """""
        output：深拷贝新实例
        """""
        return copy.deepcopy(self)