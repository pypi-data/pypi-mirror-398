"""""
模块作用：实现Majorana CSS码的距离估计、逻辑算符推导与若干构造器（由线性码/校验矩阵/标准例子）。
"""""
import numpy as np
from extendedstim.Code.LinearCode.LinearCode import LinearCode
from extendedstim.Code.QuantumCode.MajoranaCode import MajoranaCode
from extendedstim.Code.QuantumCode.QuantumCSSCode import QuantumCSSCode
from extendedstim.Physics.MajoranaOperator import MajoranaOperator
from extendedstim.tools.GaloisTools import orthogonalize, occupy, mip_distance_caculator, minus


class MajoranaCSSCode(MajoranaCode, QuantumCSSCode):

    # %%  CHAPTER：===构造方法===
    def __init__(self, generators_x, generators_z, physical_number):
        """""
        input.generators_x：X类Majorana稳定子
        input.generators_z：Z类Majorana稳定子
        input.physical_number：费米子位数
        """""
        QuantumCSSCode.__init__(self, generators_x, generators_z, physical_number)

    # %%  CHAPTER：===属性方法===
    ##  SECTION：----求码距----
    @property
    def distance(self):
        """""
        output：int，随机估计（或MIP）
        """""
        return mip_distance_caculator(self.check_matrix,minus(self.check_matrix.null_space(),self.check_matrix))

    ##  SECTION：----求码距（x方向）----
    @property
    def distance_x(self):
        """""
        output：int，基于MIP的精确/上界估计
        """""
        return mip_distance_caculator(self.check_matrix_x,minus(self.check_matrix_x.null_space(),self.check_matrix_x))

    ##  SECTION：----求码距（z方向）----
    @property
    def distance_z(self):
        """""
        output：int，基于MIP的精确/上界估计
        """""
        return mip_distance_caculator(self.check_matrix_z,minus(self.check_matrix_z.null_space(),self.check_matrix_z))

    ##  SECTION：----求逻辑算符----
    @property
    def logical_operators(self)->'list[MajoranaOperator]':
        """""
        output：np.array[MajoranaOperator]，X向和Z向配对拼接
        """""
        _=self._logical_operators_x
        return self._logical_operators_x+self._logical_operators_z

    ##  SECTION：----求逻辑算符（x方向）----
    @property
    def logical_operators_x(self)->'list[MajoranaOperator]':
        """""
        output：np.array[MajoranaOperator]，X向逻辑算符
        """""
        matrix = self.check_matrix_x
        codewords = matrix.null_space()
        independent_null_basis_list = []
        for vec in codewords:
            rank_before = np.linalg.matrix_rank(matrix)
            matrix = np.vstack([matrix, vec])
            if np.linalg.matrix_rank(matrix) == rank_before + 1:
                independent_null_basis_list.append(vec)
        basis_list = orthogonalize(independent_null_basis_list)
        majorana_logical_operators_x = []
        majorana_logical_operators_z = []
        for i in range(len(basis_list)):
            occupy_temp=occupy(basis_list[i])
            temp = MajoranaOperator.HermitianOperatorFromOccupy(occupy_temp,[])
            majorana_logical_operators_x.append(temp)
            temp = MajoranaOperator.HermitianOperatorFromOccupy([],occupy_temp)
            majorana_logical_operators_z.append(temp)
        self._logical_operators_x = majorana_logical_operators_x
        self._logical_operators_z = majorana_logical_operators_z
        return self._logical_operators_x

    ##  SECTION：----求逻辑算符（z方向）----
    @property
    def logical_operators_z(self)->'list[MajoranaOperator]':
        """""
        output：np.array[MajoranaOperator]，Z向逻辑算符
        """""
        _=self._logical_operators_x
        return self._logical_operators_z

    #%%  CHAPTER：===静态方法===
    ##  SECTION：----从校验矩阵构造Majorana CSS code----
    @staticmethod
    def FromCheckMatrix(check_matrix):
        """""
        input.check_matrix：GF(2) (m,2n)
        output：MajoranaCSSCode
        """""
        generators_x = []
        generators_z = []
        for i in range(len(check_matrix)):
            generators_x.append(MajoranaOperator.HermitianOperatorFromVector(check_matrix[i]))
            generators_z.append(MajoranaOperator.HermitianOperatorFromVector(check_matrix[i]))
        physical_number=check_matrix.shape[1]
        return MajoranaCSSCode(generators_x, generators_z, physical_number)

    ##  SECTION：----用一个线性码生成Majorana CSS code----
    @staticmethod
    def FromLinearCode(linear_code):
        """""
        input.linear_code：LinearCode
        output：MajoranaCSSCode
        """""
        assert isinstance(linear_code,LinearCode)
        generators_x = []
        generators_z = []
        check_matrix=linear_code.check_matrix
        for i in range(len(check_matrix)):
            occupy_temp=occupy(check_matrix[i])
            generators_x.append(MajoranaOperator.HermitianOperatorFromOccupy(occupy_temp,[]))
            generators_z.append(MajoranaOperator.HermitianOperatorFromOccupy([],occupy_temp))
        physical_number=check_matrix.shape[1]
        return MajoranaCSSCode(generators_x, generators_z, physical_number)
