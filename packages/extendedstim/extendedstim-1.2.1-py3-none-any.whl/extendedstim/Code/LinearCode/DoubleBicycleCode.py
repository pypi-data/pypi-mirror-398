"""""
模块作用：实现构造
"""""
import numpy as np
from extendedstim.Code.LinearCode.LinearCode import LinearCode
from extendedstim.tools.GaloisTools import cyclic_matrix


class DoubleBicycleCode(LinearCode):

    # %%  CHAPTER：===构造方法===
    def __init__(self,n:int,a_occupy:list,b_occupy:list)->None:
        """""
        input.n：循环矩阵的大小
        input.a_occupy：循环矩阵A中1的位置
        input.b_occupy：循环矩阵B中1的位置
        output：无（构造对象）
        """""

        ##  PART：----数据预处理----
        self.number_bit=n*4
        self.a_occupy=a_occupy.copy()
        self.b_occupy=b_occupy.copy()
        self.a_occupy.sort()
        self.b_occupy.sort()

        ##  PART：----构造校验矩阵----
        a_list = [1 if i in self.a_occupy else 0 for i in range(n)]
        b_list = [1 if i in self.b_occupy else 0 for i in range(n)]
        H_up = np.hstack([cyclic_matrix(n, a_list), cyclic_matrix(n, b_list), cyclic_matrix(n, a_list).T, cyclic_matrix(n, b_list).T])
        H_down = np.hstack([cyclic_matrix(n, b_list).T, cyclic_matrix(n, a_list).T, cyclic_matrix(n, b_list), cyclic_matrix(n, a_list)])
        H = np.vstack([H_up, H_down])

        ##  PART：----初始化纠错码----
        super().__init__(H)

    #%%  CHAPTER：===重载运算符===
    ##  SECTION：----打印代码----
    def __str__(self):
        n=self.number_bit//4
        S_str_a=''
        for i in self.a_occupy:
            S_str_a+=f"S^{{{i}}}_{{{n}}}"
        S_str_b=''
        for i in self.b_occupy:
            S_str_b+=f"S^{{{i}}}_{{{n}}}"
        return S_str_a+ '\n'+S_str_b