"""""
模块作用：基于有限射影几何 PG(2, 2^s) 构造LDPC线性码，使用超椭圆 (conic + nucleus) 分类直线并形成分块校验矩阵。
"""""
import numpy as np
import galois
from itertools import product
from extendedstim.Code.LinearCode.LinearCode import LinearCode
from extendedstim.tools.TypingTools import isinteger


class FiniteProjectiveGeometryCode(LinearCode):

    #%%  CHAPTER：===构造方法===
    def __init__(self,s:int)->None:
        """""
        input.s: 射影平面的维度参数（q=2^s）
        """""

        ##  ----数据预处理----
        assert isinteger(s), "s必须是整数"

        ##  ------生成校验矩阵------
        self.s=s
        H_asym = _generate_matrix(self.s)
        H_dual = np.hstack([H_asym[0:(H_asym.shape[0]-1)//2, 0:2 ** s - 1], H_asym[0:(H_asym.shape[0]-1)//2, 2 ** s:4 ** s+1]])
        assert np.all(H_dual@H_dual.T==0)
        super().__init__(H_dual)


#%%  SECTION：----生成Projective LDPC code----
def _generate_matrix(s):
    """""
    input.s：维度指数 (q=2^s)
    output：GF(2) 校验矩阵 (非对称大块)
    """""
    points = _construct_projective_plane(s)
    lines = _get_lines(points)
    M_pi = _construct_incidence_matrix(points, lines)
    n_points = len(points)

    # 步骤2: 构造超椭圆并分类点
    hyperoval, non_hyperoval = _construct_hyperoval(points, s)
    non_hyperoval_indices = [points.index(p) for p in non_hyperoval]

    # 步骤3: 分类直线
    secant_lines, skew_lines = _classify_lines(lines, hyperoval, points)

    # 步骤4: 构造 H_sk (skew lines)
    if skew_lines:
        H_sk = M_pi[skew_lines][:, non_hyperoval_indices]
        u_vector = np.ones((len(skew_lines), 1), dtype=int)
        H_sk = np.hstack([H_sk, u_vector])
    else:
        H_sk = np.zeros((0, len(non_hyperoval_indices) + 1), dtype=int)

    # 步骤5: 构造 H_se (secant lines)
    if secant_lines:
        H_se = M_pi[secant_lines][:, non_hyperoval_indices]
        u_vector = np.ones((len(secant_lines), 1), dtype=int)
        H_se = np.hstack([H_se, u_vector])
    else:
        H_se = np.zeros((0, len(non_hyperoval_indices) + 1), dtype=int)

    # 步骤6: 构造量子校验矩阵 (分块对角)
    n_sk = H_sk.shape[1] if H_sk.size > 0 else len(non_hyperoval_indices) + 1
    n_se = H_se.shape[1] if H_se.size > 0 else len(non_hyperoval_indices) + 1

    # 创建全零矩阵作为基础
    total_rows = H_sk.shape[0] + H_se.shape[0]
    total_cols = n_sk + n_se
    H_asym = np.zeros((total_rows, total_cols), dtype=int)

    # 填充 H_sk 部分
    if H_sk.size > 0:
        H_asym[:H_sk.shape[0], :H_sk.shape[1]] = H_sk

    # 填充 H_se 部分
    if H_se.size > 0:
        start_row = H_sk.shape[0]
        start_col = n_sk
        H_asym[start_row:start_row+H_se.shape[0], start_col:start_col+H_se.shape[1]] = H_se

    # 转换为伽罗瓦域矩阵
    GF2 = galois.GF(2)
    return GF2(H_asym)


#%%  SECTION：----构造有限射影平面 PG(2, 2^s)----
def _construct_projective_plane(s):
    """""
    input.s：指数 (q=2^s)
    output：列表[tuple] 归一化射影点
    """""
    q = 2 ** s
    GF = galois.GF(2 ** s)

    # 生成点集 [x, y, z] (齐次坐标)
    points = []
    for x, y, z in product(GF.elements, repeat=3):
        if x == 0 and y == 0 and z == 0:
            continue  # 排除原点

        # 标准化表示: 使第一个非零元素为1
        coords = [x, y, z]
        for i in range(3):
            if coords[i] != 0:
                scale = coords[i] ** -1
                point = tuple(c * scale for c in coords)
                if point not in points:
                    points.append(point)
                break
    return points


#%%  SECTION：----获取所有直线----
def _get_lines(points):
    """""
    input.points：射影点集
    output：列表[tuple] 直线系数 (a,b,c)
    """""
    lines = []
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            p1, p2 = points[i], points[j]
            # 计算通过两点的直线方程
            a = p1[1] * p2[2] - p1[2] * p2[1]
            b = p1[2] * p2[0] - p1[0] * p2[2]
            c = p1[0] * p2[1] - p1[1] * p2[0]

            # 标准化直线方程
            for k in range(3):
                if [a, b, c][k] != 0:
                    scale = [a, b, c][k] ** -1
                    a, b, c = a * scale, b * scale, c * scale
                    break
            line = (a, b, c)
            if line not in lines:
                lines.append(line)
    return lines


#%%  SECTION：----构造点线关联矩阵----
def _construct_incidence_matrix(points, lines):
    """""
    input.points：点集
    input.lines：直线集
    output：numpy.ndarray 01关联矩阵 (n_lines, n_points)
    """""
    n_points = len(points)
    n_lines = len(lines)
    M = np.zeros((n_lines, n_points), dtype=int)

    for i, line in enumerate(lines):
        a, b, c = line
        for j, point in enumerate(points):
            x, y, z = point
            if a * x + b * y + c * z == 0:  # 点在直线上
                M[i, j] = 1
    return M


#%%  SECTION：----构造超椭圆 (二次曲线 + 核点)----
def _construct_hyperoval(points, s):
    """""
    input.points：点集
    input.s：指数
    output：(hyperoval点列表, 非hyperoval点列表)
    """""
    q = 2 ** s
    GF = galois.GF(2 ** s)

    # 构造二次曲线 (x^2 = yz)
    conic_points = []
    for point in points:
        x, y, z = point
        if x ** 2 == y * z:  # 满足二次曲线方程
            conic_points.append(point)

    # 计算核点 (所有切线的交点)
    if conic_points:
        # 使用Galois域安全的加法
        x_sum = GF(0)
        y_sum = GF(0)
        z_sum = GF(0)
        for p in conic_points:
            x_sum += p[0]
            y_sum += p[1]
            z_sum += p[2]

        # 标准化核点
        nucleus = (x_sum, y_sum, z_sum)
        for i in range(3):
            if nucleus[i] != 0:
                scale = nucleus[i] ** -1
                nucleus = tuple(c * scale for c in nucleus)
                break
    else:
        # 默认核点 (当s=1时)
        nucleus = (GF(1), GF(0), GF(0))

    hyperoval = conic_points.copy()
    hyperoval.append(nucleus)
    non_hyperoval = [p for p in points if p not in hyperoval]

    return list(hyperoval), non_hyperoval


#%%  SECTION：----分类直线: secant 或 skew----
def _classify_lines(lines, hyperoval, points):
    """""
    input.lines：直线集
    input.hyperoval：超椭圆点集
    input.points：全部点集
    output：(secant_lines索引列表, skew_lines索引列表)
    """""
    secant_lines = []
    skew_lines = []
    for idx, line in enumerate(lines):
        # 计算直线与超椭圆的交点
        intersection_count = 0
        for point in hyperoval:
            x, y, z = point
            a, b, c = line
            if a * x + b * y + c * z == 0:  # 点在直线上
                intersection_count += 1

        if intersection_count == 2:  # secant line
            secant_lines.append(idx)
        elif intersection_count == 0:  # skew line
            skew_lines.append(idx)

    return secant_lines, skew_lines