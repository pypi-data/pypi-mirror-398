"""""
模块作用：量子电路，提供构造、执行、解码和逻辑错误率分析等一站式服务
"""""
import copy
import multiprocessing
import os
import time
from multiprocessing import Pool, cpu_count, Value
import pymatching
import qiskit
import numpy as np
import stim
import stimbposd
from qiskit.circuit import CircuitError
from qiskit.circuit.library import XGate, ZGate
from extendedstim.Physics.MajoranaOperator import MajoranaOperator
from extendedstim.Physics.PauliOperator import PauliOperator
from extendedstim.Platform.Frame import Frame
from extendedstim.Platform.Platform import Platform
from extendedstim.tools.GaloisTools import diff
from extendedstim.tools.TypingTools import isinteger, islist

sample_number_now = Value('i', 0)
error_number_now = Value('i', 0)

#%%  APPENDIX：===尝试导入Tesseract类===
##  导入尝试
try:
    from tesseract_decoder import tesseract
    import tesseract_decoder

##  无法导入的情况下用BP-OSD替代
except ImportError:
    #print("Tesseract decoder not found")
    # noinspection PyPep8Naming
    class tesseract:
        def __init__(self):
            pass

        # noinspection PyUnusedLocal
        @staticmethod
        def TesseractConfig(dem, pqlimit,det_orders, det_beam=50,beam_climbing=False,no_revisit_dets=True):
            return Config(dem, det_beam)

    class Config:
        def __init__(self, dem: stim.DetectorErrorModel, det_beam):
            self.dem=dem
            self.det_beam=det_beam

        def compile_decoder(self):
            return stimbposd.bp_osd.BPOSD(model=self.dem, bp_method='min_sum', max_bp_iters=self.det_beam)


class Circuit:
    __slots__=['majorana_number', 'pauli_number', 'sequence', 'ideal_sequence',
               '_sequence', '_noises', '_measurements', '_detectors', '_observables', '_prototype', '_reference_measurements', '_alert']

    #%%  CHAPTER：===构造方法===
    def __init__(self):
        """""
        通过circuit=Circuit()来构造一个空的量子电路
        通过circuit.append({'name': 'TRAP','majorana_number':10,'pauli_number':10})来指定初始的qubits and fermionic sites数目
        通过circuit.append({'name': 'X','target':0})等语句来添加gates，具体参考append方法
        """""

        ##  公有属性
        self.majorana_number=0  # fermionic sites的数目
        self.pauli_number=0  # qubits的数目
        self.sequence=[]  # 量子线路的操作序列
        self.ideal_sequence=[]  # 理想量子线路的操作序列

        ##  私有属性
        self._sequence:list[dict]=[]  # 记录量子线路的操作序列在真实计算使用
        self._noises=[]  # 记录noise在_sequence中的索引
        self._measurements=[]  # 记录measurement在_sequence中的索引
        self._detectors=[]  # 记录detector在_measurements中的索引
        self._observables=[]  # 记录observable在_measurements中的索引
        self._prototype=None  # 量子线路的detector error model的原型，probability可以修改
        self._reference_measurements=None  # 量子线路的参考测量结果，用于后续sample
        self._alert=False  # 记录是否有alert，用于禁用append方法

    #%%  CHAPTER：===重载运算符===
    ##  SECTION：---获取序列中的元素---
    def __getitem__(self, item: int) -> dict:
        return self.sequence[item]

    #%%  CHAPTER：===属性方法===
    ##  SECTION：----获取参考样本----
    @property
    def _reference_sample(self)->np.ndarray:
        if self._reference_measurements is None:

            ##  PART：----初始化程序----
            platform=Platform()  # 生成量子平台
            measurement_sample=np.empty(len(self._measurements), dtype=int)  # 生成测量值的样本数组
            flag_measurement=0

            ##  PART：----遍历整个操作序列----
            for i, gate in enumerate(self._sequence):
                name=gate['name']
                if name in ['X', 'Y', 'Z', 'H', 'S', 'U', 'V', 'N']:  # 执行单门
                    eval('platform.'+name.lower()+'(gate[\'target\'])')
                elif name in ['CX', 'CNX', 'BRAID', 'CNN']:  # 执行双门
                    eval('platform.'+name.lower()+'(gate[\'target\'][0],gate[\'target\'][1])')
                elif name=='R':  # 执行重置
                    platform.reset(gate['target'])
                elif name=='MPP':  # 执行测量
                    measurement_sample[flag_measurement]=platform.measure(gate['target'])
                    flag_measurement+=1
                elif name=='TRAP':  # 初始化一定数目的qubits和fermionic sites
                    platform.trap(self.majorana_number,self.pauli_number)
            self._reference_measurements=measurement_sample

        ##  PART：----返回可观测的结果----
        return self._reference_measurements

    ##  SECTION：----获取detector error model的原型----
    @property
    def _detector_error_prototype(self)->list[list]:
        if self._prototype is None:

            ##  PART：----预处理----
            ##  计算无噪声值
            measurement_sample_origin=self._reference_sample
            detector_sample_origin=diff(measurement_sample_origin, self._detectors)
            observable_sample_origin=diff(measurement_sample_origin, self._observables)

            ##  执行检验线路的稳定性
            for _ in range(10):
                measurement_sample, detector_sample, observable_sample=self.sample(noiseless=True)
                assert np.all(detector_sample==detector_sample_origin), f'原始线路的detector不是稳定的'
                assert np.all(observable_sample==observable_sample_origin), f'原始线路的observable不是稳定的'

            ##  PART：----并行采样，分析每一个noise对detectors and observables的影响----
            group_number=cpu_count()//2  # 分组数量
            sample_number=len(self._noises)//group_number  # 每个分组的噪声数量
            noise_group=[self._noises[temp*sample_number:(temp+1)*sample_number] for temp in range(group_number)]  # 噪声组合的列表
            if len(self._noises[group_number*sample_number:])>0:  # 处理最后一组噪声
                noise_group.append(self._noises[group_number*sample_number:])

            ##  计算每一个noise发生，其他noise不发生时的detector和observable
            with Pool(processes=len(noise_group)) as pool:
                results=[pool.apply_async(self._sample_batch, args=(noise_group[i],)) for i in range(len(noise_group))]
                final_results=[result.get() for result in results]

            ##  PART：----分析每一个noise对detectors and observables的影响----
            flag=0  # 记录当前noise的序号
            _dem_str_list=[]  # 初始化原型
            for i in range(len(final_results)):
                for j in range(len(final_results[i])):

                    measurement_sample, detector_sample, observable_sample=final_results[i][j]

                    ##  找到触发的detector和observable
                    detector_sample_diff=[detector_sample_origin[j]^detector_sample[j] for j in range(len(detector_sample))]
                    observable_sample_diff=[observable_sample_origin[j]^observable_sample[j] for j in range(len(observable_sample))]

                    ##  记录触发的detector和observable的位置
                    detectors_trigger=np.where(np.array(detector_sample_diff)==True)[0]
                    observables_trigger=np.where(np.array(observable_sample_diff)==True)[0]

                    ##  合成错误语句
                    if len(detectors_trigger)>0 or len(observables_trigger)>0:
                        temp_error=f'error({self._sequence[self._noises[flag]]['p']}) '
                        temp_trigger=''
                        for index in detectors_trigger:
                            temp_trigger=temp_trigger+f' D{index}'
                        for index in observables_trigger:
                            temp_trigger=temp_trigger+f' L{index}'
                        if self._sequence[self._noises[flag]]['name']=='M_ERROR':
                            _dem_str_list.append([temp_error, temp_trigger, 'M_ERROR'])
                        elif 'type' not in self._sequence[self._noises[flag]]:
                            _dem_str_list.append([temp_error, temp_trigger, 'ONE_ERROR'])
                        elif self._sequence[self._noises[flag]]['type']=='DEP1':
                            _dem_str_list.append([temp_error, temp_trigger, 'DEP1'])
                        elif self._sequence[self._noises[flag]]['type']=='DEP2':
                            _dem_str_list.append([temp_error, temp_trigger, 'DEP2'])
                        else:
                            raise NotImplementedError(f'未实现的错误类型：{self._sequence[self._noises[flag]]['name']['type']}')
                        flag+=1

            ##  赋值
            self._prototype=_dem_str_list

        ##  ----返回检测错误模型的原型----
        return self._prototype

    ##  SECTION：----生成一定错误率的检测错误模型----
    def detector_error_model(self,p_noise:int|float,p_measure:int|float) -> stim.DetectorErrorModel:
        dem_str=''
        ##  合并同类项
        dem_temp=[]
        for i, temp in enumerate(self._detector_error_prototype):
            if temp[2]=='DEP1':
                p_temp=(1-np.sqrt(1-4*p_noise/3))/2
            elif temp[2]=='DEP2':
                p_temp=(1/2)*(1 - (1 - 16 * p_noise / 15)**(1/8))
            elif temp[2]=='ONE_ERROR':
                p_temp=p_noise
            elif temp[2]=='M_ERROR':
                p_temp=p_measure
            else:
                raise ValueError
            flag=True
            for j, item in enumerate(dem_temp):
                if temp[1]==item[1]:
                    item[0]=p_temp*(1-item[0])+(1-p_temp)*item[0]
                    flag=False
                    break
            if flag:
                dem_temp.append([p_temp,temp[1]])

        ##  生成检测错误模型
        for temp in dem_temp:
            dem_str+=('\n'+f'error({temp[0]})'+temp[1])
        return stim.DetectorErrorModel(dem_str)

    #%%  CHAPTER：===对象方法===
    ##  SECTION：----添加量子线路组分操作----
    def append(self, params):
        """""
        {
        'name': str，线路操作的名称
        'target': list or int，操作作用的对象
        'p': float，操作对应的概率，不一定有
        'pauli_number': int，强制初始化的qubits数目
        'majorana_number': int，强制初始化的fermionic sites数目
        }
        支持的线路操作名称：
        'X', 'Y', 'Z', 'H', 'S'：{'name':str,'target':int or list}, single qubit上的qugate
        'X_ERROR', 'Y_ERROR', 'Z_ERROR', 'DEPOLARIZE1': {'name':str,'target':int or list}, single qubit上的噪声
        'XX_ERROR', 'XY_ERROR', ... , 'DEPOLARIZE2' {'name':str,'target':list}, two qubits上的噪声
        'U', 'V', 'N', 'P'：{'name':str,'target':int or list}, single fermionic site上的fgate
        'U_ERROR', 'V_ERROR', 'N_ERROR', 'FDEPOLARIZE1': {'name':str,'target':int or list}, single fermionic site上的噪声
        'UU_ERROR', 'UV_ERROR', ... , 'FDEPOLARIZE2': {'name':str,'target':int or list}, two fermionic sites上的噪声
        'CX', 'CNX', 'CNN', 'BRAID': {'name':str,'target':list}, two qubit or fermionic sites上的gates
        'R': {'name':str,'target':int or list}, single qubit or single fermionic sites上的重置到空态或0态
        'MZ', 'MN': {'name':str,'target':int or list}, single qubit or single fermionic sites上的measurement
        'MPP': {'name':str,'target':list or Operator}, Pauli string operators or Majorana string operators的measurement
        'TRAP'：{'name':str,'pauli_number':int,'majorana_number':int}, 强制初始化到空态和0态
        'DETECTOR': {'name':str,'target':list of int}，探测器
        'OBSERVABLE_INCLUDE': {'name':str,'target':list of int}，可观测量
        """""

        ##  PART：----数据预处理----
        assert isinstance(params, dict)
        assert not self._alert
        assert 'name' in params
        name=params["name"]  # 线路操作的名称

        ##  PART：----添加single-body gate----
        if name in ['X', 'Y', 'Z', 'H', 'S', 'X_ERROR', 'Y_ERROR', 'Z_ERROR', 'U', 'V', 'N', 'P', 'U_ERROR', 'V_ERROR', 'N_ERROR']:

            ##  作用在整数index对应目标上
            if isinteger(params['target']):
                self._sequence.append(params.copy())
                self.sequence.append(self._sequence[-1])
                self.ideal_sequence.append(self._sequence[-1])

            ##  作用在一系列目标上
            elif islist(params['target']):
                for temp in params['target']:
                    params_temp={'name': name, 'target': temp}
                    self.append(params_temp)

        ##  PART：----添加two-body gate----
        elif name in ['CX', 'CNX', 'CNN',
                      'XX_ERROR','XY_ERROR','XZ_ERROR','YX_ERROR','YY_ERROR','YZ_ERROR','ZX_ERROR','ZY_ERROR','ZZ_ERROR',
                      'UU_ERROR','UV_ERROR','UN_ERROR','VU_ERROR','VV_ERROR','VN_ERROR','NU_ERROR','NV_ERROR','NN_ERROR',
                      'UX_ERROR','UY_ERROR','UZ_ERROR','VX_ERROR','VY_ERROR','VZ_ERROR','NX_ERROR','NY_ERROR','NZ_ERROR',]:

            ##  添加单个two gate
            if islist(params['target']) and len(params['target'])==2 and isinteger(params['target'][0]) and isinteger(params['target'][1]):
                self._sequence.append(params.copy())
                self.sequence.append(self._sequence[-1])
                self.ideal_sequence.append(self._sequence[-1])

            ##  用单个列表添加多个two gates
            elif islist(params['target']) and isinteger(params['target'][0]):
                for i in range(len(params['target'])//2):
                    params_temp={'name': name, 'target': [params['target'][2*i], params['target'][2*i+1]]}
                    self.append(params_temp)

            ##  用多个列表添加多个two gates
            elif islist(params['target']):
                for temp in params['target']:
                    self.append({'name': name, 'target': temp})

            ##  其他情况抛出异常
            else:
                raise ValueError("Gate must be applied to two")

        ##  PART：----添加braid gate----
        elif name=='BRAID' or name=='braid':

            if islist(params['target']) and len(params['target'])==2 and isinteger(params['target'][0]) and isinteger(params['target'][1]):
                x=params['target'][0]  # 控制位
                y=params['target'][1]  # 目标位

                ##  控制位等于目标位时，根据verse参数判断是否添加N门
                if x==y and 'verse' not in params:
                    self._sequence.append({'name': 'P', 'target': x})
                    self.sequence.append(self._sequence[-1])
                    self.ideal_sequence.append(self._sequence[-1])
                elif x==y and 'verse' in params and params['verse']==True:
                    self._sequence.append({'name': 'P', 'target': y})
                    self.sequence.append(self._sequence[-1])
                    self.ideal_sequence.append(self._sequence[-1])
                    self._sequence.append({'name': 'N', 'target': y})
                    self.sequence.append(self._sequence[-1])
                    self.ideal_sequence.append(self._sequence[-1])

                ##  一般情况下braid gate作用在两个不同的fermionic sites上
                elif x!=y:
                    self._sequence.append({'name': 'BRAID', 'target': [x, y]})
                    self.sequence.append(self._sequence[-1])
                    self.ideal_sequence.append(self._sequence[-1])

            ##  用单个列表添加多个two gates
            elif islist(params['target']) and isinteger(params['target'][0]):
                for i in range(len(params['target'])//2):
                    params_temp={'name': name, 'target': [params['target'][2*i], params['target'][2*i+1]]}
                    self.append(params_temp)

            ##  用多个列表添加多个two gates
            elif islist(params['target']):
                for temp in params['target']:
                    self.append({'name': name, 'target': temp})

            ##  其他情况抛出异常
            else:
                raise ValueError("CX, CNX, CNN gate must be applied to two")

        ##  PART：----添加single-qubit depolarization----
        elif name=='DEPOLARIZE1':
            assert 'p' in params

            ##  作用在整数index对应目标上
            if isinteger(params['target']):
                self.sequence.append({'name': 'DEPOLARIZE1', 'target': params['target'], 'p': params['p']})
                fix=(1-np.sqrt(1-4*params["p"]/3))/2
                self._sequence.append({'name': 'X_ERROR', 'target': params["target"], 'p': fix,'type':'DEP1'})
                self._noises.append(len(self._sequence)-1)
                self._sequence.append({'name': 'Y_ERROR', 'target': params["target"], 'p': fix,'type':'DEP1'})
                self._noises.append(len(self._sequence)-1)
                self._sequence.append({'name': 'Z_ERROR', 'target': params["target"], 'p': fix,'type':'DEP1'})
                self._noises.append(len(self._sequence)-1)

            ##  作用在一系列目标上
            elif islist(params['target']):
                for temp in params['target']:
                    self.append({'name': params['name'], 'target': temp, 'p': params["p"]})

        ##  PART：----添加two-qubit depolarization----
        elif name=='DEPOLARIZE2':
            assert 'p' in params

            ##  用单个列表添加单个
            if islist(params['target']) and isinteger(params['target'][0]) and isinteger(params['target'][1]) and len (params['target'])==2:
                self.sequence.append({'name': 'DEPOLARIZE2', 'target': params['target'], 'p': params['p'],'type':'DEP2'})
                fix =(1/2)*(1 - (1 - 16 * params["p"] / 15)**(1/8))
                for case in ['X_ERROR', 'Y_ERROR', 'Z_ERROR']:
                    self._sequence.append({'name': case, 'target': params["target"][0], 'p': fix,'type':'DEP2'})
                    self._noises.append(len(self._sequence) - 1)
                for case in ['X_ERROR', 'Y_ERROR', 'Z_ERROR']:
                    self._sequence.append({'name': case, 'target': params["target"][1], 'p': fix,'type':'DEP2'})
                    self._noises.append(len(self._sequence) - 1)
                for case in ['XX_ERROR', 'XY_ERROR', 'XZ_ERROR','YX_ERROR','YY_ERROR','YZ_ERROR','ZX_ERROR','ZY_ERROR','ZZ_ERROR']:
                    self._sequence.append({'name': case, 'target': params["target"], 'p': fix,'type':'DEP2'})
                    self._noises.append(len(self._sequence) - 1)

            ##  用单个列表添加多个
            elif islist(params['target']) and isinteger(params['target'][0]) and len(params['target'])>2:
                for i in range(len(params['target'])//2):
                    self.append({'name': name, 'target':[params['target'][2*i], params['target'][2*i+1]], 'p': params['p']})

            ##  用多个列表添加多个
            elif islist(params['target']) and islist(params['target'][0]) and isinteger(params['target'][0][0]):
                for temp in params['target']:
                    self.append({'name': params['name'], 'target': temp, 'p': params["p"]})

            ##  其他情况抛出异常
            else:
                raise ValueError("Gate must be applied to two")

        ##  PART：----添加single-site depolarization----
        elif name=='FDEPOLARIZE1':
            assert 'p' in params

            ##  作用在整数index对应目标上
            if isinteger(params['target']):
                self.sequence.append({'name': 'FDEPOLARIZE1', 'target': params['target'], 'p': params['p']})
                fix=(1-np.sqrt(1-4*params["p"]/3))/2
                self._sequence.append({'name': 'U_ERROR', 'target': params["target"], 'p': fix,'type':'DEP1'})
                self._noises.append(len(self._sequence)-1)
                self._sequence.append({'name': 'V_ERROR', 'target': params["target"], 'p': fix,'type':'DEP1'})
                self._noises.append(len(self._sequence)-1)
                self._sequence.append({'name': 'N_ERROR', 'target': params["target"], 'p': fix,'type':'DEP1'})
                self._noises.append(len(self._sequence)-1)

            ##  作用在一系列目标上
            elif islist(params['target']):
                for temp in params['target']:
                    self.append({'name': params['name'], 'target': temp, 'p': params["p"]})

        ##  PART：----添加two-site depolarization----
        elif name == 'FDEPOLARIZE2':
            assert 'p' in params

            ##  用一个列表添加一个
            if islist(params['target']) and isinteger(params['target'][0]):
                self.sequence.append({'name': 'FDEPOLARIZE2', 'target': params['target'], 'p': params['p']})
                fix = (1 / 2) * (1 - (1 - 16 * params["p"] / 15) ** (1 / 8))
                for case in ['U_ERROR', 'V_ERROR', 'N_ERROR']:
                    self._sequence.append({'name': case, 'target': params["target"][0], 'p': fix,'type':'DEP2'})
                    self._noises.append(len(self._sequence) - 1)
                for case in ['U_ERROR', 'V_ERROR', 'N_ERROR']:
                    self._sequence.append({'name': case, 'target': params["target"][1], 'p': fix,'type':'DEP2'})
                    self._noises.append(len(self._sequence) - 1)
                for case in ['UU_ERROR', 'UV_ERROR', 'UN_ERROR','VU_ERROR','VV_ERROR','VN_ERROR','NU_ERROR','NV_ERROR','NN_ERROR']:
                    self._sequence.append({'name': case, 'target': params["target"], 'p': fix,'type':'DEP2'})
                    self._noises.append(len(self._sequence) - 1)

            ##  用一个列表添加多个
            elif islist(params['target']) and isinteger(params['target'][0]) and len(params['target'])>2:
                for i in range(len(params['target'])//2):
                    self.append({'name': name, 'target':[params['target'][2*i], params['target'][2*i+1]], 'p': params['p']})

            ##  用多个列表添加多个
            elif islist(params['target']) and islist(params['target'][0]) and isinteger(params['target'][0][0]):
                for temp in params['target']:
                    self.append({'name': params['name'], 'target': temp, 'p': params["p"]})

            ##  其他情况抛出异常
            else:
                raise ValueError("Gate must be applied to two")

        ##  PART：----添加site-qubit depolarization----
        elif name=='MIXTURE':
            assert 'p' in params

            ##  用单个列表添加单个
            if islist(params['target']) and isinteger(params['target'][0]):
                self.sequence.append({'name': 'MIXTURE2', 'target': params['target'], 'p': params['p']})
                fix = (1 / 2) * (1 - (1 - 16 * params["p"] / 15) ** (1 / 8))
                for case in ['U_ERROR', 'V_ERROR', 'N_ERROR']:
                    self._sequence.append({'name': case, 'target': params["target"][0], 'p': fix,'type':'DEP2'})
                    self._noises.append(len(self._sequence) - 1)
                for case in ['X_ERROR', 'Y_ERROR', 'Z_ERROR']:
                    self._sequence.append({'name': case, 'target': params["target"][1], 'p': fix,'type':'DEP2'})
                    self._noises.append(len(self._sequence) - 1)
                for case in ['UX_ERROR', 'UY_ERROR', 'UZ_ERROR', 'VX_ERROR', 'VY_ERROR', 'VZ_ERROR', 'NX_ERROR', 'NY_ERROR', 'NZ_ERROR']:
                    self._sequence.append({'name': case, 'target': params["target"], 'p': fix,'type':'DEP2'})
                    self._noises.append(len(self._sequence) - 1)

            ##  用一个列表添加多个
            elif islist(params['target']) and isinteger(params['target'][0]) and len(params['target'])>2:
                for i in range(len(params['target'])//2):
                    self.append({'name': name, 'target':[params['target'][2*i], params['target'][2*i+1]], 'p': params['p']})

            ##  用多个列表添加多个
            elif islist(params['target']) and islist(params['target'][0]) and isinteger(params['target'][0][0]):
                for temp in params['target']:
                    self.append({'name': params['name'], 'target': temp, 'p': params["p"]})

            ##  其他情况抛出异常
            else:
                raise ValueError("Gate must be applied to two")

        ##  PART：----添加single qubit and single fermionic site上的测量----
        elif name=='MZ' or name=='MN':
            target=params['target']

            ##  作用在一系列目标上
            if islist(target):
                for temp in target:
                    if 'p' in params:
                        dict_temp={'name': name, 'target': temp, 'p': params['p']}
                    else:
                        dict_temp={'name': name, 'target': temp}
                    self.append(dict_temp)

            ##  作用在整数index对应目标上
            elif isinteger(target):
                if name=='MZ':
                    if 'p' in params:
                        dict_temp={'name': 'MPP', 'target': PauliOperator([], [target], 1), 'p': params['p']}
                    else:
                        dict_temp={'name': 'MPP', 'target': PauliOperator([], [target], 1)}
                else:
                    if 'p' in params:
                        dict_temp={'name': 'MPP', 'target': MajoranaOperator([target], [target], 1j), 'p': params['p']}
                    else:
                        dict_temp={'name': 'MPP', 'target': MajoranaOperator([target], [target], 1j)}
                self.append(dict_temp)

        ##  PART：----添加qubit重置----
        elif name=='R':
            assert 'target' in params
            target=params['target']

            ##  作用在整数index对应目标上
            if isinteger(target):
                self._sequence.append({'name': name, 'target': target})
                self.sequence.append(self._sequence[-1])
                self.ideal_sequence.append(self._sequence[-1])
                if target==self.pauli_number:
                    self.pauli_number+=1
                elif target>self.pauli_number or target<0:
                    raise ValueError("R gate target must be consecutive")
                else:
                    pass

            ##  作用在一系列目标上
            elif islist(target):
                for temp in target:
                    self.append({'name': name, 'target': temp})

            ##  其他情况抛出异常
            else:
                raise ValueError

        ##  PART：----初始化方法----
        elif name=='TRAP':
            assert len(self._sequence)==0
            assert 'pauli_number' in params
            assert 'majorana_number' in params
            self.pauli_number=params["pauli_number"]
            self.majorana_number=params["majorana_number"]
            self._sequence.append({'name': name})
            self.sequence.append(self._sequence[-1])
            self.ideal_sequence.append(self._sequence[-1])

        ##  PART：----添加string算符的测量----
        elif name=='MPP':
            assert 'target' in params

            ##  在列表上
            if islist(params['target']):
                for i, temp in enumerate(params['target']):
                    dict_temp={'name': 'MPP', 'target': temp}
                    if 'index' in params:
                        dict_temp['index']=params['index'][i]
                    self.append(dict_temp)

            ##  单个算符
            elif isinstance(params['target'], (PauliOperator, MajoranaOperator)):
                dict_temp={'name': 'MPP', 'target': params['target']}
                if 'index' in params:
                    dict_temp['index']=params['index']
                self._sequence.append(dict_temp)
                self._measurements.append(len(self._sequence)-1)
                if 'p' in params:
                    self._sequence.append({'name': 'M_ERROR', 'p': params["p"]})
                    self._noises.append(len(self._sequence)-1)
                    self.sequence.append({'name': 'MPP', 'target': params['target'], 'p': params["p"]})
                    self.ideal_sequence.append({'name': 'MPP', 'target': params['target']})
                else:
                    self.sequence.append(self._sequence[-1])
                    self.ideal_sequence.append({'name': 'MPP', 'target': params['target']})

            ##  其他情况抛出异常
            else:
                raise ValueError

        ##  PART：----添加监视器----
        elif name=='DETECTOR':
            assert 'target' in params
            target=params['target']

            ##  对于负数的情况
            if all(target[i]=='negative' or target[i]<0 for i in range(len(target))):
                together=[len(self._measurements)+temp for temp in target if temp!='negative']  # 在测量中找到对应索引
                if 'negative' in target:
                    together.append('negative')
                self._detectors.append(together)

            ##  对于正数的情况
            elif all(target[i]=='negative' or target[i]>=0 for i in range(len(target))):
                together=[temp for temp in target if temp!='negative']
                if 'negative' in target:
                    together.append('negative')
                self._detectors.append(together)

            ##  抛出异常
            else:
                raise ValueError("DETECTOR gate target must be consecutive")

        ##  PART：----添加可观测量----
        elif name=='OBSERVABLE_INCLUDE':
            assert 'target' in params
            target=params['target']

            ##  对于负数的情况
            if all(target[i]=='negative' or target[i]<0 for i in range(len(target))):
                together=[len(self._measurements)+temp for temp in target if temp!='negative']  # 在测量中找到索引
                if 'negative' in target:
                    together.append('negative')
                self._observables.append(together)

            ##  对于正数的情况
            elif all(target[i]=='negative' or target[i]>=0 for i in range(len(target))):
                together=[temp for temp in target if temp!='negative']  # 在测量中找到索引
                if 'negative' in target:
                    together.append('negative')
                self._observables.append(together)

            ##  抛出异常
            else:
                raise ValueError("OBSERVABLE_INCLUDE gate target must be consecutive")

        ##  PART：----添加线路划分----
        elif name=='TICK':
            self.sequence.append({'name': 'TICK'})

        ##  PART：----抛出异常----
        else:
            raise NotImplementedError

    #%%  SECTION：----获取批量采样----
    def _sample_batch(self, noises=None, number=None,noiseless=False):
        if noises is not None:
            return [self.sample(i,noiseless) for i in noises]
        elif noises is None and isinteger(number):
            return [self.sample(noiseless=noiseless) for _ in range(number)]
        else:
            raise ValueError

    ##  SECTION：----获取采样----
    def sample(self,designated_noise_index=None,noiseless=False):
        frame=Frame()
        reference_measurement_sample=self._reference_sample
        measurement_sample=np.empty(len(self._measurements), dtype=int)  # 生成测量值的样本数组
        flag_measurement=0

        ##  遍历整个操作序列
        for i, gate in enumerate(self._sequence):
            name=gate['name']

            if name in ['H','S','P']:
                target: int=gate['target']
                if name=='H':
                    frame.h(target)
                elif name=='S':
                    frame.s(target)
                elif name=='P':
                    frame.p(target)

            ##  执行双门
            if name in ['CX', 'CNX', 'BRAID', 'CNN']:
                target: list=gate['target']
                if name=='CX':
                    frame.cx(target[0], target[1])
                elif name=='CNX':
                    frame.cnx(target[0], target[1])
                elif name=='BRAID':
                    frame.braid(target[0], target[1])
                elif name=='CNN':
                    frame.cnn(target[0], target[1])

            ##  执行重置
            elif name=='R':
                target: int=gate['target']
                frame.reset(target)

            ##  执行误差门
            elif name =='M_ERROR':
                p: float=gate['p']
                if np.random.rand()<p:
                    measurement_sample[flag_measurement-1]=-measurement_sample[flag_measurement-1]

            elif name in ['X_ERROR', 'Y_ERROR', 'Z_ERROR', 'U_ERROR', 'V_ERROR', 'N_ERROR',
                          'XX_ERROR','XY_ERROR','XZ_ERROR','YX_ERROR','YY_ERROR','YZ_ERROR','ZX_ERROR','ZY_ERROR','ZZ_ERROR',
                          'UU_ERROR','UV_ERROR','UN_ERROR','VU_ERROR','VV_ERROR','VN_ERROR','NU_ERROR','NV_ERROR','NN_ERROR',
                          'UX_ERROR','UY_ERROR','UZ_ERROR','VX_ERROR','VY_ERROR','VZ_ERROR','NX_ERROR','NY_ERROR','NZ_ERROR']:
                if (designated_noise_index is None or i==designated_noise_index) and not noiseless:
                    if designated_noise_index is None:
                        p: float=gate['p']
                    else:
                        p=1.1
                    if isinteger(gate['target']):
                        frame.error(p,name,gate['target'])
                    elif islist(gate['target']) and len(gate['target'])==2:
                        frame.error(p,name,gate['target'][0],gate['target'][1])
                    else:
                        raise ValueError

            ##  执行测量
            elif name=='MPP':
                target=gate['target']
                measurement_sample[flag_measurement]=frame.measure(target, reference_measurement_sample[flag_measurement])
                flag_measurement+=1

            ##  执行初始化
            elif name=='TRAP':
                frame.trap(self.majorana_number, self.pauli_number)

        ##  PART：----返回可观测的结果----
        detector_sample=diff(measurement_sample, self._detectors)
        observable_sample=diff(measurement_sample, self._observables)
        return measurement_sample, detector_sample, observable_sample

    ##  SECTION：----采样线路并返回错误率----
    def experiment(self,p_noise,p_measure, error_bar: float, method: str,decoder_params=None):
        """""        
        Tesseract decoder参数说明：
        {
        pqlimit：int对象，次数
        det_beam：int对象，分支查询数目
        beam_climbing：bool对象，是否梯度方法
        num_det_orders=num_det_orders，不知道什么阶数
        no_revisit_dets=no_revisit_dets，是否避免重复访问
        }
        ----------------------------------
        BP-OSD decoder参数说明：
        {
        bp_method：str对象，BP更新方法
        1. "product_sum"
        2. "min_sum"
        3. "min_sum_log"
        max_bp_iters：int对象，BP迭代次数，by default，50
        osd_method：str对象
            1. "osd_0"
            2. "osd_e": exhaustive OSD
            3. "osd_cs": combination-sweep OSD
            4. "osd_e"
        osd_order：int对象，OSD置换数目
        }
        """""

        ##  生成线路执行样本和每个样本的预测样本
        dem=self.detector_error_model(p_noise,p_measure)  # 错误模型
        group_number=os.cpu_count()//2

        ##  计算解码事件并得到一次样本数量
        start_time = time.time()
        task(dem,method,100,decoder_params=decoder_params,test=True)
        end_time = time.time()
        duration=(end_time - start_time)/100
        print('解码一个样本的时间为：',duration,'秒')
        if 5/duration>10000:
            sample_in_one_group_number=10000
        elif 5/duration<100:
            sample_in_one_group_number=100
        else:
            sample_in_one_group_number=int(5/duration)

        lock=multiprocessing.Manager().Lock()
        global sample_number_now
        global error_number_now
        sample_number_now.value=0
        error_number_now.value=0
        with Pool(processes=group_number) as pool:
            results=[pool.apply_async(task, args=(dem,method,sample_in_one_group_number,lock,error_bar,decoder_params))
                     for _ in range(group_number)]
            _=[result.get() for result in results]
        error_rate = error_number_now.value / sample_number_now.value
        sigma = np.sqrt((error_number_now.value / sample_number_now.value - (error_number_now.value / sample_number_now.value) ** 2) / sample_number_now.value) * 2 * 3.2905
        return error_rate, sigma

    ##  SECTION：----绘制线路图----
    def draw(self, filename,noiseless=False):

        # 绘制一个带有barriers和更多寄存器中，绘制一个新的电路
        F=qiskit.QuantumRegister(self.majorana_number, name='F')  # fermionic sites
        Q=qiskit.QuantumRegister(self.pauli_number, name='Q')  # qubits
        C=qiskit.ClassicalRegister(1, name='C')  # 经典寄存器
        A=qiskit.QuantumRegister(1, name='A')  # 无含义的ancilla
        circuit_qiskit=qiskit.QuantumCircuit(F, Q, C, A)
        braid=qiskit.circuit.ControlledGate(name='braid', num_qubits=2, params=[], label=None, num_ctrl_qubits=1, base_gate=XGate())
        cnn=qiskit.circuit.ControlledGate(name='CNN', num_qubits=2, params=[], label=None, num_ctrl_qubits=1, base_gate=ZGate())
        cnx=qiskit.circuit.ControlledGate(name='CNX', num_qubits=2, params=[], label=None, num_ctrl_qubits=1, base_gate=XGate())
        x_error=qiskit.circuit.Gate('X_ERROR', 1, label='X', params=[])
        y_error=qiskit.circuit.Gate('Y_ERROR', 1, label='Y', params=[])
        z_error=qiskit.circuit.Gate('Z_ERROR', 1, label='Z', params=[])
        u_error=qiskit.circuit.Gate('U_ERROR', 1, label='U', params=[])
        v_error=qiskit.circuit.Gate('V_ERROR', 1, label='V', params=[])
        n_error=qiskit.circuit.Gate('N_ERROR', 1, label='N', params=[])
        reset=qiskit.circuit.Gate('reset', 1, label=None, params=[])
        n=qiskit.circuit.Gate('N', 1, label='N', params=[])
        dep=qiskit.circuit.Gate('DEPOLARIZE', 1, label='D', params=[])

        ##  遍历电路序列，添加到qiskit电路中
        if noiseless:
            sequence=self.ideal_sequence
        else:
            sequence=self.sequence
        for gate in sequence:
            if gate['name']=='R':
                circuit_qiskit.append(reset, [Q[gate['target']]])
            elif gate['name']=='TRAP':
                circuit_qiskit.reset(Q)
                circuit_qiskit.reset(F)
            elif gate['name']=='X':
                circuit_qiskit.x(Q[gate['target']])
            elif gate['name']=='Y':
                circuit_qiskit.y(Q[gate['target']])
            elif gate['name']=='Z':
                circuit_qiskit.z(Q[gate['target']])
            elif gate['name']=='H':
                circuit_qiskit.h(Q[gate['target']])
            elif gate['name']=='S':
                circuit_qiskit.s(Q[gate['target']])
            elif gate['name']=='N':
                circuit_qiskit.append(n, [F[gate['target']]])
            elif gate['name']=='CX':
                circuit_qiskit.cx(Q[gate['target'][0]], Q[gate['target'][1]])
            elif gate['name']=='braid' or gate['name']=='BRAID':
                circuit_qiskit.append(braid, [F[gate['target'][0]], F[gate['target'][1]]])
            elif gate['name']=='CNN':
                circuit_qiskit.append(cnn, [F[gate['target'][0]], F[gate['target'][1]]])
            elif gate['name']=='CNX':
                circuit_qiskit.append(cnx, [F[gate['target'][0]], Q[gate['target'][1]]])
            elif gate['name']=='X_ERROR':
                circuit_qiskit.append(x_error, [Q[gate['target']]])
            elif gate['name']=='Y_ERROR':
                circuit_qiskit.append(y_error, [Q[gate['target']]])
            elif gate['name']=='Z_ERROR':
                circuit_qiskit.append(z_error, [Q[gate['target']]])
            elif gate['name']=='U_ERROR':
                circuit_qiskit.append(u_error, [F[gate['target']]])
            elif gate['name']=='V_ERROR':
                circuit_qiskit.append(v_error, [F[gate['target']]])
            elif gate['name']=='N_ERROR':
                circuit_qiskit.append(n_error, [F[gate['target']]])
            elif gate['name']=='DEPOLARIZE1':
                circuit_qiskit.append(dep, [Q[gate['target']]])
            elif gate['name']=='FDEPOLARIZE1':
                circuit_qiskit.append(dep, [F[gate['target']]])
            elif gate['name']=='MPP':
                op=gate['target']
                if isinstance(op, MajoranaOperator):
                    f_flag_x=op.occupy_x
                    f_flag_z=op.occupy_z
                    f_flag_n=np.intersect1d(f_flag_x, f_flag_z)
                    f_flag_x=np.setdiff1d(f_flag_x, f_flag_n)
                    f_flag_z=np.setdiff1d(f_flag_z, f_flag_n)
                    f=np.concatenate([f_flag_x, f_flag_z, f_flag_n])
                    if len(f)>1:
                        mppx=qiskit.circuit.ControlledGate(name='MPPX', num_qubits=len(f)+1, params=[], label=None, num_ctrl_qubits=len(f),
                                                           base_gate=XGate())
                        circuit_qiskit.append(mppx, F[f.tolist()]+[A[0]])
                        circuit_qiskit.measure(A[0], C[0])
                    else:
                        circuit_qiskit.measure(F[f[0]], C[0])
                elif isinstance(op, PauliOperator):
                    p_flag_x=op.occupy_x
                    p_flag_z=op.occupy_z
                    p_flag_y=np.intersect1d(p_flag_x, p_flag_z)
                    p_flag_x=np.setdiff1d(p_flag_x, p_flag_y)
                    p_flag_z=np.setdiff1d(p_flag_z, p_flag_y)
                    p=np.concatenate([p_flag_x, p_flag_y, p_flag_z])
                    if len(p)>1:
                        mppx=qiskit.circuit.ControlledGate(name='MPPX', num_qubits=len(p)+1, params=[], label=None, num_ctrl_qubits=len(p),
                                                           base_gate=XGate())
                        circuit_qiskit.append(mppx, Q[p.tolist()]+[A[0]])
                        circuit_qiskit.measure(A[0], C[0])
                    else:
                        circuit_qiskit.measure(Q[p[0]], C[0])
                else:
                    raise CircuitError("cannot set parameters on immutable base gate")
            elif gate['name']=='TICK':
                circuit_qiskit.barrier()
        ##  格式化颜色
        red='#E77081'
        blue='#5375CD'
        # green='#00857B'
        grey='#8C92AC'
        purple='#5D548C'
        # orange='#F15D22'
        pink='#FFACC5'
        cyan='#C9DCC4'

        ##  绘制线路
        circuit_qiskit.draw(output='mpl', filename=filename, style={
            'displaycolor': {'cx': None, 'cy': None, 'cz': None,
                             'X_ERROR': red, 'Y_ERROR': red, 'Z_ERROR': red,
                             'U_ERROR': red, 'V_ERROR': red, 'N_ERROR': red,
                             'R': cyan, 'measure': grey,
                             'x': blue, 'y': blue, 'z': blue, 's': blue, 'N': blue, 'U': blue, 'V': blue,
                             'CNN': blue, 'CNX': purple, 'braid': pink,
                             'MPPX': grey
                             },
            'fontsize': 12
        })

    ##  SECTION：----复制函数----
    def copy(self):
        return copy.deepcopy(self)


def task(dem,method,number,lock=None,error_bar=None,decoder_params=None,test=False):
    ##  生成线路执行样本和每个样本的预测样本
    sampler=dem.compile_sampler()  # 采样器

    if method=='bposd':
        max_bp_iters=50
        bp_method='min_sum'
        osd_method='osd_e'
        osd_order=60
        if decoder_params is not None:
            if 'max_bp_iters' in decoder_params:
                max_bp_iters=decoder_params['max_bp_iters']
            if 'bp_method' in decoder_params:
                bp_method=decoder_params['bp_method']
            if 'osd_method' in decoder_params:
                osd_method=decoder_params['osd_method']
            if 'osd_order' in decoder_params:
                osd_order=decoder_params['osd_order']
        decoder=stimbposd.bp_osd.BPOSD(model=dem, bp_method=bp_method, max_bp_iters=max_bp_iters, osd_method=osd_method, osd_order=osd_order)

    elif method=='tesseract':
        det_beam=15
        beam_climbing=True
        no_revisit_dets=True
        num_det_orders=16

        if decoder_params is not None:
            if 'det_beam' in decoder_params:
                det_beam=decoder_params['det_beam']
            if 'beam_climbing' in decoder_params:
                beam_climbing=decoder_params['beam_climbing']
            if 'num_det_orders' in decoder_params:
                num_det_orders=decoder_params['num_det_orders']
            if 'no_revisit_dets' in decoder_params:
                no_revisit_dets=decoder_params['no_revisit_dets']

        config=tesseract.TesseractConfig(dem=dem, pqlimit=200_000, det_beam=det_beam, beam_climbing=beam_climbing,
                                         det_orders=tesseract_decoder.utils.build_det_orders(
                                             dem=dem,
                                             num_det_orders=num_det_orders,
                                             method=tesseract_decoder.utils.DetOrder.DetIndex,
                                         ),
                                         no_revisit_dets=no_revisit_dets, )
        decoder=config.compile_decoder()

    elif method=='matching':
        decoder=pymatching.Matching()
        decoder.from_detector_error_model(dem)
    else:
        raise NotImplementedError

    if test:
        detector_data, obs_data, error_data = sampler.sample(shots=number)  # 样本
        valid_detector_data = detector_data[np.where(np.logical_or(np.any(obs_data == True, axis=1), np.any(detector_data == True, axis=1)))[0]]  # 有效样本
        valid_obs_data = obs_data[np.where(np.logical_or(np.any(obs_data == True, axis=1), np.any(detector_data == True, axis=1)))[0]]  # 有效样本
        predictions = decoder.decode_batch(valid_detector_data)  # 解码器对每个样本的预测

        ##  计算逻辑错误率
        num_errors = 0
        for shot in range(len(valid_detector_data)):
            actual_for_shot = valid_obs_data[shot]
            predicted_for_shot = predictions[shot]
            if not np.array_equal(actual_for_shot, predicted_for_shot):
                num_errors += 1

    else:
        while True:
            global sample_number_now
            global error_number_now
            detector_data, obs_data, error_data=sampler.sample(shots=number)  # 样本
            valid_detector_data=detector_data[np.where(np.logical_or(np.any(obs_data==True, axis=1), np.any(detector_data==True, axis=1)))[0]]  # 有效样本
            valid_obs_data=obs_data[np.where(np.logical_or(np.any(obs_data==True, axis=1), np.any(detector_data==True, axis=1)))[0]]  # 有效样本
            predictions=decoder.decode_batch(valid_detector_data)  # 解码器对每个样本的预测

            ##  计算逻辑错误率
            num_errors=0
            for shot in range(len(valid_detector_data)):
                actual_for_shot=valid_obs_data[shot]
                predicted_for_shot=predictions[shot]
                if not np.array_equal(actual_for_shot, predicted_for_shot):
                    num_errors+=1
            lock.acquire()
            sample_number_now.value += number
            error_number_now.value += num_errors
            error_rate=error_number_now.value / sample_number_now.value
            sigma = np.sqrt((error_number_now.value / sample_number_now.value - (error_number_now.value / sample_number_now.value) ** 2) / sample_number_now.value) * 2 * 3.2905
            lock.release()
            print('当前错误率为：',error_rate,'当前均方差为：',sigma)
            if sigma < error_bar * error_rate:
                break