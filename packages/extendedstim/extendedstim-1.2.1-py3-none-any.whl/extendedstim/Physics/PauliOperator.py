"""""
模块作用：实现Pauli算符在占据表示下的代数运算、厄米性与向量化。
"""""
import galois
import numpy as np
from extendedstim.Physics.Operator import Operator
from extendedstim.tools.TypingTools import islist


class PauliOperator(Operator):
    __slots__ = ['occupy_x', 'occupy_z', 'coff']

    #%%  CHAPTER：===构造方法===
    def __init__(self, occupy_x, occupy_z, coff):
        """""
        input.occupy_x：X支撑索引
        input.occupy_z：Z支撑索引
        input.coff：相位系数 (±1, ±i)
        """""
        super().__init__(occupy_x, occupy_z, coff)

    #%%  CHAPTER：===重载运算符===
    ##  SECTION：----定义算符的乘积----
    def __matmul__(self, other:'PauliOperator')->'PauliOperator':

        ##  ----数据预处理----
        assert isinstance(other, PauliOperator)

        ##  ----构造乘积----
        ##  计算占有
        occupy_x = np.setxor1d(self.occupy_x, other.occupy_x, assume_unique=False)
        occupy_z = np.setxor1d(self.occupy_z, other.occupy_z, assume_unique=False)
        exchange_times = np.sum([np.count_nonzero(self.occupy_z == temp) for temp in other.occupy_x])

        ##  计算系数
        if exchange_times % 2 == 1:
            factor = -1
        else:
            factor = 1

        ##  ----返回结果----
        return PauliOperator(occupy_x, occupy_z, self.coff * other.coff * factor)

    ##  SECTION：----定义右矩阵乘法----
    def __rmatmul__(self, other:'PauliOperator')->'PauliOperator':
        assert isinstance(other, PauliOperator)
        return other.__matmul__(self)

    ##  SECTION：----定义左标量乘法----
    def __mul__(self, other:complex|float|int)->'PauliOperator':
        assert other == 1 or other == -1 or other == 1j or other == -1j
        return PauliOperator(self.occupy_x, self.occupy_z, self.coff * other)

    ##  SECTION：----定义右标量乘法----
    def __rmul__(self, other:complex|float|int)->'PauliOperator':
        return self.__mul__(other)

    ##  SECTION：----定义字符串表示----
    def __str__(self)->str:
        return "PauliOperator(occupy_x={},occupy_z={},coff={})".format(self.occupy_x, self.occupy_z, self.coff)

    ##  SECTION：----定义相等判断----
    def __eq__(self, other:'PauliOperator')->bool:
        assert isinstance(other, PauliOperator)
        return np.array_equal(self.occupy_x, other.occupy_x) and np.array_equal(self.occupy_z, other.occupy_z) and self.coff == other.coff

    ##  SECTION：----定义取负----
    def __neg__(self)->'PauliOperator':
        return PauliOperator(self.occupy_x, self.occupy_z, -self.coff)

    #%%  CHAPTER：===属性方法===
    ##  SECTION：----定义算符是否是厄米算符----
    @property
    def is_hermitian(self)->bool:
        """""
        检查Pauli算符是否是厄米算符
        output：bool
        """""
        ##  ----计算厄米性质----
        if len(np.intersect1d(self.occupy_x, self.occupy_z, assume_unique=False)) % 2 == 0:
            if not (self.coff == 1 or self.coff == -1):
                return False
        else:
            if not (self.coff == 1j or self.coff == -1j):
                return False

        ##  ----返回结果----
        return True

    ##  SECTION：----定义算符的对偶算符----
    @property
    def dual(self)->'PauliOperator':
        """""
        计算Pauli算符的对偶算符
        output：PauliOperator
        """""
        return PauliOperator(self.occupy_z.copy(), self.occupy_x.copy(), self.coff)

    #%%  CHAPTER：===对象方法===
    ##  SECTION：----复制方法----
    def copy(self)->'PauliOperator':
        """""
        复制Pauli算符
        output：PauliOperator
        """""
        return PauliOperator(self.occupy_x.copy(), self.occupy_z.copy(), self.coff)

    #%%  CHAPTER：===静态方法===
    ##  SECTION：----定义一个厄米算符，从占据处表示----
    @staticmethod
    def HermitianOperatorFromOccupy(occupy_x:list[int]|np.ndarray,occupy_z:list[int]|np.ndarray)->'PauliOperator':
        """""
        将一个占据向量表示的Pauli算符转换为PauliOperator对象
        input.occupy_x：X支撑索引
        input.occupy_z：Z支撑索引
        output：PauliOperator
        """""

        ##  ----数据预处理----
        assert islist(occupy_x)
        assert islist(occupy_z)

        ##  ----构造厄米算符，尤其是计算系数----
        weight=len(np.intersect1d(occupy_x,occupy_z, assume_unique=False))
        if weight % 2 == 0:
            coff=1
        else:
            coff=1j

        ##  ----返回结果----
        return PauliOperator(occupy_x,occupy_z,coff)

    ##  SECTION：----定义一个厄米算符，从向量表示----
    @staticmethod
    def HermitianOperatorFromVector(vector:list[int]|np.ndarray|galois.GF(2))->'PauliOperator':
        """""
        将一个向量表示的Pauli算符转换为PauliOperator对象
        input.vector：向量表示，偶数索引为X轴，奇数索引为Z轴
        output：PauliOperator
        """""

        ##  ----数据预处理----
        assert islist(vector) or isinstance(vector, galois.GF(2))

        ##  ----构造厄米算符，尤其是计算系数----
        pauli_x = np.where(vector[0::2] == 1)[0]
        pauli_z = np.where(vector[1::2] == 1)[0]
        return PauliOperator.HermitianOperatorFromOccupy(pauli_x, pauli_z)

    ##  SECTION：----判断两个厄米算符是否对易----
    @staticmethod
    def commute(A:'PauliOperator',B:'PauliOperator')->bool:
        """""
        判断两个Pauli算符是否对易
        input.A：第一个Pauli算符
        input.B：第二个Pauli算符
        output：bool
        """""

        ##  ----数据预处理----
        assert isinstance(A, PauliOperator) and isinstance(B, PauliOperator)

        ##  ----判断是否对易----
        same_time=np.sum([np.count_nonzero(A.occupy_z==temp) for temp in B.occupy_x])
        same_time+=np.sum([np.count_nonzero(A.occupy_x==temp) for temp in B.occupy_z])

        ##  ----返回结果----
        return np.mod(same_time, 2) == 0
