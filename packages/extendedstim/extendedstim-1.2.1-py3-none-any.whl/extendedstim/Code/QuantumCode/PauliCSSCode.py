"""""
模块作用：实现Pauli CSS码的逻辑算符推导与若干标准实例（Steane、Surface），以及由线性码构造。
"""""
import numpy as np
from extendedstim.Code.QuantumCode.PauliCode import PauliCode
from extendedstim.Code.QuantumCode.QuantumCSSCode import QuantumCSSCode
from extendedstim.Physics.PauliOperator import PauliOperator
from extendedstim.tools.GaloisTools import orthogonalize, occupy, mip_distance_caculator


class PauliCSSCode(PauliCode, QuantumCSSCode):

    # %%  CHAPTER：===构造方法===
    def __init__(self, generators_x, generators_z, physical_number: int)->None:
        """""
        input.generators_x：X稳定子
        input.generators_z：Z稳定子
        input.physical_number：物理位数
        """""
        QuantumCSSCode.__init__(self, generators_x, generators_z, physical_number)

    # %%  CHAPTER：属性方法
    ##  SECTION：----求Pauli CSS code的距离（x方向）----
    @property
    def distance_x(self):
        return mip_distance_caculator(self.check_matrix_x, self.logical_operators_x)

    ##  SECTION：----求Pauli CSS code的距离（z方向）----
    @property
    def distance_z(self):
        return mip_distance_caculator(self.check_matrix_z, self.logical_operators_z)

    ##  SECTION：----求Pauli CSS code的逻辑算子（x方向）----
    @property
    def logical_operators_x(self):
        if self._logical_operators_x is not None:
            return self._logical_operators_x
        else:
            matrix = self.check_matrix_x
            codewords = matrix.null_space()
            independent_null_basis_list = []
            for vec in codewords:
                rank_before = np.linalg.matrix_rank(matrix)
                matrix = np.vstack([matrix, vec])
                if np.linalg.matrix_rank(matrix) == rank_before + 1:
                    independent_null_basis_list.append(vec)
            basis_list = orthogonalize(independent_null_basis_list)
            pauli_logical_operators_x = []
            pauli_logical_operators_z = []
            for i in range(len(basis_list)):
                occupy_temp = occupy(basis_list[i])
                temp = PauliOperator.HermitianOperatorFromOccupy(occupy_temp, [])
                pauli_logical_operators_x.append(temp)
                temp = PauliOperator.HermitianOperatorFromOccupy([], occupy_temp)
                pauli_logical_operators_z.append(temp)
            self._logical_operators_x = np.array(pauli_logical_operators_x, dtype=PauliOperator)
            self._logical_operators_z = np.array(pauli_logical_operators_z, dtype=PauliOperator)
            return self._logical_operators_x

    ##  SECTION：----求Pauli CSS code的逻辑算子（z方向）----
    @property
    def logical_operators_z(self):
        if self._logical_operators_z is not None:
            return self._logical_operators_z
        else:
            _=self.logical_operators_x
            return self._logical_operators_z

    ##  SECTION：----求Pauli CSS code的标准Steane码----
    @staticmethod
    def ColorCode(d: int) -> 'PauliCSSCode':
        """""
        input.d：奇数，表示三角形网格的边长（distance）
        output：PauliCSSCode
        """""

        if d <= 0 or d % 2 == 0:
            raise ValueError("d must be a positive odd integer")
        coords = []
        coord_map = {}
        idx = 0
        for x in range(d + 1):
            for y in range(d + 1):
                if x + y <= d:
                    coords.append((x, y))
                    coord_map[(x, y)] = idx
                    idx += 1
        num_qubits = len(coords)

        # 收集三角形面（向上和向下的小三角）
        faces = []
        for x in range(d):
            for y in range(d):
                if x + y <= d - 1:
                    a = coord_map[(x, y)]
                    b = coord_map[(x + 1, y)]
                    c = coord_map[(x, y + 1)]
                    faces.append([a, b, c])
        for x in range(d):
            for y in range(d):
                if x + y <= d - 2:
                    a = coord_map[(x + 1, y)]
                    b = coord_map[(x + 1, y + 1)]
                    c = coord_map[(x, y + 1)]
                    faces.append([a, b, c])
        generators_x = []
        generators_z = []
        for face in faces:
            # face 是包含若干顶点索引（这里为 3 个）
            generators_x.append(PauliOperator.HermitianOperatorFromOccupy(face, []))
            generators_z.append(PauliOperator.HermitianOperatorFromOccupy([], face))

        # 用 PauliCSSCode 构造结果
        return PauliCSSCode(generators_x, generators_z, num_qubits)

    ##  SECTION：----求Pauli CSS code的标准Surface码----
    @staticmethod
    def SurfaceCode(d: int) -> 'PauliCSSCode':
        """""
        input.d：奇数，表示网格边长（distance）
        output：PauliCSSCode 实例（平面 surface code）
        说明：物理比特放在 d x d 的格点上，按行主序编号 0..d*d-1。
        每个 2x2 方格产生一个 4 重子 X 和 4 重子 Z 稳定子（内部 plaquette）
        在边界上添加 2 重子边界稳定子（上/下为 X，左/右为 Z）
        """""

        ##  检查输入是否合法
        if d <= 0 or d % 2 == 0:
            raise ValueError("d must be a positive odd integer")

        ##  ----坐标与索引转换----
        def idx(r, c):
            return r * d + c

        num_qubits = d * d

        generators_x = []
        generators_z = []

        ##  ----内部 2x2 方格（plaquettes）----
        for r in range(d - 1):
            for c in range(d - 1):
                a = idx(r, c)
                b = idx(r, c + 1)
                c2 = idx(r + 1, c)
                d2 = idx(r + 1, c + 1)
                face = [a, b, c2, d2]
                # X 和 Z 稳定子均可由面产生（标准平面编码的 plaquette）
                generators_x.append(PauliOperator(face, [], 1))
                generators_z.append(PauliOperator([], face, 1))

        ##  ----边界稳定子（2 重子）----
        top_row = 0
        bottom_row = d - 1
        for c in range(d - 1):
            generators_x.append(PauliOperator([idx(top_row, c), idx(top_row, c + 1)], [], 1))
            generators_x.append(PauliOperator([idx(bottom_row, c), idx(bottom_row, c + 1)], [], 1))

        ##  ----边界稳定子（2 重子）----
        left_col = 0
        right_col = d - 1
        for r in range(d - 1):
            generators_z.append(PauliOperator([], [idx(r, left_col), idx(r + 1, left_col)], 1))
            generators_z.append(PauliOperator([], [idx(r, right_col), idx(r + 1, right_col)], 1))

        ##  ----构造并返回 PauliCSSCode 实例----
        return PauliCSSCode(generators_x, generators_z, num_qubits)

    ##  SECTION：----从LinearCode构造Pauli CSS code----
    @staticmethod
    def FromLinearCode(linear_code):
        """""
        input.linear_code：LinearCode 实例
        output：PauliCSSCode 实例
        """""
        generators_x=[]
        generators_z=[]
        for i in range(linear_code.number_checker):
            occupy_temp = occupy(linear_code.check_matrix[i])
            generators_x.append(PauliOperator.HermitianOperatorFromOccupy(occupy_temp, []))
            generators_z.append(PauliOperator.HermitianOperatorFromOccupy([], occupy_temp))
        physical_number=linear_code.number_bit
        result=PauliCSSCode(generators_x, generators_z, physical_number)
        return result
