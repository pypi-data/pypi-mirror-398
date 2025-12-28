import numpy as np
from extendedstim.Code.QuantumCode.MajoranaCSSCode import MajoranaCSSCode
from extendedstim.Physics.MajoranaOperator import MajoranaOperator


class MajoranaColorCode(MajoranaCSSCode):

    #%%  CHAPTER：----生成Majorana Color Code----
    def __init__(self, d: int) -> None:
        self.edge_stabilizers=[]
        self.d=d
        """""
        input.d：奇数，表示三角形网格的边长（distance）
        output：PauliCSSCode
        """""

        ##  基本数值罗列
        x_0=0
        y_0=0
        cell_vector=[np.array([0, 0], dtype=float), np.array([2, 0], dtype=float), np.array([0.5, np.sqrt(3)/2], dtype=float),
                     np.array([1.5, np.sqrt(3)/2], dtype=float), np.array([0.5, -np.sqrt(3)/2], dtype=float),
                     np.array([1.5, -np.sqrt(3)/2], dtype=float)]
        cells=[]
        x_now=0
        y_now=0

        ##  生成所有的六角晶格
        for i in range(d//2):
            for j in range(3):
                for k in range(d//2-i):
                    x_now_temp=x_now+k*1.5
                    cells.append([np.array([x_now_temp, y_now], dtype=float)+cell_vector[k] for k in range(6)])
                if j==0:
                    y_now+=np.sqrt(3)/2
                    x_now+=1.5
                elif j==1:
                    y_now+=np.sqrt(3)/2
                    x_now-=1.5
                elif j==2:
                    y_now+=np.sqrt(3)/2
                    x_now+=1.5

        ##  筛除不在三角形内的晶格
        cells_in_triangle=[]
        for i in range(len(cells)):
            cells_in_triangle.append([])
            for j in range(6):
                if judge_in_triangle(cells[i][j][0], cells[i][j][1],x_0,y_0,d):
                    cells_in_triangle[i].append(cells[i][j])
        position_list=[]
        stabilizer_list_x=[]
        stabilizer_list_z=[]

        ##  查找底层sites
        for i in range(len(cells_in_triangle)):
            for j in range(len(cells_in_triangle[i])):
                if abs(cells_in_triangle[i][j][1])<0.01:
                    flag=True
                    for k in range(len(position_list)):
                        if equal(cells_in_triangle[i][j], position_list[k]):
                            flag=False
                            break
                    if flag:
                        position_list.append(cells_in_triangle[i][j])

        ##  根据晶体生成stabilizers
        for i in range(len(cells_in_triangle)):
            stabilizer_temp=[]
            for j in range(len(cells_in_triangle[i])):
                flag=True
                index=0
                for k in range(len(position_list)):
                    if equal(cells_in_triangle[i][j], position_list[k]):
                        flag=False
                        index=k
                        break
                if flag:
                    stabilizer_temp.append(len(position_list))
                    position_list.append(cells_in_triangle[i][j])
                else:
                    stabilizer_temp.append(index)
            stabilizer_list_x.append(MajoranaOperator.HermitianOperatorFromOccupy(stabilizer_temp,[]))
            stabilizer_list_z.append(MajoranaOperator.HermitianOperatorFromOccupy([],stabilizer_temp))

        ##  生成边界上的stabilizers
        stabilizer_between_old=stabilizer_list_x[0:d]
        self.edge_stabilizers=[]
        for i in range(d//2):
            self.edge_stabilizers.append(stabilizer_between_old[i])
            self.edge_stabilizers.append(stabilizer_between_old[i+d//2])

        ##  赋值并直接给出logical operators
        super().__init__(stabilizer_list_x,stabilizer_list_z,len(position_list))
        self._logical_operators_x=[MajoranaOperator.HermitianOperatorFromOccupy([i for i in range(d)],[])]
        self._logical_operators_z=[MajoranaOperator.HermitianOperatorFromOccupy([],[i for i in range(d)])]

    ##  SECTION：----给出边界上的stabilizer----
    def get_between(self,index_0:int,index_1:int):
        """""
        input.index_0：int，site的索引
        input.index_1：int，site的索引
        output：MajoranaOperator，index_0到index_1之间的stabilizer
        """""
        if index_0>index_1:
            aa=index_1
            bb=index_0
        else:
            aa=index_0
            bb=index_1
        assert 0<=index_0<self.d
        assert 0<=index_1<self.d
        if aa==bb-1:
            return self.edge_stabilizers[aa].copy()
        else:
            return self.edge_stabilizers[aa]@self.edge_stabilizers[bb-1]


def judge_in_triangle(x, y,x_0,y_0,d):
    """""
    input.x：float，x坐标
    input.y：float，y坐标
    output：bool，是否在三角形内
    """""
    x_1=x_0+d//2+d-1
    # y_1=0
    x_2=x_1/2
    y_2=np.sqrt(3)*x_2

    k_0=0
    b_0=0
    k_1=(y_2-y_0)/(x_2-x_0)
    b_1=0
    k_2=-k_1
    b_2=2*y_2
    if k_0*x+b_0<y+0.01 and k_1*x+b_1>y-0.01 and k_2*x+b_2>y-0.01:
        return True
    else:
        return False

def equal(a, b):
    """""
    input.a：float，a坐标
    input.b：float，b坐标
    output：bool，是否相等
    """""
    if abs(a[0]-b[0])+abs(a[1]-b[1])<0.01:
        return True
    else:
        return False
