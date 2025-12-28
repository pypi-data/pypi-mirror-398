import stim
from extendedstim.Circuit.Circuit import Circuit
from extendedstim.Physics.PauliOperator import PauliOperator


def stim_circuit(circuit_origin: Circuit)->stim.Circuit:
    circuit=stim.Circuit()
    flag_measure=0
    for i in range(len(circuit_origin.sequence)):
        gate=circuit_origin.sequence[i]
        name=gate['name']
        if name=='X' or name=='Y' or name=='Z' or name=='H' or name=='S' or name=='P':
            circuit.append(name, [gate['target']])

        ##  添加single-qubit上的噪声
        elif name=='X_ERROR' or name=='Y_ERROR' or name=='Z_ERROR':
            circuit.append(name, [gate['target']], gate['p'])

        ##  添加single-fermionic-site gate
        elif name in ['U', 'V', 'N', 'P', 'U_ERROR', 'V_ERROR', 'N_ERROR', 'CNX', 'CNN', 'B', 'braid', 'MN', 'FDEPOLARIZE1', 'FR']:
            raise NotImplementedError('stim只支持pauli circuit')

        ##  添加受控非门
        elif name=='CX':
            target=gate['target']
            circuit.append(name, target)

        ##  添加qubit上的去极化噪声
        elif name=='DEPOLARIZE1':
            target=gate['target']
            circuit.append(name, target, gate['p'])

        ##  强制初始化
        elif name=='TRAP':
            circuit.append('R',range(circuit_origin.pauli_number))

        ##  添加string算符的测量
        elif name=='MPP':

            ##  求string算符格式化表示
            op: PauliOperator=gate['target']
            occupy_x=op.occupy_x
            occupy_z=op.occupy_z

            ##  简单测量
            if len(occupy_x)==0 and len(occupy_z)==1:
                if 'p' in gate:
                    circuit.append('MZ', [occupy_z[0]], gate['p'])
                else:
                    circuit.append('MZ', [occupy_z[0]])
                continue
            elif len(occupy_x)==1 and len(occupy_z)==0:
                if 'p' in gate:
                    circuit.append('MX', [occupy_x[0]], gate['p'])
                else:
                    circuit.append('MX', [occupy_x[0]])
                continue
            elif len(occupy_x)==1 and len(occupy_z)==1 and occupy_x[0]==occupy_z[0]:
                if 'p' in gate:
                    circuit.append('MY', [occupy_z[0]], gate['p'])
                else:
                    circuit.append('MY', [occupy_z[0]])
                continue

            ##  string operator测量
            op_str=''
            for j in range(circuit_origin.pauli_number):
                if j in occupy_x and j in occupy_z:
                    op_str+='Y'
                elif j in occupy_z:
                    op_str+='Z'
                elif j in occupy_x:
                    op_str+='X'
                else:
                    op_str+='_'
            if 'p' in gate:
                circuit.append('MPP', [stim.PauliString(op_str)], gate['p'])
            else:
                circuit.append('MPP', [stim.PauliString(op_str)])

        ##  添加qubit重置
        elif name=='R':
            circuit.append('R', [gate['target']])

        ##  检测器
        elif name=='DETECTOR':
            circuit.append(name, [stim.target_rec(temp) for temp in gate['target']])

        ##  添加可观测量
        elif name=='OBSERVABLE_INCLUDE':
            circuit.append(name, [stim.target_rec(temp) for temp in gate['target']], flag_measure)
            flag_measure+=1
        elif name=='TICK':
            pass
        else:
            raise NotImplementedError
    return circuit