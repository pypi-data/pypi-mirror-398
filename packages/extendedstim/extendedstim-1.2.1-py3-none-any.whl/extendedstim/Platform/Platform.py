"""""
模块作用：定义基于稳定子表述的平台态演化与测量模型，支持Pauli与Majorana门、噪声、测量与复位。
"""""
from galois import GF2
from extendedstim.Physics.MajoranaOperator import MajoranaOperator
from extendedstim.Physics.PauliOperator import PauliOperator
from extendedstim.tools.GaloisTools import *
from extendedstim.tools.TypingTools import isinteger


class Platform:
    GF=galois.GF(2)

    # %%  CHAPTER：===构造方法===
    def __init__(self):
        self.pauli_number = 0
        self.majorana_number = 0
        self.stabilizers_pauli = []
        self.stabilizers_majorana = []
        self.stabilizers=None
        self.coffs=None

    # %%  CHAPTER：===对象方法===
    ##  SECTION：---初始化平台，定义fermionic sites和qubits数目---
    def trap(self, majorana_number, pauli_number):
        """""
        input.majorana_number：费米子位数
        input.pauli_number：量子位数
        """""

        ##  ---数据预处理---
        assert isinteger(majorana_number) and majorana_number >= 0
        assert isinteger(pauli_number) and pauli_number >= 0

        ##  ----定义平台初态----
        ##  定义平台qubits和fermionic sites分别的数目
        self.pauli_number = pauli_number
        self.majorana_number = majorana_number
        self.stabilizers=self.GF(np.zeros((majorana_number+pauli_number,2*majorana_number+2*pauli_number),dtype=int))
        self.coffs=np.ones(majorana_number+pauli_number,dtype=complex)

        ##  初始化状态，平台处于空态与0态
        for i in range(majorana_number):
            self.stabilizers[i, 2*i]=1
            self.stabilizers[i, 2*i+1]=1
            self.coffs[i]=1j
        for i in range(pauli_number):
            self.stabilizers[i+majorana_number,2*i+1+2*majorana_number]=1
            self.coffs[i+majorana_number]=1

    ##  SECTION：----测量算符op，返回测量结果，随机坍缩----
    def measure(self,op):
        """""
        input.op：PauliOperator 或 MajoranaOperator（厄米）
        output：+1 或 -1 测量结果
        influence：更新稳定子组或一致性检查
        """""

        ##  ----数据预处理----
        assert op.is_hermitian
        if isinstance(op, MajoranaOperator):
            vector_op=np.append(op.get_vector(self.majorana_number),self.GF.Zeros(self.pauli_number*2))
        else:
            vector_op=np.append(self.GF.Zeros(self.majorana_number*2),op.get_vector(self.pauli_number))
        first_index=None
        for i in range(len(self.stabilizers)):
            pauli_commute=(np.dot(self.stabilizers[i][self.majorana_number*2::2],vector_op[self.majorana_number*2+1::2])+
                           np.dot(self.stabilizers[i][self.majorana_number*2+1::2],vector_op[self.majorana_number*2::2]))
            majorana_commute=(np.dot(self.stabilizers[i][0:self.majorana_number*2],vector_op[0:self.majorana_number*2])+
                              np.sum(vector_op[0:self.majorana_number*2])*np.sum(self.stabilizers[i][0:self.majorana_number*2]))

            if majorana_commute+pauli_commute==1 and first_index is None:
                first_index=i
            elif majorana_commute+pauli_commute==1 and first_index is not None:
                factor=np.sum([np.sum(self.stabilizers[i][temp+1:2*self.majorana_number]) for temp in range(2*self.majorana_number) if
                               self.stabilizers[first_index][temp]==1])
                self.stabilizers[i]+=self.stabilizers[first_index]
                if np.mod(factor,2)==0:
                    factor=1
                else:
                    factor=-1
                self.coffs[i]=self.coffs[i]*self.coffs[first_index]*factor
            else:
                pass
        if first_index is not None:
            if np.random.rand() < 0.5:
                self.stabilizers[first_index]=vector_op
                self.coffs[first_index]=op.coff
                return 1
            else:
                self.stabilizers[first_index]=vector_op
                self.coffs[first_index]=-op.coff
                return -1
        else:
            solution=solve(self.stabilizers,vector_op)
            coff=np.prod([self.coffs[i] for i in range(len(self.stabilizers)) if solution[i]==1])
            vector_now, factor=majorana_factor(self.majorana_number,[self.stabilizers[i] for i in range(len(self.stabilizers)) if solution[i]==1])
            coff=coff*factor
            if coff==op.coff:
                return 1
            else:
                return -1

    ##  SECTION：----X门，作用于qubit_index----
    def x(self, qubit_index: int):
        """""
        input.qubit_index：目标量子位
        influence：翻转与Z重叠的稳定子相位
        """""

        ##  PART：----数据预处理----
        assert isinteger(qubit_index) and 0 <= qubit_index < self.pauli_number

        ##  PART：----处理过程----
        ##  计算系数
        indices=np.where(self.stabilizers[:,self.majorana_number*2+qubit_index*2+1]==1)[0]
        self.coffs[indices]=-self.coffs[indices]

    ##  SECTION：----Y门，作用于qubit_index----
    def y(self, qubit_index: int):
        """""
        input.qubit_index：目标量子位
        influence：对X与Z重叠稳定子均翻相
        """""

        ##  PART：----数据预处理----
        assert isinteger(qubit_index) and 0 <= qubit_index < self.pauli_number

        ##  PART：----处理过程----
        ##  计算系数
        indices_x=np.where(self.stabilizers[:,self.majorana_number*2+qubit_index*2+1]==1)[0]
        self.coffs[indices_x]=-self.coffs[indices_x]
        indices_z=np.where(self.stabilizers[:,self.majorana_number*2+qubit_index*2]==1)[0]
        self.coffs[indices_z]=-self.coffs[indices_z]

    ##  SECTION：----Z门，作用于qubit_index----
    def z(self, qubit_index: int):
        """""
        input.qubit_index：目标量子位
        influence：翻转与X重叠的稳定子相位
        """""

        ##  PART：----数据预处理----
        assert isinteger(qubit_index) and 0 <= qubit_index < self.pauli_number

        ##  PART：----处理过程----
        ##  计算系数
        indices=np.where(self.stabilizers[:,self.majorana_number*2+qubit_index*2]==1)[0]
        self.coffs[indices]=-self.coffs[indices]

    ##  USER：---Hadamard gate，作用于qubit_index---
    def h(self, qubit_index: int):
        """""
        input.qubit_index：目标量子位
        influence：交换X/Z支撑，更新相位
        """""

        ##  PART：----数据预处理----
        assert isinteger(qubit_index) and 0 <= qubit_index < self.pauli_number

        ##  PART：----处理过程----
        ##  计算系数
        indices=np.where(np.logical_and(self.stabilizers[:,self.majorana_number*2+qubit_index*2+1]==1,self.stabilizers[:,self.majorana_number*2+qubit_index*2]==1))[0]
        self.coffs[indices]=-self.coffs[indices]

        ##  计算结果向量
        caches=self.stabilizers[:,self.majorana_number*2+qubit_index*2].copy()
        self.stabilizers[:,self.majorana_number*2+qubit_index*2]=self.stabilizers[:,self.majorana_number*2+qubit_index*2+1]
        self.stabilizers[:,self.majorana_number*2+qubit_index*2+1]=caches

    ##  USER：----S门，作用于pauli_index----
    def s(self, pauli_index: int):
        """""
        input.pauli_index：目标量子位
        influence：Z += X（相位门）
        """""

        ##  PART：----数据预处理----
        assert isinteger(pauli_index) and 0 <= pauli_index < self.pauli_number

        ##  PART：----处理过程----
        ##  计算系数
        indices=np.where(self.stabilizers[:,self.majorana_number*2+pauli_index*2]==1)[0]
        self.coffs[indices]=1j*self.coffs[indices]
        self.stabilizers[:,self.majorana_number*2+pauli_index*2+1]+=self.stabilizers[:,self.majorana_number*2+pauli_index*2]

    ##  USER：----gamma门，作用于majorana_index----
    def u(self, majorana_index: int):
        """""
        input.majorana_index：目标费米子位
        influence：依据重叠权重翻相
        """""

        ##  PART：----数据预处理----
        assert isinteger(majorana_index) and 0 <= majorana_index < self.majorana_number

        ##  PART：----处理过程----
        ##  计算系数
        weights=np.sum(self.stabilizers[:,0:2*self.majorana_number],axis=1)
        overlaps=self.GF(np.where(self.stabilizers[:, majorana_index*2]==1, 1, 0))
        indices=np.where(weights+overlaps==0)[0]
        self.coffs[indices]=-self.coffs[indices]

    ##  SECTION：----gamma_prime门，作用于majorana_index----
    def v(self, majorana_index: int):
        """""
        input.majorana_index：目标费米子位
        influence：依据Z重叠翻相
        """""
        ##  ----数据预处理----
        assert isinteger(majorana_index) and 0 <= majorana_index < self.majorana_number

        ##  ----gamma_prime门作用----
        weights=np.sum(self.stabilizers[:,0:2*self.majorana_number],axis=1)
        overlaps=self.GF(np.where(self.stabilizers[:,majorana_index*2+1]==1,1,0))
        indices=np.where(weights+overlaps==0)[0]
        self.coffs[indices]=-self.coffs[indices]

    ##  USER：----i*gamma*gamma_prime门，作用于majorana_index----
    def n(self, majorana_index: int):
        """""
        input.majorana_index：目标费米子位
        influence：依据X或Z奇偶翻相
        """""
        ##  PART：----数据预处理----
        assert isinteger(majorana_index) and 0 <= majorana_index < self.majorana_number

        ##  PART：----处理过程----
        ##  计算系数
        weights=np.sum(self.stabilizers[:,0:2*self.majorana_number],axis=1)
        overlaps=self.GF(np.where(np.logical_xor(self.stabilizers[:,majorana_index*2]==1,self.stabilizers[:,majorana_index*2+1]==1),1,0))
        indices=np.where(weights+overlaps==1)[0]
        self.coffs[indices]=-self.coffs[indices]

    ##  USER：----P门，作用于majorana_index----
    def p(self, majorana_index: int):
        """""
        input.majorana_index：目标费米子位
        influence：交换X/Z支撑
        """""

        ##  PART：----数据预处理----
        assert isinteger(majorana_index) and 0 <= majorana_index < self.majorana_number

        ##  PART：----处理过程----
        ##  计算系数
        indices=np.where(np.logical_and(self.stabilizers[:,majorana_index*2+1]==1,self.stabilizers[:,majorana_index*2]==0))[0]
        self.coffs[indices]=-self.coffs[indices]

        ##  计算结果向量
        caches=self.stabilizers[:,majorana_index*2].copy()
        self.stabilizers[:,majorana_index*2]=self.stabilizers[:,majorana_index*2+1]
        self.stabilizers[:,majorana_index*2+1]=caches

    ##  USER：----CNOT门，作用于control_index,target_index，两者是qubits，前者是控制位----
    def cx(self, control_index, target_index):
        """""
        input.control_index,target_index：量子位索引
        influence：稳定子线性变换（X/Z互相传播）
        """""

        ##  PART：----数据预处理----
        assert isinteger(control_index) and 0 <= control_index < self.pauli_number
        assert isinteger(target_index) and 0 <= target_index < self.pauli_number

        ##  PART：----处理过程----
        ##  位点坐标换算
        control_qubit_index_x=control_index*2+self.majorana_number*2
        control_qubit_index_z=control_index*2+1+self.majorana_number*2
        target_qubit_index_x=target_index*2+self.majorana_number*2
        target_qubit_index_z=target_index*2+1+self.majorana_number*2

        ##  结果向量计算
        targets_x=self.stabilizers[:,control_qubit_index_x]+self.stabilizers[:,target_qubit_index_x]
        control_z=self.stabilizers[:,control_qubit_index_z]+self.stabilizers[:,target_qubit_index_z]
        self.stabilizers[:,target_qubit_index_x]=targets_x
        self.stabilizers[:,control_qubit_index_z]=control_z

    ##  SECTION：----CN-NOT门，作用于control_index,target_index，前者是fermionic site控制位，后者是qubit目标位----
    def cnx(self, control_index:int, target_index:int):
        """""
        input.control_index：费米子控制位
        input.target_index：量子位目标
        influence：见文档推导的稳定子更新规则
        """""

        ##  PART：----数据预处理----
        assert isinteger(control_index) and 0 <= control_index < self.majorana_number
        assert isinteger(target_index) and 0 <= target_index < self.pauli_number

        ##  PART：----处理过程----
        ##  位点坐标换算
        control_majorana_index_x=control_index*2
        control_majorana_index_z=control_index*2+1
        target_qubit_index_x=self.majorana_number*2+target_index*2
        target_qubit_index_z=self.majorana_number*2+target_index*2+1

        ##  系数计算
        factor=[1j if self.stabilizers[temp,target_qubit_index_z]==1 else 1 for temp in range(len(self.stabilizers))]
        indices=np.where(np.logical_and(self.stabilizers[:,target_qubit_index_z]==1,self.stabilizers[:,control_majorana_index_z]==1))[0]
        self.coffs = self.coffs * np.array(factor)
        self.coffs[indices]=-self.coffs[indices]

        ##  结果向量计算
        targets_x= self.stabilizers[:,target_qubit_index_x]+self.stabilizers[:,control_majorana_index_x]+self.stabilizers[:,control_majorana_index_z]
        controls_x=self.stabilizers[:,control_majorana_index_x]+self.stabilizers[:,target_qubit_index_z]
        controls_z=self.stabilizers[:,control_majorana_index_z]+self.stabilizers[:,target_qubit_index_z]
        self.stabilizers[:,target_qubit_index_x]=targets_x
        self.stabilizers[:,control_majorana_index_x]=controls_x
        self.stabilizers[:,control_majorana_index_z]=controls_z

    ##  SECTION：----CN-N门，作用于control_index,target_index，前者是fermionic site控制位，后者是fermionic site目标位----
    def cnn(self, control_index:int, target_index:int):
        """""
        input.control_index,target_index：费米子索引
        influence：见文档推导的稳定子更新规则
        """""

        ##  PART：----数据预处理----
        assert isinteger(control_index) and 0<=control_index<self.majorana_number
        assert isinteger(target_index) and 0<=target_index<self.majorana_number
        if target_index<control_index:
            cache=target_index
            target_index=control_index
            control_index=cache

        ##  PART：----处理过程----
        ##  位点坐标计算
        control_majorana_index_x=control_index*2
        control_majorana_index_z=control_index*2+1
        target_majorana_index_x=target_index*2
        target_majorana_index_z=target_index*2+1

        ##  计算系数
        temp=self.stabilizers[:,(control_majorana_index_x,control_majorana_index_z,target_majorana_index_x,target_majorana_index_z)]
        indices_1j=np.where(np.logical_or(np.logical_or(np.all(temp==GF2([1,0,0,0]),axis=1),np.all(temp==GF2([0,1,0,0]),axis=1)),np.logical_or(np.all(temp==GF2([0,0,1,0]),axis=1),np.all(temp==GF2([0,0,0,1]),axis=1))))[0]
        indices_minus_1=np.where(np.logical_or(np.all(temp==GF2([1, 0, 0, 1]),axis=1),np.all(temp==GF2([0, 1, 1, 0]),axis=1)))[0]
        indices_minus_1j=np.where(np.logical_or(np.logical_or(np.all(temp==GF2([1, 1, 1, 0]),axis=1),np.all(temp==GF2([1, 1, 0, 1]),axis=1)),np.logical_or(np.all(temp==GF2([1,0,1,1]),axis=1),np.all(temp==GF2([0,1,1,1]),axis=1))))[0]
        self.coffs[indices_1j]=self.coffs[indices_1j]*1j
        self.coffs[indices_minus_1]=-self.coffs[indices_minus_1]
        self.coffs[indices_minus_1j]=self.coffs[indices_minus_1j]*(-1j)

        ##  结果向量计算
        control_x= self.stabilizers[:,control_majorana_index_x]+self.stabilizers[:,target_majorana_index_x]+self.stabilizers[:,target_majorana_index_z]
        control_z= self.stabilizers[:,control_majorana_index_z]+self.stabilizers[:,target_majorana_index_x]+self.stabilizers[:,target_majorana_index_z]
        target_x= self.stabilizers[:,target_majorana_index_x]+self.stabilizers[:,control_majorana_index_x]+self.stabilizers[:,control_majorana_index_z]
        target_z= self.stabilizers[:,target_majorana_index_z]+self.stabilizers[:,control_majorana_index_x]+self.stabilizers[:,control_majorana_index_z]
        self.stabilizers[:,control_majorana_index_x]=control_x
        self.stabilizers[:,control_majorana_index_z]=control_z
        self.stabilizers[:,target_majorana_index_x]=target_x
        self.stabilizers[:,target_majorana_index_z]=target_z

    ##  SECTION：----Braid门，前者是fermionic site控制位，后者是fermionic site目标位----
    def braid(self,control_index:int,target_index:int):
        """""
        input.control_index,target_index：费米子索引
        influence：交换特定支撑并翻相
        """""
        ##  PART：----数据预处理----
        assert isinteger(control_index) and 0<=control_index<self.majorana_number
        assert isinteger(target_index) and 0<=target_index<self.majorana_number

        ##  PART：----处理过程----
        ##  位点坐标计算
        control_majorana_index_z=control_index*2+1
        control_majorana_index_x=control_index*2
        target_majorana_index_x=target_index*2
        target_majorana_index_z=target_index*2+1

        ##  系数计算
        if target_index>control_index:
            numbers_of_mid=np.sum(self.stabilizers[:,control_majorana_index_z+1:target_majorana_index_x],axis=1)
        else:
            numbers_of_mid=np.sum(self.stabilizers[:,target_majorana_index_x+1:control_majorana_index_z],axis=1)

        factors_0=self.stabilizers[:,control_majorana_index_z]*numbers_of_mid
        factors_1=self.stabilizers[:,target_majorana_index_x]*numbers_of_mid
        factors_2=self.stabilizers[:,control_majorana_index_z]*self.stabilizers[:,target_majorana_index_x]
        factors_4=self.stabilizers[:,target_majorana_index_x]
        judge=factors_0+factors_1+factors_2+factors_4
        factors=[-1 if judge[temp]==1 else 1 for temp in range(len(self.stabilizers))]

        self.coffs=self.coffs*np.array(factors)

        ##  结果向量计算
        caches=self.stabilizers[:,control_majorana_index_z].copy()
        self.stabilizers[:,control_majorana_index_z]=self.stabilizers[:,target_majorana_index_x]
        self.stabilizers[:,target_majorana_index_x]=caches

    ##  SECTION：----执行pauli_index上的X-error----
    def error(self, p,error_pattern:str,index_0:int,index_1:int=None):
        """""
        input.pauli_index_0,pauli_index_1：目标量子位
        input.string_0,string_1：目标量子位的pauli字符串
        input.p：错误概率
        influence：以概率p在帧上施加一个X错误。
        """""
        if np.random.rand()<p:
            string_0=error_pattern[0]
            string_1=error_pattern[1]
            if string_0=='X':
                self.x(index_0)
            elif string_0=='Y':
                self.y(index_0)
            elif string_0=='Z':
                self.z(index_0)
            elif string_0=='U':
                self.u(index_0)
            elif string_0=='V':
                self.v(index_0)
            elif string_0=='N':
                self.n(index_0)
            else:
                raise ValueError(f"string_0={string_0} is not valid.")
            if string_1=='X':
                self.x(index_1)
            elif string_1=='Y':
                self.y(index_1)
            elif string_1=='Z':
                self.z(index_1)
            elif string_1=='U':
                self.u(index_1)
            elif string_1=='V':
                self.v(index_1)
            elif string_1=='N':
                self.n(index_1)
            elif string_1=='_':
                pass
            else:
                raise ValueError(f"string_0={string_0} or string_1={string_1} is not valid.")

    ##  SECTION：----将系统在pauli_index上重置为0态----
    def reset(self, pauli_index:int):
        """""
        input.pauli_index：目标量子位
        influence：将对应稳定子行设置为Z=+1
        """""

        ##  PART：----数据预处理----
        assert isinteger(pauli_index) and 0 <= pauli_index < self.pauli_number

        ##  PART：----处理过程----
        ##  重置0态
        vector_op=np.append(self.GF.Zeros(self.majorana_number*2), PauliOperator([],[pauli_index],1).get_vector(self.pauli_number))
        first_index=None
        for i in range(len(self.stabilizers)):
            pauli_commute=(np.dot(self.stabilizers[i][self.majorana_number*2::2], vector_op[self.majorana_number*2+1::2])+
                           np.dot(self.stabilizers[i][self.majorana_number*2+1::2], vector_op[self.majorana_number*2::2]))
            majorana_commute=(np.dot(self.stabilizers[i][0:self.majorana_number*2], vector_op[0:self.majorana_number*2])+
                              np.sum(vector_op[0:self.majorana_number*2])*np.sum(self.stabilizers[i][0:self.majorana_number*2]))

            if majorana_commute+pauli_commute==1 and first_index is None:
                first_index=i
            elif majorana_commute+pauli_commute==1 and first_index is not None:
                factor=majorana_factor(self.majorana_number,[self.stabilizers[i],self.stabilizers[first_index]])
                self.stabilizers[i]+=self.stabilizers[first_index]
                if np.mod(factor,2)==0:
                    factor=1
                else:
                    factor=-1
                self.coffs[i]=self.coffs[i]*self.coffs[first_index]*factor
            else:
                pass
        if first_index is not None:
            self.stabilizers[first_index]=vector_op
            self.coffs[first_index]=1
        else:
            solution=solve(self.stabilizers, vector_op)
            coff=np.prod([self.coffs[i] for i in range(len(self.stabilizers)) if solution[i]==1])
            vector_now, factor=majorana_factor(self.majorana_number,[self.stabilizers[i] for i in range(len(self.stabilizers)) if solution[i]==1])
            coff=coff*factor
            if coff==-1:
                self.x(pauli_index)

    ##  SECTION：----检测平台是否在op的本征空间，返回结果或本征值----
    def detect(self, op):

        ##  PART：----数据预处理----
        assert op.is_hermitian
        if isinstance(op, MajoranaOperator):
            vector_op=np.append(op.get_vector(self.majorana_number),self.GF.Zeros(self.pauli_number*2))
        else:
            vector_op=np.append(self.GF.Zeros(self.majorana_number*2),op.get_vector(self.pauli_number))

        solution=solve(self.stabilizers,vector_op)
        if solution is None:
            return None
        coff=np.prod([self.coffs[i] for i in range(len(self.stabilizers)) if solution[i]==1])
        vector_now, factor=majorana_factor(self.majorana_number,[vector_op]+[self.stabilizers[i] for i in range(len(self.stabilizers)) if solution[i]==1])
        coff=coff*factor
        if coff==op.coff:
            return 1
        else:
            return -1