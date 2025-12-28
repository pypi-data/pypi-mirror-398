import copy
import networkx as nx
import numpy as np
from extendedstim.Code.QuantumCode.MajoranaCSSCode import MajoranaCSSCode
from extendedstim.Code.QuantumCode.MajoranaCode import MajoranaCode
from extendedstim.Code.QuantumCode.MajoranaColorCode import MajoranaColorCode
from extendedstim.Code.QuantumCode.SubsystemCode import SubsystemCode
from extendedstim.Physics.MajoranaOperator import MajoranaOperator


class FermionicLatticeSurgery:

    # %%  CHAPTER：----生成Majorana Lattice Surgery----
    def __init__(self,code_A:MajoranaCSSCode,index_A:int,code_B:MajoranaCSSCode|None=None,index_B:int|None=None)->None:
        """""
        构造用于测量joint logical observable的lattice surgery代码
        input.code_A：Majorana CSS Code
        input.index_A：code_A中的logical observable的索引
        input.code_B：Majorana CSS Code
        input.index_B：code_B中的logical observable的索引
        """""

        ##  PART：----初始化属性----
        ##  一开始的stabilizers
        self.observable:None|MajoranaOperator=None  # 待测的joint logical observable
        self.irrelevant_stabilizers=[]  # code_A and code_B中与joint logical observable无关的stabilizer
        self.original_stabilizers_A=[]  # code_A中还未修改的stabilizer
        self.original_stabilizers_B=[]  # code_B中还未修改的stabilizer

        ##  添加的ancilla相关属性
        self.ancilla_number=0  # lattice surgery过程中生成的ancilla sites数目
        self.ancilla_stabilizers=[]  # 初始时刻ancilla stabilizers

        ##  需要生成的stabilizers
        self.modify_stabilizers_A=[]  # code_A中修改的stabilizer
        self.modify_stabilizers_B=[]  # code_B中修改的stabilizer
        self.gauge_stabilizers=[]  # lattice surgery生成的gauge stabilizers
        self.measurement_stabilizers=[]  # lattice surgery生成的measurement stabilizers

        ##  PART：----根据输入的情况不同使用两种不同的lattice surgery method----
        if index_B is None or code_B is None:
            self.code_A:MajoranaCSSCode=code_A
            self.index_A: int=index_A
            self.code_B: MajoranaCSSCode=MajoranaColorCode(code_A.logical_operators_x[self.index_A].weight)
            self.index_B:int=0
            self._ZechuanLatticeSurgery()
        else:
            if code_A.logical_operators_x[index_A].weight>code_B.logical_operators_x[index_B].weight:
                self.code_A:MajoranaCSSCode=code_A.copy()
                self.code_B:MajoranaCSSCode=code_B.copy()
                self.index_A:int=index_A
                self.index_B:int=index_B
            else:
                self.code_A:MajoranaCSSCode=code_B.copy()
                self.code_B:MajoranaCSSCode=code_A.copy()
                self.index_A:int=index_B
                self.index_B:int=index_A
            self._MajoranaLatticeSurgery()
        self.physical_number=code_A.physical_number+self.code_B.physical_number+self.ancilla_number

        ##  PART：----从logical operators取出反对易于可观测量的算符生成subsystem code----
        self.code=MajoranaCode(self.irrelevant_stabilizers+self.modify_stabilizers_A+self.modify_stabilizers_B+self.gauge_stabilizers,self.physical_number)
        self.code_after_surgery=MajoranaCode(self.irrelevant_stabilizers+self.modify_stabilizers_A+self.modify_stabilizers_B+self.measurement_stabilizers+self.gauge_stabilizers,self.physical_number)

        ##  提取bare logical operators
        self.bare_logical_operators=[]
        for i in range(len(self.code_A.logical_operators_x)):
            self.bare_logical_operators.append(self.code_A.logical_operators_z[i])
            if i!=self.index_A:
                self.bare_logical_operators.append(self.code_A.logical_operators_x[i])
        for i in range(len(self.code_B.logical_operators_x)):
            self.bare_logical_operators.append(MajoranaOperator.HermitianOperatorFromOccupy([],self.code_B.logical_operators_z[i].occupy_z))
            if i!=self.index_B:
                self.bare_logical_operators.append(MajoranaOperator.HermitianOperatorFromOccupy(self.code_B.logical_operators_x[i].occupy_x,[]))

        self.subsystem_code=SubsystemCode(self.code, self.bare_logical_operators)

    # %%  CHAPTER：实现fermionic lattice surgery, method 1
    def _MajoranaLatticeSurgery(self):
        code_A:MajoranaCSSCode=self.code_A.copy()
        code_B:MajoranaCSSCode=self.code_B.copy()
        assert isinstance(code_A, MajoranaCSSCode)
        assert isinstance(code_B, MajoranaCSSCode)
        assert isinstance(self.index_A, int)
        assert isinstance(self.index_B, int)

        # %%  PART：----数据预处理----
        ##  匹配到joint code block的编号
        majorana_number_A=code_A.physical_number
        majorana_number_B=code_B.physical_number
        logical_operator_A=code_A.logical_operators_x[self.index_A]
        logical_operator_B=code_B.logical_operators_x[self.index_B]
        logical_operator_B.occupy_x=logical_operator_B.occupy_x+majorana_number_A
        self.observable=1j*logical_operator_A@logical_operator_B
        code_A.index_map(np.arange(majorana_number_A),majorana_number_A+majorana_number_B)
        code_B.index_map(np.arange(majorana_number_A, majorana_number_A+majorana_number_B),majorana_number_A+majorana_number_B)

        ##  获取需要修改的generators
        self.original_stabilizers_A=copy.deepcopy([temp for temp in code_A.generators if len(set(temp.occupy_x) & set(logical_operator_A.occupy_x)) > 0])
        self.original_stabilizers_B=copy.deepcopy([temp for temp in code_B.generators if len(set(temp.occupy_x) & set(logical_operator_B.occupy_x)) > 0])

        ##  获取不需要修改的generators
        self.irrelevant_stabilizers=([temp for temp in code_A.generators if len(set(temp.occupy_x) & set(logical_operator_A.occupy_x)) == 0]+
                                       [temp for temp in code_B.generators if len(set(temp.occupy_x) & set(logical_operator_B.occupy_x)) == 0])

        ##  PART：获取modified stabilizers
        ancilla_mode_number=0

        ##  为待修改的A stabilizers增加ancilla及其索引
        for i in range(len(self.original_stabilizers_A)):
            result_temp = [ancilla_mode_number+temp for temp in range(len(set(self.original_stabilizers_A[i].occupy_x)&set(logical_operator_A.occupy_x)))]  #  给出新增的ancilla modes编号
            self.modify_stabilizers_A.append([self.original_stabilizers_A[i].occupy_x.tolist(), result_temp])
            ancilla_mode_number+=len(result_temp)

        ##  为待修改的B stabilizers增加ancilla及其索引
        for i in range(len(self.original_stabilizers_B)):
            result_temp = [ancilla_mode_number+temp for temp in range(len(set(self.original_stabilizers_B[i].occupy_x)&set(logical_operator_B.occupy_x)))]  #  给出新增的ancilla modes编号
            self.modify_stabilizers_B.append([self.original_stabilizers_B[i].occupy_x.tolist(), result_temp])
            ancilla_mode_number+=len(result_temp)

        # %%  PART：加入测量稳定子，左边更长
        ##  先将两边对齐的部分连起来
        for i in range(len(logical_operator_B.occupy_x)):
            self.measurement_stabilizers.append([[logical_operator_A.occupy_x[i],logical_operator_B.occupy_x[i]],[]])
        for i in range((len(logical_operator_A.occupy_x)-len(logical_operator_B.occupy_x))//2):
            self.measurement_stabilizers.append([[logical_operator_A.occupy_x[2*i+len(logical_operator_B.occupy_x)],logical_operator_A.occupy_x[2*i+len(logical_operator_B.occupy_x)+1]],[]])

        ##  遍历A modified stabilizers，根据它与measurement stabilizer的交叉情况往measurement stabilizer上加ancilla modes
        for i in range(len(self.modify_stabilizers_A)):
            flag_temp=0  # 记录目前用到了哪个ancilla mode
            for j in range(len(self.measurement_stabilizers)):
                number=len(set(self.modify_stabilizers_A[i][0])&set(self.measurement_stabilizers[j][0]))
                self.measurement_stabilizers[j][1]=self.measurement_stabilizers[j][1]+[self.modify_stabilizers_A[i][1][flag_temp+k] for k in range(number)]
                flag_temp+=number

        ##  遍历B modified stabilizers，根据它与measurement stabilizer的交叉情况往measurement stabilizer上加ancilla modes
        for i in range(len(self.modify_stabilizers_B)):
            flag_temp=0  # 记录目前用到了哪个ancilla mode
            for j in range(len(self.measurement_stabilizers)):
                number=len(set(self.modify_stabilizers_B[i][0])&set(self.measurement_stabilizers[j][0]))
                self.measurement_stabilizers[j][1]=self.measurement_stabilizers[j][1]+[self.modify_stabilizers_B[i][1][flag_temp+k] for k in range(number)]
                flag_temp+=number

        ##  处理odd-weight measurement stabilizers
        single_mode_list=[]
        for i in range(len(self.measurement_stabilizers)):
            if len(self.measurement_stabilizers[i][1])%2!=0:
                self.measurement_stabilizers[i][1].append(ancilla_mode_number)
                single_mode_list.append(ancilla_mode_number)
                ancilla_mode_number+=1

        ##  PART：图论计算规范稳定子
        ##  初始化节点
        mode_vertices=['Mode'+str(temp) for temp in range(ancilla_mode_number)]
        A_vertices=[]
        B_vertices=[]
        measurement_vertices=[]
        edges=[]

        ##  生成A modified stabilizer nodes以及对应的edges
        for i in range(len(self.modify_stabilizers_A)):
            if len(self.modify_stabilizers_A[i][1])//2==1:
                A_vertices.append('A'+str(i))
                edges.append(('A'+str(i), 'Mode'+str(self.modify_stabilizers_A[i][1][0])))
                edges.append(('A'+str(i), 'Mode'+str(self.modify_stabilizers_A[i][1][1])))
            else:
                for j in range(len(self.modify_stabilizers_A[i][1])//2):
                    A_vertices.append('A'+str(i)+'_'+str(j))
                    edges.append(('A'+str(i), 'Mode'+str(self.modify_stabilizers_A[i][1][j*2])))
                    edges.append(('A'+str(i), 'Mode'+str(self.modify_stabilizers_A[i][1][j*2+1])))

        ##  生成B modified stabilizer nodes以及对应的edges
        for i in range(len(self.modify_stabilizers_B)):
            if len(self.modify_stabilizers_B[i][1])//2==1:
                B_vertices.append('B'+str(i))
                edges.append(('B'+str(i), 'Mode'+str(self.modify_stabilizers_B[i][1][0])))
                edges.append(('B'+str(i), 'Mode'+str(self.modify_stabilizers_B[i][1][1])))
            else:
                for j in range(len(self.modify_stabilizers_B[i][1])//2):
                    B_vertices.append('B'+str(i)+'_'+str(j))
                    edges.append(('B'+str(i), 'Mode'+str(self.modify_stabilizers_B[i][1][j*2])))
                    edges.append(('B'+str(i), 'Mode'+str(self.modify_stabilizers_B[i][1][j*2+1])))

        ##  生成measurement stabilizer nodes以及对应的edges
        for i in range(len(self.measurement_stabilizers)):
            measurement_vertices.append('Measure'+str(i))
            for j in range(len(self.measurement_stabilizers[i][1])):
                edges.append(('Measure'+str(i), 'Mode'+str(self.measurement_stabilizers[i][1][j])))

        ##  生成single ancilla mode的virtual edges
        virtual_vertices=[]
        for i in range(len(single_mode_list)//2):
            virtual_vertices.append('Virtual'+str(i))
            edges.append(('Virtual'+str(i), 'Mode'+str(single_mode_list[i])))
            edges.append(('Virtual'+str(i), 'Mode'+str(single_mode_list[i])))

        ##  生成图
        graph = nx.Graph()
        graph.add_nodes_from(mode_vertices)
        graph.add_nodes_from(A_vertices)
        graph.add_nodes_from(B_vertices)
        graph.add_nodes_from(measurement_vertices)
        graph.add_nodes_from(virtual_vertices)
        graph.add_edges_from(edges)
        cyclic_basis=nx.minimum_cycle_basis(graph)
        for i in range(len(cyclic_basis)):
            modes_temp=[]
            for j in range(len(cyclic_basis[i])):
                if 'Mode' in cyclic_basis[i][j]:
                    modes_temp.append(int(cyclic_basis[i][j][4:]))
            self.gauge_stabilizers.append([[],modes_temp])

        ##  PART：将stabilizers修改为正确的格式
        alls=[self.modify_stabilizers_A,self.modify_stabilizers_B,self.measurement_stabilizers,self.gauge_stabilizers]
        for i in range(len(alls)):
            for j in range(len(alls[i])):
                occupy_x_temp=alls[i][j][0]+[temp//2+majorana_number_A+majorana_number_B for temp in alls[i][j][1] if temp%2==0]
                occupy_z_temp=[temp//2+majorana_number_A+majorana_number_B for temp in alls[i][j][1] if temp%2==1]
                alls[i][j]=MajoranaOperator.HermitianOperatorFromOccupy(occupy_x_temp,occupy_z_temp)
        self.ancilla_number=ancilla_mode_number//2

    #%%  CHAPTER：Zechuan Lattice Surgery
    def _ZechuanLatticeSurgery(self):

        #%%  SECTION：----数据标准化----
        code_A: MajoranaCSSCode=self.code_A.copy()
        code_B: MajoranaColorCode=self.code_B.copy()
        majorana_number_A=code_A.physical_number
        majorana_number_B=code_B.physical_number
        logical_operator_A=code_A.logical_operators_x[self.index_A]
        logical_operator_B=code_B.logical_operators_x[0]
        logical_operator_B.occupy_x=logical_operator_B.occupy_x+majorana_number_A
        self.observable=1j*logical_operator_A@logical_operator_B
        code_A.index_map(np.arange(majorana_number_A),majorana_number_A+majorana_number_B)
        code_B.index_map(np.arange(majorana_number_A, majorana_number_A+majorana_number_B),majorana_number_A+majorana_number_B)

        self.original_stabilizers_A=copy.deepcopy([temp for temp in code_A.generators if len(set(temp.occupy_x) & set(logical_operator_A.occupy_x)) > 0])
        self.original_stabilizers_B=copy.deepcopy([temp for temp in code_B.generators if len(set(temp.occupy_x) & set(logical_operator_B.occupy_x)) > 0])
        self.irrelevant_stabilizers=([temp for temp in code_A.generators if len(set(temp.occupy_x) & set(logical_operator_A.occupy_x)) == 0]+
                                     [temp for temp in code_B.generators if len(set(temp.occupy_x) & set(logical_operator_B.occupy_x)) == 0])

        ancilla_mode_number=0
        edge_site_bin_A:list[list[int]]=[[] for _ in range(code_B.d)]
        edge_site_bin_B:list[list[int]]=[[] for _ in range(code_B.d)]
        used_flags=[False for _ in range(len(code_B.edge_stabilizers))]

        ##  为待修改的stabilizers增加ancilla及其索引
        for i in range(len(self.original_stabilizers_A)):
            overlaps=list(set(self.original_stabilizers_A[i].occupy_x)&set(logical_operator_A.occupy_x))
            for j in range(len(overlaps)//2):
                index_0=int(np.where(logical_operator_A.occupy_x==overlaps[2*j])[0][0])
                index_1=int(np.where(logical_operator_A.occupy_x==overlaps[2*j+1])[0][0])
                edge_site_bin_A[index_0].append(ancilla_mode_number)
                edge_site_bin_A[index_1].append(ancilla_mode_number+1)
                self.modify_stabilizers_A.append([self.original_stabilizers_A[i].occupy_x.tolist(), [ancilla_mode_number, ancilla_mode_number+1]])
                edge_site_bin_B[index_0].append(ancilla_mode_number+2)
                edge_site_bin_B[index_1].append(ancilla_mode_number+3)
                self.modify_stabilizers_B.append([self.original_stabilizers_B[i].occupy_x.tolist(), [ancilla_mode_number+2, ancilla_mode_number+3]])
                small=min(index_0,index_1)
                big=max(index_0,index_1)
                used_flags[small]=True
                used_flags[big-1]=True
                self.gauge_stabilizers.append([[],[ancilla_mode_number+temp for temp in range(4)]])
                ancilla_mode_number+=4

        ##  处理落单的edge stabilizers
        for i in range(len(used_flags)):
            if not used_flags[i]:
                edge_site_bin_B[i].append(ancilla_mode_number)
                edge_site_bin_B[i].append(ancilla_mode_number+1)
                edge_site_bin_B[i+1].append(ancilla_mode_number+2)
                edge_site_bin_B[i+1].append(ancilla_mode_number+3)
                self.modify_stabilizers_B.append([code_B.get_between(i, i+1).occupy_x.tolist(), [ancilla_mode_number, ancilla_mode_number+2]])
                self.gauge_stabilizers.append([[],[ancilla_mode_number+temp for temp in range(4)]])
                ancilla_mode_number+=4

        ##  添加measurement stabilizers
        for i in range(len(edge_site_bin_A)):
            self.measurement_stabilizers.append(([logical_operator_A.occupy_x[i], logical_operator_B.occupy_x[i]],edge_site_bin_A[i]+edge_site_bin_B[i]))

        ##  PART：将stabilizers修改为正确的格式
        alls=[self.modify_stabilizers_A,self.modify_stabilizers_B,self.measurement_stabilizers,self.gauge_stabilizers]
        for i in range(len(alls)):
            for j in range(len(alls[i])):
                occupy_x_temp=alls[i][j][0]+[temp//2+majorana_number_A+majorana_number_B for temp in alls[i][j][1] if temp%2==0]
                occupy_z_temp=[temp//2+majorana_number_A+majorana_number_B for temp in alls[i][j][1] if temp%2==1]
                alls[i][j]=MajoranaOperator.HermitianOperatorFromOccupy(occupy_x_temp,occupy_z_temp)
        self.ancilla_number=ancilla_mode_number//2


if __name__ == '__main__':
    code_A=MajoranaColorCode(3)
    code_B=MajoranaColorCode(3)
    lattice_surgery=FermionicLatticeSurgery(code_A,0)
    print(lattice_surgery.subsystem_code.distance)
