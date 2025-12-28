"""""
模块作用：实现Bicycle LDPC码构造及相关差集/循环矩阵生成工具。
"""""
import numpy as np
from extendedstim.Code.LinearCode.LinearCode import LinearCode
from extendedstim.tools.GaloisTools import generate_matrix
from extendedstim.tools.TypingTools import isinteger


class BicycleCode(LinearCode):

    #%%  CHAPTER：===构造方法===
    def __init__(self, bit_number:int, weight:int, checker_number:int, seed:int)->None:
        """""
        input.bit_number：循环矩阵的大小 (偶数)
        input.weight：逻辑位数目 (偶数)
        input.checker_number：选取的行数 ( < N/2 ) 用于列权均匀化
        input.seed：随机种子
        """""

        ##  SECTION：----数据预处理-----
        assert isinteger(bit_number), "N必须是整数"
        assert isinteger(weight), "k必须是整数"
        assert isinteger(checker_number), "M必须是整数"
        assert isinteger(seed), "seed必须是整数"

        ##  SECTION：----生成校验矩阵-----
        np.random.seed(seed)
        H, diff_set = generate_matrix(bit_number, weight, checker_number)
        assert np.all(H @ H.T == 0)
        super().__init__(H)