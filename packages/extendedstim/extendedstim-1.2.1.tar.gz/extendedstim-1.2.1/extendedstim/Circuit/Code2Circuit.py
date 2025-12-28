"""""
将一个量子码转换为测试线路，计算它的physical error rate与logical error rate之间的关系
"""""
from extendedstim.Code.QuantumCode.MajoranaCode import MajoranaCode
from extendedstim.Circuit.Circuit import Circuit
from extendedstim.Code.QuantumCode.MajoranaCSSCode import MajoranaCSSCode
from extendedstim.Code.QuantumCode.PauliCSSCode import PauliCSSCode
from extendedstim.Code.QuantumCode.PauliCode import PauliCode
from extendedstim.Physics.MajoranaOperator import MajoranaOperator
from extendedstim.Physics.PauliOperator import PauliOperator
from extendedstim.tools.TypingTools import isinteger


# %%  CHAPTER：===将量子码转换为量子线路===
def Code2Circuit(code:MajoranaCode|PauliCode,noise_model:str,cycle_number:int):
    """""
    code：要转换的量子码
    p_noise：去极化噪声发生的几率
    p_measure：测量噪声发生的几率
    noise_model：噪声模型，可选值为'phenomenological'（现象级噪声）或'circuit-level'（电路级噪声）
    cycle_number：循环次数
    """""
    ##  SECTION：----数据预处理----
    assert isinteger(cycle_number) and cycle_number>=0
    assert isinstance(code,MajoranaCode) or isinstance(code,PauliCode)

    ##  SECTION：----根据量子码类型选择不同的处理函数----
    ##  处理现象级噪声
    if noise_model=='phenomenological':
        if isinstance(code,MajoranaCSSCode):
            return _MajoranaCSSCode2PhenomenologicalCircuit(code, cycle_number)
        elif isinstance(code,PauliCSSCode):
            return PauliCSSCode2PhenomenologicalCircuit(code,cycle_number)
        elif isinstance(code,MajoranaCode):
            raise NotImplementedError
        elif isinstance(code,PauliCode):
            raise NotImplementedError
        else:
            raise NotImplementedError

    ##  处理电路级噪声
    elif noise_model=='circuit-level':
        if isinstance(code,MajoranaCSSCode):
            return _MajoranaCSSCode2CircuitLevelCircuit(code, cycle_number)
        elif isinstance(code,PauliCSSCode):
            return _PauliCSSCode2CircuitLevelCircuit(code, cycle_number)
        elif isinstance(code,MajoranaCode):
            raise NotImplementedError
        elif isinstance(code,PauliCode):
            raise NotImplementedError
        else:
            raise NotImplementedError

    ##  其他类型抛出异常
    else:
        raise ValueError('noise_model must be phenomenological, circuit-level, or code-capacity')


#%%  CHAPTER：===将Majorana CSS code转换为现象级噪声下的测试线路===
def _MajoranaCSSCode2PhenomenologicalCircuit(code:MajoranaCSSCode, cycle_number:int)->Circuit:
    """""
    input.code：一个MajoranaCSSCode
    input.p_noise：去极化噪声发生的几率
    input.p_measure：测量结果出错的几率
    input.cycle_number：syndrome测量的次数
    """""

    ##  SECTION：----数据预处理----
    stabilizers_x=code.generators_x

    ##  这里我们检查N型稳定子，而不是Z型稳定子
    stabilizers_n=[]
    for i in range(len(code.generators_z)):
        stabilizers_n.append(code.generators_x[i]@code.generators_z[i])

    ##  我们检查逻辑N算符
    logical_x=code.logical_operators_x
    logical_z=code.logical_operators_z
    logical_occupy = [1j * logical_x[temp] @ logical_z[temp] for temp in range(len(logical_x))]  # 粒子数算符组作为逻辑算符组

    ##  计算数目
    majorana_number=code.physical_number  # fermionic sites的数目
    stabilizer_number = len(stabilizers_x) + len(stabilizers_n)  # 稳定子的数目

    ##  SECTION：----生成线路----
    ##  初始化
    circuit = Circuit()
    circuit.append({'name':'TICK'})
    circuit.append({'name':'TRAP','majorana_number':majorana_number,'pauli_number':0})
    circuit.append({'name':'TICK'})

    ##  测量逻辑算符
    observable_include= []  # 记录可观测量的索引
    for i,logical_operator in enumerate(logical_occupy):
        circuit.append({"name":"MPP","target":logical_operator})
        observable_include.append(len(circuit._measurements)-1)

    ##  记录N型测量稳定子的值
    for i,stabilizer in enumerate(stabilizers_n):
        circuit.append({"name":"MPP","target":stabilizer})

    ##  循环多轮，多轮测量错误与量子噪声信道
    for _ in range(cycle_number):

        ##  量子噪声信道
        for i in range(majorana_number):
            circuit.append({"name": "FDEPOLARIZE1", "target": i, "p": 0})

        ##  测量X型稳定子
        for i,stabilizer in enumerate(stabilizers_x):
            circuit.append({"name":"MPP","target":stabilizer,'p':0})

        ##  测量Z型稳定子
        for i,stabilizer in enumerate(stabilizers_n):
            circuit.append({"name":"MPP","target":stabilizer,'p':0})

        ##  添加探测器，区分第一轮的情况
        if _==0:
            for i in range(stabilizer_number//2):
                circuit.append({"name": "DETECTOR", "target": [i-stabilizer_number//2, i- stabilizer_number - stabilizer_number//2]})
        else:
            for i in range(stabilizer_number):
                circuit.append({"name":"DETECTOR","target":[i-stabilizer_number, i - 2*stabilizer_number]})

    ##  最后一轮测量稳定子横向测量
    for i in range(code.physical_number):
        circuit.append({"name":"MN","target":i,'p':0})

    ##  添加N型测量稳定子的探测器
    for i,stabilizer in enumerate(stabilizers_n):
        target=[]  # 确定检测的N测量与之前的测量
        stabilizer_now=MajoranaOperator([],[],1)  # 记录实际测量乘积对应的算符
        for index in stabilizer.occupy_x:
            target.append(-code.physical_number+index)
            stabilizer_now=stabilizer_now@MajoranaOperator([index],[index],1j)
        target.append(-code.physical_number - stabilizer_number // 2 + i)  # 添加之前的N测量
        if stabilizer_now.coff!=stabilizer.coff:
            target.append('negative')
        circuit.append({'name':'DETECTOR','target':target})

    ##  测量逻辑算符
    for i,logical_operator in enumerate(logical_occupy):
        circuit.append({"name":"MPP","target":logical_operator})
        circuit.append({"name":"OBSERVABLE_INCLUDE","target":[len(circuit._measurements)-1, observable_include[i]]})

    ##  ----返回线路----
    return circuit


#%%  CHAPTER：===将Majorana CSS code转换为线路级噪声下的测试线路===
def _MajoranaCSSCode2CircuitLevelCircuit(code:MajoranaCSSCode, cycle_number:int)->Circuit:
    """""
    input.code：一个MajoranaCSSCode
    input.p_noise：去极化噪声发生的几率
    input.p_measure：测量结果出错的几率
    input.cycle_number：syndrome测量的次数
    """""

    ##  SECTION：----数据预处理----
    ##  获取稳定子
    stabilizers_x=code.generators_x
    stabilizers_z=code.generators_z
    stabilizers_n=[]
    for i in range(len(code.generators_z)):
        stabilizers_n.append(code.generators_x[i]@code.generators_z[i])

    ##  获取逻辑算符
    logical_x=code.logical_operators_x
    logical_z=code.logical_operators_z
    logical_occupy=[1j*logical_x[temp]@logical_z[temp] for temp in range(len(logical_x))]  # 粒子数算符组作为逻辑算符组

    ##  获取数目
    majorana_number=code.physical_number
    stabilizer_number = len(stabilizers_x) + len(stabilizers_z)
    pauli_number=stabilizer_number

    ##  ----生成线路----
    ##  初始化
    circuit = Circuit()
    circuit.append({'name':'TRAP','majorana_number':majorana_number,'pauli_number':pauli_number})
    circuit.append({'name':'TICK'})

    ##  测量逻辑算符
    observable_include= []  # 记录可观测量的索引
    for i,logical_operator in enumerate(logical_occupy):
        circuit.append({"name":"MPP","target":logical_operator})
        observable_include.append(len(circuit._measurements)-1)

    ##  确定第一轮算符的值
    for i,stabilizer in enumerate(stabilizers_n):
        circuit.append({"name":"MPP","target":stabilizer})
    circuit.append({'name':'TICK'})

    ##  添加第一轮噪声
    for i in range(majorana_number):
        circuit.append({"name": "FDEPOLARIZE1", "target": i, "p":0})
    for i in range(pauli_number):
        circuit.append({"name": "DEPOLARIZE1", "target": i, "p": 0})
    circuit.append({'name':'TICK'})

    ##  循环多轮，多轮测量错误与量子噪声信道
    for _ in range(cycle_number):

        ##  添加稳定子测量
        for i,stabilizer in enumerate(stabilizers_x):
            sequence_temp=syndrome_majorana_css_measurement_circuit(stabilizer, i, 'x')
            for temp in sequence_temp:
                circuit.append(temp)
            circuit.append({'name':'TICK'})

        for i,stabilizer in enumerate(stabilizers_z):
            sequence_temp=syndrome_majorana_css_measurement_circuit(stabilizer, i + len(stabilizers_x), 'z')
            for temp in sequence_temp:
                circuit.append(temp)
            circuit.append({'name':'TICK'})

        ##  第一轮只添加N检测器
        if _==0:
            for i in range(stabilizer_number // 2):
                circuit.append({"name": "DETECTOR","target": [i - stabilizer_number ,i-stabilizer_number // 2, i - 3*stabilizer_number//2]})
        else:

            ##  添加X检测器
            for i in range(stabilizer_number//2):
                circuit.append({"name":"DETECTOR","target":[i-stabilizer_number, i - 2*stabilizer_number]})

            ##  添加N检测器
            for i in range(stabilizer_number // 2):
                circuit.append({"name": "DETECTOR","target": [i - stabilizer_number ,i-stabilizer_number//2, i - 3*stabilizer_number // 2,i-2*stabilizer_number]})

    ##  最后一轮测量稳定子横向测量
    for i in range(code.physical_number):
        circuit.append({"name":"MN","target":i,'p':0})

    for i,stabilizer in enumerate(stabilizers_n):
        target=[]
        stabilizer_now=MajoranaOperator([],[],1)
        for index in stabilizer.occupy_x:
            target.append(-code.physical_number+index)
            stabilizer_now=stabilizer_now@MajoranaOperator([index],[index],1j)
        target.append(-code.physical_number - stabilizer_number // 2 + i)
        target.append(-code.physical_number - stabilizer_number + i)
        if stabilizer_now.coff!=stabilizer.coff:
            target.append('negative')
        circuit.append({'name':'DETECTOR','target':target})

    ##  测量逻辑算符
    for i,logical_operator in enumerate(logical_occupy):
        circuit.append({"name":"MPP","target":logical_operator})
        circuit.append({"name":"OBSERVABLE_INCLUDE","target":[len(circuit._measurements)-1, observable_include[i]]})

    ##  ----返回线路----
    return circuit


#%%  CHAPTER：将Pauli CSS code转换为现象级噪声下的测试线路
def PauliCSSCode2PhenomenologicalCircuit(code:PauliCSSCode,cycle_number:int)->tuple[Circuit, Circuit]:
    """""
    input.code：一个PauliCSSCode
    input.p_noise：去极化噪声发生的几率
    input.p_measure：测量结果出错的几率
    input.cycle_number：syndrome测量的次数
    """""

    ##  ----数据预处理----
    ##  获取稳定子
    stabilizers_x=code.generators_x
    stabilizers_z=code.generators_z

    ##  获取逻辑算符
    logical_x=code.logical_operators_x
    logical_z=code.logical_operators_z

    ##  获取数目
    stabilizer_number=len(stabilizers_x)+len(stabilizers_z)
    pauli_number=code.physical_number

    ##  SECTION：----生成线路----
    ##  强制初始化
    circuit_x=Circuit()
    circuit_z=Circuit()
    circuit_x.append({'name': 'TRAP', 'majorana_number':0,'pauli_number':pauli_number})
    circuit_x.append({'name': 'H', 'majorana_number':0,'pauli_number':pauli_number})
    circuit_z.append({'name': 'TRAP', 'majorana_number':0,'pauli_number':pauli_number})

    ##  循环多轮，多轮测量错误与量子噪声信道
    for _ in range(cycle_number):

        ##  量子噪声信道
        for i in range(pauli_number):
            circuit_x.append({"name":"DEPOLARIZE1","target":i,"p":0})
            circuit_z.append({"name":"DEPOLARIZE1","target":i,"p":0})

        ##  测量稳定子
        for i, stabilizer in enumerate(stabilizers_x):
            circuit_x.append({"name": "MPP", "target": stabilizer,'p':0})
            circuit_z.append({"name": "MPP", "target": stabilizer,'p':0})
        for i, stabilizer in enumerate(stabilizers_z):
            circuit_z.append({"name": "MPP", "target": stabilizer,'p':0})
            circuit_x.append({"name": "MPP", "target": stabilizer,'p':0})

        ##  区分第一轮和其他轮
        if _==0:
            for i in range(stabilizer_number//2):
                circuit_z.append({"name": "DETECTOR", "target": [-stabilizer_number//2+i]})
                circuit_x.append({"name": "DETECTOR", "target": [-stabilizer_number+i]})
        else:
            ##  添加检测器
            for i in range(stabilizer_number):
                circuit_z.append({"name": "DETECTOR", "target": [-i-1, -i-stabilizer_number-1]})
                circuit_x.append({"name": "DETECTOR", "target": [-i-1, -i-stabilizer_number-1]})

    ##  最后一轮测量稳定子横向测量
    for i in range(code.physical_number):
        circuit_x.append({"name": "MPP", "target": PauliOperator([i], [],1),'p':0})
        circuit_z.append({"name": "MPP", "target": PauliOperator([], [i],1),'p':0})

    for i, stabilizer in enumerate(stabilizers_x):
        target=[]
        for index in stabilizer.occupy_x:
            target.append(-code.physical_number+index)
        target.append(-code.physical_number-stabilizer_number+i)
        circuit_x.append({'name': 'DETECTOR', 'target': target})

    for i, stabilizer in enumerate(stabilizers_z):
        target=[]
        for index in stabilizer.occupy_z:
            target.append(-code.physical_number+index)
        target.append(-code.physical_number-stabilizer_number//2+i)

        circuit_z.append({'name': 'DETECTOR', 'target': target})

    ##  测量逻辑算符
    for i in range(len(logical_x)):
        circuit_z.append({"name": "MPP", "target": logical_z[i]})
        circuit_x.append({"name": "MPP", "target": logical_x[i]})
        circuit_z.append({"name": "OBSERVABLE_INCLUDE", "target": [len(circuit_z._measurements)-1]})
        circuit_x.append({"name": "OBSERVABLE_INCLUDE", "target": [len(circuit_x._measurements)-1]})

    ##  SECTION：----返回线路----
    return circuit_x, circuit_z


#%%  CHAPTER：将Pauli CSS code转换为电路级噪声下的测试线路
def _PauliCSSCode2CircuitLevelCircuit(code:PauliCSSCode, cycle_number:int)->tuple[Circuit,Circuit]:
    """""
    input.code：一个PauliCSSCode
    input.p_noise：去极化噪声发生的几率
    input.p_measure：测量结果出错的几率
    input.cycle_number：syndrome测量的次数
    """""

    ##  SECTION：----数据预处理----
    ##  获取稳定子
    stabilizers_x=code.generators_x
    stabilizers_z=code.generators_z

    ##  获取逻辑算符
    logical_x=code.logical_operators_x
    logical_z=code.logical_operators_z

    ##  获取数目
    stabilizer_number = len(stabilizers_x) + len(stabilizers_z)
    data_number=code.physical_number
    pauli_number=data_number+stabilizer_number

    ##  SECTION：----生成线路----
    ##  强制初始化
    circuit_x = Circuit()
    circuit_z = Circuit()
    circuit_x.append({'name': 'TRAP', 'majorana_number':0,'pauli_number':pauli_number})
    circuit_z.append({'name': 'TRAP', 'majorana_number':0,'pauli_number':pauli_number})
    circuit_z.append({'name':'TICK'})
    circuit_x.append({'name':'TICK'})
    circuit_x.append({'name':'H', 'target': list(range(data_number))})

    ##  施加第一轮噪声
    for i in range(pauli_number):
        circuit_z.append({"name": "DEPOLARIZE1", "target": i, "p": 0})
        circuit_x.append({"name": "DEPOLARIZE1", "target": i, "p": 0})

    circuit_z.append({'name':'TICK'})
    circuit_x.append({'name':'TICK'})

    ##  循环多轮，多轮测量错误与量子噪声信道
    for _ in range(cycle_number):

        ##  测量稳定子
        for i, stabilizer in enumerate(stabilizers_x):
            sequence_temp = syndrome_pauli_css_measurement_circuit(stabilizer, i + data_number, 'x')
            for temp in sequence_temp:
                circuit_z.append(temp)
                circuit_x.append(temp)
            circuit_z.append({'name':'TICK'})
            circuit_x.append({'name':'TICK'})
        for i, stabilizer in enumerate(stabilizers_z):
            sequence_temp = syndrome_pauli_css_measurement_circuit(stabilizer, i + data_number + len(stabilizers_x), 'z')
            for temp in sequence_temp:
                circuit_z.append(temp)
                circuit_x.append(temp)
            circuit_z.append({'name':'TICK'})
            circuit_x.append({'name':'TICK'})
        ##  添加检测器
        if _==0:
            for i in range(stabilizer_number//2):
                circuit_z.append({"name": "DETECTOR", "target": [-stabilizer_number//2 +i]})
                circuit_x.append({"name": "DETECTOR", "target": [-stabilizer_number +i]})
        else:
            for i in range(stabilizer_number):
                circuit_z.append({"name": "DETECTOR", "target": [-i - 1, -i - stabilizer_number - 1]})
                circuit_x.append({"name": "DETECTOR", "target": [-i - 1, -i - stabilizer_number - 1]})

    ##  最后一轮测量稳定子横向测量
    for i in range(code.physical_number):
        circuit_x.append({"name": "MPP", "target": PauliOperator([i], [], 1),'p':0})
        circuit_z.append({"name": "MPP", "target": PauliOperator([], [i], 1),'p':0})

    for i, stabilizer in enumerate(stabilizers_x):
        target=[]
        for index in stabilizer.occupy_x:
            target.append(-code.physical_number+index)
        target.append(-code.physical_number-stabilizer_number+i)

        circuit_x.append({'name': 'DETECTOR', 'target': target})

    for i, stabilizer in enumerate(stabilizers_z):
        target=[]
        for index in stabilizer.occupy_z:
            target.append(-code.physical_number+index)
        target.append(-code.physical_number-stabilizer_number//2+i)

        circuit_z.append({'name': 'DETECTOR', 'target': target})

    ##  测量逻辑算符
    for i in range(len(logical_x)):
        circuit_z.append({"name": "MPP", "target": logical_z[i]})
        circuit_x.append({"name": "MPP", "target": logical_x[i]})
        circuit_z.append({"name": "OBSERVABLE_INCLUDE", "target": [len(circuit_z._measurements)-1]})
        circuit_x.append({"name": "OBSERVABLE_INCLUDE", "target": [len(circuit_x._measurements)-1]})

    ##  ----返回线路----
    return circuit_x, circuit_z


# %%  CHAPTER：===生成Majorana CSS stabilizer测量线路===
def syndrome_majorana_css_measurement_circuit(stabilizer:MajoranaOperator, qubit_index:int, type:str)->list[dict]:
    """""
    input.stabilizer：一个MajoranaOperator，代表stabilizer
    input.qubit_index：一个整数，代表测量的qubit索引
    input.type：一个字符串，代表测量的类型，只能是'x'或'X'或'z'或'Z'
    input.p_noise：去极化噪声发生的几率
    input.p_measure：测量结果出错的几率
    """""

    ##  ———数据预处理———
    sequence = []  # 线路序列
    flag = True  # 门类型标志

    ##  判断稳定子类型
    if type == 'x' or type == 'X':
        occupy=stabilizer.occupy_x
    elif type == 'z' or type == 'Z':
        occupy=stabilizer.occupy_z
    else:
        raise ValueError

    ##  ----生成线路----
    ##  将qubit置于负号匹配
    sequence.append({'name': 'X', 'target': qubit_index})
    sequence.append({'name': 'DEPOLARIZE1', 'target': qubit_index, 'p': 0})

    ##  生成前一半线路
    for j in range(len(occupy)):
        majorana_index_now = occupy[j]

        ##  最后一位与qubit作用CNX gate
        if j == len(occupy) - 1:
            sequence.append({'name': 'CNX', 'target': [majorana_index_now, qubit_index], })
            sequence.append({'name': 'MIXTURE', 'target': [majorana_index_now, qubit_index], 'p': 0})
            break

        majorana_index_down = occupy[j + 1]  # 后一个fermionic site

        ##  作用braid gate
        if flag:
            ##  根据稳定子类型选择braid形式
            if type == 'X' or type == 'x':
                order_target = [majorana_index_down, majorana_index_now]
            elif type == 'Z' or type == 'z':
                order_target = [majorana_index_now, majorana_index_down]
            else:
                raise ValueError

            ##  添加braid gate
            sequence.append({"name": "BRAID", "target": order_target, })
            sequence.append({'name': 'FDEPOLARIZE2', 'target': order_target, 'p': 0})
            flag = False

        ##  作用CNN gate
        else:
            sequence.append({'name': 'CNN', 'target': [majorana_index_now, majorana_index_down], })
            sequence.append({'name': 'FDEPOLARIZE2', 'target': [majorana_index_now, majorana_index_down], 'p':0})
            flag = True

    ##  生成syndrome extraction circuit的另一半
    flag = True
    for j in range(len(occupy) - 1):
        majorana_index_now = occupy[-1 - j]  # 当前的fermionic site
        majorana_index_up = occupy[-1 - j - 1]  # 上一个fermionic site

        ##  作用braid gate
        if flag:
            if type == 'X' or type == 'x':
                order_target = [majorana_index_now, majorana_index_up]
            elif type == 'Z' or type == 'z':
                order_target = [majorana_index_up, majorana_index_now]
            else:
                raise ValueError
            sequence.append({'name': 'N', 'target': [majorana_index_now]})
            sequence.append({'name': 'BRAID', 'target': order_target})
            sequence.append({'name': 'N', 'target': [majorana_index_now]})
            sequence.append({'name': 'FDEPOLARIZE2', 'target': order_target, 'p': 0})
            flag = False

        ##  作用CNN gate
        else:
            sequence.append({'name': 'CNN', 'target': [majorana_index_now, majorana_index_up]})
            sequence.append({'name': 'FDEPOLARIZE2', 'target': [majorana_index_now, majorana_index_up], 'p': 0})
            flag = True

    ##  在qubit上测量结果并重置
    sequence.append({'name': 'MZ', 'target': qubit_index, 'p':0})
    sequence.append({'name': 'R', 'target': qubit_index})
    sequence.append({'name': 'DEPOLARIZE1', 'target': qubit_index, 'p': 0})

    ##  ——-—返回线路序列———-
    return sequence


# %%  CHAPTER：===生成Pauli CSS stabilizer测量线路===
def syndrome_pauli_css_measurement_circuit(stabilizer:PauliOperator, qubit_index:int, type:str)->list[dict]:
    """""
    input.stabilizer：一个PauliOperator，代表stabilizer
    input.qubit_index：一个整数，代表测量的qubit索引
    input.type：一个字符串，代表测量的类型，只能是'x'或'X'或'z'或'Z'
    input.p_noise：去极化噪声发生的几率
    input.p_measure：测量结果出错的几率
    """""

    ##  ———数据预处理———
    sequence = []  # 线路序列

    ##  判断稳定子类型
    if type == 'x' or type == 'X':
        occupy=stabilizer.occupy_x
    elif type == 'z' or type == 'Z':
        occupy=stabilizer.occupy_z
    else:
        raise ValueError

    ##  ----生成纠缠线路----
    if type=='X' or type == 'x':
        sequence.append({'name': 'H', 'target': qubit_index})
        sequence.append({'name': 'DEPOLARIZE1', 'target': qubit_index, 'p':0})
    for j in range(len(occupy)):
        if type == 'Z' or type == 'z':
            sequence.append({'name': 'CX', 'target': [occupy[j], qubit_index]})
            sequence.append({'name': 'DEPOLARIZE2', 'target': [occupy[j], qubit_index], 'p': 0})
        elif type == 'X' or type == 'x':
            sequence.append({'name': 'CX', 'target': [qubit_index,occupy[j]]})
            sequence.append({'name': 'DEPOLARIZE2', 'target': [occupy[j],qubit_index], 'p': 0})
        else:
            raise ValueError
    if type=='X' or type == 'x':
        sequence.append({'name': 'H', 'target': qubit_index})
        sequence.append({'name': 'DEPOLARIZE1', 'target': qubit_index, 'p': 0})

    ##  在qubit上测量结果并重置
    sequence.append({'name': 'MZ', 'target': qubit_index, 'p':0})
    sequence.append({'name': 'R', 'target': qubit_index})
    sequence.append({'name': 'DEPOLARIZE1', 'target': qubit_index, 'p': 0})

    ##  ———返回线路序列———
    return sequence
