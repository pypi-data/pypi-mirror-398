import numpy as np
from extendedstim.Code.LinearCode.LinearCode import LinearCode
from extendedstim.tools.GaloisTools import shift, solve
import galois


class DoubleBivariantBicycleCode(LinearCode):
    __slots__=['l','m','a_x_list','a_y_list','b_x_list','b_y_list']

    #%%  CHAPTER：===构造方法===
    def __init__(self,l:int,m:int,a_x_list:list[int],a_y_list:list[int],b_x_list:list[int],b_y_list:list[int]):
        """""
        input.l：循环矩阵的大小 (偶数)
        input.m：循环矩阵的大小 (偶数)
        input.a_x_list：A中x多项式的幂列表
        input.a_y_list：A中y多项式的幂列表
        input.b_x_list：B中x多项式的幂列表
        input.b_y_list：B中y多项式的幂列表
        """""
        self.l=l
        self.m=m
        self.a_x_list=a_x_list
        self.a_y_list=a_y_list
        self.b_x_list=b_x_list
        self.b_y_list=b_y_list
        GF=galois.GF(2)
        x=GF(np.kron(shift(l, 1), np.eye(m, dtype=int)))
        y=GF(np.kron(np.eye(l, dtype=int), shift(m, 1)))
        A=None
        B=None
        for i in range(len(a_x_list)):
            if A is None:
                A=np.linalg.matrix_power(x, a_x_list[i])@np.linalg.matrix_power(y, a_y_list[i])
            else:
                A=A+np.linalg.matrix_power(x, a_x_list[i])@np.linalg.matrix_power(y, a_y_list[i])
        for i in range(len(b_x_list)):
            if B is None:
                B=np.linalg.matrix_power(x, b_x_list[i])@np.linalg.matrix_power(y, b_y_list[i])
            else:
                B=B+np.linalg.matrix_power(x, b_x_list[i])@np.linalg.matrix_power(y, b_y_list[i])
        A_T=A.T
        B_T=B.T
        H_top=np.hstack((A, B, A_T, B_T))
        H_bottom=np.hstack((B_T, A_T, B, A))
        H=GF(np.vstack((H_top, H_bottom)))
        super().__init__(H)

    #%%  CHAPTER：===属性方法===
    ##  SECTION：----字符串表示----
    def __str__(self):
        A_str=''
        B_str=''
        for i in range(len(self.a_x_list)):
            if i==0:
                A_str=A_str+f"x^{self.a_x_list[i]}y^{self.a_y_list[i]}"
            else:
                A_str=A_str+f"+x^{self.a_x_list[i]}y^{self.a_y_list[i]}"
        for i in range(len(self.b_x_list)):
            if i==0:
                B_str=B_str+f"x^{self.b_x_list[i]}y^{self.b_y_list[i]}"
            else:
                B_str=B_str+f"+x^{self.b_x_list[i]}y^{self.b_y_list[i]}"
        return f"|{self.l*self.m*4}|{self.l}|{self.m}|"+A_str+"|"+B_str+"|"