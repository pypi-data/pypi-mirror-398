"""""
模块作用：定义CSS量子码抽象基类，区分X/Z两类生成元并提供相应的秩、校验矩阵与距离抽象接口。
"""""
from abc import abstractmethod
import numpy as np
from extendedstim.Code.QuantumCode.QuantumCode import QuantumCode
from extendedstim.Physics.Operator import Operator
from extendedstim.tools.TypingTools import islist, isinteger


class QuantumCSSCode(QuantumCode):

    #%%  CHAPTER：===构造方法===
    def __init__(self, generators_x, generators_z, physical_number):
        """""
        input.generators_x：X类稳定子
        input.generators_z：Z类稳定子
        input.physical_number：物理位数
        """""

        ##  检查输入是否合法
        assert islist(generators_x) and islist(generators_z)
        assert isinteger(physical_number)
        assert physical_number>0

        ##  赋值
        self.generators_x=[]
        self.generators_z=[]
        for generator in generators_x:
            assert isinstance(generator,Operator)
            self.generators_x.append(generator)
        for generator in generators_z:
            assert isinstance(generator,Operator)
            self.generators_z.append(generator)
        self.checker_number_x=len(generators_x)
        self.checker_number_z = len(generators_z)
        self._logical_operators_x=None
        self._logical_operators_z=None
        super().__init__(generators_x+generators_z, physical_number)

    #%%  CHAPTER：===属性方法===
    ##  SECTION：----求逻辑算符（X方向）----
    @property
    @abstractmethod
    def logical_operators_x(self):
        """""
        output：X类逻辑算符数组
        """""
        pass

    ##  SECTION：----求逻辑算符（Z方向）----
    @property
    @abstractmethod
    def logical_operators_z(self):
        """""
        output：Z类逻辑算符数组
        """""
        pass

    ##  SECTION：----求校验矩阵的秩（X方向）----
    @property
    def rank_x(self):
        """""
        output：int，rank(Hx)
        """""
        return np.linalg.matrix_rank(self.check_matrix_x)

    ##  SECTION：----求校验矩阵的秩（Z方向）----
    @property
    def rank_z(self):
        """""
        output：int，rank(Hz)
        """""
        return np.linalg.matrix_rank(self.check_matrix_z)

    ##  SECTION：----求校验矩阵（X方向）----
    @property
    def check_matrix_x(self):
        """""
        output：GF(2)矩阵，生成元X的占据向量的偶下标子向量
        """""
        matrix=Operator.get_matrix(self.generators_x, self.physical_number)
        matrix=matrix[:,0::2]
        return matrix

    ##  SECTION：----求校验矩阵（Z方向）----
    @property
    def check_matrix_z(self):
        """""
        output：GF(2)矩阵，生成元Z的占据向量的奇下标子向量
        """""
        matrix=Operator.get_matrix(self.generators_z, self.physical_number)
        matrix = matrix[:, 1::2]
        return matrix

    ##  SECTION：----求码距（X方向）----
    @property
    @abstractmethod
    def distance_x(self):
        """""
        output：int，X向最小非平凡逻辑权重
        """""
        pass

    ##  SECTION：----求码距（Z方向）----
    @property
    @abstractmethod
    def distance_z(self):
        pass
