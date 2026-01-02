#!/usr/bin/env python
# coding=utf-8
import numpy as np
import math
import multiprocessing as mp  # 添加多进程（并行计算）库
import pyransac3d as pyrsc
import zelas2.Multispectral as p1  # 添加自己的库
import plotly.graph_objects as go  # 添加其他显示库
import zelas2.voxel as vl  # 添加体素类
import zelas2.ransac as rs
import zelas2.Ellipse as ep
from ellipse import LsqEllipse  # 添加椭圆拟合算法
from tqdm import tqdm
import open3d as o3d
from scipy.spatial import ConvexHull
import cv2 as cv
from sklearn.neighbors import KDTree
import zelas2.Multispectral as zm
import matplotlib.pyplot as plt
from itertools import accumulate
import zelas2.RedundancyElimination as zr

def fit_cicle_rough(xyzic):
    '隧道点云整体粗拟合'
    # 限制坐标范围
    xyzic_0 = xyzic[xyzic[:, 0] > -2.9, :]
    xyzic_0 = xyzic_0[xyzic_0[:, 0] < 3, :]
    xyzic_00 = xyzic_0[xyzic_0[:, 2] < 4.5, :]
    xyzic_0 = xyzic_00[xyzic_00[:, 2] > 0.5, :]
    # 整体拟合
    print('RANSAC输入点云数量为', len(xyzic_0))
    model = CircleLeastSquareModel()  # 类的实例化:用最小二乘生成已知模型
    data = np.vstack([xyzic_0[:, 0], xyzic_0[:, 2]]).T  # 整理数据
    result = model.fit(data)  # 拟合圆
    x_0 = result.a * -0.5
    z_0 = result.b * -0.5
    r_0 = 0.5 * math.sqrt(result.a ** 2 + result.b ** 2 - 4 * result.c)  # 圆心及坐标半径
    dis = np.abs((xyzic_0[:, 0] - x_0) ** 2 + (xyzic_0[:, 2] - z_0) ** 2 - r_0 ** 2)  # 点到圆的距离
    # 求均值和标准差
    dis_mean = np.mean(dis)
    dis_std = np.std(dis)
    print('距离均值：', dis_mean, '距离标准差', dis_std)
    # 保留阈值内点云
    xyzic_dis = np.c_[xyzic_0, dis]  # 合并数组
    tt = 0.5  # 标准差倍数
    threshold = np.array([dis_mean - dis_std * tt, dis_mean + dis_std * tt])
    item = np.where(np.logical_and(xyzic_dis[:, -1] > threshold[0], xyzic_dis[:, -1] < threshold[1]))
    xyzic_1 = xyzic_dis[item, :-1]  # 剩余点云
    xyzic_1 = xyzic_1[0, :, :]
    return xyzic_1

def random_partition(n, n_data):
    """return n random rows of data and the other len(data) - n rows"""
    all_idxs = np.arange(n_data)  # 获取n_data下标索引
    np.random.shuffle(all_idxs)  # 打乱下标索引
    idxs1 = all_idxs[:n]
    idxs2 = all_idxs[n:]
    return idxs1, idxs2


class CircleLeastSquareModel:
    # 最小二乘 fitting circle
    def __init__(self):
        pass

    def fit(self, data):
        A = []
        B = []
        for d in data:
            A.append([-d[0], -d[1], -1])
            B.append(d[0] ** 2 + d[1] ** 2)
        A_matrix = np.array(A)
        B_matrix = np.array(B)
        C_matrix = A_matrix.T.dot(A_matrix)
        result = np.linalg.inv(C_matrix).dot(A_matrix.T.dot(B_matrix))
        model = CircleLeastSquareModel()
        model.a = result[0]
        model.b = result[1]
        model.c = result[2]
        return model  # 返回最小平方和向量

    # get error 为每个数据点和拟合后的结果之间的误差的平方，换其他模型也可以用
    def get_error(self, data, model):
        err_per_point = []
        for d in data:
            B = d[0] ** 2 + d[1] ** 2
            B_fit = model.a * d[0] + model.b * d[1] + model.c
            err_per_point.append((B + B_fit) ** 2)  # sum squared error per row
        return np.array(err_per_point)


def ransac(data, model, n, k, t, d, debug=False, return_all=False):
    """
    参考:http://scipy.github.io/old-wiki/pages/Cookbook/RANSAC
    伪代码:http://en.wikipedia.org/w/index.php?title=RANSAC&oldid=116358182
    输入:
        data - 样本点
        model - 假设模型:事先自己确定
        n - 生成模型所需的最少样本点
        k - 最大迭代次数
        t - 阈值:作为判断点满足模型的条件
        d - 拟合较好时,需要的样本点最少的个数,当做阈值看待
    输出:
        bestfit - 最优拟合解（返回nil,如果未找到）

    iterations = 0
    bestfit = nil #后面更新
    besterr = something really large #后期更新besterr = thiserr
    while iterations < k
    {
        maybeinliers = 从样本中随机选取n个,不一定全是局内点,甚至全部为局外点
        maybemodel = n个maybeinliers 拟合出来的可能符合要求的模型
        alsoinliers = emptyset #满足误差要求的样本点,开始置空
        for (每一个不是maybeinliers的样本点)
        {
            if 满足maybemodel即error < t
                将点加入alsoinliers
        }
        if (alsoinliers样本点数目 > d)
        {
            %有了较好的模型,测试模型符合度
            bettermodel = 利用所有的maybeinliers 和 alsoinliers 重新生成更好的模型
            thiserr = 所有的maybeinliers 和 alsoinliers 样本点的误差度量
            if thiserr < besterr
            {
                bestfit = bettermodel
                besterr = thiserr
            }
        }
        iterations++
    }
    return bestfit
    """
    iterations = 0
    bestfit = None
    besterr = np.inf  # 设置默认值
    best_inlier_idxs = None
    while iterations < k:
        maybe_idxs, test_idxs = random_partition(n, data.shape[0])
        maybe_inliers = data[maybe_idxs, :]  # 获取size(maybe_idxs)行数据(Xi,Yi)
        test_points = data[test_idxs]  # 若干行(Xi,Yi)数据点
        maybemodel = model.fit(maybe_inliers)  # 拟合模型
        test_err = model.get_error(test_points, maybemodel)  # 计算误差:平方和最小
        also_idxs = test_idxs[test_err < t]
        also_inliers = data[also_idxs, :]
        if debug:
            print('test_err.min()', test_err.min())
            print('test_err.max()', test_err.max())
            print('numpy.mean(test_err)', np.mean(test_err))
            print('iteration %d:len(alsoinliers) = %d' % (iterations, len(also_inliers)))
        if len(also_inliers > d):
            betterdata = np.concatenate((maybe_inliers, also_inliers))  # 样本连接
            bettermodel = model.fit(betterdata)
            better_errs = model.get_error(betterdata, bettermodel)
            thiserr = np.mean(better_errs)  # 平均误差作为新的误差
            if thiserr < besterr:
                bestfit = bettermodel
                besterr = thiserr
                best_inlier_idxs = np.concatenate((maybe_idxs, also_idxs))  # 更新局内点,将新点加入
        iterations += 1
        if bestfit is None:
            raise ValueError("did't meet fit acceptance criteria")
        if return_all:
            return bestfit, {'inliers': best_inlier_idxs}
        else:
            return bestfit


def c_refit(x, z, c, num_cpu=mp.cpu_count()):
    '进行第三次圆拟合'
    name_c = np.unique(c)  # 盾构环名
    model = CircleLeastSquareModel()  # 类的实例化:用最小二乘生成已知模型
    # 并行计算加速算法准备
    # num_cpu = mp.cpu_count()  # 电脑线程数
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    num_all = len(name_c)  # 圆环数
    xzrc = np.empty([num_all, 4])  # 新建一个存储每个圆环的容器
    tik = cut_down(num_all)
    tik_b = 0  # 分块输出计时器
    # 并行计算分块运行
    multi_res = [pool.apply_async(c_seam_block_3, args=(x, z, c, model, name_c, tik[i], tik[i + 1])) for i in
                 range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    for res in multi_res:
        xzrc[tik[tik_b]:tik[tik_b + 1], :] = res.get()  # 将每个进程得到的结果分block的发送到容器当中
        tik_b += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    return xzrc


def fit_circle(x, z, c, num_cpu=mp.cpu_count(), t=0.5):
    '''
    双次圆拟合的单次圆拟合函数（需要执行两次）
    :param x: 点云x坐标
    :param z: 点云z坐标
    :param c: 每个点云所属的圆环名
    :param num_cpu: 开启多线程的CPU核心数
    :param t: ransac拟合参数
    :return: xzrc：拟合每个圆环的圆心和半径
    '''
    c_un = np.unique(c)  # 圆环名精简
    num_all = len(c_un)  # 圆环数
    model = CircleLeastSquareModel()  # 圆拟合模型建立
    # 并行计算加速准备
    # num_cpu = mp.cpu_count()  # 电脑线程数
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    xzrc = np.empty([num_all, 4])  # 新建一个存储每个圆环的容器
    tik = cut_down(num_all)  # 分块器
    tik_b = 0  # 分块输出计时器
    # 并行计算每个圆环
    multi_res = [pool.apply_async(c_seam_block, args=(x, z, c, model, c_un, tik[i], tik[i + 1], t)) for i in
                 range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    for res in multi_res:
        xzrc[tik[tik_b]:tik[tik_b + 1], :] = res.get()  # 将每个进程得到的结果分block的发送到容器当中
        tik_b += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    print('平均圆心', np.mean(xzrc[:, 0]), np.mean([xzrc[:, 1]]), '平均半径', np.mean(xzrc[:, 2]))
    return xzrc


def c_seam(x, z, c):
    """
    将盾构隧道点云拟合出每个圆环（参数）
    :param x: 点云x坐标数组
    :param z: 点云z坐标数组
    :param c: 每个点云所属圆环名
    :return: 每个圆环的圆心和半径
    """
    # x0 = x
    # z0 = z  # 备份初值
    # c0 = c
    name_c = np.unique(c)  # 盾构环名
    model = CircleLeastSquareModel()  # 类的实例化:用最小二乘生成已知模型
    '''
    plt.figure(figsize=(4, 4))  # 设置显示窗口形状
    plt.plot(x, z)  # 显示初始点云
    plt.show()
    '''
    # 求平均值
    mean_z = np.mean(z)
    # mean_x = np.mean(x)
    # 确定初值
    # r0 = (np.max(x)-np.min(x)) / 2  # 确定初始半径
    # x0 = np.min(x)+r0  # 确定初始圆心坐标
    # z0 = mean_z + std_z/4
    # 寻找点云z轴出现最多的那一区间并剔除所在区间内的点云，留下剩下的
    # plt.hist(z, bins=50)
    # plt.show()
    # 将符合条件的数组全部提取出来(大于z的平均值)
    idz = (z >= mean_z)
    x = x[idz]
    z = z[idz]
    c = c[idz]
    data = np.vstack([x, z]).T
    result = model.fit(data)
    x_0 = result.a * -0.5
    z_0 = result.b * -0.5
    r_0 = 0.5 * math.sqrt(result.a ** 2 + result.b ** 2 - 4 * result.c)
    # circle_0 = Circle(xy=(x_0, z_0), radius=r_0, alpha=0.5, fill=False, label="least square ransac fit circle")
    # plt.gcf().gca().add_artist(circle_0)
    d_dis = 0.15
    dis = np.abs((x - x_0) ** 2 + (z - z_0) ** 2 - r_0 ** 2)
    id_r0 = dis < d_dis
    x = x[id_r0]
    z = z[id_r0]
    c = c[id_r0]
    '''
    idx = (x >= mean_x)
    x = x[idx]
    z = z[idx]
    c = c[idx]
    '''
    # plt.plot(x, z)
    # plt.show()  # 显示窗口
    # 并行计算加速算法准备
    num_cpu = mp.cpu_count()  # 电脑线程数
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    num_all = len(name_c)  # 圆环数
    xzrc = np.empty([num_all, 4])  # 新建一个存储每个圆环的容器
    tik = cut_down(num_all)
    tik_b = 0  # 分块输出计时器
    # 并行计算分块运行
    multi_res = [pool.apply_async(c_seam_block, args=(x, z, c, model, name_c, tik[i], tik[i + 1])) for i in
                 range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    for res in multi_res:
        xzrc[tik[tik_b]:tik[tik_b + 1], :] = res.get()  # 将每个进程得到的结果分block的发送到容器当中
        tik_b += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    '''
    xzrc = np.empty([num_all, 4])  # 新建一个存储每个圆环的容器
    j = 0
    for c1 in name_c:
        # x0_c1 = x0[c0 == c1]
        # z0_c1 = z0[c0 == c1]
        x_c1 = x[c == c1]
        z_c1 = z[c == c1]  # 提取单环的全部点云二维坐标
        data1 = np.vstack([x_c1, z_c1]).T
        # run RANSAC 算法
        # model = CircleLeastSquareModel()  # 类的实例化:用最小二乘生成已知模型
        ransac_fit, ransac_data = ransac(data1, model, 50, 2000, 0.5, 100, debug=False, return_all=True)  # ransac迭代
        x1 = ransac_fit.a * -0.5
        z1 = ransac_fit.b * -0.5
        r1 = 0.5 * math.sqrt(ransac_fit.a ** 2 + ransac_fit.b ** 2 - 4 * ransac_fit.c)
        # circle3 = Circle(xy=(x1, z1), radius=r1, alpha=0.5, fill=False, label="least square ransac fit circle")
        # plt.gcf().gca().add_artist(circle3)
        # plt.plot(x0_c1, z0_c1)
        # plt.show()
        # 存储数据
        xzrc[j, 0] = x1
        xzrc[j, 1] = z1
        xzrc[j, 2] = r1
        xzrc[j, 3] = c1
        j += 1
    '''
    return xzrc


# 环缝提取_分块
def c_seam_block(x, z, c, model, name_c, begin_, over_, t=0.13):
    num_ = over_ - begin_  # 计算每个块的圆环数量
    xzrc = np.empty([num_, 4])
    j = 0  # 循环计数器
    for c1 in name_c[begin_:over_]:
        x_c1 = x[c == c1]
        z_c1 = z[c == c1]  # 提取单环的全部点云二维坐标
        data1 = np.vstack([x_c1, z_c1]).T
        ransac_fit, ransac_data = ransac(data1, model, 50, 2000, t, 300, debug=False, return_all=True)  # ransac迭代
        'n:拟合模型所需的最小数据值数 k:算法中允许的最大迭代次数 t:用于确定数据点何时适合模型的阈值 d:断言模型很好地符合数据所需的接近数据值的数量'
        x1 = ransac_fit.a * -0.5
        z1 = ransac_fit.b * -0.5
        r1 = 0.5 * math.sqrt(ransac_fit.a ** 2 + ransac_fit.b ** 2 - 4 * ransac_fit.c)
        xzrc[j, 0] = x1
        xzrc[j, 1] = z1
        xzrc[j, 2] = r1
        xzrc[j, 3] = c1
        j += 1
    # print('每块最后一个值为', name_c[begin_:over_])
    print('已完成第', begin_, '至第', over_, '的圆环')
    return xzrc


# 环缝提取_分块
def c_seam_block_3(x, z, c, model, name_c, begin_, over_):
    num_ = over_ - begin_  # 计算每个块的圆环数量
    xzrc = np.empty([num_, 4])
    j = 0  # 循环计数器
    for c1 in name_c[begin_:over_]:
        x_c1 = x[c == c1]
        z_c1 = z[c == c1]  # 提取单环的全部点云二维坐标
        data1 = np.vstack([x_c1, z_c1]).T
        ransac_fit, ransac_data = ransac(data1, model, 500, 2000, 0.2, 1000, debug=False, return_all=True)  # ransac迭代
        x1 = ransac_fit.a * -0.5
        z1 = ransac_fit.b * -0.5
        r1 = 0.5 * math.sqrt(ransac_fit.a ** 2 + ransac_fit.b ** 2 - 4 * ransac_fit.c)
        xzrc[j, 0] = x1
        xzrc[j, 1] = z1
        xzrc[j, 2] = r1
        xzrc[j, 3] = c1
        j += 1
    # print('每块最后一个值为', name_c[begin_:over_])
    print('已完成第', begin_, '至第', over_, '的圆环')
    return xzrc


# 建立断点
# def cut_down(num, Piece=mp.cpu_count()):
#     tik = []
#     if num <= Piece:
#         tik.append(0)
#         print('点云数量过少，不能分块')
#     else:
#         n_pool = math.ceil(num / Piece)  # 每个池处理的最大点云数量
#         print('每个block的tik位置为', n_pool)
#         for i in range(0, Piece):
#             tik.append(i * n_pool)
#     tik.append(num)
#     return tik  # 输出每个断点位置
def cut_down(num, Piece=mp.cpu_count()):
    if num <= Piece:
        print('点云数量过少，不能分区间')
        return [0, num]
    block_size, remainder = divmod(num, Piece)  # 计算整除和余数
    # 生成每个块的大小（前remainder个块+1）
    sizes = [block_size + 1] * remainder + [block_size] * (Piece - remainder)
    print('每个区间的数量',sizes)
    # 计算累加分块点（从0开始）
    tik = np.array(list(accumulate(sizes, initial=0)))
    return tik


# 点云分割算法(非并行)
def cut_points(xzrc, xyzi, dr=0.15):
    # 准备工作
    inxyzc = []  # 新建符合条件的点云容器
    outxyzc = []  # 新建不符合条件的点云容器
    line_y = []  # 圆心的y的容器
    # 提取圆环当中符合条件的点云
    for i in xzrc[:, -1]:
        xyz_c = xyzi[xyzi[:, -1] == i, :]  # 提取当前的圆环点云
        line_y.append(np.mean(xyzi[xyzi[:, -1] == i, 1]))  # 提取圆心y坐标
        r_c = xzrc[xzrc[:, -1] == i, 2]  # 提取当前圆环半径
        for j in range(len(xyz_c)):
            R2 = (xzrc[xzrc[:, -1] == i, 0] - xyz_c[j, 0]) ** 2 + (xzrc[xzrc[:, -1] == i, 1] - xyz_c[j, 2]) ** 2
            d_r = np.abs(R2 - r_c ** 2)
            if d_r < dr:
                inxyzc.append(xyz_c[j, :])
            else:
                outxyzc.append(xyz_c[j, :])
    xyzc_in = np.array(inxyzc)  # 添加点云分割后的点云
    line_y = np.array(line_y)  # 顺便返回点云圆心y坐标
    xyzc_out = np.array(outxyzc)  # 添加点云分割后不符合的点云
    return xyzc_in, line_y, xyzc_out


def get_CenterDis(xzrc, xyzi, cpu_count=mp.cpu_count()):
    '求圆心距（并行）'
    n_points = len(xyzi)  # 点云数量
    dis = np.empty([n_points])  # 总距离容器
    tik = cut_down(n_points, cpu_count)  # 分块起始点
    # 并行计算准备
    pool = mp.Pool(processes=cpu_count)  # 开启多进程池，数量为cpu
    multi_res = [pool.apply_async(get_CenterDis_block, args=(xzrc, xyzi, tik[i], tik[i + 1])) for i in
                 range(cpu_count)]  # 将每个block需要处理的点云区间发送到每个进程当中
    tik_ = 0  # 计数器
    for res in multi_res:
        dis[tik[tik_]:tik[tik_ + 1]] = res.get()
        tik_ += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    return dis


def cut_point_ep(points, xzlwp, cpu_count=mp.cpu_count(), dr=0.15):
    '点云分割椭圆算法'
    n_points = len(points)  # 点云数量
    dis = np.empty([n_points])  # 总距离容器
    tik = cut_down(n_points, cpu_count)  # 分块起始点
    # 并行计算准备
    pool = mp.Pool(processes=cpu_count)  # 开启多进程池，数量为cpu
    multi_res = [pool.apply_async(cut_points_block_ep, args=(points, xzlwp, tik[i], tik[i + 1])) for i in
                 range(cpu_count)]  # 将每个block需要处理的点云区间发送到每个进程当中
    tik_ = 0  # 计数器
    for res in multi_res:
        dis[tik[tik_]:tik[tik_ + 1]] = res.get()
        tik_ += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    dis_mean = np.mean(dis)
    dis_std = np.std(dis)
    print('总距离均值', dis_mean, '总距离方差', dis_std)
    xyz_in = points[dis <= dr, :]
    xyz_out = points[dis > dr, :]
    return xyz_in, xyz_out


def cut_points_block_ep(points, xzlwp, a, b):
    '点云分割椭圆分块算法'
    dis = np.empty([b - a])  # 点到圆心的距离
    c = np.unique(points[:, -1])
    for i in range(b - a):
        xyz_ = points[a + i, :3]  # 当前点的空间位置
        c_i = points[a + i, -1]  # 当前点圆环名  ，-1
        xzlwp_ = xzlwp[c == c_i, :]  # 圆心位置
        xzlwp_ = xzlwp_.flatten()
        # xzlwp_ = np.reshape(xzlwp_, [-1])
        # arg_Ellipse = np.array([center[0], center[1], np.max([width, height]), np.min([width, height]), phi])  # 合并椭圆参数
        dis_ = ep.dis_ellipse(points[a + i, 0], points[a + i, 2], xzlwp_)  # 求点到椭圆的距离
        # dis_0 = dis_0.reshape(-1, 1)  # 便于查看
        dis[i] = np.nan_to_num(dis_, nan=1)  # 将空值转换为1
    return dis


# 点云分割算法优化
def cut_point(xzrc, xyzi, dr=0.15, cpu_count=mp.cpu_count(), xyz_c=None, d_r=None):
    n_points = len(xyzi)  # 点云数量
    dis = np.empty([n_points])  # 总距离容器
    tik = cut_down(n_points, cpu_count)  # 分块起始点
    # 并行计算准备
    pool = mp.Pool(processes=cpu_count)  # 开启多进程池，数量为cpu
    multi_res = [pool.apply_async(cut_points_block_new, args=(xzrc, xyzi[:, :5], tik[i], tik[i + 1])) for i in
                 range(cpu_count)]  # 将每个block需要处理的点云区间发送到每个进程当中
    tik_ = 0  # 计数器
    for res in multi_res:
        dis[tik[tik_]:tik[tik_ + 1]] = res.get()
        tik_ += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    # 统计距离均值和标准差
    dis_mean = np.mean(dis)
    dis_std = np.std(dis)
    print('总距离均值', dis_mean, '总距离方差', dis_std)
    # 根据距离进行点云分割+为纵缝提取做基础
    if xyz_c is None and d_r is None:
        xyz_in = xyzi[dis <= dr, :]
        xyz_out = xyzi[dis > dr, :]
    elif xyz_c is not None and d_r is None:
        xyz_in = xyz_c[dis <= dr, :]
        xyz_out = xyz_c[dis > dr, :]
    elif xyz_c is None and d_r is not None:
        item = np.where(np.logical_and(dis > d_r, dis < dr))
        xyz_in = xyzi[item, :]
        xyz_in = xyz_in[0, :, :]
        xyz_out = None
    # RMSE
    dis = dis[dis <= dr]
    RMSE = np.sqrt(np.sum(dis ** 2) / len(dis))
    print('RMSE:', RMSE)
    return xyz_in, xyz_out


# 点云分割算法优化(分块）
def cut_points_block_new(xzrc, xyzi, a, b):
    dis = np.empty([b - a])  # 点到圆心的距离
    c = xzrc[:, -1]
    for i in range(b - a):
        xyz_ = xyzi[a + i, :3]  # 当前点的空间位置
        c_i = xyzi[a + i, -1]  # 当前点圆环名  ，默认为-1列
        xzr_ = xzrc[c == c_i, :3]  # 圆心位置
        R2 = (xyz_[0] - xzr_[0, 0]) ** 2 + (xyz_[2] - xzr_[0, 1]) ** 2  # 点到圆心的距离
        dis[i] = np.abs(R2 - xzr_[0, -1] ** 2)
        # dis[i] = R2 - xzr_[0, -1] ** 2
    return dis

def get_CenterDis_block(xzrc, xyzi, a, b):
    '25.4.18分块求点到圆心的距离'
    dis = np.empty([b - a])  # 点到圆心的距离
    c = xzrc[:, -1]
    for i in range(b - a):
        xyz_ = xyzi[a + i, :3]  # 当前点的空间位置
        c_i = xyzi[a + i, -1]  # 当前点圆环名  ，默认为-1列
        xzr_ = xzrc[c == c_i, :3]  # 圆心位置
        R2 = (xyz_[0] - xzr_[0, 0]) ** 2 + (xyz_[2] - xzr_[0, 1]) ** 2  # 点到圆心的距离
        dis[i] = R2
    return dis

# 拟合直线算法
def fit_line_3d(xyz):
    line = pyrsc.Line()  # 创建直线拟合的类
    # A:直线的斜率，B：直线的截距，inliers：内点索引，
    # thresh：内点的距离阈值
    # maxIteration：RANSAC算法的拟合次数
    A, B, inliers = line.fit(xyz, thresh=0.05, maxIteration=500)
    line_xyz = np.vstack([A, B]).T  # 将直线设置为3行2列的表示方法
    return line_xyz


# 环缝提取算法
def discern_CS(xyzic):
    i = xyzic[:, -2]
    i_new = p1.normalization(i, 255)  # 强度值离散化，强度值直方图均衡化
    # 强度值累加
    c = np.unique(xyzic[:, -1])  # 返回圆环名的容器
    i_allC = np.zeros(len(c))  # 存储总强度值容器
    tik_c = 0
    for i in c:
        i_c = i_new[xyzic[:, -1] == i]  # 提取当前圆环xyzi值
        i_allC[tik_c] = np.sum(i_c)  # 单环强度值求和
        tik_c += 1  # 计数器递增
    # 缩放
    V = 255  # 缩放差
    i_allC_new = p1.normalization(i_allC, V)  # 和再次进行直方图均衡化
    R = 0.30  # 惩罚参数
    N = 40  # 左右迭代参与环数
    T = V * R  # 惩罚值
    # 判断环缝位置
    c_in = []  # 环缝容器
    # xyz_c_in = []
    for i in range(N, len(c) - N):
        Gl = np.sum(i_allC_new[(i - (N + 1)):i]) / (N - 2)  # 当前圆环左侧强度值均值
        Gr = np.sum(i_allC_new[(i + 1):(i + N)]) / (N - 2)  # 当前圆环右侧强度值均值
        Dl = Gl - i_allC_new[i]
        Dr = Gr - i_allC_new[i]  # 求左右差值
        if Dl >= T and Dr >= T:  # 如果超过惩罚阈值
            c_in.append(i)
            # xyz_c_in.append(xyzic[xyzic[:, -1] == c[i], :3])
    print('环缝圆环名为', c[c_in])
    # 折线图先显示一下
    # line1 = go.Scatter(x=c, y=i_allC_new, name='强度值趋势')  # 建立折线
    # line2 = go.Scatter(x=c, y=i_allC_new)  # 建立折线
    # fig = go.Figure([line1, line2])  # 建立窗口
    # fig.show()  # 显示
    '输出'
    xyz = xyzic[np.isin(xyzic[:, -1], c[c_in]), :3]  # 返回xyzic[:, -1]中有c[c_in]的行数
    '显示'
    line = go.Scatter(x=c, y=i_allC_new, name='强度值和趋势')
    # fig = go.Figure(line)
    # fig.show()
    print('离散化前最高强度值和为', np.max(i_allC), '离散化前最低强度值和为', np.min(i_allC))
    return xyz, c[c_in], line


# 基于半径的环缝提取算法
def radius_CS(rc):
    num = len(rc)
    c_new, index = np.unique(rc[:, 1], return_index=True)
    r_new = rc[index, 0]  # 按照顺序变化的半径趋势
    r_255 = p1.normalization(r_new, 255)  # 离散化后的半径比值
    line = go.Scatter(x=c_new, y=r_255, name='拟合半径趋势')
    # fig = go.Figure(line)
    # fig.show()
    mean_r_255 = np.mean(r_255)  # 半径的平均比值
    N = 40  # 左右迭代参与环数
    T = 12  # 惩罚值
    c_in = []  # 环缝容器
    for i in range(N, num - N):
        if r_255[i] > mean_r_255:
            Gl = np.sum(r_255[(i - (N + 1)):i]) / (N - 2)  # 当前圆环左侧半径值均值
            Gr = np.sum(r_255[(i + 1):(i + N)]) / (N - 2)  # 当前圆环右侧半径值均值
            Dl = r_255[i] - Gl
            Dr = r_255[i] - Gr  # 求左右差值
            if Dl >= T and Dr >= T:  # 如果超过惩罚阈值
                c_in.append(i)
    print('环缝圆环名为(基于半径)', rc[c_in, 1])
    print('离散化前最大半径为', np.max(r_new), '离散化前最小半径为', np.min(r_new))
    return rc[c_in, 1], line


# 基于每个圆环的平均强度值提取环缝
def meanIc_CS(xyzic, xzrc, num_cpu=mp.cpu_count()):
    # 圆环分割
    xzc_p = np.c_[xyzic[:, 0], xyzic[:, 2], xyzic[:, -1]]  # 圆柱面数据
    xzc_c = np.c_[xzrc[:, 0], xzrc[:, 1], xzrc[:, -1]]  # 圆心数据
    belong = Split_ring_mp(xzc_p, xzc_c, n=10000)  # 将圆平均分成多少份(并行计算)
    print('已完成切蛋糕')
    # 摘除非圆柱上的点
    belong_order = np.unique(belong)  # 从小到大升序排序
    num_belong = len(belong_order)  # 点云有多少份
    points_3500 = xyzic[belong < -3500, :]
    points_1500 = xyzic[belong > -1500, :]  # 摘除非圆柱上的点
    points_new = np.vstack([points_3500, points_1500])  # 圆柱上新的点
    points_new[:, -2] = p1.normalization(points_new[:, -2], 255)  # 强度值离散化
    # xyzic[:, -2] = p1.normalization(xyzic[:, -2], 255)  # 强度值离散化
    # 计算每个环的平均强度值
    i_c = np.empty(len(xzrc))
    # 并行计算准备
    num_C = len(xzrc)
    c_un = np.unique(xzrc[:, -1])  # 圆环从小到大排列
    tik = cut_down(num_C, num_cpu)  # 分块起止点
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    multi_res = [pool.apply_async(find_cImean_block, args=(points_new, c_un, tik[i], tik[i + 1])) for i in  # points_new
                 range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    tik_ = 0  # 计数器
    for res in multi_res:
        i_c[tik[tik_]:tik[tik_ + 1]] = res.get()
        tik_ += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    # 后期整理
    i_c = p1.normalization(i_c, 255)  # 均值离散化
    i_c_mean = np.mean(i_c)  # 平均强度值均值
    i_c_std = np.std(i_c)  # 平均强度值方差
    print('均值', i_c_mean, '标准差', i_c_std)
    # 基于强度值求环缝
    c_ = []  # 环缝的存储名
    c_id = []  # 环缝的存储下标器
    N = 60  # 左右环的收集平均值的间隔
    dis_max = i_c_mean - i_c_std * 3  # 最大差值
    j = N  # 环名下标计数器
    for i in range(N, len(i_c) - N):
        if i_c[i] <= i_c_mean - i_c_std * 2 and i_c[i] <= i_c[i - 1] and i_c[i] <= i_c[i + 1]:
            Il = np.mean(i_c[(i - N):i])
            Ir = np.mean(i_c[(i + 1):(i + 1 + N)])  # 求左右50邻域平均强度值
            if Il - i_c[i] >= dis_max and Ir - i_c[i] >= dis_max:
                c_.append(i)
                c_id.append(j)
        j += 1
    # c_name = c_un[np.array(c_)]  # 粗估环缝名
    # 精简环缝值
    c_nei = 70  # 确定左右邻域搜索数
    id_c_ry = np.empty(len(c_id))
    k = 0
    for i in c_id:
        c_i_70 = i_c[(i - c_nei):(i + c_nei + 1)]  # 找到环缝的左右60邻域
        id_i_120 = np.argmin(c_i_70)  # 找到邻域的最小值
        id_c_ry[k] = id_i_120 + i - c_nei  # 找到局部最小值的准确下标
        k += 1
    c_reduce = np.unique(id_c_ry)  # 精简环缝下标
    c_reduce = c_reduce.astype(int)
    print('环缝id', c_reduce)
    c_name_reduce = c_un[c_reduce]  # 细挑后的环缝名
    print('环缝名', c_name_reduce)
    # c_name_reduce = c_name_reduce.astype(int)
    return c_name_reduce, c_reduce


# 分块求每个环的平均强度值
def find_cImean_block(points_new, c_un, tik0, tik1):
    i_c_ = np.empty(tik1 - tik0)
    j = 0
    for i in c_un[tik0:tik1]:
        i_c_[j] = np.mean(points_new[points_new[:, 4] == i, 3])
        j += 1
    return i_c_


# 圆环y轴提取算法
def find_cy(y, c):
    c_name = np.unique(c)  # 返回圆环名
    y_c = np.empty(len(c_name))  # 存储圆心容器
    n = 0
    for i in c_name:
        y_c[n] = np.mean(y[c == i])  # 求当前圆环的平均y值
        n += 1
    return y_c


# 求圆环表面积（输入y值和半径）
def find_LateralArea(y, r):
    long = np.max(y) - np.min(y)  # 求侧面积长
    r_mean = np.mean(r)  # 求底半径
    width = r_mean * 3.14159 * 2  # 求侧面积宽
    LateralArea = long * width  # 求侧面积
    return LateralArea


# 精简环缝名
def reduce_c(c):
    c_ = np.unique(c)  # 将圆环名从小到大排列并删除重复圆环名
    c_new = [c_[0]]  # 初始圆环
    for i in range(len(c) - 1):
        if c_[i + 1] - c_[i] > 10:
            c_new.append(c_[i + 1])  # 留下精简后的圆环
    c_new = np.array(c_new)
    print(c_new)
    return c_new


# 求体素体元边长
def find_Larea(y, r, v=2.0):
    area = find_LateralArea(y, r)  # 求侧面积
    density = p1.num_area(len(y), area)  # 求密度
    pixel_ = 1 / np.sqrt(density) * v  # 求体素网格边长
    print('默认的体素边长为', pixel_)
    return pixel_


# 计算每个点到圆心的距离(非并行计算)
def dis_tcac(xyzic, xzrc):
    num = len(xyzic)
    dis_all = np.empty(num, dtype=np.float16)
    for i in range(num):
        xi = xyzic[i, 0]
        zi = xyzic[i, 2]
        index = xzrc[:, -1] == xyzic[i, -1]
        ri = xzrc[index, -2]
        length = np.sqrt((xi - xzrc[index, 0]) ** 2 + (zi - xzrc[index, 1]) ** 2)
        # dis_all[i] = length - ri  # 求点云距离面上的距离
        dis_all[i] = length  # 求点云距离圆心的距离
    # dis_all = p1.normalization(dis_all, 255)
    return dis_all


# 将圆环分成n份(点云以及圆环)
def Split_ring(xzc_point, xzc_c, n=10160):
    # 求每个点的反正切
    num = len(xzc_point)  # 点云数量
    d_y = np.empty([num])  # 存储点云y截距容器
    d_x = np.empty([num])  # 存储点云x截距容器
    belong = np.empty([num])  # 存储点云标签值容器
    j = 0  # 迭代计数器
    for i in xzc_point:
        ci = i[-1]
        xz_c = xzc_c[xzc_c[:, -1] == ci, :2]
        # k[j] = (i[1] - xz_c[0, 1])/(i[0] - xz_c[0, 0])
        d_y[j] = (i[1] - xz_c[0, 1])
        d_x[j] = (i[0] - xz_c[0, 0])
        # print(k[j])
        j += 1
    # angle = np.arctan(k)  # 求反正切值
    angle = np.arctan2(d_y, d_x)  # 求反正切值
    # 将角度分解
    max_a = np.pi * 2  # 最大角度
    single_a = max_a / n  # 求每个块的过渡
    for j in range(num):
        belong[j] = np.floor(angle[j] / single_a)  # 点云归属标签赋值
        # print(belong[j])
    return belong


# 将圆环分成n份(点云以及圆环)并行计算
def Split_ring_mp(xzc_point, xzc_c, n=10160, num_cpu=mp.cpu_count()):
    # 求每个点的反正切
    num = len(xzc_point)  # 点云数量
    d_yx = np.empty([num, 2])  # 存储点云截距的容器
    belong = np.empty([num])  # 存储点云标签值容器
    # 并行计算准备
    tik = cut_down(num, num_cpu)  # 分块起止点
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    multi_res = [pool.apply_async(find_arctan_block, args=(xzc_point, xzc_c, tik[i], tik[i + 1])) for i in
                 range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    tik_ = 0  # 计数器
    for res in multi_res:
        d_yx[tik[tik_]:tik[tik_ + 1], :] = res.get()
        tik_ += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    angle = np.arctan2(d_yx[:, 0], d_yx[:, 1])  # 求反正切值
    # 将角度分解
    single_a = np.pi * 2 / n  # 求每个块的过渡
    # 并行计算点云归属块
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    multi_res = [pool.apply_async(find_belong_block, args=(angle, single_a, tik[i], tik[i + 1])) for i in
                 range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    tik_ = 0  # 计数器
    for res in multi_res:
        belong[tik[tik_]:tik[tik_ + 1]] = res.get()
        tik_ += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    return belong


# 并行计算每个点的反正切
def find_arctan_block(xzc_point, xzc_c, tik0, tik1):
    d_yx_ = np.empty([tik1 - tik0, 2])
    j = 0  # 计数器
    for i in range(tik0, tik1):
        ci = xzc_point[i, -1]
        xz_c = xzc_c[xzc_c[:, -1] == ci, :2]
        d_yx_[j, 0] = (xzc_point[i, 1] - xz_c[0, 1])
        d_yx_[j, 1] = (xzc_point[i, 0] - xz_c[0, 0])
        j += 1
    print('已完成', tik0, '-', tik1, '的反正切')
    return d_yx_


# 计算每个点云属于哪个环块
def find_belong_block(angle, single_a, tik0, tik1):
    belong_ = np.empty(tik1 - tik0)
    j = 0  # 计数器
    for i in range(tik0, tik1):
        belong_[j] = np.floor(angle[i] / single_a)  # 点云归属标签赋值
        j += 1
    print('已完成', tik0, '-', tik1, '的环块归属')
    return belong_


# 纵缝提取(输入点云和环缝名及拟合参数)
def find_LJ_old(xyzic, c_in_, xzrc):
    '旧函数，已停止使用'
    xyz_LJ = []  # 存储纵缝容器
    num_c_in_ = len(c_in_)  # 环缝数量
    for i in range(num_c_in_ - 1):
        # 求出当前圆环的数据
        print('正在处理第', i + 1, '个环块')
        ci_xyz0 = xyzic[c_in_[i] <= xyzic[:, -1], :]
        ci_xyzi = ci_xyz0[ci_xyz0[:, -1] <= c_in_[i + 1], :]  # 当前两环缝之间的所有点云
        del ci_xyz0
        dis_all = dis_tcac(ci_xyzi, xzrc)  # 求当前环所有点云的距离
        '体素化'
        r = np.mean(xzrc[:, 2])
        # pixel_ = find_Larea(ci_xyzi[:, 1], r, v=1)  # 求体素体元边长
        pixel_ = find_Larea(ci_xyzi[:, 1], r, v=1.5)  # 求体素体元边长
        ci_voxel = vl.voxel(ci_xyzi[:, :3], pixel=pixel_)  # 建立体素
        del pixel_
        voxel_i = ci_voxel.P2V(ci_xyzi[:, 3])  # 连接点云强度值
        voxel_dis = ci_voxel.P2V(dis_all)  # 连接点云与圆心距离
        '种子点搜索'
        # 符合条件的点云
        ci_xyzi_begin_index = [ci_xyzi[:, -1] == (c_in_[i] + 5)]  # 符合种子点的开启条件
        ci_xyzi_begin = ci_xyzi[ci_xyzi_begin_index, :]  # 种子点云
        num_begin = len(ci_xyzi_begin_index)  # 种子点云数量
        '纵缝搜索迭代'
        # 种子体元入栈
        for i in range(num_begin):
            if voxel_i[ci_xyzi_begin[i, 0], ci_xyzi_begin[i, 1], ci_xyzi_begin[i, 1]] < 1:  # 未完成：范围暂时未确定
                pass
        # 滤波
        '''
        '将点云进行分块'
        xzc_p = np.c_[ci_xyzi[:, 0], ci_xyzi[:, 1], ci_xyzi[:, -1]]  # 点云需要的数据
        xzc_c = np.c_[xzrc[:, 0], xzrc[:, 1], xzrc[:, -1]]  # 圆环需要的数据
        belong = Split_ring(xzc_p, xzc_c, n)  # 将当前点云环分成n份
        belong_n = np.unique(belong)  # 从小到大升序排序
        num_belong = len(belong_n)  # 点云有多少份
        dis_all = dis_tcac(ci_xyzi, xzrc)  # 求当前环所有点云的距离
        
        # 计算每份点云的平均距离
        dis_c = np.empty([num_belong])
        k = 0
        for j in belong_n:
            dis_c[k] = np.mean(dis_all[belong == j])  # 平均距离赋值
            k += 1
        '判断是否为纵缝'
        i_all = []  # 记录所有符合条件的块
        n = 5  # 邻域参数
        dis_d = 0.02  # 差值阈值
        for l in range(n, num_belong - n):
            if dis_c[l] >= dis_c[l - 1] and dis_c[l] >= dis_c[l + 1] and dis_c[l] >= (np.mean(xzrc[:, 2]) + np.std(xzrc[:, 2]) * 10) and dis_c[l] - dis_c[l - n] >= 0.008 and dis_c[l] - dis_c[l + n] >= 0.008:
                # 求左右邻域平均值  存在求值问题
                Cl = np.mean(dis_c[(l - n * 4):l])
                Cr = np.mean(dis_c[(l + 1):(l + 1 + n * 4)])
                if dis_c[l] - Cl >= dis_d and dis_c[l] - Cr >= dis_d:
                    i_all.append(l)
        i_all = np.array(i_all)  # 数组化
        if len(i_all) > 0:
            print(len(i_all))
            index_p = belong_n[i_all]  # 符合条件的归属  IndexError: arrays used as indices must be of integer (or boolean) type
            index_pp = np.isin(belong, index_p)  # 符合归属的点下标
            xyz_LJ = np.append(xyz_LJ, ci_xyzi[index_pp, :])
        '''

    return xyz_LJ


def popStack(fit_i_id_un):  # 输入种子点体素位置
    first = fit_i_id_un[0, :]  # 提出来第一个
    other = fit_i_id_un[1:, :]  # 把剩下的留下
    return first, other


def bl_ABCD2(xyz, c, ρθ, n=0.02):
    '用曲率判断断面点云属于哪类模板'
    '合并数据'
    xyzcρθ = np.c_[xyz, c, ρθ]  # 合并数据
    F1 = None  # 提取第一个缝的容器
    '分别寻找A,B,C,D环块默认第一纵缝角度区间点云'
    # A环块
    F_a1 = xyzcρθ[xyzcρθ[:, -1] >= 2965, :]
    F_a1 = F_a1[F_a1[:, -1] <= 2975, :]
    # B环块
    F_b1 = xyzcρθ[xyzcρθ[:, -1] >= 3390, :]
    F_b1 = F_b1[F_b1[:, -1] <= 3400, :]
    # C环块
    F_c1 = xyzcρθ[xyzcρθ[:, -1] >= 2535, :]
    F_c1 = F_c1[F_c1[:, -1] <= 2545, :]
    # D环块
    F_d1 = xyzcρθ[xyzcρθ[:, -1] >= 3810, :]
    F_d1 = F_d1[F_d1[:, -1] <= 3820, :]
    '掐头去尾'
    F_a1 = F_a1[F_a1[:, 1] <= (np.max(F_a1[:, 1]) - n), :]
    F_a1 = F_a1[F_a1[:, 1] >= (np.min(F_a1[:, 1]) + n), :]
    F_b1 = F_b1[F_b1[:, 1] <= (np.max(F_b1[:, 1]) - n), :]
    F_b1 = F_b1[F_b1[:, 1] >= (np.min(F_b1[:, 1]) + n), :]
    F_c1 = F_c1[F_c1[:, 1] <= (np.max(F_c1[:, 1]) - n), :]
    F_c1 = F_c1[F_c1[:, 1] >= (np.min(F_c1[:, 1]) + n), :]
    F_d1 = F_d1[F_d1[:, -2] <= (np.max(F_d1[:, 1]) - n), :]
    F_d1 = F_d1[F_d1[:, 1] >= (np.min(F_d1[:, 1]) + n), :]
    'A B C D环块体元数量'
    num_F_a1 = len(F_a1)
    num_F_b1 = len(F_b1)
    num_F_c1 = len(F_c1)
    num_F_d1 = len(F_d1)
    '分别计算ABCD环块符合曲率阈值的体元数量'
    m = 0.05  # 曲率阈值
    # 计算数量
    num_a1 = len(F_a1[F_a1[:, 3] > m, :])
    num_b1 = len(F_b1[F_b1[:, 3] > m, :])
    num_c1 = len(F_c1[F_c1[:, 3] > m, :])
    num_d1 = len(F_d1[F_d1[:, 3] > m, :])  # 曲率大于等于0.05的体素数量
    p = np.array([num_a1 / num_F_a1, num_b1 / num_F_b1, num_c1 / num_F_c1, num_d1 / num_F_d1])  # 计算比率
    print(p)  # 打印比率值
    '判断环块模板'
    belong_ = np.argmax(p)  # 环块归属
    # 只需要下标，不需要返回别的
    belong_ = np.argmax(p)  # 环块归属
    if belong_ == 0:
        print('此环块判断属于A模板')
        F1 = F_a1[:, :3]
    elif belong_ == 1:
        print('此环块判断属于B模板')
        F1 = F_b1[:, :3]
    elif belong_ == 2:
        print('此环块判断属于C模板')
        F1 = F_c1[:, :3]
    elif belong_ == 3:
        print('此环块判断属于D模板')
        F1 = F_d1[:, :3]
    return belong_, F1


def bl_ABCD(voxel_Y_points_local, i, n=5):
    '通过曲率值判断环块属于哪类模板'
    '输入曲率赋值后的体素'
    poyi_ = np.c_[voxel_Y_points_local, i]
    # np.savetxt('E:\\PointCloudSourceFile\\txt\\Shield\\poyi'+str()+, poyi_)
    F1 = None
    '分别寻找A,B,C环块默认第一纵缝区间点云'
    '''
    # A环块
    F_a1 = poyi_[poyi_[:, 1] >= 2090, :]
    F_a1 = F_a1[F_a1[:, 1] <= 2105, :]
    # B环块
    F_b1 = poyi_[poyi_[:, 1] >= 2390, :]
    F_b1 = F_b1[F_b1[:, 1] <= 2405, :]
    # C环块
    F_c1 = poyi_[poyi_[:, 1] >= 1790, :]
    F_c1 = F_c1[F_c1[:, 1] <= 1805, :]
    # D环块
    F_d1 = poyi_[poyi_[:, 1] >= 2690, :]
    F_d1 = F_d1[F_d1[:, 1] <= 2705, :]
    '''
    # A环块
    F_a1 = poyi_[poyi_[:, 1] >= 2965, :]
    F_a1 = F_a1[F_a1[:, 1] <= 2975, :]
    # B环块
    F_b1 = poyi_[poyi_[:, 1] >= 3390, :]
    F_b1 = F_b1[F_b1[:, 1] <= 3400, :]
    # C环块
    F_c1 = poyi_[poyi_[:, 1] >= 2535, :]
    F_c1 = F_c1[F_c1[:, 1] <= 2545, :]
    # D环块
    F_d1 = poyi_[poyi_[:, 1] >= 3810, :]
    F_d1 = F_d1[F_d1[:, 1] <= 3820, :]
    '通过Y轴坐标掐头去尾'
    F_a1 = F_a1[F_a1[:, -2] <= (np.max(F_a1[:, -2]) - n), :]
    F_a1 = F_a1[F_a1[:, -2] >= (np.min(F_a1[:, -2]) + n), :]
    F_b1 = F_b1[F_b1[:, -2] <= (np.max(F_b1[:, -2]) - n), :]
    F_b1 = F_b1[F_b1[:, -2] >= (np.min(F_b1[:, -2]) + n), :]
    F_c1 = F_c1[F_c1[:, -2] <= (np.max(F_c1[:, -2]) - n), :]
    F_c1 = F_c1[F_c1[:, -2] >= (np.min(F_c1[:, -2]) + n), :]
    F_d1 = F_d1[F_d1[:, -2] <= (np.max(F_d1[:, -2]) - n), :]
    F_d1 = F_d1[F_d1[:, -2] >= (np.min(F_d1[:, -2]) + n), :]
    'A B C环块体元数量'
    num_F_a1 = len(F_a1)
    num_F_b1 = len(F_b1)
    num_F_c1 = len(F_c1)
    num_F_d1 = len(F_d1)
    '分别计算ABC环块符合曲率阈值的体元数量'
    m = 0.05  # 曲率阈值 0.04
    num_a1 = len(F_a1[F_a1[:, -1] > m, :])
    num_b1 = len(F_b1[F_b1[:, -1] > m, :])
    num_c1 = len(F_c1[F_c1[:, -1] > m, :])
    num_d1 = len(F_d1[F_d1[:, -1] > m, :])  # 曲率大于等于0.05的体素数量
    p = np.array([num_a1 / num_F_a1, num_b1 / num_F_b1, num_c1 / num_F_c1, num_d1 / num_F_d1])  # 计算比值
    print(p)
    '判断环块模板'
    belong_ = np.argmax(p)  # 环块归属
    if belong_ == 0:
        print('此环块判断属于A模板')
        F1 = F_a1[:, :3]
    elif belong_ == 1:
        print('此环块判断属于B模板')
        F1 = F_b1[:, :3]
    elif belong_ == 2:
        print('此环块判断属于C模板')
        F1 = F_c1[:, :3]
    elif belong_ == 3:
        print('此环块判断属于D模板')
        F1 = F_d1[:, :3]
    # return belong_, F1, poyi_
    return belong_, F1


def find_LJ_FV(xyzicc, RB_S, RB_E, xzrcy):
    '2022.11.5非体素化极坐标纵缝提取版'
    # 准备工作
    num_c = len(RB_S) - 2  # 参与计算的环块个数 = all-2
    type_RingBlock = np.empty(num_c)  # 环块所属模板类型容器
    θg = np.array([[[415, 425], [3700, 3765], [3880, 3945]], [[1690, 1700], [2425, 2490], [2605, 2670]], [[1685, 1695], [3270, 3335], [3450, 3515]], [[410, 420], [2845, 2905], [3025, 3090]]])
    # 开始循环
    F_all = {}  # 存储缝的词典
    for i in range(num_c):
        print('正在处理第', i + 1, '个环块')
        # 遍历到当前环块
        xyzicc_ = xyzicc[xyzicc[:, -2] < RB_E[i + 1], :]
        xyzicc_ = xyzicc_[xyzicc_[:, -2] > RB_S[i + 1], :]  # 循环到当前环块的所有点云
        # np.savetxt('E:\\PointCloudSourceFile\\txt\\Shield\\ShieldRing-'+str(i)+'.txt',xyzicc_,fmt='%.05f')
        '计算当前中轴线（非体素化使用）'
        xzrcy_ = xzrcy[xzrcy[:, -2] < RB_E[i + 1], :]
        xzrcy_ = xzrcy_[xzrcy_[:, -2] > RB_S[i + 1], :]  # 当前环块的空间圆心点
        # 拟合中轴线
        line_ = np.vstack([xzrcy_[:, 0], xzrcy_[:, -1], xzrcy_[:, 1]]).T  # 圆心位置容器
        KB_line_ = fit_line_3d(line_)  # ransac空间直线拟合
        # 找到拟合后的新圆心
        n = 0  # 计数器
        xyzc_new = np.empty([len(xzrcy_[:, -1]), 4])
        xyzc_new[:, 1] = xzrcy_[:, -1]
        xyzc_new[:, -1] = xzrcy_[:, -2]
        for j in xzrcy_[:, -1]:
            k_ = (j - KB_line_[1, 1]) / KB_line_[1, 0]  # 求k
            x_ = k_ * KB_line_[0, 0] + KB_line_[0, 1]  # 求X
            z_ = k_ * KB_line_[2, 0] + KB_line_[2, 1]  # 求Z
            xyzc_new[n, 0] = x_
            xyzc_new[n, 2] = z_
            n += 1
        ρθ_ = p1.XYZ2ρθ_mp(xyzicc_[:, :-1], xyzc_new, n=4250)  # 合并圆柱位置和点云属性
        # 判断环块类型
        type_RingBlock[i], Fa_ = bl_ABCD2(xyzicc_[:, :3], xyzicc_[:, -1], ρθ_)  # 返回F1缝点云以及环块所属
        F_all[str(i) + 'a'] = Fa_  # 顺便提取A缝
        '寻找其他纵缝'
        xyzcρθ_ = np.c_[xyzicc_[:, :3], xyzicc_[:, -1], ρθ_]
        Fb_, Fc_, Fd_ = findF_others2(xyzcρθ_, θg[int(type_RingBlock[i])])
        F_all[str(i) + 'b'] = Fb_[:, :3]
        F_all[str(i) + 'c'] = Fc_[:, :3]
        F_all[str(i) + 'd'] = Fd_[:, :3]
    return type_RingBlock, F_all


def find_LJ_un(xyzicc, RB_S, RB_E, xzrcy):
    '2022.11.22纵缝提取普适性版'
    # 准备工作
    num_c = len(RB_S) - 2  # 参与计算的环块个数 = all-2
    F_all = {}  # 存储缝的词典
    m = 0.004 * 6  # 斜缝搜索提取最高圆心距的差值 4
    θ23_all = np.arange(2425, 3946)  # 所有斜缝经历的角度区间
    k = 0.024  # 斜缝的斜率的绝对值（y/角度值）
    for i in range(num_c):  # 按完整环块进行循环
        print('正在处理第', i + 1, '个环块')
        # 遍历到当前环块
        xyzicc_ = xyzicc[xyzicc[:, -2] < RB_E[i + 1], :]
        xyzicc_ = xyzicc_[xyzicc_[:, -2] > RB_S[i + 1], :]  # 循环到当前环块的所有点云
        np.set_printoptions(precision=5)  # 设置小数位置为5位
        '计算当前中轴线（非体素化使用）'
        xzrcy_ = xzrcy[xzrcy[:, -2] < RB_E[i + 1], :]
        xzrcy_ = xzrcy_[xzrcy_[:, -2] > RB_S[i + 1], :]  # 当前环块的空间圆心点
        # 拟合中轴线
        line_ = np.vstack([xzrcy_[:, 0], xzrcy_[:, -1], xzrcy_[:, 1]]).T  # 圆心位置容器
        KB_line_ = fit_line_3d(line_)  # ransac空间直线拟合
        # 找到拟合后的新圆心
        n = 0  # 计数器
        xyzc_new = np.empty([len(xzrcy_[:, -1]), 4])
        xyzc_new[:, 1] = xzrcy_[:, -1]
        xyzc_new[:, -1] = xzrcy_[:, -2]
        for j in xzrcy_[:, -1]:
            k_ = (j - KB_line_[1, 1]) / KB_line_[1, 0]  # 求k
            x_ = k_ * KB_line_[0, 0] + KB_line_[0, 1]  # 求X
            z_ = k_ * KB_line_[2, 0] + KB_line_[2, 1]  # 求Z
            xyzc_new[n, 0] = x_
            xyzc_new[n, 2] = z_
            n += 1
        ρθ_ = p1.XYZ2ρθ_mp(xyzicc_[:, :-1], xyzc_new, n=4250)  # 合并圆柱位置和点云属性
        # θ_un_ = np.unique(ρθ_[:, 1])  # 对角度值进行精简
        xyziccρθ_ = np.c_[xyzicc_, ρθ_]  # 点云属性集中
        del xyzicc_, ρθ_
        # output_ = xyziccρθ_[xyziccρθ_[:, -2] >= (np.max(xyziccρθ_[:, -2])-m), :6]
        # output_ = output_[output_[:, -1] >= 0.05, :]
        # np.savetxt('E:\\PointCloudSourceFile\\txt\\Shield\\p-m'+str(i)+'.txt', output_)
        # 寻找纵缝（一）
        '计算每个角度区间大于0.05的概率'
        θ_tik_ = np.arange(2960, 3820 + 1, 10)  # 将角度每10分一个
        p_θ_ = np.zeros(len(θ_tik_) - 1)  # 存储
        ρ_mean_θ_ = np.zeros(len(θ_tik_) - 1)  # 长度
        for l in range(len(θ_tik_) - 1):
            l_ = xyziccρθ_[xyziccρθ_[:, -1] <= θ_tik_[l + 1], :]
            l_ = l_[l_[:, -1] >= θ_tik_[l], :]  # 提取当前角度区间点云
            l_c_ = l_[l_[:, -3] > 0.05, :]  # 提取大于0.05的曲率
            if len(l_) > 0:
                p_θ_[l] = len(l_c_) / len(l_)  # 符合曲率条件的比值
                ρ_mean_θ_[l] = np.mean(l_c_[:, -2])
        index_02 = np.argwhere(p_θ_ >= 0.15)  # 首先遍历比值大于0.2的区间段
        print(index_02)
        index_max_ρ = np.argmax(ρ_mean_θ_[index_02])  # 找到最大圆心距的下标
        print(index_max_ρ)
        # 输出正确的纵缝点云
        index_Ture = index_02[index_max_ρ]
        print(index_Ture)
        l_ = xyziccρθ_[xyziccρθ_[:, -1] <= θ_tik_[index_Ture + 1], :]
        l_ = l_[l_[:, -1] >= θ_tik_[index_Ture], :]  # 提取当前角度区间点云
        LJ_1_ = l_[l_[:, -3] >= 0.05, :5]  # 提取大于0.05的曲率
        F_all[str(i) + 'a'] = LJ_1_  # 将缝存储到容器中
        # 寻找纵缝（二、三）
        '准备工作'
        y_min_ = np.min(xyziccρθ_[:, 1])
        y_max_ = np.max(xyziccρθ_[:, 1])  # 求y的开始和结束
        LJ_2_, LJ_3_, p_lr = find_LJ23(xyziccρθ_, y_max_, y_min_, θ23_all, m, k)  # 通过并行计算求出两条斜缝
        F_all[str(i) + 'b'] = LJ_2_
        F_all[str(i) + 'c'] = LJ_3_
        # np.savetxt('E:\\PointCloudSourceFile\\txt\\Shield\\p_all_lr.txt', p_lr)

        # 寻找第四个缝

        '''
        '限制纵缝搜索区间'
        θ_tik_ = np.arange(2960, 3820+1, 10)
        p_θ_ = np.zeros(len(θ_tik_)-1)  # 长度
        for l in range(len(θ_tik_)-1):
            l_ = xyziccρθ_[xyziccρθ_[:, -1] <= θ_tik_[l+1], :]
            l_ = l_[l_[:, -1] >= θ_tik_[l], :]  # 提取当前角度区间点云
            l_c_ = l_[l_[:, -3] > 0.05, :]  # 提取大于0.05的曲率
            if len(l_) > 0:
                p_θ_[l] = len(l_c_)/len(l_)  # 符合曲率条件的比值
        # 画一条折线图
        # line = go.Scatter(x=np.arange(len(θ_tik_)-1), y=p_θ_)
        # fig = go.Figure(line)
        # fig.show()
        id_max_ = np.argmax(p_θ_)
        # 输出峰值
        l_ = xyziccρθ_[xyziccρθ_[:, -1] <= θ_tik_[id_max_ + 1], :]
        l_ = l_[l_[:, -1] >= θ_tik_[id_max_], :]  # 提取当前角度区间点云
        LJ_1_ = l_[l_[:, -3] > 0.05, :5]  # 提取大于0.05的曲率
        # np.savetxt('E:\\PointCloudSourceFile\\txt\\Shield\\LJ1_'+str(i)+'.txt', LJ_1_)
        '''
    return F_all


def find_LJ_Curve(xyzic, RB_S, RB_E, xzrcy, n=3000):
    '2023.6.26纵缝提取深度剩余法'
    # 准备工作
    num_c = len(RB_S) - 2  # 参与计算的环块个数 = all-2
    F_all = {}  # 存储缝的词典
    xyzc = np.c_[xzrcy[:, 0], xzrcy[:, -1], xzrcy[:, 1], xzrcy[:, -2]]  # 每个圆环的
    r_mean = np.mean(xzrcy[:, -3])  # 平均半径
    cl = r_mean * 2 * np.pi  # 周长
    pixel = cl / n  # 体素平面半径
    k = -6  # 斜缝搜索斜率
    # 开始循环盾构环
    for i in range(num_c):
        print('正在处理第', i + 1, '个环块')
        # 遍历到当前环块
        xyzic_ = xyzic[xyzic[:, -1] < RB_E[i + 1], :]
        xyzic_ = xyzic_[xyzic_[:, -1] > RB_S[i + 1], :]  # 循环到当前环块的所有点云
        # np.savetxt('E:\\PointCloudSourceFile\\txt\\Shield\\ShieldRing-' + str(i) + '.txt', xyzic_, fmt='%.05f')
        # ρθ_ = XYZ2ρθ_mp(xyzic_, xyzc, n, xzrcy[:, -3])  # 合并圆柱位置和点云属性  # 加一个求半径的
        ρθy_ = XYZ2ρθy_mp(xyzic_, xyzc, n, xzrcy[:, -3])  # 合并圆柱位置和点云属性
        xyzicρθy_ = np.c_[xyzic_, ρθy_]  # 点云属性集中
        # 进一步剔除其他非必要点
        xyzicρθy_ = xyzicρθy_[xyzicρθy_[:, -3] >= (np.max(xyzicρθy_[:, -3]) - 2.5 * pixel), :]
        xyzicρθy_ = xyzicρθy_[xyzicρθy_[:, 1] >= (np.min(xyzicρθy_[:, 1]) + 10 * pixel), :]
        xyzicρθy_ = xyzicρθy_[xyzicρθy_[:, 1] <= (np.max(xyzicρθy_[:, 1]) - 10 * pixel), :]
        xyzicρθy_[:,-1] -= np.min(xyzicρθy_[:, -1])
        # np.savetxt('E:\\MyCodeWorkPlace\\Python\\Shield tunnel Deformation monitoring\\xyzicρθy_.txt',xyzicρθy_,fmt='%.05f')
        # ρθY = vl.XYZ2ρθY(xyzicρθ_[:, :5], xzrcy[:, :-1], n=n)  # 点极坐标  （后期需要和以上算法进行合并）
        PV = vl.voxel_ρθY(xyzicρθy_[:,-3:], pixel=[pixel, 1, pixel])  # 建立体素
        PV.P2V(xyzicρθy_[:, 3])  # 有值体素赋值
        # PV.watch_voxel(r_mean,r_mean,n)
        '在给定框架内，找到所有起点的角度值，然后给一个斜率模板直线'
        θ_all = np.unique(PV.points_local_un[:, 1])  # 第一个环的有值体素弧度值容器
        dis_all_rl = np.zeros([θ_all.shape[0], 2])  # 存储距离容器
        j = 0  # 计数器
        for l in θ_all:
            b_r = 248 - k * l  # 确定截距值
            b_l = k * l  # 确定截距值
            dis_r = p1.get_distance_point2line(PV.points_local_un[:, 1:], [k, b_r])  # 体素在这条线上所有的平面距离
            dis_l = p1.get_distance_point2line(PV.points_local_un[:, 1:], [-k, b_l])  # 体素在这条线上所有的平面距离
            dis_all_rl[j, 0] = PV.points_local_un[dis_r <= 3, 1:].shape[0]  # 距离不超过3的体素数量
            dis_all_rl[j, 1] = PV.points_local_un[dis_l <= 3, 1:].shape[0]  # 距离不超过3的体素数量
            j += 1  # 刷新计数器
        index_r = np.argmax(dis_all_rl[:, 0])
        index_l = np.argmax(dis_all_rl[:, 1])  # 最大值位置
        b_r = 248 - k * θ_all[index_r]  # 确定截距值
        b_l = k * θ_all[index_l]  # 右侧截距值
        dis_r = p1.get_distance_point2line(PV.points_local_un[:, 1:], [k, b_r])  # 体素在这条线上所有的平面距离
        dis_l = p1.get_distance_point2line(PV.points_local_un[:, 1:], [-k, b_l])  # 体素在这条线上所有的平面距离
        out_r = PV.points_local_un[dis_r <= 3, :]
        out_l = PV.points_local_un[dis_l <= 3, :]  # 输出体素
        F_all[str(i) + 'c'] = xyzicρθy_[PV.V2P(out_r), :5]
        F_all[str(i) + 'd'] = xyzicρθy_[PV.V2P(out_l), :5]
    return F_all


def find_LJ_MAX(xyzicc, RB_S, RB_E, xzrcy, n=4250):
    '2023.4.10纵缝提取普适性版'
    # 准备工作
    num_c = len(RB_S) - 2  # 参与计算的环块个数 = all-2
    F_all = {}  # 存储缝的词典
    xyzc = np.c_[xzrcy[:, 0], xzrcy[:, -1], xzrcy[:, 1], xzrcy[:, -2]]
    r = xzrcy[:, -3]  # 半径
    θ1 = np.arange(int(2425 / 4250 * n), int(3946 / 4250 * n + 1))  # 纵缝1区间点云
    θ2 = np.arange(int(410 / 4250 * n), int(1700 / 4250 * n + 1))  # 纵缝2区间点云 410-1700
    k = 0.024 * n / 4250  # 默认斜率
    for i in range(num_c):
        print('正在处理第', i + 1, '个环块')
        # 遍历到当前环块
        xyzicc_ = xyzicc[xyzicc[:, -2] < RB_E[i + 1], :]
        xyzicc_ = xyzicc_[xyzicc_[:, -2] > RB_S[i + 1], :]  # 循环到当前环块的所有点云
        ρθ_ = XYZ2ρθ_mp(xyzicc_[:, :-1], xyzc, n, r)  # 合并圆柱位置和点云属性  # 加一个求半径的
        xyziccρθ_ = np.c_[xyzicc_, ρθ_]  # 点云属性集中
        # xyziccρθ_ρ_ = xyziccρθ_[xyziccρθ_[:, -2] >= 0, :]  # 在隧道上的点云
        del xyzicc_, ρθ_
        # 寻找纵缝1
        num_θ1all = np.zeros(len(θ1))
        pp = np.zeros(len(θ2))
        for j in range(len(θ1)):
            xyziccρθ_p_o = xyziccρθ_[xyziccρθ_[:, -1] == θ1[j], :]
            p_o_c = xyziccρθ_p_o[xyziccρθ_p_o[:, -3] >= 0.05, :]
            num_θ1all[j] = len(p_o_c)
            # pp[j] = len(p_o_c)/len(xyziccρθ_p_o)
            # num_θ1all[j] =len(xyziccρθ_p_o)
        # np.savetxt('E:\\2023硕士研究上\\0：盾构隧道论文\\23.4.20\\o-p_0a.txt', pp, fmt='%.05f')
        # np.savetxt('E:\\2023硕士研究上\\0：盾构隧道论文\\曲率概率.txt', pp)
        # np.savetxt('E:\\2023硕士研究上\\0：盾构隧道论文\\最大圆心距.txt', max_p)
        id1_max = np.argmax(num_θ1all)
        out_a = xyziccρθ_[xyziccρθ_[:, -1] == θ1[id1_max], :6]
        than_005 = out_a[out_a[:, -1] >= 0.05]
        max_x = np.max(than_005[:, 0])
        min_x = np.min(than_005[:, 0])
        index = np.where(np.logical_and(out_a[:, 0] >= min_x, out_a[:, 0] <= max_x))
        out_a = out_a[index, :]  # 剩余点云
        F_all[str(i) + 'a'] = out_a[0, :, :]
        print('a的缝的位置为', min_x, '-', max_x)
        # 寻找纵缝2
        num_θ2all = np.zeros(len(θ2))
        for j in range(len(θ2)):
            xyziccρθ_p_o = xyziccρθ_[xyziccρθ_[:, -1] == θ2[j], :]
            p_o_c = xyziccρθ_p_o[xyziccρθ_p_o[:, -3] >= 0.05, :]
            num_θ2all[j] = len(p_o_c)
            if len(xyziccρθ_p_o) > 0:
                pp[j] = len(p_o_c) / len(xyziccρθ_p_o)
        np.savetxt('E:\\2023硕士研究上\\0：盾构隧道论文\\23.4.20\\to-p_0b.txt', np.c_[θ2, pp], fmt='%.05f')
        id2_max = np.argmax(num_θ2all)
        out_b = xyziccρθ_[xyziccρθ_[:, -1] == θ2[id2_max], :6]
        than_005 = out_b[out_b[:, -1] >= 0.05]
        max_x = np.max(than_005[:, 0])
        min_x = np.min(than_005[:, 0])
        index = np.where(np.logical_and(out_b[:, 0] >= min_x, out_b[:, 0] <= max_x))
        out_b = out_b[index, :]  # 剩余点云
        F_all[str(i) + 'b'] = out_b[0, :, :]
        print('b的缝的位置为', min_x, '-', max_x)
        # 寻找纵缝34  点的旋转算法
        θ3 = np.arange(int(2425 / 4250 * n), int(3765 / 4250 * n + 1))  # 纵缝3区间点云

    return F_all


def θy2θY(θy, k):
    '二维点集坐标转为新二维点集坐标'
    dy = np.max(θy[:, 1]) - np.min(θy[:, 1])
    а = np.arctan2(k)  # 角度值
    sink = np.sin(а)  # 正弦值
    y_new = dy / sink  # 输出新的长度

    return


def find_LJ_MAX_c(xyzic, RB_S, RB_E, xzrcy, n=4250):
    '计算每个Piece中点到圆心的距离，然后求距离数组的方差'
    # 准备工作
    num_c = len(RB_S) - 2  # 参与计算的环块个数 = all-2
    F_all = {}  # 存储缝的词典
    xyzc = np.c_[xzrcy[:, 0], xzrcy[:, -1], xzrcy[:, 1], xzrcy[:, -2]]
    r = xzrcy[:, -3]  # 半径
    θ1 = np.arange(int(2425 / 4250 * n), int(3946 / 4250 * n + 1))  # 纵缝1区间点云
    θ2 = np.arange(int(410 / 4250 * n), int(1700 / 4250 * n + 1))  # 纵缝2区间点云 410-1700
    for i in range(num_c):
        print('正在处理第', i + 1, '个环块')
        # 遍历到当前环块
        xyzicc_ = xyzic[xyzic[:, -1] < RB_E[i + 1], :]
        xyzicc_ = xyzicc_[xyzicc_[:, -1] > RB_S[i + 1], :]  # 循环到当前环块的所有点云
        ρθ_ = XYZ2ρθ_mp(xyzicc_, xyzc, n, r)  # 合并圆柱位置和点云属性  # 加一个求半径的
        xyziccρθ_ = np.c_[xyzicc_, ρθ_]  # 点云属性集中
        # 寻找纵缝1
        num_θ1all = np.zeros(len(θ1))
        for j in range(len(θ1)):
            xyziccρθ_p_o = xyziccρθ_[xyziccρθ_[:, -1] == θ1[j], :]
            num_θ1all[j] = np.var(xyziccρθ_p_o[:, -2])

        # np.savetxt('E:\\2023硕士研究上\\0：盾构隧道论文\\23.4.20\\o-p_'+str(i)+'a.txt', np.c_[θ1, num_θ1all], fmt='%.05f')
        # np.savetxt('E:\\2023硕士研究上\\0：盾构隧道论文\\曲率概率.txt', pp)
        # np.savetxt('E:\\2023硕士研究上\\0：盾构隧道论文\\最大圆心距.txt', max_p)
        '''
        num_un = np.unique(num_θ1all)
        print(np.mean(num_un))
        print(np.std(num_un))
        '''
        num_θ1all = np.nan_to_num(num_θ1all)
        index_ = num_θ1all >= 0.000083
        out_a = xyziccρθ_[np.isin(xyziccρθ_[:, -1], θ1[index_]), :6]
        '''
        than_005 = out_a[out_a[:, -1] >= 0.05]
        max_x = np.max(than_005[:, 0])
        min_x = np.min(than_005[:, 0])
        index = np.where(np.logical_and(out_a[:, 0] >= min_x, out_a[:, 0] <= max_x))
        out_a = out_a[index, :]  # 剩余点云
        '''
        F_all[str(i) + 'a'] = out_a
        # print('a的缝的位置为', min_x, '-', max_x)
        # 寻找纵缝2
        num_θ2all = np.zeros(len(θ2))
        for j in range(len(θ2)):
            xyziccρθ_p_o = xyziccρθ_[xyziccρθ_[:, -1] == θ2[j], :]
            num_θ2all[j] = np.var(xyziccρθ_p_o[:, -2])
        # np.savetxt('E:\\2023硕士研究上\\0：盾构隧道论文\\23.4.20\\o-p_' + str(i) + 'b.txt', np.c_[θ2, num_θ2all], fmt='%.05f')
        num_θ2all = np.nan_to_num(num_θ2all)
        index_ = num_θ2all >= 0.000083
        out_b = xyziccρθ_[np.isin(xyziccρθ_[:, -1], θ2[index_]), :6]
        '''
        than_005 = out_b[out_b[:, -1] >= 0.05]
        max_x = np.max(than_005[:, 0])
        min_x = np.min(than_005[:, 0])
        index = np.where(np.logical_and(out_b[:, 0] >= min_x, out_b[:, 0] <= max_x))
        out_b = out_b[index, :]  # 剩余点云
        '''
        F_all[str(i) + 'b'] = out_b
    return F_all


def XYZ2ρθ_mp(xyzic, xyzc, n, r, num_cpu=mp.cpu_count()):
    '点云笛卡尔转极坐标（p修改版，并行版）'
    num = len(xyzic)  # 点云数量
    tik = cut_down(num)  # 并行计算分块
    ρθ = np.empty([num, 2])  # 新建一个存储点云ρθ的容器
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    # 开始进行并行计算
    multi_res = [pool.apply_async(get_ρθ_block, args=(xyzic, xyzc, tik[i], tik[i + 1], n, r)) for i in
                 range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    tik_ = 0  # 计数器
    for res in multi_res:
        ρθ[tik[tik_]:tik[tik_ + 1], :] = res.get()
        tik_ += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    # 归零化
    min_ρθ = ρθ.min(0)  # 求最小值
    # ρθ[:, 0] -= min_ρθ[0]
    ρθ[:, 1] -= min_ρθ[1]
    return ρθ

def XYZ2ρθy_mp(xyzic, xyzc, n, r, num_cpu=mp.cpu_count()):
    '点云笛卡尔转极坐标（p修改版，并行版）'
    num = len(xyzic)  # 点云数量
    tik = cut_down(num)  # 并行计算分块
    ρθy = np.empty([num, 3])  # 新建一个存储点云ρθ的容器
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    # 开始进行并行计算
    multi_res = [pool.apply_async(get_ρθ_block, args=(xyzic, xyzc, tik[i], tik[i + 1], n, r)) for i in
                 range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    tik_ = 0  # 计数器
    for res in multi_res:
        ρθy[tik[tik_]:tik[tik_ + 1], :-1] = res.get()
        tik_ += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    # 转移y坐标
    ρθy[:, 2] = xyzic[:,1]
    # 归零化
    min_ρθy = ρθy.min(0)  # 求最小值
    # ρθ[:, 0] -= min_ρθ[0]
    ρθy[:, 1] -= min_ρθy[1]
    ρθy[:, 2] -= min_ρθy[2]
    return ρθy

def get_ρθ_block(xyzic, xyzc, Ts, Te, n, r):
    '分块只求ρθ的函数'
    # 准备工作
    single_a = np.pi * 2 / n  # 求每个块的过渡
    ρθ_ = np.empty([Te - Ts, 2])
    j = 0  # 计数器
    for i in range(Ts, Te):
        # 求圆心距
        xyz_ = xyzic[i, :3]  # 当前点的空间位置
        c_i = xyzic[i, -1]  # 当前点圆环名
        c_xyz_ = xyzc[xyzc[:, -1] == c_i, :3]  # 圆心位置
        R2 = (xyz_[0] - c_xyz_[0, 0]) ** 2 + (xyz_[2] - c_xyz_[0, 2]) ** 2  # 点到圆心的距离
        r_ = r[xyzc[:, -1] == c_i]  # 半径大小
        ρθ_[j, 0] = np.sqrt(R2) - r_  # 点云到中轴线的距离
        # 求角度
        angle_ = np.arctan2((xyzic[i, 2] - c_xyz_[0, 2]), (xyzic[i, 0] - c_xyz_[0, 0]))  # 求反正切值
        ρθ_[j, 1] = np.floor(angle_ / single_a)  # 点云归属标签赋值
        j += 1  # 计数器更新
    print('极坐标属性添加已完成', Te / len(xyzic) * 100, '%')
    return ρθ_


def find_LJ23(xyziccρθ, y_max, y_min, θ23_all, m, k, num_cpu=mp.cpu_count()):
    '通过并行计算求出两条斜缝'
    # 准备工作
    num_θ23 = len(θ23_all)
    tik = cut_down(num_θ23, num_cpu)  # 总循环分块
    print('使用cpu的核为', len(tik))
    p_all_lr = np.empty([num_θ23, 2])  # 建立斜直线大于0.05的比例数组(左,右)
    # p_max_lr = np.empty([num_θ23, 2])  # 建立最大圆心距统计数组
    # p_mean_lr = np.empty([num_θ23, 2])  # 建立平均圆心距统计数组
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    # 开始进行并行计算
    multi_res = [pool.apply_async(find_LJ23_block, args=(xyziccρθ, y_max, y_min, k, tik[i], tik[i + 1], θ23_all)) for i in
                 range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    tik_ = 0  # 计数器
    for res in multi_res:
        p_all_lr[tik[tik_]:tik[tik_ + 1], :] = res.get()
        tik_ += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    # 后续处理
    print('最大左比例', np.max(p_all_lr[:, 0]))
    print('最大右比例', np.max(p_all_lr[:, 1]))  # 检查
    np.savetxt('E:\\2023硕士研究上\\0：盾构隧道论文\\.txt', p_all_lr)
    '输出左缝'
    id_l = np.argmax(p_all_lr[:, 0])  # 找到最大的下标
    o_id_l_ = θ23_all[id_l]  # 角度值
    b_l_ = y_min - k * o_id_l_  # 求当前直线的b截距
    # 确认搜索的点云范围(o_min-o_max)
    o_max_l_ = (y_max - b_l_) / k
    ps_c_l_ = xyziccρθ[xyziccρθ[:, -1] >= o_id_l_, :]
    ps_c_l_ = ps_c_l_[ps_c_l_[:, -1] <= o_max_l_, :]
    oy_l_ = np.c_[ps_c_l_[:, -1], ps_c_l_[:, 1]]
    dis_l_ = p1.get_distance_point2line(oy_l_, [k, b_l_])
    LJ2_dis_ = ps_c_l_[dis_l_ <= 0.10, :]
    LJ2 = LJ2_dis_[LJ2_dis_[:, -2] >= (np.max(LJ2_dis_[:, -2]) - m), :5]
    '输出右缝'
    id_r = np.argmax(p_all_lr[:, 1])  # 找到最大的下标
    o_id_r_ = θ23_all[id_r]  # 角度值
    b_r_ = y_min - (-1 * k) * o_id_r_  # 求当前直线的b截距
    # 确认搜索的点云范围(c_min-c_max)
    o_max_r_ = (y_max - b_r_) / (-1 * k)
    ps_c_r_ = xyziccρθ[xyziccρθ[:, -1] <= o_id_r_, :]
    ps_c_r_ = ps_c_r_[ps_c_r_[:, -1] >= o_max_r_, :]
    oy_r_ = np.c_[ps_c_r_[:, -1], ps_c_r_[:, 1]]
    dis_r_ = p1.get_distance_point2line(oy_r_, [(-1 * k), b_r_])
    LJ3_dis_ = ps_c_r_[dis_r_ <= 0.10, :]
    LJ3 = LJ3_dis_[LJ3_dis_[:, -2] >= (np.max(LJ3_dis_[:, -2]) - m), :5]
    '''
    '显示折线图'
    line1 = go.Scatter(x=θ23_all, y=p_all_lr[:, 0], name='左缝比例变化趋势')
    line2 = go.Scatter(x=θ23_all, y=p_max_lr[:, 0], name='左缝最高圆心距变化趋势')
    line3 = go.Scatter(x=θ23_all, y=p_mean_lr[:, 0], name='左缝平均圆心距变化趋势')
    line4 = go.Scatter(x=θ23_all, y=p_all_lr[:, 1], name='右缝比例变化趋势')
    line5 = go.Scatter(x=θ23_all, y=p_max_lr[:, 1], name='右缝最高圆心距变化趋势')
    line6 = go.Scatter(x=θ23_all, y=p_mean_lr[:, 1], name='右缝平均圆心距变化趋势')
    # 显示
    fig = go.Figure([line1, line2, line3, line4, line5, line6])
    fig.show()
    '''
    return LJ2, LJ3, p_all_lr


def find_LJ23_block(xyziccρθ, y_max, y_min, k, tik0, tik1, θ23_all):
    '求斜缝的分块函数'
    # 准备工作
    p_block_lr = np.empty([tik1 - tik0, 2])  # 分块存储容器
    # p_max_lr = np.empty([tik1-tik0, 2])  # 建立最大圆心距统计数组
    # p_mean_lr = np.empty([tik1-tik0, 2])  # 建立平均圆心距统计数组
    # p_all_lr = np.empty([tik1-tik0, 6])
    j = 0  # 计数器
    for i in θ23_all[tik0:tik1]:  # 单块循环
        '计算左斜缝'
        b_l_ = y_min - k * i  # 求当前直线的b截距
        # 确认搜索的点云范围(o_min-o_max)
        o_max_l_ = (y_max - b_l_) / k  # 求搜索区间最大角度值
        ps_l_c_ = xyziccρθ[xyziccρθ[:, -1] >= i, :]
        ps_l_c_ = ps_l_c_[ps_l_c_[:, -1] <= o_max_l_, :]  # 满足角度范围的点云
        oy_l_ = np.c_[ps_l_c_[:, -1], ps_l_c_[:, 1]]  # 每个点云的角度值和y值
        dis_l_ = p1.get_distance_point2line(oy_l_, [k, b_l_])  # 求距离
        ps_dis_l_ = ps_l_c_[dis_l_ <= 0.10, :]  # 满足距离小于0.1的点云
        ps_dis_c_l_ = ps_dis_l_[ps_dis_l_[:, -3] >= 0.05, :]  # 曲率大于等于0.05的点云
        p_block_lr[j, 0] = len(ps_dis_c_l_) / len(ps_dis_l_)  # 比例
        # p_all_lr[j, 1] = np.nanmax(ps_dis_c_l_[:, -2])
        # p_all_lr[j, 2] = np.mean(ps_dis_c_l_[:, -2])
        '搜索右斜缝'
        b_r_ = y_min - (-1 * k) * i  # 求当前直线的b截距
        o_max_r_ = (y_max - b_r_) / (k * -1)  # 求搜索区间最大角度值
        ps_r_c_ = xyziccρθ[xyziccρθ[:, -1] >= o_max_r_, :]
        ps_r_c_ = ps_r_c_[ps_r_c_[:, -1] <= i, :]  # 满足角度范围的点云
        oy_r_ = np.c_[ps_r_c_[:, -1], ps_r_c_[:, 1]]  # 每个点云的角度值和y值
        dis_r_ = p1.get_distance_point2line(oy_r_, [k * -1, b_r_])  # 求距离
        ps_dis_r_ = ps_r_c_[dis_r_ <= 0.10, :]  # 满足距离小于0.1的点云
        ps_dis_c_r_ = ps_dis_r_[ps_dis_r_[:, -3] >= 0.05, :]  # 曲率大于等于0.05的点云
        p_block_lr[j, 1] = len(ps_dis_c_r_) / len(ps_dis_r_)  # 比例
        # p_all_lr[j, 4] = np.nanmax(ps_dis_c_r_[:, -2])
        # p_all_lr[j, 5] = np.mean(ps_dis_c_r_[:, -2])
        j += 1
    # print('已完成', θ23_all[tik0], '-', θ23_all[tik1], '角度值')
    return p_block_lr


def find_LJ_P(xyzicc, RB_S, RB_E, xzrc):
    '2022.10.3纵缝提取改进版'
    # 准备工作
    num_c = len(RB_S) - 2  # 参与计算的环块个数 = all-2
    type_RingBlock = np.empty(num_c)  # 环块所属模板类型容器
    θg = np.array([[[415, 425], [3700, 3765], [3880, 3945]], [[1690, 1700], [2425, 2490], [2605, 2670]], [[1685, 1695], [3270, 3335], [3450, 3515]], [[410, 420], [2845, 2905], [3025, 3090]]])
    # 开始循环
    F_all = {}  # 存储缝的词典
    # V_θY = {}  # 存储纵缝体素θY起始范围和分辨率
    P_F_all = []  # 非标签纵缝存储器
    for i in range(num_c):
        print('正在处理第', i + 1, '个环块')
        # 遍历到当前环块
        xyzicc_ = xyzicc[xyzicc[:, -2] < RB_E[i + 1], :]
        xyzicc_ = xyzicc_[xyzicc_[:, -2] > RB_S[i + 1], :]  # 循环到当前环块的所有点云
        '''
        '计算当前中轴线（非体素化使用）'
        xzrcy_ = xzrcy[xzrcy[:, -2] < RB_E[i + 1], :]
        xzrcy_ = xzrcy_[xzrcy_[:, -2] > RB_S[i + 1], :]  # 当前环块的空间圆心点
        # 拟合中轴线
        line_ = np.vstack([xzrcy_[:, 0], xzrcy_[:, -1], xzrcy_[:, 1]]).T  # 圆心位置容器
        KB_line_ = fit_line_3d(line_)  # ransac空间直线拟合
        # 找到拟合后的新圆心
        n = 0  # 计数器
        xyzc_new = np.empty([len(xzrcy_[:, -1]), 4])
        xyzc_new[:, 1] = xzrcy_[:, -1]
        xyzc_new[:, -1] = xzrcy_[:, -2]
        for j in xzrcy_[:, -1]:
            k_ = (j-KB_line_[1, 1])/KB_line_[1, 0]  # 求k
            x_ = k_ * KB_line_[0, 0] + KB_line_[0, 1]  # 求X
            z_ = k_ * KB_line_[2, 0] + KB_line_[2, 1]  # 求Z
            xyzc_new[n, 0] = x_
            xyzc_new[n, 2] = z_
            n += 1
        '体素化'
        # 体素化前的标准化处理
        '''
        ρθY_ = p1.XYZ2ρθY_mp(xyzicc_[:, :-1], xzrc, n=4250)  # 合并圆柱位置和点云属性  # 角度分解已发生改变
        # 极坐标体素化并赋值
        v_ρθY_ = vl.voxel_ρθY(ρθY_)
        voxel_Y_c = v_ρθY_.P2Vm(xyzicc_[:, -1])  # 体素赋值（体素赋曲率）
        # v_ρθY_.watchVoxel_plt()  # 显示体素
        # V_θY[str(i) + 'a'] = np.array([[,],[,]])
        # 输出
        # np.savetxt('E:\\PointCloudSourceFile\\txt\\Shield\\ρθY_'+str(i)+'.txt', v_ρθY_.points_local)
        # 将现有存储点云的大数组与角度数组进行合并
        xyziccθY_ = np.c_[xyzicc_, v_ρθY_.points_local[:, 1:]]
        # 判断环块类型
        type_RingBlock[i], v_F_a_ = bl_ABCD(v_ρθY_.points_local, xyzicc_[:, -1])  # 通过曲率判断
        # 单独处理F1
        p_Fa_id = v_ρθY_.V2P(v_F_a_)  # 返回符合条件A1的点云下标
        p_Fa_b = xyziccθY_[p_Fa_id, :]  # 返回体素对应的点云
        p_Fa_ = p_Fa_b[p_Fa_b[:, 5] > 0.05, :]
        F_all[str(i) + 'a'] = p_Fa_
        '''
        
        if len(P_F_all) == 0:
            P_F_all = p_Fa_
        else:
            P_F_all = np.vstack((P_F_all, p_Fa_))
        
        '''
        del p_Fa_, p_Fa_b
        # 寻找其他纵缝
        v_F_b_, v_F_c_, v_F_d_ = findF_others(voxel_Y_c, v_ρθY_.points_local_un, θg[int(type_RingBlock[i])])
        # 提取B纵缝
        p_Fb_id = v_ρθY_.V2P(v_F_b_)  # 返回符合条件A的点云下标
        p_b_ = xyziccθY_[p_Fb_id, :]
        F_all[str(i) + 'b'] = p_b_[p_b_[:, 5] > 0.05, :]
        # P_F_all = np.vstack((P_F_all, p_b_[p_b_[:, 5] > 0.05, :]))
        del v_F_b_, p_b_
        # 提取C纵缝
        p_Fc_id = v_ρθY_.V2P(v_F_c_)  # 返回符合条件A的点云下标
        p_c_ = xyziccθY_[p_Fc_id, :]
        F_all[str(i) + 'c'] = p_c_
        # P_F_all = np.vstack((P_F_all, p_c_))
        del v_F_c_, p_c_
        # 提取D纵缝
        p_Fd_id = v_ρθY_.V2P(v_F_d_)  # 返回符合条件A的点云下标
        p_d_ = xyziccθY_[p_Fd_id, :]
        F_all[str(i) + 'd'] = p_d_
        # P_F_all = np.vstack((P_F_all, p_d_))
        del v_F_d_, p_d_

    return type_RingBlock, F_all


def find_LJ(xyzicc, C_name, xzrc):
    '2022.6.27 纵缝提取函数(基于曲率)'
    # 准备工作
    num_c_id = len(C_name)  # 环缝数量
    type_RingBlock = np.empty(num_c_id - 1)  # 环块所属模板类型容器
    P_a = []
    P_b = []
    P_c = []
    P_F1 = []  # 存储各环块缝的容器
    # 开始循环
    for i in range(num_c_id - 1):
        print('正在处理第', i + 1, '个环块')
        xyzicc_ = xyzicc[xyzicc[:, -2] < C_name[i + 1], :]
        xyzicc_ = xyzicc_[xyzicc_[:, -2] > C_name[i], :]  # 循环到当前环块的所有点云
        # 体素化前的标准化处理
        ρθY_ = p1.XYZ2ρθY(xyzicc_[:, :-1], xzrc)  # 合并圆柱位置和点云属性
        # 极坐标体素化并赋值
        v_ρθY_ = vl.voxel_ρθY(ρθY_)
        voxel_Y_c = v_ρθY_.P2V(xyzicc_[:, -1])  # 体素赋值（体素赋曲率）
        # 判断环块类型
        belong_, F1 = bl_ABCD(v_ρθY_.points_local, xyzicc_[:, -1])  # 通过曲率判断
        # 单独处理F1
        p_F1_id = v_ρθY_.V2P(F1)  # 返回符合条件A1的点云下标
        p_F1_b = xyzicc_[p_F1_id, :]
        p_F1_ = p_F1_b[p_F1_b[:, -1] > 0.04, :]
        if len(P_F1) == 0:
            P_F1 = p_F1_
        else:
            P_F1 = np.append(P_F1, p_F1_, axis=0)  # 将所有F1缝点云全部保存
        if belong_ == 0:
            F_a = findF_a(voxel_Y_c, v_ρθY_.points_local_un)  # 返回A区域纵缝
            p_Fa_id = v_ρθY_.V2P(F_a)  # 返回符合条件A的点云下标
            p_a_ = xyzicc_[p_Fa_id, :]
            if len(P_a) == 0:
                P_a = p_a_
            else:
                P_a = np.append(P_a, p_a_, axis=0)  # 将所有A缝点云全部保存
        elif belong_ == 1:
            F_b = findF_b(voxel_Y_c, v_ρθY_.points_local_un)  # 返回B区域纵缝1
            p_Fb_id = v_ρθY_.V2P(F_b)  # 返回符合条件A1的点云下标
            p_b_ = xyzicc_[p_Fb_id, :]
            if len(P_b) == 0:
                P_b = p_b_
            else:
                P_b = np.append(P_b, p_b_, axis=0)  # 将所有B1点云全部保存
        elif belong_ == 2:
            F_c = findF_c(voxel_Y_c, v_ρθY_.points_local_un)  # 返回B区域纵缝1
            p_Fc_id = v_ρθY_.V2P(F_c)  # 返回符合条件A1的点云下标
            p_c_ = xyzicc_[p_Fc_id, :]
            if len(P_c) == 0:
                P_c = p_c_
            else:
                P_c = np.append(P_c, p_c_, axis=0)  # 将所有B1点云全部保存
        elif belong_ == 3:  # 如果环块所属模板为D
            pass
        type_RingBlock[i] = belong_  # 模板类型传递

    if len(np.unique(type_RingBlock)) == 3:
        P_F = np.vstack((P_F1, P_a, P_b, P_c))  # 合并所有缝点云
    else:
        P_F = np.vstack((P_F1, P_a, P_b))  # 合并所有缝点云
    return type_RingBlock, P_F


def findF_a(v_c, v_p_un):
    '寻找模板A的纵缝点云'
    # 输入（强度值体素，缝A1体元位置）
    # 未 高斯混合模型（2类）（离心距，强度值）
    # 未 采用26邻域搜索符合强度值的点云
    ag = np.array([[2605, 2660], [2735, 2785], [285, 305]])  # A类234纵缝所在角度区间
    m = 5  # 高度差阈值
    v_Fa2_id = []  # 容器
    v_Fa3_id = []
    # A4
    v_Fa4_before = v_p_un[v_p_un[:, 1] < ag[2, 1], :]
    v_Fa4_before = v_Fa4_before[v_Fa4_before[:, 1] > ag[2, 0], :]  # 符合A4角度的体素
    v_Fa4_b_Y = v_Fa4_before[v_Fa4_before[:, -1] <= (np.max(v_Fa4_before[:, -1]) - 15), :]
    v_Fa4_b_Y = v_Fa4_b_Y[v_Fa4_b_Y[:, -1] >= (np.min(v_Fa4_before[:, -1]) + 15), :]  # 掐头去尾
    P_max_A4 = np.max(v_Fa4_b_Y[:, 0])  # 求非缝最高P
    del v_Fa4_b_Y
    v_Fa4 = v_Fa4_before[v_Fa4_before[:, 0] > (P_max_A4 - m), :]
    del v_Fa4_before
    # A2
    v_Fa2_before = v_p_un[v_p_un[:, 1] <= ag[0, 1], :]
    v_Fa2_before = v_Fa2_before[v_Fa2_before[:, 1] >= ag[0, 0], :]  # 符合A2角度的体素
    v_Fa2_b_Y = v_Fa2_before[v_Fa2_before[:, -1] <= (np.max(v_Fa2_before[:, -1]) - 15), :]
    v_Fa2_b_Y = v_Fa2_b_Y[v_Fa2_b_Y[:, -1] >= (np.min(v_Fa2_before[:, -1]) + 15), :]  # 掐头去尾
    del v_Fa2_before
    # 大于曲率0.05的体元
    for i in range(len(v_Fa2_b_Y)):
        if v_c[int(v_Fa2_b_Y[i, 0]), int(v_Fa2_b_Y[i, 1]), int(v_Fa2_b_Y[i, 2])] > 0.05:
            v_Fa2_id.append(i)
    v_Fa2 = v_Fa2_b_Y[v_Fa2_id, :]
    v_Fa2 = Reduced_diagonal_seam(v_Fa2, -1, v_Fa2_b_Y)  # 去噪
    del v_Fa2_b_Y
    '''
    P_max_a2 = np.max(v_Fa2_b_Y[:, 0])  # 求非缝最高P
    del v_Fa2_before
    v_Fa2 = v_Fa2_b_Y[v_Fa2_b_Y[:, 0] >= (P_max_a2-4), :]
    v_Fa2 = Reduced_diagonal_seam(v_Fa2, -1)
    '''
    # A3
    v_Fa3_before = v_p_un[v_p_un[:, 1] <= ag[1, 1], :]
    v_Fa3_before = v_Fa3_before[v_Fa3_before[:, 1] >= ag[1, 0], :]  # 符合A2角度的体素
    v_Fa3_b_Y = v_Fa3_before[v_Fa3_before[:, -1] <= (np.max(v_Fa3_before[:, -1]) - 15), :]
    v_Fa3_b_Y = v_Fa3_b_Y[v_Fa3_b_Y[:, -1] >= (np.min(v_Fa3_before[:, -1]) + 15), :]  # 掐头去尾
    del v_Fa3_before
    for i in range(len(v_Fa3_b_Y)):
        if v_c[int(v_Fa3_b_Y[i, 0]), int(v_Fa3_b_Y[i, 1]), int(v_Fa3_b_Y[i, 2])] > 0.05:
            v_Fa3_id.append(i)
    v_Fa3 = v_Fa3_b_Y[v_Fa3_id, :]
    v_Fa3 = Reduced_diagonal_seam(v_Fa3, 1, v_Fa3_b_Y)
    del v_Fa3_b_Y
    '''
    P_max_a3 = np.max(v_Fa3_b_Y[:, 0])  # 求非缝最高P
    del v_Fa3_before
    v_Fa3 = v_Fa3_b_Y[v_Fa3_b_Y[:, 0] >= (P_max_a3-4), :]
    v_Fa3 = Reduced_diagonal_seam(v_Fa3, 1)
    '''
    # 合并所有缝
    v_Fa = np.vstack((v_Fa4, v_Fa2, v_Fa3))
    return v_Fa


def findF_b(v_c, v_p_un):
    '寻找模板B的纵缝点云'
    bg = np.array([[1193, 1200], [1710, 1755], [1838, 1885]])  # B类234纵缝所在角度区间
    m = 5  # 高度差阈值
    v_Fb3_id = []
    v_Fb4_id = []
    # B1
    # B2
    v_Fb2_before = v_p_un[v_p_un[:, 1] <= bg[0, 1], :]
    v_Fb2_before = v_Fb2_before[v_Fb2_before[:, 1] >= bg[0, 0], :]  # 符合b2角度的体素
    v_Fb2_b_Y = v_Fb2_before[v_Fb2_before[:, -1] <= (np.max(v_Fb2_before[:, -1]) - 15), :]
    v_Fb2_b_Y = v_Fb2_b_Y[v_Fb2_b_Y[:, -1] >= (np.min(v_Fb2_before[:, -1]) + 15), :]
    P_max = np.max(v_Fb2_b_Y[:, 0])  # 求非缝最高P
    v_Fb2 = v_Fb2_before[v_Fb2_before[:, 0] > (P_max - m), :]
    del v_Fb2_before
    # B3
    v_Fb3_before = v_p_un[v_p_un[:, 1] <= bg[1, 1], :]
    v_Fb3_before = v_Fb3_before[v_Fb3_before[:, 1] >= bg[1, 0], :]  # 符合A2角度的体素
    v_Fb3_b_Y = v_Fb3_before[v_Fb3_before[:, -1] <= (np.max(v_Fb3_before[:, -1]) - 15), :]
    v_Fb3_b_Y = v_Fb3_b_Y[v_Fb3_b_Y[:, -1] >= (np.min(v_Fb3_before[:, -1]) + 15), :]
    del v_Fb3_before
    # P_max_B3 = np.max(v_Fb3_b_Y[:, 0])  # 求非缝最高P
    # del v_Fb3_before
    # v_Fb3 = v_Fb3_b_Y[v_Fb3_b_Y[:, 0] >= (P_max_B3-4), :]
    for i in range(len(v_Fb3_b_Y)):
        if v_c[int(v_Fb3_b_Y[i, 0]), int(v_Fb3_b_Y[i, 1]), int(v_Fb3_b_Y[i, 2])] >= 0.05:
            v_Fb3_id.append(i)
    v_Fb3 = v_Fb3_b_Y[v_Fb3_id, :]
    del v_Fb3_b_Y
    v_Fb3 = Reduced_diagonal_seam(v_Fb3)
    # B4
    v_Fb4_before = v_p_un[v_p_un[:, 1] <= bg[2, 1], :]
    v_Fb4_before = v_Fb4_before[v_Fb4_before[:, 1] >= bg[2, 0], :]  # 符合A2角度的体素
    v_Fb4_b_Y = v_Fb4_before[v_Fb4_before[:, -1] <= (np.max(v_Fb4_before[:, -1]) - 15), :]
    v_Fb4_b_Y = v_Fb4_b_Y[v_Fb4_b_Y[:, -1] >= (np.min(v_Fb4_before[:, -1]) + 15), :]
    del v_Fb4_before
    # P_max_B4 = np.max(v_Fb4_b_Y[:, 0])  # 求非缝最高P
    # del v_Fb4_before
    # v_Fb4 = v_Fb4_b_Y[v_Fb4_b_Y[:, 0] >= (P_max_B4-4), :]
    for i in range(len(v_Fb4_b_Y)):
        if v_c[int(v_Fb4_b_Y[i, 0]), int(v_Fb4_b_Y[i, 1]), int(v_Fb4_b_Y[i, 2])] >= 0.05:
            v_Fb4_id.append(i)
    v_Fb4 = v_Fb4_b_Y[v_Fb4_id, :]
    del v_Fb4_b_Y
    v_Fb4 = Reduced_diagonal_seam(v_Fb4)
    # 合并所有缝
    v_Fb = np.vstack((v_Fb2, v_Fb3, v_Fb4))  # 合并所有缝
    return v_Fb


def findF_c(v_c, v_p_un):
    '寻找模板C的纵缝点云'
    cg = np.array([[1195, 1200], [2310, 2357], [2438, 2484]])  # C类234纵缝所在角度区间
    v_Fc3_id = []
    v_Fc4_id = []
    # C1
    # C2
    v_Fc2_before = v_p_un[v_p_un[:, 1] <= cg[0, 1], :]
    v_Fc2_before = v_Fc2_before[v_Fc2_before[:, 1] >= cg[0, 0], :]  # 符合b2角度的体素
    v_Fc2_b_Y = v_Fc2_before[v_Fc2_before[:, -1] <= (np.max(v_Fc2_before[:, -1]) - 15), :]
    v_Fc2_b_Y = v_Fc2_b_Y[v_Fc2_b_Y[:, -1] >= (np.min(v_Fc2_before[:, -1]) + 15), :]
    P_max = np.max(v_Fc2_b_Y[:, 0])  # 求非缝最高P
    v_Fc2 = v_Fc2_before[v_Fc2_before[:, 0] > (P_max - 5), :]
    del v_Fc2_before
    # C3
    v_Fc3_before = v_p_un[v_p_un[:, 1] <= cg[1, 1], :]
    v_Fc3_before = v_Fc3_before[v_Fc3_before[:, 1] >= cg[1, 0], :]  # 符合A2角度的体素
    v_Fc3_b_Y = v_Fc3_before[v_Fc3_before[:, -1] <= (np.max(v_Fc3_before[:, -1]) - 15), :]
    v_Fc3_b_Y = v_Fc3_b_Y[v_Fc3_b_Y[:, -1] >= (np.min(v_Fc3_before[:, -1]) + 15), :]
    del v_Fc3_before
    # P_max_c3 = np.max(v_Fc3_b_Y[:, 0])  # 求非缝最高P
    # del v_Fc3_before
    # v_Fc3 = v_Fc3_b_Y[v_Fc3_b_Y[:, 0] >= (P_max_c3-4), :]
    for i in range(len(v_Fc3_b_Y)):
        if v_c[int(v_Fc3_b_Y[i, 0]), int(v_Fc3_b_Y[i, 1]), int(v_Fc3_b_Y[i, 2])] > 0.05:
            v_Fc3_id.append(i)
    v_Fc3 = v_Fc3_b_Y[v_Fc3_id, :]
    v_Fc3 = Reduced_diagonal_seam(v_Fc3, -1, v_Fc3_b_Y)
    del v_Fc3_b_Y
    # C4
    v_Fc4_before = v_p_un[v_p_un[:, 1] <= cg[2, 1], :]
    v_Fc4_before = v_Fc4_before[v_Fc4_before[:, 1] >= cg[2, 0], :]  # 符合A2角度的体素
    v_Fc4_b_Y = v_Fc4_before[v_Fc4_before[:, -1] <= (np.max(v_Fc4_before[:, -1]) - 15), :]
    v_Fc4_b_Y = v_Fc4_b_Y[v_Fc4_b_Y[:, -1] >= (np.min(v_Fc4_before[:, -1]) + 15), :]
    del v_Fc4_before
    # P_max_c4 = np.max(v_Fc4_b_Y[:, 0])  # 求非缝最高P
    # del v_Fc4_before
    # v_Fc4 = v_Fc4_b_Y[v_Fc4_b_Y[:, 0] >= (P_max_c4-4), :]
    for i in range(len(v_Fc4_b_Y)):
        if v_c[int(v_Fc4_b_Y[i, 0]), int(v_Fc4_b_Y[i, 1]), int(v_Fc4_b_Y[i, 2])] > 0.05:
            v_Fc4_id.append(i)
    v_Fc4 = v_Fc4_b_Y[v_Fc4_id, :]
    v_Fc4 = Reduced_diagonal_seam(v_Fc4, 1, v_Fc4_b_Y)
    del v_Fc4_b_Y
    # 合并所有缝
    v_Fc = np.vstack((v_Fc2, v_Fc3, v_Fc4))  # 合并所有缝
    return v_Fc


def findF_others2(xyzcρθ, θg):
    '''
    寻找其他的纵缝点云(非体素版)
    :param xyzc: 点云坐标+曲率
    :param ρθ: 点云圆心距和角度值
    :return:
    '''
    m = 5 * 0.004  # 高度差阈值
    m_ = 4 * 0.004  # 斜缝高度差阈值
    c_ = 0.05  # 曲率阈值
    # xyzcρθ = np.c_[xyzc, ρθ]  # 合并数组
    'B缝'
    Fb_ = xyzcρθ[xyzcρθ[:, -1] <= θg[0, 1], :]
    Fb_ = Fb_[Fb_[:, -1] >= θg[0, 0], :]
    ρ_max = np.max(Fb_[:, -2])
    Fb_ = Fb_[Fb_[:, -2] >= (ρ_max - m), :]
    'C缝'
    Fc_ = xyzcρθ[xyzcρθ[:, -1] <= θg[1, 1], :]
    Fc_ = Fc_[Fc_[:, -1] >= θg[1, 0], :]
    ρ_max = np.max(Fc_[:, -2])
    Fc_ = Fc_[Fc_[:, -2] >= (ρ_max - m_), :]
    Fc_ = Fc_[Fc_[:, 3] >= c_, :]
    'D缝'
    Fd_ = xyzcρθ[xyzcρθ[:, -1] <= θg[2, 1], :]
    Fd_ = Fd_[Fd_[:, -1] >= θg[2, 0], :]
    ρ_max = np.max(Fd_[:, -2])
    Fd_ = Fd_[Fd_[:, -2] >= (ρ_max - m_), :]
    Fd_ = Fd_[Fd_[:, 3] >= c_, :]
    return Fb_, Fc_, Fd_


def findF_others(v_c, v_p_un, θg):
    '寻找其他的纵缝点云'
    m = 5  # 高度差阈值
    c_ = 0.05
    # b
    v_Fb_before = v_p_un[v_p_un[:, 1] <= θg[0, 1], :]
    v_Fb_before = v_Fb_before[v_Fb_before[:, 1] >= θg[0, 0], :]  # 符合b角度的体素
    P_max = np.max(v_Fb_before[:, 0])  # 求非缝最高P
    v_Fb_ = v_Fb_before[v_Fb_before[:, 0] > (P_max - m), :]
    del v_Fb_before
    # c
    v_Fc_before = v_p_un[v_p_un[:, 1] <= θg[1, 1], :]
    v_Fc_before = v_Fc_before[v_Fc_before[:, 1] >= θg[1, 0], :]  # 符合c角度的体素
    Pc_max = np.max(v_Fc_before[:, 0])
    v_Fc_before = v_Fc_before[v_Fc_before[:, 0] >= (Pc_max - m + 1), :]
    # 大于曲率0.05的体元
    v_Fc_id = []
    for i in range(len(v_Fc_before)):
        if v_c[int(v_Fc_before[i, 0]), int(v_Fc_before[i, 1]), int(v_Fc_before[i, 2])] > c_:
            v_Fc_id.append(i)
    v_Fc_ = v_Fc_before[v_Fc_id, :]
    # v_Fc_ = RemovalOfLongitudinalSeamAbnormality(v_Fc_)  # 剔除异常值
    del v_Fc_before
    # d
    v_Fd_before = v_p_un[v_p_un[:, 1] <= θg[2, 1], :]
    v_Fd_before = v_Fd_before[v_Fd_before[:, 1] >= θg[2, 0], :]  # 符合A2角度的体素
    Pd_max = np.max(v_Fd_before[:, 0])
    v_Fd_before = v_Fd_before[v_Fd_before[:, 0] >= (Pd_max - m + 1), :]
    v_Fd_id = []
    for i in range(len(v_Fd_before)):
        if v_c[int(v_Fd_before[i, 0]), int(v_Fd_before[i, 1]), int(v_Fd_before[i, 2])] > c_:
            v_Fd_id.append(i)
    v_Fd_ = v_Fd_before[v_Fd_id, :]
    # v_Fd_ = RemovalOfLongitudinalSeamAbnormality(v_Fd_)  # 剔除异常值
    return v_Fb_, v_Fc_, v_Fd_


def Reduced_diagonal_seam(v_xf, Complexity=0, v_before=None):
    "斜缝去噪(体素条件下)"
    # Complexity=0,1,-1 0:不需要判断斜率，1：斜率大于0，-1：斜缝小于0。复杂情况下需要 原体素
    global k, b
    'k值去噪'
    # 求得斜缝四至
    Y_max = np.max(v_xf[:, -1])
    Y_min = np.min(v_xf[:, -1])
    id_Y_max = np.argmax(v_xf[:, -1])
    id_Y_min = np.argmin(v_xf[:, -1])
    O_Y_max = v_xf[id_Y_max, 1]
    O_Y_min = v_xf[id_Y_min, 1]
    O_max = np.max(v_xf[:, 1])
    O_min = np.min(v_xf[:, 1])
    # 求O的平均数
    O_m = np.around(np.mean(v_xf[:, 1]))
    Y_O_m = np.mean(v_xf[v_xf[:, 1] == O_m, -1])
    # 求斜率和截距
    if Complexity == 0:
        k = (Y_max - Y_O_m) / (O_Y_max - O_m)  # 最高点
        b = Y_O_m - k * O_m
        # print('无干扰的直线K值', k)
    elif Complexity == 1:
        k = (Y_max - Y_min) / (O_max - O_min)
        b = Y_max - k * O_max
    elif Complexity == -1:
        k = (Y_max - Y_min) / (O_min - O_max)
        b = Y_max - k * O_min
    # 计算每个体元到线的距离
    print('斜率为', k)
    dis = np.abs(k * v_xf[:, 1] + b - v_xf[:, -1])  # 距离容器
    d_dis = 22  # 阈值  15
    # 去噪
    v_xf_new = v_xf[dis <= d_dis, :]
    '二次处理'
    # 只是为了要最大的P值
    if Complexity != 0:
        # 求Y中位数
        Y_m = np.floor(np.median(v_xf_new[:, -1]))
        O_Y_m = np.mean(v_xf_new[v_xf_new[:, -1] == Y_m, 1])
        # if Complexity > 0 and np.abs(k-5.4) > 2:
        if Complexity > 0:
            k = 5.4
        # elif Complexity < 0 and np.abs(k+5.4) > 2:
        elif Complexity < 0:
            k = -5.4
        b = Y_m - k * O_Y_m
        # 符合P范围的体元
        P_max = np.max(v_xf_new[:, 0])
        v_xf_new = v_before[v_before[:, 0] <= P_max, :]
        v_xf_new = v_xf_new[v_xf_new[:, 0] >= (P_max - 5), :]
        dis = np.abs(k * v_xf_new[:, 1] + b - v_xf_new[:, -1])  # 距离容器
        v_xf_new = v_xf_new[dis <= d_dis, :]
    return v_xf_new


def RemovalOfLongitudinalSeamAbnormality(v_xf):
    '2022.10.19剔除异常纵缝体素'
    # 找到斜缝的角度值左右值体素平面位置
    θ_max = np.max(v_xf[:, 1])
    θ_min = np.min(v_xf[:, 1])
    id_θ_max = np.argmax(v_xf[:, 1])
    id_θ_min = np.argmin(v_xf[:, 1])
    Y_θ_max = v_xf[id_θ_max, -1]
    Y_θ_min = v_xf[id_θ_min, -1]
    # 求直线的k,b
    k = (Y_θ_max - Y_θ_min) / (θ_max - θ_min)
    print('斜率为', k)
    b = Y_θ_max - k * θ_max
    # 求体素到直线的距离
    d_dis = 15  # 边长倍数阈值
    dis = np.abs(k * v_xf[:, 1] + b - v_xf[:, -1])  # 距离容器
    v_xf_new = v_xf[dis <= d_dis, :]
    return v_xf_new


def Line_completion(F_all):
    "点云线补全算法（算法多余，现已停止使用）"
    for i in F_all.keys():
        F_ = F_all.get(i)  # 每一个标签的点云
        Y_all_un = np.unique(F_[:, -1])  # 求所有Y的下标分布
        num_Y = len(Y_all_un)  # Y的遍历长度
        num_mean = int(len(F_) / num_Y)  # 求每个Y的平均点云数量
        print('此纵缝的平均Y单位点数量为', num_mean)
        # 求Y递增数列
        Y_arg = np.arange(np.min(Y_all_un), np.max(Y_all_un) + 1)
        # 使用Ransac直线拟合，建立O与Y之间的关系式
        k_, b_ = rs.fit_2Dline_ransac(F_[:, -2:], sigma=0.15)
        print('拟合直线的斜率为', k_, '拟合直线的半径为', b_)
        if k_ == 0:
            θ_ = np.around(np.mean(F_[:, -2]))  # 四舍五入
            θ_un_ = np.ones(num_Y) * θ_
        else:
            θ_un_ = np.unique(np.around((Y_arg - b_) / k))  # 四舍五入、
        # 设置点云起始位置以及分辨率

        # 按照Y值进行遍历，找到中轴是否存在点云，若是，则不需要补全，若不是，则需要补全
        l = 0  # 递增遍历
        for j in range(Y_all_un):
            Y_have_ = F_[F_[:, -1] == j, :]
            θ_have_ = Y_have_[Y_have_[:, -2] == θ_un_[l]]
            l += 1
            if len(θ_have_) == 0:  # 判断需要补全
                pass
        # 遍历Y，以公式查看O的范围，然后根据点的多少确定是否进行补点（最好建立一个O的左右范围点数量横切面直方图）
        # 进行补点
        # 返回到F_all
    return F_all


def Fitellipse(xyzic, xmax=3, xmin=-2.9, ymax=4.5, ymin=0.5):
    '椭圆拟合'
    '1.限制坐标范围'
    xyzic_0 = xyzic[xyzic[:, 0] > xmin, :]
    xyzic_0 = xyzic_0[xyzic_0[:, 0] < xmax, :]
    xyzic_0 = xyzic_0[xyzic_0[:, 2] < ymax, :]
    xyzic_0 = xyzic_0[xyzic_0[:, 2] > ymin, :]
    '2.整体拟合'
    xz_0 = np.c_[xyzic_0[:, 0], xyzic_0[:, 2]]  # 对拟合点进行降维
    reg = LsqEllipse().fit(xz_0)  # 输入二维点
    center, width, height, phi = reg.as_parameters()  # 求解
    print(f'center: {center[0]:.3f}, {center[1]:.3f}')  # 椭圆点中心
    print(f'width: {width:.3f}')  # 椭圆长半轴
    print(f'height: {height:.3f}')  # 椭圆短半轴
    print(f'phi: {phi:.3f}')  # 椭圆旋转角
    '3.求点到椭圆的距离'
    arg_Ellipse = np.array([center[0], center[1], np.max([width, height]), np.min([width, height]), phi])  # 合并椭圆参数
    distances = ep.dis_ellipse(xyzic[:, 0], xyzic[:, 2], arg_Ellipse)  # 求点到椭圆的距离
    distances = np.nan_to_num(distances, nan=0)  # 将空值转换为0
    '4.求均值和标准差'
    dis_mean = np.mean(distances)
    dis_std = np.std(distances)
    print(dis_std, dis_mean)
    m = -0.25  # 标准差倍数
    threshold = dis_mean + dis_std * m  # 阈值
    print(threshold)
    xyzic_0 = xyzic[distances < threshold, :]
    '5.第二次拟合'
    index, outdex, xzlwp, dis = fit_Ellipse_starmap(xyzic_0[:, 0], xyzic_0[:, 2], xyzic_0[:, -1], xyzic)  # 求每个圆环的参数
    xyzic_0 = xyzic[index, :]
    return

def fit_Ellipse_starmap(x, z, c, points,num_cpu=mp.cpu_count(), dr=0.05):
    '异步并行计算拟合椭圆 Parallel computing for fitting ellipses'
    c_un = np.unique(c)  # 所有序列数
    num_c = len(c_un)  # 圆环数
    xzlwp = np.empty([num_c, 5])  # 新建一个存储每个椭圆参数的容器
    dis_all = np.zeros(len(points))  # 距离容器
    # 并行计算加速准备 #Accelerated preparation for parallel computing
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    # tik = cut_down(num_c)  # 分块器
    # tik2 = p0.cut_down(len(points))  # 分块器
    j = 0  # 分块输出计时器
    # 并行计算每个圆环 Parallel computing for each torus
    # 并行计算
    multi_res = pool.starmap_async(fit_Ellipse_single, ((x[c==c_un[i]], z[c==c_un[i]], c_un[i], points) for i in
                 tqdm(range(num_c),desc='分配任务拟合单个椭圆参数',unit='个cross-section',total=num_c)))
    # multi_res = [pool.starmap_async(fit_Ellipse_single, (x[c==c[i]].reshape(1,-1), z[c==c[i]].reshape(1,-1), c_un[i], points)) for i in
    #              tqdm(range(num_c))]  # 将每个block需要处理的点云区间发送到每个进程当中
    for res in tqdm(multi_res.get(), total=num_c, desc='导出单个椭圆参数', unit='个cross-section'):
    # for res in tqdm(multi_res):
        # xzlwp[tik[tik_b]:tik[tik_b + 1], :] = res.get()  # 将每个进程得到的结果分block的发送到容器当中
        # res_block = res.get()
        dis_all += res[0]
        # dis_all += res_block[0]  # 距离累加
        xzlwp[j, :] = res[1]  # 拟合值回归
        j += 1
    pool.close()  # 禁止进程池再接收任务  #Prohibit process pools from receiving tasks again
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算  #After all processes have completed their calculations, exit parallel computing
    # 下标
    index = dis_all <= dr
    outdex = dis_all > dr
    # RMSE
    dis_index = dis_all[dis_all <= dr]  # 在椭圆上的距离集合
    RMSE = np.sqrt(np.sum(dis_index**2)/len(dis_index))
    print('RMSE:', RMSE)
    print('保留点比例：',len(dis_index)/len(points))
    return index, outdex, xzlwp, dis_all

def fit_Ellipse_single(x, z, c_, points):
    '单环求椭圆参数 Calculating Ellipse Parameters by Blocks'
    # num_ = e-b
    # c_un = np.unique(c)
    dis_ = np.zeros(len(points))
    # dis_ = np.zeros(num_)
    xzlwp = np.empty([5])
    # j = 0  # 循环计数器 cycle counter
    # for c1 in c_un[b:e]:
    # x_c1 = x[c == c1]
    # z_c1 = z[c == c1]  # 提取单环的全部点云二维坐标  Extract all point cloud 2D coordinates of a single ring
    xz_ = np.vstack([x, z]).T
    reg = LsqEllipse().fit(xz_)  # 输入二维点  Enter 2D points
    center, width, height, phi = reg.as_parameters()  # 求解 solve
    xzlwp[0] = center[0]
    xzlwp[1] = center[1]
    xzlwp[2] = np.max([width, height])
    xzlwp[3] = np.min([width, height])
    xzlwp[4] = phi
    dis_[points[:, 4] == c_] = ep.dis_ellipse(points[points[:, 4]==c_, 0], points[points[:, 4]==c_, 2], xzlwp)
    dis_ = np.nan_to_num(dis_, nan=0)  # 若距离为nan，则转换为1
    return dis_,xzlwp

def get_dis_θ(xz,xyzic):
    '求单截面点云相邻点的角度差240530,by:Mengyao Gao'
    # num = len(xyzic)  # 点云数量
    angle = np.arctan2(xyzic[:, 0]-xz[0], xyzic[:, 2]-xz[1]) * 180 / np.pi  # 点云求角度值
    diff = np.diff(angle)  # 计算相邻角度差值
    # plt.hist(diff, bins=3600)
    # plt.show()
    print('mean',np.mean(diff))
    print('std',np.std(diff))
    condition = (np.abs(diff) >= 0.03) & (np.abs(diff) <= 0.08)
    new_xyzic = xyzic[1:][condition]
    return new_xyzic,diff[condition]  # 符合条件的点云，相邻点角度差值

def get_wrong(xzlwp_l,xzlwp_r,xyzic_l,xyzic_r,n=5000):
    '基于实际变化的全局错台量分析20240530'
    x0_m = np.mean([xzlwp_l[0], xzlwp_r[0]])
    z0_m = np.mean([xzlwp_l[2], xzlwp_r[2]])  # 圆心轴
    angle_l = np.arctan2(xyzic_l[:, 0] - x0_m, xyzic_l[:, 2] - z0_m) * 180 / np.pi  # 点云求角度值
    angle_r = np.arctan2(xyzic_r[:, 0] - x0_m, xyzic_r[:, 2] - z0_m) * 180 / np.pi  # 点云求角度值
    single_a = np.pi * 2 / n  # 求每个块的过渡
    belong_l = np.floor(angle_l / single_a)
    belong_r = np.floor(angle_r / single_a)  # 属于区间
    b_l_un = np.unique(belong_l)
    b_r_un = np.unique(belong_r)  # 排序
    b_common = np.intersect1d(b_l_un, b_r_un)  # 共同区间
    print('共同区间数量',len(b_common))
    w_all = np.zeros([len(b_common)])  # 求错容器
    j = 0
    for i in b_common:
        xyz_l_ = np.mean(xyzic_l[belong_l == i, :3], axis=0)
        # print(xyz_l_)
        xyz_r_ = np.mean(xyzic_r[belong_r == i, :3], axis=0)
        # print(xyz_r_)
        w_all[j] = np.linalg.norm(np.array([xyz_l_[0],xyz_l_[2]])-np.array([xyz_r_[0],xyz_r_[2]]))
        print(w_all[j])
        j += 1
    # w_all = w_all[w_all <= 0.01]
    return np.max(w_all)

def conv_hull(points: np.ndarray):
    """
    生成凸包 参考文档：https://blog.csdn.net/io569417668/article/details/106274172
    :param points: 待生成凸包的点集
    :return: 索引 list
    """
    # pcl = array_to_pointcloud(points)
    # hull, lst = pcl.compute_convex_hull()
    hull = ConvexHull(points)
    lst = hull.vertices
    return lst

# 这里会返回列表类型
def load_data_txt(path):
    file = open(path, 'r')
    data = file.read().split('\n')
    lst = _data_trans(data)
    return lst


def array_to_pointcloud(np_array):
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(np_array)
    return pcd


def _data_trans(data):
    lst = []
    for num in data:
        num_list = num.split()
        lst.append([eval(i) for i in num_list])
    lst.pop()
    return lst

def in_convex_polyhedron(points_set: np.ndarray, test_points: np.ndarray):
    """
    检测点(集)是否在三维凸包内
    :param points_set: 凸包，需要对分区的点进行凸包生成 具体见conv_hull函数
    :param test_points: 需要检测的点 可以是多个点
    :return: bool类型
    """
    assert type(points_set) == np.ndarray
    assert type(test_points) == np.ndarray
    bol = np.zeros(test_points.shape[0], dtype=bool)
    ori_set = points_set
    ori_edge_index = conv_hull(ori_set)
    ori_edge_index = np.sort(np.unique(ori_edge_index))
    for i in tqdm(range(test_points.shape[0])):
        new_set = np.concatenate((points_set, test_points[i, np.newaxis]), axis=0)
        new_edge_index = conv_hull(new_set)
        new_edge_index = np.sort(np.unique(new_edge_index))
        bol[i] = (new_edge_index.tolist() == ori_edge_index.tolist())
    return bol

def trans_2D(data,R=2.75):
    '三维数据转二维数据'
    data_x = data[:, 0]
    data_y = data[:, 1]
    data_z = data[:, 2]
    data_i = data[:, 3]
    data_l = data[:, 4]

    # R = 2.75
    data_2D = np.empty((len(data), 5))

    for i in range(len(data)):
        xi = data_x[i]
        yi = data_y[i]
        zi = data_z[i]
        ii = data_i[i]
        li = data_l[i]
        if xi > 0:
            arf = np.arccos(zi / np.power((xi * xi + zi * zi), 0.5))
            new_x = arf * R
            data_2D[i, :] = [new_x, yi, R, ii, li]
        else:
            arf = np.arccos(zi / np.power((xi * xi + zi * zi), 0.5))
            new_x = -1 * arf * R
            data_2D[i, :] = [new_x, yi, R, ii, li]
    return data_2D


# 2D重采样(转成图像)
def resample(data, path):
    x = data[:, 0]
    y = data[:, 1]
    intensity = data[:, 3]
    pixel = 0.006

    max_x = np.max(x)
    min_x = np.max(x)
    max_y = np.max(y)
    min_y = np.min(y)

    length = int(math.ceil((max_x - min_x) / pixel))
    width = int(math.ceil((max_y - min_y) / pixel))
    image = np.empty([width + 1, length + 1])

    for i in range(len(data)):
        xi = np.ceil((x - min_x) / pixel).astype(int)
        yi = np.ceil((y - min_y) / pixel).astype(int)
        image[yi, xi] = intensity[i]

    image.astype(np.float32)
    image_ = cv.imwrite(path, image)
    return image_

def get_angle_all(xz,x0,z0,cpu_count=mp.cpu_count()):
    '求所有点的反正切'
    num = len(xz)
    angle_all = np.empty(num)
    # 并行计算加速准备
    pool = mp.Pool(processes=cpu_count)  # 开启多进程池，数量为cpu
    # 并行计算
    multi_res = pool.starmap_async(get_angle, ((xz[i,0],xz[i,1],x0,z0) for i in
                 tqdm(range(num),desc='分配任务给每个点求角度',unit='points',total=num)))
    j = 0  # 分块输出计时器
    for res in tqdm(multi_res.get(), total=num, desc='导出每个点的反正切', unit='points'):
        angle_all[j] = res
        j += 1
    pool.close()  # 禁止进程池再接收任务  #Prohibit process pools from receiving tasks again
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算  #After all processes have completed their calculations, exit parallel computing
    return angle_all

def get_angle(x,z,x0,z0):
    '求单个点的反正切角度'
    x_diff = x-x0
    z_diff = z-z0
    if x_diff >= 0 and z_diff > 0:  # Quadrant I
        angle = math.degrees(math.atan(z_diff / x_diff))
    elif x_diff <= 0 and z_diff > 0:  # Quadrant II
        angle = 90 + math.degrees(math.atan((-x_diff) / z_diff))
    elif x_diff <= 0 and z_diff < 0:  # Quadrant III
        angle = 180 + math.degrees(math.atan((-z_diff) / (-x_diff)))
    elif x_diff >= 0 and z_diff < 0:  # Quadrant IV
        angle = 270 + math.degrees(math.atan(x_diff / (-z_diff)))
    else:  # Point is on an axis (angle = 0, pi/2, pi, 3pi/2)
        angle = 0  # Adjust this based on the specific axis position
    return angle

def find_closest_pair(l_min,l_max,r_min,r_max):
    '找到2对数中最近的两个数，并返回下标'
    # 建立2*2容器
    dis_angle = np.empty([2,2])
    # 求差值
    diff0 = abs(l_min-r_min)
    diff1 = 360 - abs(l_min-r_min)
    diff = min(diff0,diff1)
    dis_angle[0,0] = diff

    diff0 = abs(l_min-r_max)
    diff1 = 360 - abs(l_min-r_max)
    diff = min(diff0,diff1)
    dis_angle[0,1] = diff

    diff0 = abs(l_max-r_min)
    diff1 = 360 - abs(l_max-r_min)
    diff = min(diff0,diff1)
    dis_angle[1,0] = diff

    diff0 = abs(l_max-r_max)
    diff1 = 360 - abs(l_max-r_max)
    diff = min(diff0,diff1)
    dis_angle[1,1] = diff
    # 找到最小的两个角度范围
    min_index = np.argmin(dis_angle)
    if min_index == 0:
        angle_mean = np.mean([l_min,r_min])
    elif min_index == 1:
        angle_mean = np.mean([l_min, r_max])
    elif min_index == 2:
        angle_mean = np.mean([l_max, r_min])
    elif min_index == 3:
        angle_mean = np.mean([l_max, r_max])
    return angle_mean

def Fit_Ellipse_Intersecting_line_mp(xyzic,n=7,T=0.15,a=2,cpu_count=mp.cpu_count()):
    '基于点集拟合直线剔除非衬砌点算法'
    # 首先进行整体粗拟合
    xyzic1 = fit_cicle_rough(xyzic)
    # np.savetxt('code\\241201\\25421_1.txt',xyzic1,fmt='%.05f')
    # 准备工作
    C_un = np.unique(xyzic[:,4])
    num_C = len(C_un)
    # 并行计算加速准备
    pool = mp.Pool(processes=cpu_count)  # 开启多进程池，数量为cpu
    # 并行计算
    multi_res = pool.starmap_async(del_out_1, ((xyzic[xyzic[:,4]==C_un[i],:],xyzic1[xyzic1[:,4]==C_un[i],:],n,T,a) for i in
                 tqdm(range(num_C),desc='分配任务给每个断面剔除非衬砌点',unit='断面',total=num_C)))
    j = 0  # 分块输出计时器
    for res in tqdm(multi_res.get(), total=num_C, desc='导出每个断面的衬砌点', unit='断面'):
        if j==0:
            xyzic_in = res
        else:
            xyzic_in = np.r_[xyzic_in,res]
        j += 1
    pool.close()  # 禁止进程池再接收任务  #Prohibit process pools from receiving tasks again
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算  #After all processes have completed their calculations, exit parallel computing
    return xyzic_in

def del_out_1(xyzi,xyzi1,n=7,dr=0.15,a=2):
    '21.11.30最新剔除算法单环'
    # 二次拟合
    model = CircleLeastSquareModel()  # 类的实例化:用最小二乘生成已知模型
    xzrc = fit_circle_Intersecting(model,xyzi1,t=0.13)
    dis = np.abs((xyzi[:,0] - xzrc[0]) ** 2 + (xyzi[:,2] - xzrc[1]) ** 2 - xzrc[2] ** 2)
    xyzi2 = xyzi[dis<=dr,:]
    xyzi3 = fit_circle_line_dis(xyzi2,xzrc[0],xzrc[1],xzrc[2],n=n,a=a)
    print('保留率',len(xyzi3)/len(xyzi))
    return xyzi3


def ellipse_foci(x0, y0, a, b, theta_rot):
    """
    计算椭圆的焦点坐标
    参数：
    x0, y0: 椭圆中心坐标
    a, b: 椭圆的长半轴和短半轴
    theta_rot: 椭圆相对于坐标轴的旋转角度（弧度制）
    返回：
    foci: 焦点坐标 (F1, F2)，每个焦点为 (x, y)
    """
    # 计算焦点到中心的距离 c
    a1 = np.max([a, b])
    b1 = np.min([a, b])
    c = np.sqrt(a1**2 - b1**2)
    # 计算焦点坐标
    F1_x = x0 + c * np.cos(theta_rot)
    F1_y = y0 + c * np.sin(theta_rot)
    F2_x = x0 - c * np.cos(theta_rot)
    F2_y = y0 - c * np.sin(theta_rot)
    return np.array([[F1_x, F1_y], [F2_x, F2_y]])

def fit_cicle_Intersecting(xyzic):
    '隧道点云整体粗拟合'
    # 限制坐标范围
    xyzic_0 = xyzic[xyzic[:, 0] > -2.9, :]
    xyzic_0 = xyzic_0[xyzic_0[:, 0] < 3, :]
    xyzic_00 = xyzic_0[xyzic_0[:, 2] < 4.5, :]
    xyzic_0 = xyzic_00[xyzic_00[:, 2] >= 2.6, :]
    # 整体拟合
    # print('RANSAC输入点云数量为', len(xyzic_0))
    model = CircleLeastSquareModel()  # 类的实例化:用最小二乘生成已知模型
    data = np.vstack([xyzic_0[:, 0], xyzic_0[:, 2]]).T  # 整理数据
    result = model.fit(data)  # 拟合圆
    x_0 = result.a * -0.5
    z_0 = result.b * -0.5
    r_0 = 0.5 * math.sqrt(result.a ** 2 + result.b ** 2 - 4 * result.c)  # 圆心及坐标半径
    # print('圆心',x_0,z_0,'半径',r_0)
    dis = np.abs((xyzic_0[:, 0] - x_0) ** 2 + (xyzic_0[:, 2] - z_0) ** 2 - r_0 ** 2)  # 点到圆的距离
    # 求均值和标准差
    dis_mean = np.mean(dis)
    dis_std = np.std(dis)
    # print('距离均值：', dis_mean, '距离标准差', dis_std)
    # 保留阈值内点云
    xyzic_dis = np.c_[xyzic_0, dis]  # 合并数组
    tt = 0.5  # 标准差倍数
    threshold = np.array([dis_mean - dis_std * tt, dis_mean + dis_std * tt])
    item = np.where(np.logical_and(xyzic_dis[:, -1] > threshold[0], xyzic_dis[:, -1] < threshold[1]))
    xyzic_1 = xyzic_dis[item, :-1]  # 剩余点云
    xyzic_1 = xyzic_1[0, :, :]
    # print('拟合保留比例',len(xyzic_1)/len(xyzic))
    return xyzic_1,x_0,z_0,r_0

def fit_circle_Intersecting(model,xyzic,t):
    xz = xyzic[:,[0,2]]
    c0 = xyzic[0,4]
    ransac_fit, _ = ransac(xz, model, 50, 2000, t, 300, debug=False, return_all=True)  # ransac迭代
    'n:拟合模型所需的最小数据值数 k:算法中允许的最大迭代次数 t:用于确定数据点何时适合模型的阈值 d:断言模型很好地符合数据所需的接近数据值的数量'
    x0 = ransac_fit.a * -0.5
    z0 = ransac_fit.b * -0.5
    r0 = 0.5 * math.sqrt(ransac_fit.a ** 2 + ransac_fit.b ** 2 - 4 * ransac_fit.c)  # 拟合后圆的参数
    return np.array([x0,z0,r0,c0])

def fit_circle_line_dis(xyzic,x0,z0,r,n=7,a=2):
    '基于局部点聚类拟合直线与圆交点间距离的精细拟合'
    num = len(xyzic)
    label = np.zeros(num)
    dis_all = np.zeros(num)
    Tree = KDTree(xyzic[:,[0,2]])
    for i in range(num):
        # 询问最近的 n 个邻居
        distances, indices = Tree.query([xyzic[i,[0,2]]], k=n)
        ps_ = xyzic[indices[0],:]
        k,b = fit_line_least_squares(ps_[:,[0,2]])
        ps_n,pa_ = line_circle_intersection(x0, z0, r, k, b)
        # print(ps_n)
        if ps_n == 2 :  # 如果有两个交点
            dis = np.sqrt((pa_[0,0]-pa_[1,0])**2+(pa_[0,1]-pa_[1,1])**2)
            label[i] = 2
            dis_all[i] = dis
            '''
            if dis<=td:
                label[i] = 1
            else:
                label[i] = 0
            '''
        elif ps_n == 1:
            label[i] = 1
        elif ps_n == 0:
            # xi = xyzic[i,0]
            # zi = xyzic[i,2]
            # dis_ = np.abs(np.sqrt((xi-x0)**2+(zi-z0)**2)-r)
            # if dis_<td0:
            label[i] = 1
            # else:
            #     label[i] = 0
    # 求等于2的中垂线距离均值和标准差
    mean_dis_2 = np.mean(dis_all[label==2])
    std_dis_2 = np.std(dis_all[label==2])
    td = mean_dis_2+std_dis_2*a
    print(mean_dis_2,std_dis_2)
    for i in range(num):
        if label[i] == 2 and dis_all[i] < td:
            label[i] = 1
        elif label[i] == 2 and dis_all[i] >= td:
            label[i] = 0
    
    bool_arr = label.astype(bool)
    xyzic_ = xyzic[bool_arr,:]
    # dis_all_ = dis_all[bool_arr]
    # print(len(xyzic_)/len(xyzic))
    # xyzicd = np.c_[xyzic_,dis_all_]
    return xyzic_ 

def fit_line_least_squares(points):
    # 将点分解为 x 和 y 列表
    x = np.array([point[0] for point in points])
    y = np.array([point[1] for point in points])

    # 计算各项求和
    n = len(points)
    sum_x = np.sum(x)
    sum_y = np.sum(y)
    sum_xy = np.sum(x * y)
    sum_x2 = np.sum(x * x)

    # 计算斜率 m 和截距 b
    m = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
    b = (sum_y - m * sum_x) / n

    return m, b

def line_circle_intersection(h, k, r, m, b):
    # 计算二次方程的系数
    A = 1 + m**2
    B = 2 * (m * (b - k) - h)
    C = h**2 + (b - k)**2 - r**2
    
    # 计算判别式
    discriminant = B**2 - 4 * A * C
    
    if discriminant > 0:  # 两个交点
        x1 = (-B + np.sqrt(discriminant)) / (2 * A)
        x2 = (-B - np.sqrt(discriminant)) / (2 * A)
        y1 = m * x1 + b
        y2 = m * x2 + b
        return 2, np.array([[x1, y1], [x2, y2]])  # 两个交点
    elif discriminant == 0:  # 一个交点
        x = -B / (2 * A)
        y = m * x + b
        return 1, [(x, y)]  # 一个交点
    else:  # 没有交点
        return 0, []  # 无交点


def find_CS_FixedLength(txti_in,num_cpu=mp.cpu_count(),z_range=1):
    '环缝提取（固定长度版）'
    # 点云强度值离散化
    txti_in[:, 3] = zm.normalization(txti_in[:, 3], 255)  # 强度值离散化
    # 计算每个环的平均强度值
    num_C = len(np.unique(txti_in[:,4]))  # 圆环数量
    i_c = np.empty(num_C)  # 新建一个存储圆环平均强度值的容器
    # 并行计算准备
    c_un = np.unique(txti_in[:,4])  # 圆环从小到大排列
    # num_cpu = mp.cpu_count()  # 设置并行计算线程数
    tik = cut_down(num_C, num_cpu)  # 分块起止点
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    # 限制txt_in
    z_max = np.max(txti_in[:, 2])
    z_min = np.min(txti_in[:, 2])
    d_z = z_max-z_min
    t_z = z_min+d_z*(1-z_range)  # 参与统计的阈值
    txti_free = txti_in[txti_in[:,2]>=t_z,:]  # 参与统计的点云
    multi_res = [pool.apply_async(find_cImean_block, args=(txti_free, c_un, tik[i], tik[i + 1])) for i in  # points_new
                    range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    tik_ = 0  # 计数器
    for res in multi_res:
        i_c[tik[tik_]:tik[tik_ + 1]] = res.get()
        tik_ += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    # 后期整理
    i_c = p1.normalization(i_c, 255)  # 均值离散化
    # np.savetxt('ci.txt', np.c_[self.xzrc[:, -1], i_c], fmt='%.05f')
    i_c_mean = np.mean(i_c)  # 平均强度值均值
    i_c_std = np.std(i_c)  # 平均强度值方差
    print('均值', i_c_mean, '标准差', i_c_std)
    # 基于强度值求环缝
    c_ = []  # 环缝的存储名
    c_id = []  # 环缝的存储下标器
    N = 60  # 左右环的收集平均值的间隔
    dis_max = i_c_mean - i_c_std * 3  # 最大差值
    j = N  # 环名下标计数器
    for i in range(N, len(i_c) - N):
        if i_c[i] <= i_c_mean - i_c_std * 2 and i_c[i] <= i_c[i - 1] and i_c[i] <= i_c[i + 1]:
            Il = np.mean(i_c[(i - N):i])
            Ir = np.mean(i_c[(i + 1):(i + 1 + N)])  # 求左右50邻域平均强度值
            if Il - i_c[i] >= dis_max and Ir - i_c[i] >= dis_max:
                c_.append(i)
                c_id.append(j)
        j += 1
    # c_name = c_un[np.array(c_)]  # 粗估环缝名
    # 精简环缝值
    c_nei = 70  # 确定左右邻域搜索数
    id_c_ry = np.empty(len(c_id))  # 圆环名下标ID
    k = 0
    for i in c_id:
        c_i_70 = i_c[(i - c_nei):(i + c_nei + 1)]  # 找到环缝的左右60邻域
        id_i_120 = np.argmin(c_i_70)  # 找到邻域的最小值
        id_c_ry[k] = id_i_120 + i - c_nei  # 找到局部最小值的准确下标
        k += 1
    c_reduce = np.unique(id_c_ry)  # 精简环缝下标
    c_reduce = c_reduce.astype(int)
    # np.savetxt('E:\\2025寒假阶段\\15环缝纵缝识别论文\\major revisions\\Code\\FMD\\c_id_25421.txt', c_reduce)
    print('环缝id', c_reduce)
    c_name_reduce = c_un[c_reduce]  # 细挑后的环缝名
    # np.savetxt('E:\\2023硕士研究上\\0：盾构隧道论文\\c_name_reduce.txt', c_name_reduce)
    print('环缝名', c_name_reduce)
    '找出每个最低点的所在圆环区间最大和最小X值'
    # 找到环缝缓冲区间
    # num_CS = len(c_name_reduce)  # 环缝数量
    c_x_max_names = np.zeros(len(c_reduce))
    c_x_min_names = np.zeros(len(c_reduce))
    mid = 30  # 缓冲区间半径
    # 判断缓冲区的准备工作
    RB_S = np.array(c_un[0])  # 环块开始位置
    RB_E = []  # 环块结束位置
    mid_ = 3  # 3
    c_name_ins = np.zeros([len(c_reduce), 2])
    for i in range(len(c_reduce)):
        id_ = [c_name_reduce[i] - mid, c_name_reduce[i] + mid]
        c_ = np.arange(id_[0], id_[1])
        # test = np.isin(self.txti_in[:, -1], c_)
        id_x_max_ = np.argmax(txti_in[np.isin(txti_in[:, 4], c_), 0])
        id_x_min_ = np.argmin(txti_in[np.isin(txti_in[:, 4], c_), 0])
        c_id_c_max = txti_in[np.isin(txti_in[:, 4], c_), 4]
        c_id_c_min = txti_in[np.isin(txti_in[:, 4], c_), 4]
        c_x_max_names[i] = c_id_c_max[id_x_max_]
        c_x_min_names[i] = c_id_c_min[id_x_min_]
        list_ = [c_name_reduce[i], c_x_max_names[i], c_x_min_names[i]]
        c_name_ins[i, 0] = np.min(list_) - mid_
        c_name_ins[i, 1] = np.max(list_) + mid_
        # 添加衬砌表面起止位置
        RB_S = np.append(RB_S, c_name_ins[i, 1])  # 添加起始位置
        RB_E = np.append(RB_E, c_name_ins[i, 0])  # 添加结束位置
    RB_E = np.append(RB_E, c_un[-1])  # 结束位置封顶
    # np.savetxt('E:\\2025寒假阶段\\15环缝纵缝识别论文\\major revisions\\Code\\FMD\\25421.RB_S.txt', RB_S)
    # np.savetxt('E:\\2025寒假阶段\\15环缝纵缝识别论文\\major revisions\\Code\\FMD\\25421.RB_E.txt', RB_E)
    # np.savetxt('E:\\2025寒假阶段\\15环缝纵缝识别论文\\major revisions\\Code\\FMD\\搜索区间.txt', c_name_ins)
    '''
    '找到对应y值'
    y_un = np.unique(txti_in[:, 1])
    y_name_ins = np.empty([len(c_name_reduce), 2])
    y_name = np.empty(len(c_name_reduce))
    for i in range(len(c_name_reduce)):
        y_name[i] = y_un[c_un == c_name_reduce[i]]
        y_name_ins[i, 0] = y_un[c_un == c_name_ins[i, 0]]
        y_name_ins[i, 1] = y_un[c_un == c_name_ins[i, 1]]
    '''
    '找到缓冲区间环缝名'
    for i in range(len(c_reduce)):
        if i == 0:
            seams_all = np.arange(c_name_ins[i, 0], c_name_ins[i, 1])
        else:
            seams_all = np.append(seams_all, np.arange(c_name_ins[i, 0], c_name_ins[i, 1]))
    c_xyzic = txti_in[np.isin(txti_in[:, 4], seams_all), :]  # 返回xyzic[:, -1]中有c[c_in]的行数
    # 精简衬砌表面
    id_del = np.isin(np.isin(txti_in[:, 4], seams_all), False)  # 除去环缝点云的点云下标
    txti_delC = txti_in[id_del, :]  # 去除环缝的点云
    return txti_delC, c_xyzic

def find_CS_STSD(txti_in,num_cpu=mp.cpu_count()):
    '环缝提取STSD版本'
    # 点云强度值离散化
    txti_in[:, 3] = zm.normalization(txti_in[:, 3], 255)  # 强度值离散化
    # 计算每个环的平均强度值
    num_C = len(np.unique(txti_in[:,4]))  # 圆环数量
    i_c = np.empty(num_C)  # 新建一个存储圆环平均强度值的容器
    # 并行计算准备
    c_un = np.unique(txti_in[:,4])  # 圆环从小到大排列
    num_cpu = mp.cpu_count()  # 设置并行计算线程数
    tik = cut_down(num_C, num_cpu)  # 分块起止点
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    multi_res = [pool.apply_async(find_cImean_block, args=(txti_in, c_un, tik[i], tik[i + 1])) for i in  # points_new
                 range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    tik_ = 0  # 计数器
    for res in multi_res:
        i_c[tik[tik_]:tik[tik_ + 1]] = res.get()
        tik_ += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    # 后期整理
    i_c = zm.normalization(i_c, 255)  # 均值离散化
    # np.savetxt('c_i.txt', np.c_[c_un, i_c], fmt='%.05f')

    return txti_delC, c_xyzic


def find_CS_plus(txti_in,num_cpu=mp.cpu_count(),z_range=1):
    '环缝提取（普适版）'
    # 点云强度值离散化
    txti_in[:, 3] = zm.normalization(txti_in[:, 3], 255)  # 强度值离散化
    # 计算每个环的平均强度值
    num_C = len(np.unique(txti_in[:,4]))  # 圆环数量
    i_c = np.empty(num_C)  # 新建一个存储圆环平均强度值的容器
    # 并行计算准备
    c_un = np.unique(txti_in[:,4])  # 圆环从小到大排列
    num_cpu = mp.cpu_count()  # 设置并行计算线程数
    tik = cut_down(num_C, num_cpu)  # 分块起止点
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    # 限制txt_in
    z_max = np.max(txti_in[:, 2])
    z_min = np.min(txti_in[:, 2])
    d_z = z_max - z_min
    t_z = z_min + d_z * (1 - z_range)  # 参与统计的阈值
    txti_free = txti_in[txti_in[:, 2] >= t_z, :]  # 参与统计的点云
    multi_res = [pool.apply_async(find_cImean_block, args=(txti_free, c_un, tik[i], tik[i + 1])) for i in  # points_new
                 range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    tik_ = 0  # 计数器
    for res in multi_res:
        i_c[tik[tik_]:tik[tik_ + 1]] = res.get()
        tik_ += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    # 后期整理
    i_c = zm.normalization(i_c, 255)  # 均值离散化
    # np.savetxt('c_i.txt',np.c_[c_un,i_c],fmt='%.05f')

    # 创建画布和坐标系
    plt.figure(figsize=(8, 5))  # 设置画布大小
    # 绘制折线图
    plt.plot(
        c_un,
        i_c,
        color='blue',  # 线条颜色
        linestyle='-',  # 线型（实线）
        linewidth=2,  # 线宽
        marker='o',  # 数据点标记样式
        markersize=8,  # 标记大小
        label='示例数据'
    )
    # 添加标题和标签
    # plt.title("简单折线图示例", fontsize=14)
    plt.xlabel("Cross-section", fontsize=12)
    plt.ylabel("Intensity", fontsize=12)
    # 显示图例
    plt.legend()
    # 显示网格
    plt.grid(True, linestyle='--', alpha=0.5)
    # 显示图表
    # plt.show()

    # 找到强度值的最低点以及其他的极低点
    id_min = np.argmin(i_c)
    num_cut_CS = 255  # 平均强度值极低点间隔 # 530
    num_CS_0 = np.int16(np.round(num_C / num_cut_CS))  # 假想环缝数量
    print('环缝数量为', num_CS_0)
    Begin_CS_0 = id_min % num_cut_CS  # 假想起始位置
    id_CS_0 = np.arange(Begin_CS_0, num_C, num_cut_CS)  # 假想环缝位置
    belong_i_l = 15  # 强度值搜索半径  # 30
    belong_i_r = 25
    mid_ = 1  # 余量区间 3
    RB_S = np.array(c_un[0])  # 环块开始位置
    RB_E = []  # 环块结束位置
    c_name_ins = np.empty(num_CS_0)  # 极低值容器
    for i in range(num_CS_0):
        # 求强度值极低点
        id_min_i_ = np.argmin(i_c[id_CS_0[i] - belong_i_l:id_CS_0[i] + belong_i_r]) + id_CS_0[i] - belong_i_l
        # 寻找最大X值与最小X值位置
        c_name_ins[i] = c_un[id_min_i_]  # 强度值极低点位置
        # name_min_i_ = xzrc[id_min_i_, -1]  # 强度值极低点位置
        names_c_ = np.arange(c_name_ins[i] - belong_i_l, c_name_ins[i] + belong_i_r)  # X的搜索范围
        id_x_max_ = np.argmax(txti_in[np.isin(txti_in[:, 4], names_c_), 0])  # 最大X的id
        id_x_min_ = np.argmin(txti_in[np.isin(txti_in[:, 4], names_c_), 0])  # 最小X的id
        id_c_x_max = txti_in[np.isin(txti_in[:, 4], names_c_), 4]
        id_c_x_min = txti_in[np.isin(txti_in[:, 4], names_c_), 4]
        name_c_x_max_ = id_c_x_max[id_x_max_]
        name_c_x_min_ = id_c_x_min[id_x_min_]  # 最大X和最小X的环名
        list_ = [c_name_ins[i], name_c_x_max_, name_c_x_min_]  # 关键环名压缩
        c_name_l_ = np.min(list_) - mid_
        c_name_r_ = np.max(list_) + mid_
        # 添加衬砌表面起止位置
        RB_S = np.append(RB_S, c_name_l_)  # 添加起始位置
        RB_E = np.append(RB_E, c_name_r_)  # 添加结束位置
    RB_E = np.append(RB_E, c_un[-1])  # 结束位置封顶
    for i in range(num_CS_0):
        if i == 0:
            seams_all = np.arange(RB_S[i + 1], RB_E[i])  # IndexError: too many indices for array: array is 1-dimensional, but 2 were indexed
        else:
            seams_all = np.append(seams_all, np.arange(RB_S[i + 1], RB_E[i]))
    c_xyzic = txti_in[np.isin(txti_in[:, 4], seams_all), :]  # 返回xyzic[:, -1]中有c[c_in]的行数
    # 精简衬砌表面
    id_del = np.isin(np.isin(txti_in[:, 4], seams_all), False)  # 除去环缝点云的点云下标
    txti_delC = txti_in[id_del, :]  # 去除环缝的点云
    return txti_delC, c_xyzic

def find_CS_buffer(txti_in,num_cpu=mp.cpu_count(),z_range=1):
    '''
    环缝提取（含缓冲区）
    :return: 返回环缝的名称
    '''
    # 点云强度值离散化
    txti_in[:, 3] = p1.normalization(txti_in[:, 3], 255)  # 强度值离散化
    # 计算每个环的平均强度值
    c_un = np.unique(txti_in[:,4])  # 圆环从小到大排列
    num_C = len(c_un)  # 圆环数量
    i_c = np.empty(num_C)  # 新建一个存储圆环平均强度值的容器
    # 并行计算准备
    num_cpu = mp.cpu_count()  # 设置并行计算线程数
    tik = cut_down(num_C, num_cpu)  # 分块起止点
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    # 限制txt_in
    z_max = np.max(txti_in[:, 2])
    z_min = np.min(txti_in[:, 2])
    d_z = z_max - z_min
    t_z = z_min + d_z * (1 - z_range)  # 参与统计的阈值
    txti_free = txti_in[txti_in[:, 2] >= t_z, :]  # 参与统计的点云
    multi_res = [pool.apply_async(find_cImean_block, args=(txti_free, c_un, tik[i], tik[i + 1])) for i in  # points_new
                 range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    tik_ = 0  # 计数器
    for res in multi_res:
        i_c[tik[tik_]:tik[tik_ + 1]] = res.get()
        tik_ += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    # 后期整理
    i_c = p1.normalization(i_c, 255)  # 均值离散化
    i_c_mean = np.mean(i_c)  # 平均强度值均值
    i_c_std = np.std(i_c)  # 平均强度值方差
    print('均值', i_c_mean, '标准差', i_c_std)
    # 输出强度值
    CI = np.c_[c_un,i_c]
    # np.savetxt('E:\\2023硕士研究下\\3：《一种基于空间特征一致性的盾构隧道点云接缝提取算法》\\问题环缝强度值.txt',CI,fmt='%.5f')
    # 基于强度值求环缝
    c_ = []  # 环缝的存储名
    c_id = []  # 环缝的存储下标器
    N = 60  # 左右环的收集平均值的间隔
    dis_max = i_c_mean - i_c_std * 3  # 最大差值
    j = N  # 环名下标计数器
    for i in range(N, len(i_c) - N):
        if i_c[i] <= i_c_mean - i_c_std * 2 and i_c[i] <= i_c[i - 1] and i_c[i] <= i_c[i + 1]:
            Il = np.mean(i_c[(i - N):i])
            Ir = np.mean(i_c[(i + 1):(i + 1 + N)])  # 求左右50邻域平均强度值
            if Il - i_c[i] >= dis_max and Ir - i_c[i] >= dis_max:
                c_.append(i)
                c_id.append(j)
        j += 1

    # c_name = c_un[np.array(c_)]  # 粗估环缝名
    # 精简环缝值
    c_nei = 70  # 确定左右邻域搜索数
    id_c_ry = np.empty(len(c_id))  # 圆环名下标ID
    k = 0
    for i in c_id:
        c_i_70 = i_c[(i - c_nei):(i + c_nei + 1)]  # 找到环缝的左右60邻域
        id_i_120 = np.argmin(c_i_70)  # 找到邻域的最小值
        id_c_ry[k] = id_i_120 + i - c_nei  # 找到局部最小值的准确下标
        k += 1
    c_reduce = np.unique(id_c_ry)  # 精简环缝下标
    c_reduce = c_reduce.astype(int)
    print('环缝id', c_reduce)
    # np.savetxt('E:\\2023硕士研究上\\0：盾构隧道论文\\c_reduce.txt', c_reduce)
    c_name_reduce = c_un[c_reduce]  # 细挑后的环缝名
    # np.savetxt('E:\\2023硕士研究上\\0：盾构隧道论文\\c_name_reduce.txt', c_name_reduce)
    print('环缝名', c_name_reduce)
    '显示圆环平均变化强度值'
    # line1 = go.Scatter(x=c_un, y=i_c, name='Average reflection intensity value of each circle point clouds')
    # i_c_mean_all = [np.mean(i_c)] * len(xzrc)
    # line2 = go.Scatter(x=c_un, y=i_c_mean_all, name='Average strength value of each circle')
    # line3 = go.Scatter(x=xzrc[:, -1], y=xzrc[:, -2], name='Average reflection intensity value of each circle point clouds')
    # fig = go.Figure(line1)
    # fig.show()
    '找出剩下的所有环缝(60)'
    tb = 35  # 豁免计算的左右缓冲区圆环数量
    tc = 40  # 缓冲区外的计算均值的圆环数量
    seams_all = []  # 所有提取出的环缝容器
    RB_S = np.array(c_un[0])  # 环块开始位置
    RB_E = []  # 环块结束位置
    for i in range(len(c_reduce)):  # 寻找周围圆环名
        # 找到需要用的圆环下标
        id_l_b_ = c_reduce[i] - tb - tc
        id_l_e_ = c_reduce[i] - tb
        id_r_b_ = c_reduce[i] + tb
        id_r_e_ = c_reduce[i] + tb + tc
        # 计算左右平均值-8倍标准差
        i_mean_l_ = np.mean(i_c[id_l_b_:id_l_e_]) - np.std(i_c[id_l_b_:id_l_e_]) * 8
        i_mean_r_ = np.mean(i_c[id_r_b_:id_r_e_]) - np.std(i_c[id_r_b_:id_r_e_]) * 8
        # 显示
        # line_i_l_ = go.Scatter(x=c_un[id_l_b_:id_l_e_], y=[i_mean_l_]*tc, name='Average strength value of left 40')
        # line_i_r_ = go.Scatter(x=c_un[id_r_b_:id_r_e_], y=[i_mean_r_]*tc, name='Average strength value of right 40')
        # fig = go.Figure([line1, line_i_l_, line_i_r_])
        # fig.show()
        # 找到最后一个大于和第一个小于的边界圆环
        # ppp = np.where(i_c[id_l_b_:c_reduce[i]] < i_mean_l_)
        LeftInterval_ = np.array(np.where(i_c[id_l_b_:c_reduce[i]] > i_mean_l_))  # 准备找最后一个
        RightInterval_ = np.array(np.where(i_c[c_reduce[i]:id_r_e_] > i_mean_r_))  # 准备找第一个
        # 找到环缝起始和结束ID
        id_l_ = np.max(LeftInterval_) + id_l_b_
        id_r_ = np.min(RightInterval_) + c_reduce[i]
        name_l_ = int(c_un[id_l_])
        name_r_ = int(c_un[id_r_])
        name_i_ = np.arange(name_l_, name_r_, 1)  # 所有的环缝名集合
        seams_all = np.append(seams_all, name_i_)  # 添加所有环缝名
        RB_S = np.append(RB_S, np.max(name_i_))  # 添加起始位置
        RB_E = np.append(RB_E, np.min(name_i_))  # 添加结束位置
    print('衬砌表面起止位置为', RB_S, RB_E)
    RB_E = np.append(RB_E, c_un[-1])
    # 输出点云
    c_xyzic = txti_in[np.isin(txti_in[:, 4], seams_all), :]  # 返回xyzic[:, -1]中有c[c_in]的行数
    '将txt_in中的环缝点云抹掉'
    id_del = np.isin(np.isin(txti_in[:, 4], seams_all), False)  # 除去环缝点云的点云下标
    # print(id_del)
    txti_delC = txti_in[id_del, :]  # 去除环缝的点云
    return txti_delC, c_xyzic


