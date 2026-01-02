#!/usr/bin/env python
# coding=utf-8

import random
import math
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Circle
import numpy as np
import scipy.linalg as sl
import scipy as sp


true_x = 5  # 真值x为5
true_y = 5  # 真值y为5
true_r = 10  # 真值半径为10
points_num = 150  # 点云数量
inline_points = 130  # 符合点云数量
points_x = []
points_y = []


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
    iterations = 0  # 迭代次数
    bestfit = None
    besterr = np.inf  # 设置默认值
    best_inlier_idxs = None
    while iterations < k:  # 如果没有超过最多迭代次数
        maybe_idxs, test_idxs = random_partition(n, data.shape[0])  # 打乱顺序
        maybe_inliers = data[maybe_idxs, :]  # 获取size(maybe_idxs)行数据(Xi,Yi)
        test_points = data[test_idxs]  # 若干行(Xi,Yi)数据点
        maybemodel = model.fit(maybe_inliers)  # 拟合模型
        test_err = model.get_error(test_points, maybemodel)  # 计算误差:平方和最小
        also_idxs = test_idxs[test_err < t]
        also_inliers = data[also_idxs, :]
        if debug:
            print ('test_err.min()', test_err.min())
            print ('test_err.max()', test_err.max())
            print ('numpy.mean(test_err)', np.mean(test_err))
            print ('iteration %d:len(alsoinliers) = %d' % (iterations, len(also_inliers)))
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


def random_partition(n, n_data):
    """return n random rows of data and the other len(data) - n rows"""
    all_idxs = np.arange(n_data)  # 获取n_data下标索引
    np.random.shuffle(all_idxs)  # 打乱下标索引
    idxs1 = all_idxs[:n]
    idxs2 = all_idxs[n:]
    return idxs1, idxs2


'''最小二乘拟合直线模型'''


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


def fit_2Dline_ransac(points, sigma, iters=1000, P=0.99):
    """
    使用ransac算法拟合直线
    :param points: 二维点集
    :param sigma: 数据和模型之间可接受的差值
    :param iters: 最大迭代次数
    :param P: 得到正确模型的概率
    :return:
    最佳的斜率和截距
    """
    # 最好的模型的参数估计
    best_a = 0  # 直线斜率
    best_b = 0  # 直线截距
    n_total = 0  # 内点数量
    for i in range(iters):
        # 随机选两个求解模型
        sample_index = random.sample(range(len(points)), 2)
        x_1 = points[sample_index[0], 0]
        y_1 = points[sample_index[0], 1]
        x_2 = points[sample_index[1], 0]
        y_2 = points[sample_index[1], 1]
        if x_2 == x_1:
            continue
        # y=ax+b 求解出a,b
        a = (y_2-y_1)/(x_2-x_1)
        b = y_1-a*x_1
        # 算出内点数目
        total_inlier = 0
        for index in range(len(points)):
            y_estimate = a * points[index, 0] + b
            if abs(y_estimate - points[index, 1]) < sigma:
                total_inlier += 1
        # 判断当前模型是否比之前估算的模型好
        if total_inlier > n_total:
            iters = math.log(1-P)/math.log(1-pow(total_inlier/len(points), 2))
            n_total = total_inlier
            best_a = a
            best_b = b
        # 判断是否当前模型已经符合超过一半的点
        if total_inlier>len(points)//2:
            break

    return best_a, best_b

def fit_circle_single(xz):
    '拟合单个圆形'
    model = CircleLeastSquareModel()
    result = model.fit(xz)
    x0 = result.a * -0.5
    z0 = result.b * -0.5
    r = 0.5 * math.sqrt(result.a **2 + result.b** 2 - 4*result.c)
    return np.array([x0,z0,r])



if __name__ == "__main__":
    '''生成随机点， 作为数据源'''
    for i in range(1, points_num):
        # print(random.randint(-5, 15))
        a = random.uniform(true_x - true_r, true_x + true_r)
        x = round(a, 2)
        up_down = random.randrange(-1, 2, 2)
        y = true_y + up_down * math.sqrt(true_r ** 2 - (x - true_x) ** 2)
        b1 = random.uniform(-0.05, 0.05)
        b2 = random.uniform(-0.05, 0.05)
        c1 = random.uniform(0.3, 0.8)
        c2 = random.uniform(0.3, 0.8)
        error_b1 = round(b1, 2)
        error_b2 = round(b1, 2)
        error_c1 = round(c1, 2)
        error_c2 = round(c2, 2)
        if i <= inline_points:
            points_x.append(x + error_b1)
            points_y.append(y + error_b2)
        else:
            up_down1 = random.randrange(-1, 2, 2)
            points_x.append(x + error_c1)
            points_y.append(y + error_c2)
    plt.plot(points_x, points_y, "ro", label="data points")
    plt.axis('equal')
    # plt.show()
    circle1 = Circle(xy=(true_x, true_y), radius=true_r, alpha=0.5, fill=False, label="true circle")  # 先给一个初值去计算圆
    plt.gcf().gca().add_artist(circle1)
    model = CircleLeastSquareModel()  # 类的实例化:用最小二乘生成已知模型
    data = np.vstack([points_x, points_y]).T
    result = model.fit(data)
    x0 = result.a * -0.5
    y0 = result.b * -0.5
    r = 0.5 * math.sqrt(result.a ** 2 + result.b ** 2 - 4 * result.c)
    circle2 = Circle(xy=(x0, y0), radius=r, alpha=0.5, fill=False, label="least square fit circle")  # 第一次拟合后的圆
    plt.gcf().gca().add_artist(circle2)

    print("circle x is %f, y is %f, r is %f" % (x0, y0, r))
    # run RANSAC 算法
    ransac_fit, ransac_data = ransac(data, model, 20, 1000, 20, 50, debug=False, return_all=True)  # ransac迭代
    x1 = ransac_fit.a * -0.5
    y1 = ransac_fit.b * -0.5
    r_1 = 0.5 * math.sqrt(ransac_fit.a ** 2 + ransac_fit.b ** 2 - 4 * ransac_fit.c)
    circle3 = Circle(xy=(x1, y1), radius=r_1, alpha=0.5, fill=False, label="least square ransac fit circle")
    plt.gcf().gca().add_artist(circle3)
    points_x_array = np.array(points_x)
    points_y_array = np.array(points_y)
    plt.plot(points_x_array[ransac_data['inliers']], points_y_array[ransac_data['inliers']], 'bx',
               label="RANSAC data")
    print("ransac circle x is %f, y is %f, r is %f" % (x1, y1, r_1))
    plt.grid()
    plt.legend(loc='upper right')
    plt.show()
