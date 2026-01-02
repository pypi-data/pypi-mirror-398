# coding=utf-8
import numpy as np
from ellipse import LsqEllipse
from scipy.optimize import minimize
import multiprocessing as mp  # 添加多线程库
import zelas2.Multispectral as p0
import math
"""
本源代码有两个功能：This source code has two functions：
1：二维点拟合椭圆：fitellipse  # 无法使用  2D point fitting ellipse: fitellipse # cannot be used
2：点到椭圆的最近距离（后续可以将切点也找到）# 现已停止使用 ：dis_ellipse  The closest distance from a point to an ellipse (you can also find the tangent point later): dis_ Ellipses 
3: 点到椭圆的最近距离（无bug版）find_dis_mp：多线程版，block为非线程版
注：其他类与函数为内部函数，无法对外使用  Note: Other classes and functions are internal functions and cannot be used externally
已知bug：dis_ellipse的精度不能太高，否则计算会有误差  Known bug: dis_ The accuracy of ellipses should not be too high, otherwise there may be errors in the calculation
"""


class CostFunction_ellipse3:
    """Cost function for ellipse fit (x=[A B C D E]. Initialised with points."""

    def __init__(self, pts):
        self.pts = pts

    def f(self, x1):
        """Evaluate cost function fitting ellipse"""
        x = self.pts[0, :]
        y = self.pts[1, :]
        x = x[:, np.newaxis]
        y = y[:, np.newaxis]
        x1 = x1[np.newaxis, :]
        D = np.hstack((x * x, x * y, y * y, x, y, np.ones_like(x)))
        # S = np.dot(D.T,D)
        C = np.zeros([6, 6])
        C[0, 2] = C[2, 0] = 2
        C[1, 1] = -1
        aa = np.dot(x1, D.T)
        aa = np.dot(aa, D)
        aa = np.dot(aa, x1.T)
        bb = np.dot(x1, C)
        bb = np.dot(bb, x1.T)
        d = aa - bb
        return np.sum(d)


def solve_ellipse(A, B, C, D, E, F):
    Xc = (B * E - 2 * C * D) / (4 * A * C - B ** 2)
    Yc = (B * D - 2 * A * E) / (4 * A * C - B ** 2)

    FA1 = 2 * (A * Xc ** 2 + C * Yc ** 2 + B * Xc * Yc - F)
    FA2 = np.sqrt((A - C) ** 2 + B ** 2)

    MA = np.sqrt(FA1 / (A + C + FA2))
    SMA = np.sqrt(FA1 / (A + C - FA2)) if A + C - FA2 != 0 else 0

    if B == 0 and F * A < F * C:
        Theta = 0
    elif B == 0 and F * A >= F * C:
        Theta = 90
    elif B != 0 and F * A < F * C:
        alpha = np.arctan((A - C) / B) * 180 / np.pi
        Theta = 0.5 * (-90 - alpha) if alpha < 0 else 0.5 * (90 - alpha)
    else:
        alpha = np.arctan((A - C) / B) * 180 / np.pi
        Theta = 90 + 0.5 * (-90 - alpha) if alpha < 0 else 90 + 0.5 * (90 - alpha)

    if MA < SMA:
        MA, SMA = SMA, MA
    Theta = Theta * np.pi / 180  # 角度转弧度（matlab为默认弧度） Angle to radian (default radian in MATLAB)
    return [Xc, Yc, MA, SMA, Theta]


def fitellipse(xy):
    '点云拟合椭圆 Point cloud fitting ellipse'
    shapes = xy.T  # 数据转置  #Data transposition
    '拟合椭圆'
    e3 = CostFunction_ellipse3(shapes)
    x2 = np.array([0.01] * 6, dtype='float64')
    res1 = minimize(e3.f, x2, method='Powell')
    '模型求解'
    arg = solve_ellipse(res1.x[0], res1.x[1], res1.x[2], res1.x[3], res1.x[4], res1.x[5])  # 圆心、长短半轴、倾角  #Center, major and minor half axes, inclination angle
    print('椭圆圆心为', arg[0], arg[1], '椭圆长短半轴为', arg[2], arg[3], '椭圆极角为', arg[-1])
    return np.array(arg)  # 返回[椭圆圆心x,椭圆圆心y,椭圆长半轴,椭圆短半轴,倾角]  Returns [ellipse center x, ellipse center y, ellipse major half axis, ellipse minor half axis, inclination angle]


def solve_cubic_eq(a0, a1, a2):
    '解一元三次函数'
    np.set_printoptions(precision=17)
    Q = (3 * a1 - a2 ** 2) / 9
    R = (9 * np.multiply(a2, a1) - 27 * a0 - 2 * a2 ** 3) / 54
    D = np.float_power(Q, 3) + np.float_power(R, 2)  # 与matlab结果不一致
    SD = np.emath.sqrt(D)  # 负数平方根
    S = np.zeros(len(R))
    T = np.zeros(len(R))
    i = np.where(D >= 0)[0]  # 符合条件的下标
    if len(i) > 0:
        S[i] = pow((R[i] + SD[i]), (1 / 3))
        T[i] = pow((R[i] - SD[i]), (1 / 3))
    i = np.where(D < 0)[0]
    if len(i) > 0:
        S[i] = (R[i] + SD[i]) ** (1 / 3)
        T[i] = (R[i] - SD[i]) ** (1 / 3)
    z = np.array([-a2 / 3 + (S + T) / 2, -a2 / 3 - (S + T) / 2 + np.emath.sqrt(-3) * (S - T) / 2, -a2 / 3 - (S + T) / 2 - np.emath.sqrt(-3) * (S - T) / 2]).T
    return z


def solve_quartic_eq(a0, a1, a2, a3):
    '解一元四次方程组'
    b2 = a2 * -1
    np.set_printoptions(precision=14)
    b1 = np.multiply(a1, a3) - 4 * a0  # 计算值正负号与matlab1有差距
    b0 = 4 * np.multiply(a2, a0) - a1 ** 2 - np.multiply(a3 ** 2, a0)
    y = solve_cubic_eq(b0, b1, b2)
    a0 = np.zeros([len(a0), np.size(y, 1)]) + a0.reshape((len(a0), 1))
    a1 = np.zeros([len(a1), np.size(y, 1)]) + a1.reshape((len(a1), 1))
    a2 = np.zeros([len(a2), np.size(y, 1)]) + a2.reshape((len(a2), 1))
    a3 = np.zeros([len(a3), np.size(y, 1)]) + a3.reshape((len(a3), 1))
    R = np.emath.sqrt(a3 ** 2 / 4 - a2 + y)
    S = np.zeros_like(R)
    T = np.zeros_like(R)
    i = R == 0
    t1 = i.any().any()
    if t1:
        S[i] = 3 * a3[i] ** 2 / 4 - 2 * a2[i]
        T[i] = 2 * np.emath.sqrt(y[i] ** 2 - 4 * a0[i])
    else:
        i = i == False
        S[i] = 3 * a3[i] ** 2 / 4 - R[i] ** 2 - 2 * a2[i]
        T[i] = (4 * np.multiply(a3[i], a2[i]) - 8 * a1[i] - a3[i] ** 3) / (4 * R[i])
        # np.divide((4 * np.multiply(a3[i],a2[i]) - 8 * a1[i] - a3[i]**3),(4 * R[i]),T[i])
    D = np.sqrt(S + T)
    E = np.sqrt(S - T)
    # s = np.array([-a3 / 2 + R + D, - a3 / 2 + R - D, - a3 / 2 - R + E, - a3 / 2 - R - E]) / 2
    s = np.c_[-a3 / 2 + R + D, - a3 / 2 + R - D, - a3 / 2 - R + E, - a3 / 2 - R - E] / 2
    return s


def sub2ind(sz, row, col):
    'matlab.sub2ind 函数'
    n_rows = sz[0]
    return [n_rows * (c - 1) + r for r, c in zip(row, col)]


def dis_ellipse(x, y, argE):
    '点到椭圆的距离 Distance from point to ellipse'
    # 准备工作
    a = argE[2]  # 长半轴  #Long semiaxis
    b = argE[3]  # 短半轴  #Short half axis
    d = a ** 2 - b ** 2
    # 将点转换为极坐标系 #Convert points to polar coordinate systems
    x -= argE[0]
    y -= argE[1]
    q = np.dot(np.c_[x, y], np.array([[np.cos(argE[-1]), np.sin(argE[-1]) * -1], [np.sin(argE[-1]), np.cos(argE[-1])]]))
    x = q[:, 0]
    y = q[:, 1]
    # 将点投影到第一象限当中  #Project points into the first quadrant
    xq = np.abs(x)
    yq = np.abs(y)
    # 编辑方程参数  #Edit equation parameters
    a3 = 2 * yq * b / d
    a2 = (a ** 2 * xq ** 2 + b ** 2 * yq ** 2) / d ** 2 - 1
    a1 = a3 * -1
    a0 = -1 * b ** 2 * yq ** 2 / d ** 2
    # 解四次方程。如果找不到有效的根，请将xp、yp和dist设置为Inf  #Solve the quartic equation. If a valid root cannot be found, please set xp, yp, and dist to Inf
    sinv = np.real(solve_quartic_eq(a0, a1, a2, a3))
    cosv = np.sqrt(1 - sinv ** 2)
    '''
    i = sinv < 0
    sinv[i] = np.inf
    cosv[i] = np.inf
    i = sinv > 1
    sinv[i] = np.inf
    cosv[i] = np.inf
    '''
    i = np.logical_or(sinv < 0, sinv > 1)
    sinv[i] = np.inf
    cosv[i] = np.inf
    xp = a * cosv
    yp = b * sinv
    # 找到距离最小的根  #Find the root with the smallest distance
    dist2 = (xq.reshape(-1, 1) - xp) ** 2 + (yq.reshape(-1, 1) - yp) ** 2
    # where_are_nan = np.isnan(dist2)
    # dist2[where_are_nan] = 1.1
    j = np.argmin(dist2, axis=1)
    # size = np.shape(dist2)
    num = np.arange(len(dist2))
    # ind = sub2ind(size, num, j)
    sinv = sinv[num, j]
    # Deal with the degrading cases
    i = np.logical_and(yq == 0, xq >= d / a)
    sinv[i] = 0
    i = np.logical_and(yq == 0, xq < d / a)
    sinv[i] = np.sqrt(1 - a ** 2 * xq[i] ** 2 / d ** 2)
    # 查找第一象限中的正交接触点  #Find the positive contact point in the first quadrant
    cosv = np.sqrt(1 - sinv ** 2)
    xp = a * cosv
    yp = b * sinv
    dist = np.sqrt((xq - xp) ** 2 + (yq - yp) ** 2)
    return dist

def fit_Ellipse_mp(x, z, c, points,num_cpu=mp.cpu_count(), dr=0.05):
    '并行计算拟合椭圆 Parallel computing for fitting ellipses'
    num_c = len(np.unique(c))  # 圆环数
    xzlwp = np.empty([num_c, 5])  # 新建一个存储每个椭圆参数的容器
    dis_all = np.zeros(len(points))  # 距离容器
    # 并行计算加速准备 #Accelerated preparation for parallel computing
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    tik = p0.cut_down(num_c)  # 分块器
    # tik2 = p0.cut_down(len(points))  # 分块器
    tik_b = 0  # 分块输出计时器
    # 并行计算每个圆环 Parallel computing for each torus
    multi_res = [pool.apply_async(fit_Ellipse_block, args=(x, z, c, tik[i], tik[i + 1],points)) for i in
                 range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    for res in multi_res:
        # xzlwp[tik[tik_b]:tik[tik_b + 1], :] = res.get()  # 将每个进程得到的结果分block的发送到容器当中
        res_block = res.get()
        dis_all  += res_block[0]
        xzlwp[tik[tik_b]:tik[tik_b + 1], :] = res_block[1]
        tik_b += 1
    pool.close()  # 禁止进程池再接收任务  #Prohibit process pools from receiving tasks again
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算  #After all processes have completed their calculations, exit parallel computing
    # 下标
    index = dis_all <= dr
    outdex = dis_all > dr
    # RMSE
    dis_all = dis_all[dis_all<=dr]
    RMSE = np.sqrt(np.sum(dis_all**2)/len(dis_all))
    print('RMSE:', RMSE)
    return index, outdex, xzlwp, dis_all

def fit_Ellipse_block(x, z, c, b, e,points):
    '分块求椭圆参数 Calculating Ellipse Parameters by Blocks'
    num_ = e-b
    c_un = np.unique(c)
    dis_ = np.zeros(len(points))
    # dis_ = np.zeros(num_)
    xzlwp = np.empty([num_, 5])
    j = 0  # 循环计数器 cycle counter
    for c1 in c_un[b:e]:
        x_c1 = x[c == c1]
        z_c1 = z[c == c1]  # 提取单环的全部点云二维坐标  Extract all point cloud 2D coordinates of a single ring
        data1 = np.vstack([x_c1, z_c1]).T
        reg = LsqEllipse().fit(data1)  # 输入二维点  Enter 2D points
        center, width, height, phi = reg.as_parameters()  # 求解 solve

        xzlwp[j, 0] = center[0]
        xzlwp[j, 1] = center[1]
        xzlwp[j, 2] = np.max([width, height])
        xzlwp[j, 3] = np.min([width, height])
        xzlwp[j, 4] = phi

        # xzlwp_ = np.array([center[0],center[1],np.max([width, height]),np.min([width, height]),phi])

        # 求点到直线的距离  Find the distance from a point to a straight line
        # dis_[points[:, -1]==c1] = dis_ellipse(points[points[:, -1]==c1, 0], points[points[:, -1]==c1, 2], xzlwp[j,:])
        dis_[points[:, -1]==c1] = dis_ellipse(points[points[:, -1]==c1, 0], points[points[:, -1]==c1, 2], xzlwp[j,:])
        j += 1
    print('已完成第', b, '至第', e, '的圆环')
    dis_ = np.nan_to_num(dis_, nan=1)  # 若距离为nan，则转换为1
    return dis_,xzlwp

class Ellipse:
    def __init__(self, x, y, width, height, angle=0):
        '''
        :param x: 圆心x
        :param y: 圆心y
        :param width:长轴（不一定大于短轴）
        :param height:短轴
        :param angle:偏转角（弧度）
        '''
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.angle = angle

    def rotation_matrix(self):
        """
        Returns the rotation matrix for the ellipse's rotation.返回椭圆旋转的旋转矩阵。
        """
        a = math.cos(self.angle)
        b = math.sin(self.angle)
        return np.array([[a, -b], [b, a]])

    def get_point(self, angle):
        """
        Returns the point on the ellipse at the specified local angle.以指定的局部角度返回椭圆上的点。
        """
        r = self.rotation_matrix()
        xe = 0.5 * self.width * math.cos(angle)
        ye = 0.5 * self.height * math.sin(angle)
        return np.dot(r, [xe, ye]) + [self.x, self.y]

    def get_points(self, count):
        """
        Returns an array of points around the ellipse in the specified count.返回指定计数的椭圆周围的点数组。
        """
        t = np.linspace(0, 2 * math.pi, count)
        xe = 0.5 * self.width * np.cos(t)
        ye = 0.5 * self.height * np.sin(t)
        r = self.rotation_matrix()
        return np.dot(np.column_stack([xe, ye]), r.T) + [self.x, self.y]

    def find_distance1(self, x, tolerance=1e-8, max_iterations=10000, learning_rate=0.01):
        """
        Finds the minimum distance between the specified point and the ellipse
        using gradient descent.查找指定点和椭圆之间的最小距离-使用梯度下降。
        """
        x = np.asarray(x)
        r = self.rotation_matrix()
        x2 = np.dot(r.T, x - [self.x, self.y])
        t = math.atan2(x2[1], x2[0])
        a = 0.5 * self.width
        b = 0.5 * self.height
        iterations = 0
        error = tolerance
        errors = []
        ts = []

        while error >= tolerance and iterations < max_iterations:
            cost = math.cos(t)
            sint = math.sin(t)
            x1 = np.array([a * cost, b * sint])
            xp = np.array([-a * sint, b * cost])
            dp = 2 * np.dot(xp, x1 - x2)
            t -= dp * learning_rate
            error = abs(dp)
            errors.append(error)
            ts.append(t)
            iterations += 1

        ts = np.array(ts)
        errors = np.array(errors)
        y = np.linalg.norm(x1 - x2)
        success = error < tolerance and iterations < max_iterations
        return dict(x=t, y=y, error=error, iterations=iterations, success=success, xs=ts, errors=errors)

    def find_distance2(self, x, tolerance=1e-8, max_iterations=1000):
        """
        Finds the minimum distance between the specified point and the ellipse
        using Newton's method.查找指定点和椭圆之间的最小距离-使用牛顿法。
        return：
            x: 距离最近点所在的椭圆弧度值
            y: 最短距离
        """
        x = np.asarray(x)  # 输入值转换为numpy格式
        r = self.rotation_matrix()  # 旋转矩阵
        x2 = np.dot(r.T, x - [self.x, self.y])
        t = math.atan2(x2[1], x2[0])
        a = 0.5 * self.width
        b = 0.5 * self.height

        # If point is inside ellipse, generate better initial angle based on vertices 如果点在椭圆内，则根据顶点生成更好的初始角度
        if (x2[0] / a) ** 2 + (x2[1] / b) ** 2 < 1:
            ts = np.linspace(0, 2 * math.pi, 24, endpoint=False)
            xe = a * np.cos(ts)
            ye = b * np.sin(ts)
            delta = x2 - np.column_stack([xe, ye])
            t = ts[np.argmin(np.linalg.norm(delta, axis=1))]

        iterations = 0
        error = tolerance
        errors = []
        ts = []

        while error >= tolerance and iterations < max_iterations:
            cost = math.cos(t)
            sint = math.sin(t)
            x1 = np.array([a * cost, b * sint])
            xp = np.array([-a * sint, b * cost])
            xpp = np.array([-a * cost, -b * sint])
            delta = x1 - x2
            dp = np.dot(xp, delta)
            dpp = np.dot(xpp, delta) + np.dot(xp, xp)
            t -= dp / dpp
            error = abs(dp / dpp)
            errors.append(error)
            ts.append(t)
            iterations += 1

        ts = np.array(ts)
        errors = np.array(errors)
        y = np.linalg.norm(x1 - x2)
        success = error < tolerance and iterations < max_iterations
        return dict(x=t, y=y, error=error, iterations=iterations, success=success, xs=ts, errors=errors)

def find_dis_mp(x,z,l,s,t,points_xz,num_cpu = mp.cpu_count()):
    '求点数组到椭圆的最近距离，在椭圆内的为﹣，在椭圆外的为+（基于并行计算）'
    # 准备工作
    num_xz = len(points_xz)  # 点云数量
    tik = p0.cut_down(num_xz)  # 分块器
    E = Ellipse(x,z,l*2,s*2,t)  # 建立椭圆类
    dis_all = np.empty(num_xz)  # 距离容器
    # j = 0  # 循环计数器
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    # 开始并行计算
    multi_res = [pool.apply_async(find_dis_block, args=(E, points_xz, tik[i], tik[i + 1])) for i in
                 range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    tik_b = 0  # 分块输出计时器
    for res in multi_res:
        dis_all[tik[tik_b]:tik[tik_b + 1]] = res.get()
        tik_b += 1
        print('求距离进度',tik_b,'/',num_cpu)
    pool.close()  # 禁止进程池再接收任务  #Prohibit process pools from receiving tasks again
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算  #After all processes have completed their calculations, exit parallel computing
    print('开始添加正负号')
    print(dis_all)
    sign = E_sign(points_xz,[x,z],l,s,t)  # 获取园内圆外判断
    dis_all = np.multiply(dis_all,sign)  # 融合距离和判断
    return dis_all

def E_sign(points, Center, MA1, MA2,Theta):
    '本函数只取得正负号'
    x0, y0 = Center[0], Center[1]
    a = MA1
    b = MA2
    phi = Theta
    x, y = points[:, 0], points[:, 1]
    cos_phi = np.cos(phi)
    sin_phi = np.sin(phi)
    X = x - x0
    Y = y - y0
    x_rot = cos_phi * X + sin_phi * Y
    y_rot = -sin_phi * X + cos_phi * Y
    distances = (x_rot / a) ** 2 + (y_rot / b) ** 2
    # 获取正负号
    distances -= 1
    distances = np.sign(distances)
    return distances

def find_dis_block(E,points_xz, b=0, e=0):
    num_ = e - b  # 分块的点云数量
    dis_all_ = np.empty(num_)  # 分块的距离容器
    j = 0  # 计数器
    for i in points_xz[b:e,:]:
        dis_ = E.find_distance2(i)  # 求单点
        dis_all_[j] = dis_["y"]  # 只要距离
        j += 1  # 刷新计数器
    return dis_all_

def Find_dis_second_Ellipse_mp(xzc, xzlst, num_ps, C_un):
    '单线程求点到椭圆的距离（精拟合）'
    dis_all = np.empty(num_ps)  # 距离容器
    tik = p0.cut_down(num_ps)  # 分块器
    xzlstc = np.c_[xzlst, C_un]
    for i in range(len(tik)-1):
        start, end = tik[i], tik[i + 1]
        dis_all[start:end] = find_dis_second_Ellipse_block(xzc, xzlstc, start, end)
        print('求距离进度', i, '/', num_ps)
    return dis_all

def find_dis_second_Ellipse_block(xzc, xzlstc, b, e):
    num_ = e - b  # 分块的点云数量
    dis_all_ = np.empty(num_)  # 分块的距离容器
    j = 0  # 计数器
    for i in xzc[b:e, :]:
        xzlst_ = xzlstc[xzlstc[:,-1]==i[-1],:-1]
        # print(xzlst_)
        E = Ellipse(xzlst_[0,0], xzlst_[0,1], xzlst_[0,2] * 2, xzlst_[0,3] * 2, xzlst_[0,4])  # 建立椭圆类
        # print([i[0],i[1]])
        dis_ = E.find_distance2(i[0:2])  # 求单点
        dis_all_[j] = dis_["y"]  # 只要距离
        '添加正负号'
        sign_ = E_sign_single(i[:2],[xzlst_[0,0], xzlst_[0,1]],xzlst_[0,2],xzlst_[0,3],xzlst_[0,4])
        dis_all_[j] = np.multiply(dis_all_[j], sign_)  # 融合距离和判断
        j += 1  # 刷新计数器
    return dis_all_

def E_sign_single(points, Center, MA1, MA2,Theta):
    '本函数只取得单点正负号'
    x0, y0 = Center[0], Center[1]
    a = MA1
    b = MA2
    phi = Theta
    x, y = points[0], points[1]
    cos_phi = np.cos(phi)
    sin_phi = np.sin(phi)
    X = x - x0
    Y = y - y0
    x_rot = cos_phi * X + sin_phi * Y
    y_rot = -sin_phi * X + cos_phi * Y
    distances = (x_rot / a) ** 2 + (y_rot / b) ** 2
    # 获取正负号
    distances -= 1
    distances = np.sign(distances)
    return distances

def fit_ellipse_1(xyzic,xmax=3, xmin=-2.9, ymax=4.5, ymin=0.5):
    '高精度拟合单个椭圆20240530'
    # 1:限制坐标范围
    xyzic_0 = xyzic[xyzic[:, 0] > xmin, :]
    xyzic_0 = xyzic_0[xyzic_0[:, 0] < xmax, :]
    xyzic_0 = xyzic_0[xyzic_0[:, 2] < ymax, :]
    xyzic_0 = xyzic_0[xyzic_0[:, 2] > ymin, :]
    # 2：第一次拟合
    xz_0 = np.c_[xyzic_0[:, 0], xyzic_0[:, 2]]  # 对拟合点进行降维
    reg = LsqEllipse().fit(xz_0)  # 输入二维点
    center, width, height, phi = reg.as_parameters()  # 求解
    print(f'center: {center[0]:.3f}, {center[1]:.3f}')
    print(f'width: {width:.3f}')
    print(f'height: {height:.3f}')
    print(f'phi: {phi:.3f}')  # 打印
    # 3：点到椭圆的距离
    # arg_Ellipse = np.array([center[0], center[1], np.max([width, height]), np.min([width, height]), phi])  # 合并椭圆参数
    # distances = ep.dis_ellipse(xyzic[:, 0], xyzic[:, 2], arg_Ellipse)  # 求点到椭圆的距离
    dis = find_dis_mp(center[0], center[1], width, height, phi,xyzic[:,[0,2]])
    print('mean',np.mean(dis))
    print('std',np.std(dis))
    # plt.hist(dis, bins=100)
    # plt.show()
    # p1.view_pointclouds(xyzic[:,:3],dis,'dis','jet')
    td = 0.000
    dis_td = dis[dis>=td]
    xyzic_1 = xyzic[dis>=td,:]
    td = 0.05
    xyzic_1 = xyzic_1[dis_td <= td, :]
    dis_td = dis_td[dis_td <= td]
    # p1.view_pointclouds(xyzic_1[:, :3], dis_td, 'dis', 'jet')
    # 4.第二次拟合
    xz_0 = np.c_[xyzic_1[:, 0], xyzic_1[:, 2]]  # 对拟合点进行降维
    reg = LsqEllipse().fit(xz_0)  # 输入二维点
    center, width, height, phi = reg.as_parameters()  # 求解
    print(f'center: {center[0]:.3f}, {center[1]:.3f}')
    print(f'width: {width:.3f}')
    print(f'height: {height:.3f}')
    print(f'phi: {phi:.3f}')  # 打印
    dis = find_dis_mp(center[0], center[1], width, height, phi,xyzic[:,[0,2]])
    dis_min = find_dis_mp(center[0], center[1], width, height, phi,xyzic_1[:,[0,2]])
    print('mean',np.mean(dis_min))
    print('std',np.std(dis_min))
    td = np.mean(dis_min)+1.4*np.std(dis_min)
    xyzic_f = xyzic[np.abs(dis) <= td,:]
    dis = dis[np.abs(dis) <= td]
    # p1.view_pointclouds(xyzic_f[:, :3], dis, 'dis', 'jet')
    # 5.最终参数
    xz_0 = np.c_[xyzic_f[:, 0], xyzic_f[:, 2]]  # 对拟合点进行降维
    reg = LsqEllipse().fit(xz_0)  # 输入二维点
    center, width, height, phi = reg.as_parameters()  # 求解
    print(f'center: {center[0]:.3f}, {center[1]:.3f}')
    print(f'width: {width:.3f}')
    print(f'height: {height:.3f}')
    print(f'phi: {phi:.3f}')  # 打印
    return np.array([center[0], center[1], width, height, phi]),xyzic_f  # 返回椭圆参数和在椭圆上的点


if __name__ == '__main__':
    '椭圆拟合例子 Ellipse fitting example'
    # arg_Ellipse = fitellipse(xy) # size(xy) = [n,2]
    '点到椭圆例子Example of point to ellipse'
    eps = np.array([0, 0, 1, .5, np.pi / 6])  # Ellipse parameter
    # Plane point coordinates
    x = np.array([0.0,10.2,7.98760,1.198760,1.198730,0.198760,-4.999760])
    y = np.array([0.0,7.198730,8.198760,5.198760,7.198730,8.198760,-4.779760])
    dist = dis_ellipse(x, y, eps)  # Finding the Distance from a Point to an Ellipse
    print(dist)