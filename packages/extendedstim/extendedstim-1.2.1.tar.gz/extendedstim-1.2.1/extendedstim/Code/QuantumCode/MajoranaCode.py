"""""
模块作用：实现Majorana稳定子码的基本属性：距离、逻辑算符、奇偶性与基于校验矩阵的构造。
"""""
import galois
import numpy as np
from extendedstim.Code.QuantumCode.QuantumCode import QuantumCode
from extendedstim.Physics.MajoranaOperator import MajoranaOperator
from extendedstim.tools.GaloisTools import orthogonalize, solve, mip_distance_caculator, minus


class MajoranaCode(QuantumCode):

    #%%  CHAPTER：===构造方法===
    def __init__(self,generators,physical_number):
        """""
        input.generators：MajoranaOperator 列表
        input.physical_number：费米子位数
        output：无
        """""
        super().__init__(generators, physical_number)

    #%%  CHAPTER：===属性方法===
    ##  SECTION：----求码距----
    @property
    def distance(self):
        """""
        output：int，通过mip工具计算最小权重
        """""
        return mip_distance_caculator(self.check_matrix,minus(self.check_matrix.null_space(),self.check_matrix))

    ##  SECTION：----求逻辑算符----
    @property
    def logical_operators(self):
        """""
        output：np.array[MajoranaOperator] 独立逻辑算符集合
        """""
        matrix = self.check_matrix
        codewords = matrix.null_space()
        independent_null_basis_list = []
        for vec in codewords:
            rank_before = np.linalg.matrix_rank(matrix)
            matrix = np.vstack([matrix, vec])
            if np.linalg.matrix_rank(matrix) == rank_before + 1:
                independent_null_basis_list.append(vec)
        basis_list = orthogonalize(independent_null_basis_list)
        majorana_logical_operators = []
        for i in range(len(basis_list)):
            temp = MajoranaOperator.HermitianOperatorFromVector(basis_list[i])
            majorana_logical_operators.append(temp)
        majorana_logical_operators = np.array(majorana_logical_operators, dtype=MajoranaOperator)
        return majorana_logical_operators

    ##  SECTION：----判断是否为偶数码----
    @property
    def even_or_odd(self):
        """""
        output："even" 或 "odd"，判断是否存在全1解 H x = 1
        """""
        H=self.check_matrix
        ones=galois.GF2(np.ones(H.shape[1],dtype=int))
        if solve(H,ones) is None:
            return "odd"
        else:
            return "even"

    #%%  CHAPTER：===静态方法===
    ##  SECTION：----基于校验矩阵构造code----
    @staticmethod
    def FromCheckMatrix(check_matrix):
        """""
        input.check_matrix：GF(2) (m,2n)
        output：MajoranaCode 实例
        """""
        generators = np.empty(check_matrix.shape[0],dtype=MajoranaOperator)
        for temp in range(check_matrix.shape[0]):
            occupy_x=np.where(check_matrix[temp,0::2]==1)[0]
            occupy_z=np.where(check_matrix[temp,1::2]==1)[0]
            generators[temp]=MajoranaOperator.HermitianOperatorFromOccupy(occupy_x,occupy_z)
        physical_number=check_matrix.shape[1]
        return MajoranaCode(generators,physical_number)
