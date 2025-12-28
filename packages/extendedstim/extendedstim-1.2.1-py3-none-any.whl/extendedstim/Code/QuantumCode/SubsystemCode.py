from extendedstim.Code.QuantumCode.MajoranaCode import MajoranaCode
from extendedstim.Code.QuantumCode.PauliCode import PauliCode
from extendedstim.Physics.MajoranaOperator import MajoranaOperator
from extendedstim.Physics.PauliOperator import PauliOperator
from extendedstim.tools.GaloisTools import mip_distance_caculator


class SubsystemCode:
    def __init__(self,code:MajoranaCode|PauliCode,bare_logical_operators):
        """""
        input.code：MajoranaCode 或 PauliCode 实例
        input.gauges：MajoranaOperator 或 PauliOperator 列表，作为码面上的测量算子
        output：无
        """""
        self.code=code
        self.bare_logical_operators=bare_logical_operators
        if isinstance(code,MajoranaCode):
            self.code_type=MajoranaCode
            self.operator_type=MajoranaOperator
        elif isinstance(code,PauliCode):
            self.code_type=PauliCode
            self.operator_type=PauliOperator
        else:
            raise ValueError("code must be MajoranaCode or PauliCode")

    @property
    def logical_operators(self)->list[MajoranaOperator|PauliOperator]:
        """""
        output：list[MajoranaOperator|PauliOperator]，独立逻辑算符集合
        """""
        return self.bare_logical_operators

    @property
    def distance(self)->int:
        """""
        output：int，码距
        """""
        return mip_distance_caculator(self.code.check_matrix,self.operator_type.get_matrix(self.bare_logical_operators,self.code.physical_number))