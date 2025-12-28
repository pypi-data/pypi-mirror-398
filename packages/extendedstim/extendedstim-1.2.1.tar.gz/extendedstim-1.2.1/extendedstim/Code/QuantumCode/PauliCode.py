"""""
模块作用：实现Pauli稳定子码的基础属性与从校验矩阵构造。
"""""
import galois
import numpy as np
from extendedstim.Code.QuantumCode.QuantumCode import QuantumCode
from extendedstim.Physics.MajoranaOperator import MajoranaOperator
from extendedstim.Physics.PauliOperator import PauliOperator
from extendedstim.tools.GaloisTools import mip_distance_caculator,minus


class PauliCode(QuantumCode):

    # %%  CHAPTER：===构造方法===
    def __init__(self, generators, physical_number):
        """""
        input.generators：Pauli/等价表示生成元
        input.physical_number：qubits数
        """""
        super().__init__(generators, physical_number)

    # %%  CHAPTER：===属性方法===
    ##  SECTION：----求码距----
    @property
    def distance(self):
        return mip_distance_caculator(self.check_matrix, minus(self.check_matrix.null_space(),self.check_matrix))

    ##  TODO：求Pauli code的逻辑算子
    @property
    def logical_operators(self):
        """""
            input.H：m x 2n 的稳定子矩阵（可为 galois.GF2 或 numpy 0/1 矩阵），行张成稳定子群
            output：
                logical_basis：k x 2n 的 numpy 0/1 矩阵，表示逻辑算子基（每行为一个 (x|z) 向量）
                pairs：列表[(p0,q0),(p1,q1),...]，每个元素为两个索引，指向 logical_basis 中互为一对（symplectic = 1）
            说明：返回的基是中央化子模稳定子后的独立代表，且用辛 Gram‑Schmidt 尝试配对成 X/Z 对
            """""

        # %%  USER：----生成辛形式矩阵 J (2n x 2n)----
        def symplectic_form(n):
            """""
            input.n：物理 qubit 数
            output：2n x 2n 的 numpy 0/1 矩阵，表示辛形式 J：
                    J = [[0, I],
                         [I, 0]]
            """""
            I=np.eye(n, dtype=int)
            Z=np.zeros((n, n), dtype=int)
            top=np.hstack((Z, I))
            bot=np.hstack((I, Z))
            return np.vstack((top, bot))


        # %%  USER：----辛内积（两个 (x|z) 向量）----
        def symplectic_product(a, b):
            """""
            input.a,b：长度 2n 的 0/1 向量（numpy 1D）
            output：0 或 1（GF(2) 内积 x·z' + z·x'）
            """""
            n2=a.shape[0]
            n=n2//2
            x_a=a[:n]
            z_a=a[n:]
            x_b=b[:n]
            z_b=b[n:]
            return int((x_a@z_b+z_a@x_b)%2)

        # ---格式化为 GF(2) 矩阵并转换为 numpy 0/1 ---
        Hgf=self.check_matrix
        H_np=np.array(Hgf, dtype=int)
        m, n2=H_np.shape
        n=n2//2

        # ---构造辛形式 J 并求中央化子 NullSpace(A) 其中 A = H * J ---
        J=symplectic_form(n)
        A=(H_np@J)%2
        A_gf=galois.GF2(A)
        null=A_gf.null_space()  # 返回 r x 2n 的矩阵（GF(2)）
        if null.size==0:
            return np.zeros((0, n2), dtype=int), []

        null_np=np.array(null, dtype=int)

        # ---从中央化子中取模稳定子的差空间（取代表）---
        # 基于增量线性无关性测试（GF(2) 秩）
        span=np.array(H_np, dtype=int) if H_np.shape[0]>0 else np.zeros((0, n2), dtype=int)
        span_rank=np.linalg.matrix_rank(span) if span.size else 0
        reps=[]
        for i in range(null_np.shape[0]):
            v=null_np[i:i+1, :]
            new_span=np.vstack((span, v)) if span.size else v.copy()
            new_rank=np.linalg.matrix_rank(new_span)
            if new_rank>span_rank:
                # 选择这个代表，并把它加入 span（相当于把它视作新增的稳定子生成元以避免重复）
                reps.append(v.flatten())
                span=new_span
                span_rank=new_rank

        if len(reps)==0:
            return np.zeros((0, n2), dtype=int), []

        logical_basis=np.vstack(reps)

        # ---辛 Gram‑Schmidt，把基配成互反对易的对（寻找 symplectic = 1 的配对）---
        basis=[logical_basis[i].copy() for i in range(logical_basis.shape[0])]
        pairs=[]
        i=0
        while i<len(basis):
            v=basis[i]
            partner_idx=None
            for j in range(i+1, len(basis)):
                if symplectic_product(v, basis[j])==1:
                    partner_idx=j
                    break
            if partner_idx is None:
                # 没有找到反对易的向量，可能是完全对易的逻辑单元（孤立），记为单元素对（None 表示没有配对）
                pairs.append((i, None))
                i+=1
                continue

            # 找到配对 partner_idx，执行消去使其它向量与该对对易
            w=basis[partner_idx]
            for t in range(len(basis)):
                if t==i or t==partner_idx:
                    continue
                if symplectic_product(basis[t], v)==1:
                    # basis[t] <- basis[t] + w
                    basis[t]=(basis[t]+w)%2
                if symplectic_product(basis[t], w)==1:
                    # basis[t] <- basis[t] + v
                    basis[t]=(basis[t]+v)%2
            # 记录这一对并移动到下一个未处理
            pairs.append((i, partner_idx))
            i+=1
            # 继续（注意：此处不删除元素，仅按索引记录，结果基仍按原顺序）

        # 返回 basis 矩阵与 pairs（索引对应 basis 的行）
        logical_basis_final=np.vstack(basis)
        results=[]
        for i in range(len(logical_basis_final)):
            results.append(PauliOperator.HermitianOperatorFromVector(logical_basis_final[i]))
        return results

    # %%  CHAPTER：===静态方法===
    ##  SECTION：----基于校验矩阵构造Pauli code----
    @staticmethod
    def FromCheckMatrix(check_matrix):
        """""
        input.check_matrix：GF(2) (m,2n)
        output：PauliCode 实例
        """""
        generators = np.empty(check_matrix.shape[0], dtype=MajoranaOperator)
        for temp in range(check_matrix.shape[0]):
            occupy_x = np.where(check_matrix[temp, 0::2] == 1)[0]
            occupy_z = np.where(check_matrix[temp, 1::2] == 1)[0]
            generators[temp] = PauliOperator.HermitianOperatorFromOccupy(occupy_x, occupy_z)
        physical_number = check_matrix.shape[1] // 2
        return PauliCode(generators, physical_number)
