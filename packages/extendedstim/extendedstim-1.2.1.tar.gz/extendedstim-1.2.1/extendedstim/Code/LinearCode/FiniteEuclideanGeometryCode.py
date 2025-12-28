"""""
模块作用：基于有限Euclidean几何 (EG(m,q)) 构造LDPC线性码，利用几何直线族形成自对偶或稀疏校验矩阵。
"""""
import galois
import numpy as np
from extendedstim.Code.LinearCode.LinearCode import LinearCode
from extendedstim.tools.TypingTools import isinteger


class FiniteEuclideanGeometryCode(LinearCode):

    #%%  CHAPTER：===构造方法===
    def __init__(self,dimension:int,power:int,prime:int=2)->None:
        """""
        input.dimension: 有限Euclidean geometry的维度 m
        input.power: 有限域的生成幂 (q = prime^power)
        input.prime: 有限域的生成元素素数 base
        output：无（构造对象）
        """""

        ##  ----PART：数据预处理----
        assert isinteger(dimension), "dimension必须是整数"
        assert isinteger(power), "power必须是整数"
        assert isinteger(prime), "prime必须是整数"

        ##  ------PART：生成校验矩阵------
        self.dimension=dimension  # 有限Euclidean geometry的维度
        self.prime=prime  # 有限域的生成元素素数
        self.power=power  # 有限域的生成幂
        q=prime**power  # 坐标值的个数
        number_point=q**dimension  # 点的个数
        GF=galois.GF(q**dimension, repr='power')  # 用q**m有限域表示m维GF(q)上的几何点
        a=GF.primitive_element  # 几何有限域的基元
        J=int((q**(dimension-1)-1)//(q-1))  # 线的数目

        ##  计算所有的循环族的直线集合
        number_class=0
        line_matrix=np.empty((J, number_point-1, q), dtype=type(a))  # 直线集合构成循环族的集合
        for i in range(number_point-1):
            point_b=a**i  # 直线斜率
            line_vector=np.empty((number_point-1, q), dtype=type(point_b))  # 直线集合构成的循环族

            ##  生成第一条直线
            for j in range(q):
                point_temp=a+GF.elements[j]*point_b
                line_vector[0, j]=point_temp
            line_vector[0, :]=np.sort(line_vector[0, :])

            ##  要求不过原点
            if line_vector[0, 0]==GF.elements[0]:
                continue

            ##  求直线族中其他直线
            for j in range(1, number_point-1):
                line_vector[j, :]=[(a**j)*temp for temp in line_vector[0, :]]
                line_vector[j, :]=np.sort(line_vector[j, :])

            ##  判断生成的直线族是否重复
            for j in range(number_class):
                flag=False
                for k in range(number_point-1):
                    if line_vector[0, 0]==line_matrix[j, k, 0]:
                        if line_vector[0, 1]==line_matrix[j, k, 1]:
                            flag=True
                            break
                if flag:
                    break
                if j==number_class-1:
                    line_matrix[number_class, :, :]=line_vector
                    number_class=number_class+1
            if number_class==0:
                line_matrix[number_class, :, :]=line_vector
                number_class=1

            if number_class==J:
                break

        ##  拼接成校验矩阵
        H_list=[]
        for i in range(number_class):
            H=np.zeros((number_point-1, number_point-1), dtype=int)
            for j in range(number_point-1):
                for k in range(q):
                    element_temp=str(line_matrix[i, j, k])
                    if element_temp=='1':
                        element_temp=0
                    elif element_temp=='0':
                        raise ValueError
                    elif element_temp=='α':
                        element_temp=1
                    else:
                        element_temp=int(element_temp[2::])
                    H[j, int(element_temp)]=1
            H_list.append(H)

        ##  构造完整的校验矩阵
        H_left=np.hstack([H_j.T for H_j in H_list])  # Transposed blocks
        H_right=np.hstack(H_list)  # Original blocks
        H=np.hstack([H_left, H_right])

        ##  PART：----校验矩阵的自对偶性并构造纠错码----
        assert np.all(np.mod(H@H.T,2)==0)
        super().__init__(H)
