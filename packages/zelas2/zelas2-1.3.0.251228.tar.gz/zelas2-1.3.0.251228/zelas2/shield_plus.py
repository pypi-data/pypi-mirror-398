# 本代码适用于25年3月的纵缝提取
import os
from typing import Union
import numpy as np
import zelas2.shield as zs
import multiprocessing as mp
import zelas2.Multispectral as zm
from sympy.codegen.ast import Return
from tqdm import tqdm
import cv2
from scipy.spatial.transform import Rotation
import zelas2.RedundancyElimination as zr
from sklearn.neighbors import KDTree  # 添加机器学习的skl.KDT的函数组
from multiprocessing import shared_memory
from sklearn.cluster import DBSCAN
import zelas2.ransac as zR
import zelas2.TheHeartOfTheMilitaryGod as zt
from scipy.spatial.distance import pdist, squareform
from scipy.signal import find_peaks
import zelas2.Ellipse as ze
from scipy.stats import mode
import random
import math
from matplotlib.path import Path # Matplotlib 提供了方便的点在多边形内判断工具
from scipy.optimize import minimize_scalar
from scipy.optimize import least_squares
from sklearn.neighbors import NearestNeighbors
from scipy.spatial import cKDTree
from sklearn.linear_model import RANSACRegressor
import scipy.spatial as spt  # 求凸壳用的库
def find_continuous_segments_numpy(arr):
    """
    找到一维数组中所有连续整数段的起始和终止数，返回 NumPy 数组
    :param arr: 一维整数数组（已排序）
    :return: NumPy 数组，每行为 (起始数, 终止数)
    """
    segments = []  # 存储所有连续段
    start = arr[0]  # 当前连续段的起始数
    for i in range(1, len(arr)):
        if arr[i] != arr[i - 1] + 1:  # 检测中断点
            segments.append((start, arr[i - 1]))  # 保存当前连续段
            start = arr[i]  # 开始新的连续段
    # 添加最后一个连续段
    segments.append((start, arr[-1]))
    # 转换为 NumPy 数组
    return np.array(segments, dtype=int)

def get_ρθ(xz_p, xzr):
    '求每个盾构环的极径差和反正切'
    num_p = len(xz_p)  # 当前截面点数量
    ρ = np.sqrt((xz_p[:,0]-xzr[0])**2+(xz_p[:,1]-xzr[1])**2)-xzr[2]
    θ = np.empty(num_p)
    for i in range(num_p):
        θ[i] = zs.get_angle(xz_p[i,0],xz_p[i,1],xzr[0],xzr[1])
    return np.c_[ρ,θ]

def find_seed(θyρvci,ρ_td,r,cpu=mp.cpu_count(),c_ignore=4):
    '寻找符合纵缝特征的种子点'
    θyρvci_up = θyρvci[θyρvci[:,2]>=ρ_td,:]  # 低于衬砌点的不要
    # 准备工作
    pool = mp.Pool(processes=cpu)  # 开启多进程池，数量为cpu
    c_un = np.unique(θyρvci[:,4])
    num_c = len(np.unique(θyρvci[:,4]))  # 截面数
    # good_index = []
    # 并行计算
    multi_res = pool.starmap_async(find_seed_cs, ((θyρvci,np.uint64(θyρvci_up[θyρvci_up[:,4]==c_un[i],5]),c_un[i],r,c_ignore) for i in
                 tqdm(range(num_c),desc='分配任务寻找种子点',unit='个截面',total=num_c)))
    j = 0
    for res in tqdm(multi_res.get(),total=num_c,desc='输出种子点下标'):
        if j==0:
            good_index = res
        else:
            good_index = np.hstack((good_index, res))
        j += 1
    pool.close()  # 关闭所有进程
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    return np.int64(good_index)


def find_seed_cs(θyρvci,id_θyρvci_up_c,c,r,c_ignore=4):
    '''
    寻找单个截面符合纵缝特征的种子点
    θyρvci : 点云信息
    id_θyρvci_up_c ：符合搜索的点云下标
    c ：当前截面
    r :当前截面半径
    c_ignore ：忽略的截面数
    '''
    good_ind = []  # 空下标
    θ_l_td = 0.15 * np.pi * r / 180
    for i in id_θyρvci_up_c:
        if θyρvci[i,3]==0:  # 如果当前点为线特征
            # 找到搜索截面
            θyρ_c_ = θyρvci[θyρvci[:, 4] <= c + c_ignore, :]
            θyρ_c_ = θyρ_c_[θyρ_c_[:, 4] >= c - c_ignore, :]
            # 判断左侧是否有球特征
            θ_l_ = θyρvci[i,0] - θ_l_td  # 左侧角度阈值
            θyρ_l_ = θyρ_c_[θyρ_c_[:, 0] < θyρvci[i, 0], :]
            θyρ_l_ = θyρ_l_[θyρ_l_[:, 0] >= θ_l_, :]
            # 判断右侧是否有球特征
            θ_r_ = θyρvci[i,0] + θ_l_td  # 右侧角度阈值
            θyρ_r_ = θyρ_c_[θyρ_c_[:, 0] > θyρvci[i, 0], :]
            θyρ_r_ = θyρ_r_[θyρ_r_[:, 0] <= θ_r_, :]
            if 2 in θyρ_l_[:, 3] and 2 in θyρ_r_[:, 3]:  # 如果左右都有球特征
                good_ind.append(θyρvci[i,5])  # 作为种子点
    return good_ind

def distance_to_line(point, line):
    """计算点到直线的几何距离"""
    x0, y0 = point
    x1, y1, x2, y2 = line
    numerator = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
    denominator = np.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)
    return numerator / denominator if denominator != 0 else 0

def merge_similar_lines(lines, angle_thresh=np.pi / 18, rho_thresh=20):
    """合并相似直线（极坐标参数相近的线段）"""
    merged = []
    for line in lines:
        rho, theta = line_to_polar(line[0])
        found = False
        for m in merged:
            m_rho, m_theta = m[0]
            # 检查角度和距离差异
            if abs(theta - m_theta) < angle_thresh and abs(rho - m_rho) < rho_thresh:
                m[0] = ((m_rho + rho) / 2, (m_theta + theta) / 2)  # 合并平均值
                m[1].append(line)
                found = True
                break
        if not found:
            merged.append([(rho, theta), [line]])

    # 转换回线段格式（取合并后的极坐标生成新线段）
    merged_lines = []
    for m in merged:
        rho, theta = m[0]
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a * rho
        y0 = b * rho
        # 生成足够长的线段（覆盖图像范围）
        scale = 1000
        x1 = int(x0 + scale * (-b))
        y1 = int(y0 + scale * (a))
        x2 = int(x0 - scale * (-b))
        y2 = int(y0 - scale * (a))
        merged_lines.append([x1, y1, x2, y2])

    return merged_lines[:5]  # 最多返回前5条

def find_lines(θy):
    '通过数字图像操作将纵缝找到并返回种子点'
    '0.整理数据'
    θy = θy*100
    θy[:, 0] -= np.min(θy[:, 0])
    θy[:, 1] -= np.min(θy[:, 1])
    θy = np.uint64(θy)
    x_max = np.max(θy[:,0])
    y_max = np.max(θy[:,1]) # 求边界
    print('二维边长',x_max,y_max)
    '1.创建图像'
    img = np.zeros((int(y_max)+1, int(x_max)+1), dtype=np.uint8)
    for x,y in θy:
        img[y, x] = 255
    '''
    cv2.imshow("Image", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    '''
    '2.直线检测'
    # 霍夫变换检测直线
    lines = cv2.HoughLinesP(img, rho=1, theta=np.pi / 180, threshold=50, minLineLength=50, maxLineGap=50)  # 检测单位像素、角度、超过像素阈值、最小长度阈值、最大间断阈值
    # --- 提取前5条最长的直线 ---
    detected_lines = []
    if lines is not None:
        lines = lines[:, 0, :]
        # 按线段长度排序（从最长到最短）
        lines = sorted(lines, key=lambda x: np.linalg.norm(x[2:] - x[:2]), reverse=True)[:6]
        detected_lines = lines
    threshold_distance = 2.0  # 点到直线的最大允许距离（根据噪声调整）
    # 初始化：所有点标记为未分配
    assigned = np.zeros(len(θy), dtype=bool)
    line_points_list = []  # 存储每条直线的点
    line_indices_list = []  # 存储每条直线的点索引
    for line in detected_lines:
        distances = np.array([distance_to_line(p, line) for p in θy])
        # 筛选未分配且距离小于阈值的点
        mask = (distances < threshold_distance) & ~assigned
        line_points = θy[mask]
        line_points_list.append(line_points)
        indices = np.where(mask)[0]
        line_indices_list.append(indices)
        assigned |= mask  # 标记已分配的点
    # 合并前5条直线的点
    all_line_points = np.vstack(line_points_list)
    # 分离噪声点
    noise_points = θy[~assigned]
    '''
    # --- 可视化结果 ---
    # 创建彩色图像用于显示
    result_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    # 绘制检测到的直线（绿色）
    for line in detected_lines:
        x1, y1, x2, y2 = line
        cv2.line(result_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    # 绘制属于直线的点（红色）
    for p in all_line_points:
        cv2.circle(result_img, tuple(p), 2, (0, 0, 255), -1)
    '''
    '''
        # 预定义5种颜色（BGR格式）
    colors = [
        (0, 0, 255),   # 红色
        (0, 255, 0),   # 绿色
        (255, 0, 0),   # 蓝色
        (0, 255, 255), # 黄色
        (255, 0, 255)  # 品红色
    ]
    # 绘制每条直线及其对应的点
    for i, (line, line_points) in enumerate(zip(detected_lines, line_points_list)):
        color = colors[i % len(colors)]  # 循环使用颜色列表
        # 绘制直线
        x1, y1, x2, y2 = line
        cv2.line(result_img, (x1, y1), (x2, y2), color, 2)
    '''
    '''
    # 绘制噪声点（蓝色）
    for p in noise_points:
        cv2.circle(result_img, tuple(p.astype(int)), 2, (255, 0, 0), -1)
    cv2.imshow("Result", result_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    '''
    # 去除 line_indices_list 中的空元素
    line_indices_list = [indices for indices in line_indices_list if len(indices) > 0]
    return line_indices_list


def merge_similar_lines(lines, angle_thresh=5, dist_thresh=10):
    """
    合并角度和位置相近的线段
    :param lines: 线段列表，格式为 [[x1,y1,x2,y2], ...]
    :param angle_thresh: 角度差阈值（度）
    :param dist_thresh: 线段中心点距离阈值（像素）
    :return: 合并后的线段列表
    """
    merged = []
    for line in lines:
        x1, y1, x2, y2 = line
        # 计算线段角度（弧度）
        angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
        # 计算线段中心点
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2

        # 检查是否与已合并线段近似
        found = False
        for m in merged:
            m_angle, m_cx, m_cy = m['angle'], m['cx'], m['cy']
            # 角度差和中心点距离
            angle_diff = abs(angle - m_angle)
            dist = np.sqrt((cx - m_cx) ** 2 + (cy - m_cy) ** 2)

            if angle_diff < angle_thresh and dist < dist_thresh:
                # 合并线段（延长端点）
                m['x1'] = min(m['x1'], x1, x2)
                m['y1'] = min(m['y1'], y1, y2)
                m['x2'] = max(m['x2'], x1, x2)
                m['y2'] = max(m['y2'], y1, y2)
                found = True
                break

        if not found:
            merged.append({
                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                'angle': angle, 'cx': cx, 'cy': cy
            })
    # 转换为坐标格式
    return [[m['x1'], m['y1'], m['x2'], m['y2']] for m in merged]


def fit_3d_line(points):
    """
    Fit a 3D line to a point cloud using PCA.
    Parameters:
    points (numpy.ndarray): Nx3 array of 3D points.
    Returns:
    tuple: (centroid, direction_vector)
        centroid is a point on the line (numpy.ndarray of shape (3,)),
        direction_vector is the direction vector of the line (numpy.ndarray of shape (3,)).
    """
    # 计算点云的质心
    centroid = np.mean(points, axis=0)
    # 将点云中心化
    centered_points = points - centroid
    # 计算协方差矩阵
    cov_matrix = np.cov(centered_points.T)
    # 计算协方差矩阵的特征值和特征向量
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
    # 找到最大特征值对应的特征向量作为方向向量
    direction_vector = eigenvectors[:, np.argmax(eigenvalues)]
    # Centroid (a point on the line): [1.5 1.5 1.5]
    # Direction vector: [0.57735027 0.57735027 0.57735027]
    return centroid, direction_vector


def distance_to_line_3D(points, centroid, direction):
    """
    计算点到三维直线的距离。
    Parameters:
    points (numpy.ndarray): Nx3 的3D点。
    centroid (numpy.ndarray): 直线上的一点，形状为 (3,)。
    direction (numpy.ndarray): 直线的单位方向向量，形状为 (3,)。
    Returns:
    numpy.ndarray: 每个点到直线的距离，形状为 (N,)。
    """
    # 计算点与质心的向量差
    vec = points - centroid
    # 计算叉乘 (支持批量计算)
    cross_product = np.cross(vec, direction)
    # 距离为叉乘的模长
    distances = np.linalg.norm(cross_product, axis=1)
    return distances

def find_CS_25(xyzic,GirthInterval=245,num_cpu=mp.cpu_count(),z_range=1):
    '环缝提取，固定长度版，25年修补版'
    xyzic[:, 3] = zm.normalization(xyzic[:, 3], 255)  # 强度值离散化
    # 计算每个环的平均强度值
    c_un = np.unique(xyzic[:, 4])  # 圆环从小到大排列
    num_C = len(c_un)  # 截面数量
    # 并行计算准备
    tik = zs.cut_down(num_C, num_cpu)  # 分块起止点
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    # 限制参与计算的比例
    z_max = np.max(xyzic[:, 2])
    z_min = np.min(xyzic[:, 2])
    d_z = z_max - z_min
    t_z = z_min + d_z * (1 - z_range)  # 参与统计的阈值
    ps_free = xyzic[xyzic[:, 2] >= t_z, :]  # 参与统计的点云
    i_c = np.empty(num_C)  # 新建一个存储圆环平均强度值的容器
    multi_res = [pool.apply_async(zs.find_cImean_block, args=(ps_free, c_un, tik[i], tik[i + 1])) for i in
                 range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    tik_ = 0  # 计数器
    for res in multi_res:
        i_c[tik[tik_]:tik[tik_ + 1]] = res.get()
        tik_ += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    # 后期整理
    i_c = zm.normalization(i_c, 255)  # 均值离散化
    i_c_mean = np.mean(i_c)  # 平均强度值均值
    i_c_std = np.std(i_c)  # 平均强度值方差
    print('截面强度值均值', i_c_mean, '截面强度值标准差', i_c_std)
    # 找到强度值的最低点以及其他的极低点
    id_min = np.argmin(i_c)
    num_CS_0 = int(np.round(num_C / GirthInterval))  # 假想环缝数量
    print('理论的环缝数量为',str(num_CS_0))
    Begin_CS_0 = id_min % GirthInterval  # 假想起始位置
    id_CS_0 = np.arange(Begin_CS_0, num_C, GirthInterval)  # 假想环缝位置
    print('假想环缝位置',c_un[id_CS_0])
    belong_i = 75  # 强度值搜索半径  # 30
    mid_ = 2  # 余量区间 3
    RB_S = np.array(c_un[0])  # 衬砌开始位置
    RB_E = []  # 衬砌结束位置
    c_name_ins = np.empty(num_CS_0)  # 极低值容器
    c_ = []  # 环缝的存储名
    c_id = []  # 环缝的存储下标器
    N = 8  # 环缝间隔
    #   dis_max = i_c_mean - i_c_std * 3  # 最大差值
    for i in range(num_CS_0):
        # 确保索引在有效范围内
        id_start = max(0, id_CS_0[i] - belong_i)
        id_end = min(len(i_c), id_CS_0[i] + belong_i)
        # 求强度值极低点
        id_min_i_ = np.argmin(i_c[id_start:id_end]) + id_start
        c_name_ins[i] = c_un[id_min_i_]  # 强度值极低点位置
        print('修改后的第', i, '个极低值位置为', c_un[id_min_i_])
        # 寻找以强度值为主的开始和结束位置
        id_min = int(c_name_ins[i] - N)
        id_max = int(c_name_ins[i] + N)
        # 添加衬砌表面起止位置
        RB_E = np.append(RB_E, id_min)  # 添加结束位置
        RB_S = np.append(RB_S, id_max)  # 添加起始位置
    RB_E = np.append(RB_E, c_un[-1])  # 结束位置封顶
    for i in range(num_CS_0):
        if i == 0:
            seams_all = np.arange(RB_E[i], RB_S[i + 1])  # IndexError: too many indices for array: array is 1-dimensional, but 2 were indexed
        else:
            seams_all = np.append(seams_all, np.arange(RB_E[i], RB_S[i + 1]))
    c_xyzic = xyzic[np.isin(xyzic[:, 4], seams_all), :]  # 返回xyzic[:, -1]中有c[c_in]的行数
    # 精简衬砌表面
    id_del = np.isin(np.isin(xyzic[:, 4], seams_all), False)  # 除去环缝点云的点云下标
    txti_delC = xyzic[id_del, :]  # 去除环缝的点云

    return  txti_delC, c_xyzic

def fit_3d_circle(xyz):
    '拟合三维圆'
    num, dim = xyz.shape
    # 求解平面法向量
    L1 = np.ones((num, 1))
    A = np.linalg.inv(xyz.T @ xyz) @ xyz.T @ L1
    # 构建矩阵B和向量L2
    B_rows = (num - 1) * num // 2
    B = np.zeros((B_rows, 3))
    L2 = np.zeros(B_rows)
    count = 0
    for i in range(num):
        for j in range(i + 1, num):
            B[count] = xyz[j] - xyz[i]
            L2[count] = 0.5 * (np.sum(xyz[j] ** 2) - np.sum(xyz[i] ** 2))
            count += 1
    # 构造矩阵D和向量L3
    D = np.zeros((4, 4))
    D[0:3, 0:3] = B.T @ B
    D[0:3, 3] = A.flatten()  # 前三行第四列为A
    D[3, 0:3] = A.T  # 第四行前三列为A的转置
    B_transpose_L2 = B.T @ L2
    L3 = np.concatenate([B_transpose_L2, [1]]).reshape(4, 1)
    # 求解圆心坐标C
    C = np.linalg.inv(D.T) @ L3
    C = C[:3].flatten()  # 提取前三个元素作为圆心
    # 计算半径
    distances = np.linalg.norm(xyz - C, axis=1)
    r = np.mean(distances)
    return np.concatenate([C, [r]])

def fit_3d_circle_mp(xyzc,num_thread=mp.cpu_count()):
    '并行拟合三维圆算法'
    c_un = np.unique(xyzc[:,3])  # 截面序列
    num_c = len(c_un)  # 截面数量
    xyzr_all = np.empty([num_c,4])  # 输出容器
    pool = mp.Pool(processes=num_thread)  # 开启多进程池，数量为cpu
    j = 0  # 分块输出计时器
    # 并行计算
    multi_res = pool.starmap_async(fit_3d_circle, ((xyzc[xyzc[:,3]==c_un[i],:3],) for i in
                 tqdm(range(num_c),desc='分配任务拟合单个三维圆参数',unit='个cross-section',total=num_c)))
    for res in tqdm(multi_res.get(), total=num_c, desc='导出单个三维圆参数', unit='个cross-section'):
        xyzr_all[j,:] = res
        j += 1
    pool.close()  # 禁止进程池再接收任务  #Prohibit process pools from receiving tasks again
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算  #After all processes have completed their calculations, exit parallel computing
    return xyzr_all

def STSD_add_C(las,inx_d = 0.006168):
    '对STSD数据集添加截面序列号'
    # 整理基本信息
    xyz = las.xyz
    I = las.intensity
    inx = las.inx
    label = las.classification
    # 人工制作截面序列号
    inx_un = np.unique(inx)
    inx_min = np.min(inx)
    inx_max = np.max(inx)
    inx_range = np.arange(start=inx_min, stop=inx_max + inx_d, step=inx_d)
    k = 0
    xyzicl = np.c_[xyz,I,inx,label]
    for i in inx_range:
        j = i+inx_d
        xyzicl_ = xyzicl[xyzicl[:,4]<j,:]
        xyzicl_ = xyzicl_[xyzicl_[:, 4] >= i, :]
        xyzicl_[:,4] = k
        if k == 0:
            xyzicl_out = xyzicl_
        else:
            xyzicl_out = np.r_[xyzicl_out,xyzicl_]
        k += 1
    return xyzicl_out

def get_nei_dis_mp(xyz,r,tree,dis_all,cpu=mp.cpu_count()-6):
    '求每个点的平均凸起(建议线程数不超过核心数)'
    # 准备工作
    num = len(xyz)
    dis_in = np.empty(num)  # 存储平均突起的容器
    tik = zs.cut_down(num, cpu)  # 并行计算分块
    pool = mp.Pool(processes=cpu)  # 开启多进程池，数量为cpu
    # 开始进行并行计算
    multi_res = [pool.apply_async(get_nei_dis_block, args=(xyz[tik[i]:tik[i + 1],:], dis_all, tree, r)) for i in
                 range(cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    tik_ = 0  # 计数器
    for res in multi_res:
        dis_in[tik[tik_]:tik[tik_ + 1]] = res.get()
        print('已完成',str(tik[tik_]),'到',str(tik[tik_+1]))
        tik_ += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    return dis_in

def get_nei_dis_block(xyz_,dis_all,tree,r):
    '分块求每个点的平均凸起'
    num_ = len(xyz_)
    dis_in_ = np.zeros(num_)  # 存储平均突起的容器
    for i in tqdm(range(num_)):
        xyz__ = xyz_[i,:]
        indices, dises = tree.query_radius(xyz__.reshape(1, -1), r=r, return_distance=True,
                                           sort_results=True)  # 返回每个点的邻近点下标列表
        indices = indices[0]
        if len(indices) >= 2:
            dis_all_ = dis_all[indices]  # 临近点圆心距  # dis_all是全部的dis_all
            dis_mean = np.mean(dis_all_[1:])  # 当前点平均圆心距
            dis_ = dis_all_[0] - dis_mean  # 求当前点平均突起
            dis_in_[i] = dis_
    return dis_in_

def get_nei_line_density_c(ca_,width):
    '计算截面每个点左右密度差'
    num_ = len(ca_)
    dd_all_ = np.zeros(num_)
    for i in range(num_):
        a_ = ca_[i, 1]
        a_min = a_ - width
        a_max = a_ + width  # 左右角度区间
        count_l = np.sum((ca_[:, 1] > a_min) & (ca_[:, 1] < a_))
        count_r = np.sum((ca_[:, 1] > a_) & (ca_[:, 1] < a_max))  # 左右角度区间点数
        with np.errstate(divide='ignore', invalid='ignore'):
            ratios = np.minimum(count_l, count_r) / np.maximum(count_l, count_r) # 避免除以零的情况
        # 处理NaN和Inf情况（当分母为0时）
        ratios = np.nan_to_num(ratios, nan=0.0, posinf=1.0, neginf=-1.0)
        dd_all_[i] = ratios
    return dd_all_

def get_nei_line_density_mp(ca,width=360/500,cpu=mp.cpu_count()):
    '计算每个点左右密度差(请先对点云按照截面序列号进行排序)'
    # 准备工作
    # num = len(ca)
    # dd_all = np.empty(num)
    # 按照第一列进行排序
    ca = ca[ca[:, 0].argsort()]
    # 统计每个截面的点数
    # unique_sections, section_counts = np.unique(ca[:, 0], return_counts=True)
    unique_sections = np.unique(ca[:, 0])
    num_c = len(unique_sections)
    pool = mp.Pool(processes=cpu)  # 开启多进程池，数量为cpu
    # 开始进行并行计算
    multi_res = pool.starmap_async(get_nei_line_density_c, ((ca[ca[:,0]==unique_sections[i],:], width) for i in
                 tqdm(range(num_c),desc='分配任务给每个截面求左右密度差',unit='cross-sections',total=num_c)))
    j = 0  # 分块输出计时器
    for res in tqdm(multi_res.get(), total=num_c, desc='导出每个点的左右密度差', unit='cross-sections'):
        if j==0:
            dd_all = res
        else:
            dd_all= np.append(dd_all,res)
        j += 1
    pool.close()  # 禁止进程池再接收任务  #Prohibit process pools from receiving tasks again
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算  #After all processes have completed their calculations, exit parallel computing
    return dd_all

def Curvature_r_mp(xyz,r=0.04,cpu=mp.cpu_count()):
    '并行按照球半径计算曲率'
    # 准备工作
    pool = mp.Pool(processes=cpu)  # 开启多进程池，数量为cpu
    num = len(xyz)  # 返回点云数量
    # start, end = block(num, cpu)  # 返回每个block的起始点云下标和终止点云下标
    tik = zr.cut_down(num, cpu)  # 去除bug后的分块函数
    tree = KDTree(xyz)  # 创建树
    j = 0  # 分块输出计数器
    curvature_all = np.empty(shape=len(xyz))  # 新建一个容器：整个点云的曲率数集
    multi_res = [pool.apply_async(curvature_r_block, args=(xyz,tik[i],tik[i+1], tree, r)) for i in range(cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    for res in multi_res:
        curvature_all[tik[j]:tik[j+1]] = res.get()  # 将每个进程得到的结果分block的发送到容器当中
        print('已完成第', tik[j], '至第', tik[j + 1], '的点云')
        j += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    curvature_all = np.nan_to_num(curvature_all, nan=0.0)
    return curvature_all  # 返回全部点云曲率集

def Curvature_r_mp_shm(xyz,r=0.04,cpu=mp.cpu_count()):
    '并行按照球半径计算曲率(共享内存)'
    # 准备工作
    pool = mp.Pool(processes=cpu)  # 开启多进程池，数量为cpu
    num = len(xyz)  # 返回点云数量
    # start, end = block(num, cpu)  # 返回每个block的起始点云下标和终止点云下标
    tik = zr.cut_down(num, cpu)  # 去除bug后的分块函数
    tree = KDTree(xyz)  # 创建树
    j = 0  # 分块输出计数器
    curvature_all = np.empty(shape=len(xyz))  # 新建一个容器：整个点云的曲率数集
    '创建共享内存'
    shm = shared_memory.SharedMemory(create=True, size=xyz.nbytes)
    #  将数据复制到共享内存
    shared_array = np.ndarray(xyz.shape, dtype=xyz.dtype, buffer=shm.buf)
    shared_array[:] = xyz[:]
    print(f"共享内存创建完成: {shm.name}")
    print(f"共享内存大小: {shm.size} 字节")
    multi_res = [pool.apply_async(curvature_r_block, args=(shared_array,tik[i],tik[i+1], tree, r)) for i in range(cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    for res in multi_res:
        curvature_all[tik[j]:tik[j+1]] = res.get()  # 将每个进程得到的结果分block的发送到容器当中
        print('已完成第', tik[j], '至第', tik[j + 1], '的点云')
        j += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    # 清理共享内存
    shm.close()
    shm.unlink()  # 重要：释放共享内存
    curvature_all = np.nan_to_num(curvature_all, nan=0.0)
    return curvature_all  # 返回全部点云曲率集

def curvature_r_block(xyz,start,end,tree,r):
    '分块按照球半径计算曲率'
    # xyz_32 = np.column_stack((xyz[:, 0], xyz[:, 1], xyz[:, 2])).astype(np.float32)
    # pcd = o3d.geometry.PointCloud()
    # pcd.points = o3d.utility.Vector3dVector(xyz_32)
    # pcd_tree = o3d.geometry.KDTreeFlann(pcd)
    curvature_all = np.empty(end-start)
    # num_ = len(xyz_)
    # curvature_all = np.empty(num_)
    j = 0
    for i in tqdm(range(start,end)):
        # [_, idx, _] = pcd_tree.search_knn_vector_3d(pcd.points[i], n)  # 求每个点最近的n个点
        # id_kntree[i, :] = idx  # 求出每个点最邻近的n个点的下标
        xyz_ = xyz[i,:]
        indices, dises = tree.query_radius(xyz_.reshape(1, -1), r=r, return_distance=True,
                                           sort_results=True)  # 返回每个点的邻近点下标列表
        indices = indices[0]
        xyz_n = xyz[indices, :]
        cv, _ = zr.pca(xyz_n)  # 求每个点的特征值和特征向量
        c = zr.curvature_(cv,-1)  # 求出当前点的曲率
        # print(c)
        curvature_all[j] = c
        j += 1
    return curvature_all


def Curvature_r(xyz,r=0.04,job=-1):
    '按照球半径计算曲率'
    num = len(xyz)
    curvature_all = np.empty(num)
    tree = KDTree(xyz)  # 创建树
    for i in tqdm(range(num)):
        xyz_ = xyz[i,:]
        indices, dises = tree.query_radius(xyz_.reshape(1, -1), r=r, return_distance=True,
                                           sort_results=True)  # 返回每个点的邻近点下标列表
        indices = indices[0]
        xyz_n = xyz[indices, :]
        cv, _ = zr.pca(xyz_n)  # 求每个点的特征值和特征向量
        c = zr.curvature_(cv,job)  # 求出当前点的曲率
        # print(c)
        curvature_all[i] = c

    return curvature_all

def get_JCFI_mp(xyzic: Union[list, np.ndarray],ps_out: Union[list, np.ndarray], r: float,cpu:int = mp.cpu_count()) ->np.ndarray:
    '计算JCFI指数'
    '1.求曲率'
    C_all = Curvature_r_mp(xyzic[:, :3], r=0.04,cpu=cpu)
    '2.求平均凸起'
    ps = np.r_[xyzic,ps_out]
    del ps_out
    xzrc = zs.fit_circle(xyzic[:, 0], xyzic[:, 2], xyzic[:, 4], num_cpu=cpu)
    # xzry = zs.fit_circle(xyzic[:, 0], xyzic[:, 2], xyzic[:, 1], num_cpu=cpu)
    # xyziy = np.c_[ps[:, :4], ps[:, 1]]
    # dis_all = zs.get_CenterDis(xzry,xyziy,cpu_count=cpu)
    dis_all = zs.get_CenterDis(xzrc, ps, cpu_count=cpu)
    # tree = KDTree(xyzic)
    # del xzry,xyziy
    tree = KDTree(ps[:, :3])  # 创建树
    del ps
    dis_in = get_nei_dis_mp(xyzic[:, :3], r, tree, dis_all, cpu=cpu)
    '3.求点云左右密度差'
    # 求点云角度
    x0 = np.mean(xzrc[:, 0])
    z0 = np.mean(xzrc[:, 1])
    angle_all = zs.get_angle_all(xyzic[:,[0,2]],x0,z0,cpu_count=cpu)
    ps_Cda = np.c_[xyzic,C_all,dis_in,angle_all]
    ca = np.c_[xyzic[:,4],angle_all]
    dd_all = get_nei_line_density_mp(ca,cpu=cpu)
    ps_Cda = ps_Cda[ps_Cda[:, 4].argsort()]
    xyzicJ = np.c_[ps_Cda[:,:7],dd_all,ps_Cda[:,5]*ps_Cda[:,6]*dd_all]
    # xyzicJ = np.c_[xyzic,ps_Cda[:,5]*ps_Cda[:,6]*dd_all]
    # 将 NaN 替换为 0
    xyzicJ = np.nan_to_num(xyzicJ, nan=0.0)
    return xyzicJ

def get_JCFI_noout(xyzic: Union[list, np.ndarray], r: float, cpu:int = mp.cpu_count()) ->np.ndarray:
    '求JCFI(无非衬砌点情况)'
    '1.求曲率'
    C_all = Curvature_r_mp_shm(xyzic[:, :3], r=r,cpu=cpu)
    '2.求平均凸起'
    # xzrc = zs.fit_circle(xyzic[:, 0], xyzic[:, 2], xyzic[:, 4], num_cpu=cpu)
    ig = 10
    c_max = np.max(xyzic[:,4])-ig
    c_min = np.min(xyzic[:,4])+ig
    xyzic_min = xyzic[xyzic[:,4] >= c_min,:]
    xyzic_min = xyzic_min[xyzic_min[:,4] <= c_max,:]
    xzrc = zs.fit_circle(xyzic_min[:, 0], xyzic_min[:, 2], xyzic_min[:, 4], num_cpu=cpu)  # 拟合各截面
    # dis_all = zs.get_CenterDis(xzrc, xyzic, cpu_count=cpu)
    x0 = np.mean(xzrc[:, 0])
    z0 = np.mean(xzrc[:, 1])  # 平均圆心
    R = np.mean(xzrc[:, 2])
    dis_all = np.sqrt((xyzic[:, 0] - x0) ** 2 + (xyzic[:, 2] - z0) ** 2) - R
    tree = KDTree(xyzic[:, :3])  # 创建树
    dis_in = get_nei_dis_mp(xyzic[:, :3], r, tree, dis_all, cpu=cpu)
    '3.求点云左右密度差'
    angle_all = zs.get_angle_all(xyzic[:,[0,2]],x0,z0,cpu_count=cpu)
    ps_Cda = np.c_[xyzic,C_all,dis_in,angle_all]
    ca = np.c_[xyzic[:,4],angle_all]
    dd_all = get_nei_line_density_mp(ca,cpu=cpu)
    ps_Cda = ps_Cda[ps_Cda[:, 4].argsort()]
    '4.计算周长'
    # perimeter = angle_all / 360 * 2 * np.pi * R  # 基于周长求各点实际位置
    # perimeter = perimeter[ps_Cda[:, 4].argsort()]
    angle_all = zs.get_angle_all(ps_Cda[:, [0, 2]], x0, z0, cpu_count=cpu)
    perimeter = angle_all / 360 * 2 * np.pi * R
    # xyzicJP = np.c_[xyzic, ps_Cda[:, 5] * ps_Cda[:, 6] * dd_all]
    # xyzicJ = np.c_[ps_Cda[:, :7], dd_all, ps_Cda[:, 5] * ps_Cda[:, 6] * dd_all]
    xyzicJP = np.c_[ps_Cda[:,:5], ps_Cda[:, 5] * ps_Cda[:, 6] * dd_all,perimeter]
    # 将 NaN 替换为 0
    xyzicJP = np.nan_to_num(xyzicJP, nan=0.0)
    return xyzicJP

def get_JCFI_ZF(xyzic: Union[list, np.ndarray], r: float,cpu:int = mp.cpu_count(),R=2.7) ->np.ndarray:
    '求JCFI(纵缝版)'
    '1.求曲率'
    C_all = Curvature_r_mp_shm(xyzic[:, :3], r=r,cpu=cpu)
    '2.求平均凸起'
    xzrc = zs.fit_circle(xyzic[:, 0], xyzic[:, 2], xyzic[:, 4], num_cpu=cpu)
    dis_all = zs.get_CenterDis(xzrc, xyzic, cpu_count=cpu)
    tree = KDTree(xyzic[:, :3])  # 创建树
    dis_in = get_nei_dis_mp(xyzic[:, :3], r, tree, dis_all, cpu=cpu)
    '3.求点云左右密度差'
    x0 = np.mean(xzrc[:, 0])
    z0 = np.mean(xzrc[:, 1])
    angle_all = zs.get_angle_all(xyzic[:,[0,2]],x0,z0,cpu_count=cpu)
    ps_Cda = np.c_[xyzic,C_all,dis_in,angle_all]
    ca = np.c_[xyzic[:,4],angle_all]
    dd_all = get_nei_line_density_mp(ca,cpu=cpu)
    ps_Cda = ps_Cda[ps_Cda[:, 4].argsort()]
    # xyzicJ = np.c_[xyzic, ps_Cda[:, 5] * ps_Cda[:, 6] * dd_all]
    # xyzicJ = np.c_[ps_Cda[:, :7], dd_all, ps_Cda[:, 5] * ps_Cda[:, 6] * dd_all]
    '4.计算周长'
    # perimeter = angle_all / 360 * 2 * np.pi * R  # 基于周长求各点实际位置
    # perimeter = perimeter[ps_Cda[:, 4].argsort()]
    angle_all = zs.get_angle_all(ps_Cda[:, [0, 2]], x0, z0, cpu_count=cpu)
    perimeter = angle_all / 360 * 2 * np.pi * R
    xyzicJpC = np.c_[ps_Cda[:,:5], ps_Cda[:, 5] * ps_Cda[:, 6] * dd_all, perimeter,ps_Cda[:, 5]]
    # 将 NaN 替换为 0
    xyzicJpC = np.nan_to_num(xyzicJpC, nan=0.0)
    return xyzicJpC

def get_VY(shared_array,r,tree,i):
    '计算单点的Y方向分量'
    indices= tree.query_radius(shared_array[i,:3].reshape(1, -1), r=r, return_distance=False,
                                       sort_results=False)  # 返回每个点的邻近点下标列表
    indices = indices[0]
    xyz_ = shared_array[indices,:3]
    if len(xyz_)>=3:
        cov = np.cov(xyz_.T)
        eigenvals, eigenvecs = np.linalg.eigh(cov)
        v1 = eigenvecs[:, -1]  # 最大特征值对应的方向（主方向）
        vY = v1[1]
    else:
        vY = 0
    return vY

def get_HF_bulge(c_all,c_interval=500,c_long=20,num_min=40):
    '基于环缝凸起提取'
    # 整理截面序列与点数量
    c_un, num_c = np.unique(c_all, return_counts=True)
    # print(np.mean(num_c))
    # print(np.std(num_c))
    cn = np.c_[c_un,num_c]
    # 找到最大索引
    ind_max = np.argmax(num_c)
    c_max = c_un[ind_max]
    c_max_l = c_max-c_long
    c_max_r = c_max+c_long  # 假定左右缝极限
    # 筛选范围内的数据
    mask = (c_un >= c_max_l) & (c_un <= c_max_r) & (num_c >= num_min)
    # 获取满足条件的c_un值
    c_un_min = np.min(c_un)
    c_un_max = np.max(c_un)
    c_num_long = int(np.ceil((c_un_max-c_un_min)/c_interval))  # 假想环缝数量
    c_lf_all = np.zeros([c_num_long,2])  # 环缝起始和结束位置容器
    # valid_c_un = c_un[mask]  # 极低值起始和结束
    ind_c0_begin = (c_max-c_un_min) % c_interval + c_un_min # 假想起始位置
    for i in range(c_num_long):
        id_min_i_ =  (c_un >= (ind_c0_begin-c_long*7)) & (c_un <= (ind_c0_begin+c_long*7))  # 搜索极低值半径
        cn_ = cn[id_min_i_,:]  # 搜索半径内的数据
        id_max_ = np.argmax(cn_[:,1])  # 点数量最多的位置
        c_name_max = cn_[id_max_,0] # 所在截面序列号
        mask_ = (c_un >= c_name_max-c_long) & (c_un <= c_name_max+c_long) & (num_c >= num_min)  # 复合条件的索引
        valid_c_un_ = c_un[mask_]  # 极低值起始和结束
        c_lf_all[i,0]=valid_c_un_[0]
        c_lf_all[i,1]=valid_c_un_[-1]  # 环缝起始和结束位置
        # 刷新假想位置
        ind_c0_begin += c_interval
    # 创建所有范围的条件
    # 方法1：删除起始值和结束值都为0的行
    mask = ~((c_lf_all[:, 0] == 0) & (c_lf_all[:, 1] == 0))
    c_lf_all = c_lf_all[mask]
    print('环缝截面区间',c_lf_all)
    conditions = [(c_all >= start) & (c_all <= end)
                  for start, end in c_lf_all]
    # 合并所有条件
    final_mask = np.logical_or.reduce(conditions)
    inverse_mask = ~final_mask
    return final_mask, inverse_mask, c_lf_all

def get_HF_bulge_scipy(c_all,c_long=20,num_min=40):
    '基于环缝凸起提取'
    c_un, num_c = np.unique(c_all, return_counts=True)
    peaks, properties = find_peaks(num_c,height=np.mean(num_c) * 0.5,  # 最小峰值高度
                                   distance=int(len(num_c) * 0.1),  # 峰值间最小距离
                                   prominence=np.std(num_c) * 0.3)  # 峰值突出度
    c_un_maxes = c_un[peaks]  # 峰值对应的c值
    num_c_un_maxes = len(c_un_maxes)  # 峰值的数量
    c_lf_all = np.zeros([num_c_un_maxes, 2])  # 环缝起始和结束位置容器
    for i in range(num_c_un_maxes):
        mask_ = (c_un >= c_un_maxes[i]-c_long) & (c_un <= c_un_maxes[i]+c_long) & (num_c >= num_min)  # 复合条件的索引
        valid_c_un_ = c_un[mask_]  # 极低值起始和结束
        c_lf_all[i,0]=valid_c_un_[0]
        c_lf_all[i,1]=valid_c_un_[-1]  # 环缝起始和结束位置
    print('环缝截面区间', c_lf_all)
    conditions = [(c_all >= start) & (c_all <= end)
                  for start, end in c_lf_all]
    # 合并所有条件
    final_mask = np.logical_or.reduce(conditions)
    inverse_mask = ~final_mask
    return final_mask, inverse_mask, c_lf_all

def get_HF_JCFI(ps,r=0.07,cpu=mp.cpu_count()):
    '基于JCFI提取环缝'
    # 1.将大于阈值的点提取出来
    mean_J = np.mean(ps[:,5])  # JCFI均值
    std_J = np.std(ps[:,5])  # JCFI标准差
    v_J = mean_J+std_J*3
    # v_J = 0.079
    print('均值为',mean_J,'标准差为',std_J,'阈值为',v_J)
    # 剔除第一波点云
    ps_J = ps[ps[:, 5] > v_J, :]  # 符合条件的环缝
    ps_no_1 = ps[ps[:,5]<=v_J,:] # 第一轮被剔除的环缝
    # 2.计算ps_J在Y轴方向的分量
    tree = KDTree(ps_J[:, :3])  # 创建树
    num_J = len(ps_J)  # 种子点数量
    vectors_Y = np.zeros(num_J)  # Y方向分量
    '创建共享内存'
    shm = shared_memory.SharedMemory(create=True, size=ps_J.nbytes)
    #  将数据复制到共享内存
    shared_array = np.ndarray(ps_J.shape, dtype=ps_J.dtype, buffer=shm.buf)
    shared_array[:] = ps_J[:]
    print(f"共享内存创建完成: {shm.name}")
    print(f"共享内存大小: {shm.size} 字节")
    '开启并行计算'
    pool = mp.Pool(processes=cpu)
    multi_res = pool.starmap_async(get_VY, ((shared_array,r,tree,i) for i in
                 tqdm(range(num_J),desc='分配任务计算单点Y方向分量',unit='个点',total=num_J)))
    j = 0
    for res in tqdm(multi_res.get(),total=num_J,desc='输出Y方向分量'):
        vectors_Y[j] = res
        j += 1
    pool.close()  # 关闭所有进程
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    # 清理共享内存
    shm.close()
    shm.unlink()  # 重要：释放共享内存
    # 3.高斯混合模型分解成三类，要接近0那类
    labels = zm.use_gmm(vectors_Y.reshape(-1, 1),3)
    gmm_0 = vectors_Y[labels == 0]
    gmm_1 = vectors_Y[labels == 1]
    gmm_2 = vectors_Y[labels == 2]
    # 计算每个类别的平均值
    mean_0 = np.mean(gmm_0)
    mean_1 = np.mean(gmm_1)
    mean_2 = np.mean(gmm_2)
    # 计算与0的距离（绝对值）
    dist_0 = abs(mean_0)
    dist_1 = abs(mean_1)
    dist_2 = abs(mean_2)
    # 找到距离0最近的类别
    distances = [dist_0, dist_1, dist_2]
    min_index = distances.index(min(distances))
    # 根据索引选择对应的数组
    if min_index == 0:
        ps_gmm = ps_J[labels == 0, :]
        ps_no_2 = ps_J[labels == 1, :]
        ps_no_3 = ps_J[labels == 2, :]
    elif min_index == 1:
        ps_gmm = ps_J[labels == 1, :]
        ps_no_2 = ps_J[labels == 0, :]
        ps_no_3 = ps_J[labels == 2, :]
    else:
        ps_gmm = ps_J[labels == 2, :]  # 为下一步准备的点云
        ps_no_2 = ps_J[labels == 0, :]
        ps_no_3 = ps_J[labels == 1, :]  # 剔除的点云
    # 4. 实例分割并返回环缝截面序列
    in_index,out_index,hf_lf = get_HF_bulge_scipy(ps_gmm[:,4])
    # 5.输出环缝点云，非环缝点云，和环缝点云截面区间集合
    ps_hf = ps_gmm[in_index,:]
    ps_no_4 = ps_gmm[out_index,:]
    ps_no = np.r_[ps_no_1,ps_no_2,ps_no_3,ps_no_4]
    return ps_hf,ps_no,hf_lf

def get_HF_SJFI_pipeline(ps,r=0.035,cpu=mp.cpu_count(),R=2.7,dis_c=4):
    '基于SJFI提取环缝'
    '1.计算SJFI'
    # 计算曲率
    C_all = Curvature_r_mp_shm(ps[:, :3], r=r,cpu=cpu)
    # 计算环缝高度差
    dis_min_all, perimeter = get_dis_min_mp(ps,dis_c, cpu, R)  # 周长在这里
    # 计算SJFI
    S = (1-ps[:,3])*C_all*dis_min_all
    S = np.nan_to_num(S,nan=0.0)
    # np.savetxt('ps_S.txt',np.c_[ps,S],fmt='%.05f')
    '2.初步剔除'
    mean_S = np.mean(S)
    std_S = np.std(S)
    td = 2
    S_td = mean_S + std_S*td  # 阈值
    ps_s = ps[S>=S_td,:]  # 初步剔除后的点云
    p_s = perimeter[S>=S_td]  # 周长1
    ps_ = ps[S<S_td,:]
    p_ = perimeter[S<S_td]  # 周长2
    '3.实例化环缝'
    c_un, num_c = np.unique(ps_s[:,4], return_counts=True)
    mean_c = np.mean(num_c)
    std_c = np.std(num_c)
    print(mean_c,std_c)
    # # 画图
    # plt.figure(figsize=(8, 5))  # 设置图像大小（可选）
    # plt.plot(c_un, np.nan_to_num(num_S), label='sin(x)', color='tab:blue', linewidth=1.5)
    # 使用峰值检测找到环缝
    peaks, properties = find_peaks(num_c,height=np.mean(num_c)+np.std(num_c),  # 最小峰值高度
                                   distance=400,  # 峰值间最小距离
                                   prominence=np.std(num_c) * 0.3)  # 峰值突出度
    c_un_maxes = c_un[peaks]  # 峰值对应的c值
    num_c_un_maxes = len(c_un_maxes)  # 峰值的数量
    C_td = mean_c * 1.5 # +std_c  # 阈值
    lf_bounds = np.zeros([num_c_un_maxes,2])  # 左右边界集合
    j = 0
    for p in peaks:
        left_bound = 0
        for i in range(p, -1, -1):
            if num_c[i] <= C_td:
                left_bound = i + 1
                lf_bounds[j, 0] = c_un[left_bound]
                break
        # 向右找第一个 num_c <= C_td 的位置
        lf_bounds[j, 1] = c_un[-1]
        for i in range(p, len(num_c)):
            if num_c[i] <= C_td:
                right_bound = i - 1
                lf_bounds[j, 1] = c_un[right_bound]
                break
        j += 1
    print(lf_bounds)  # 先右后左
    conditions = [(ps_s[:,4] >= start) & (ps_s[:,4] <= end)
                  for start, end in lf_bounds]
    # 合并所有条件
    final_mask = np.logical_or.reduce(conditions)
    inverse_mask = ~final_mask
    ps_hf = ps_s[final_mask,:]
    ps_fh = ps_s[inverse_mask,:]
    ps_fh = np.r_[ps_,ps_fh]
    # 同样对周长进行处理
    p_hf = p_s[final_mask]
    p_fh = p_s[inverse_mask]
    p_fh = np.r_[p_,p_fh]
    label_ps_hf = np.zeros(len(ps_hf))
    ps_hf = np.c_[ps_hf,label_ps_hf]
    '4.实例化环缝'
    for i in range(num_c_un_maxes):
        mask = (ps_hf[:, 4] >= lf_bounds[i,0]) & (ps_hf[:, 4] <= lf_bounds[i,1])
        ps_hf[mask,5] = i
    '5.计算环缝每点的密度'
    density_all = np.zeros(len(ps_hf))
    for i in range(num_c_un_maxes):
        mask = ps_hf[:, 5] == i
        ps_group = ps_hf[mask, :]
        original_indices = np.where(mask)[0]
        if len(ps_group) == 0:
            continue
        # 2. 构建sklearn的KDTree（支持任意k维，默认欧氏距离）
        kdtree = KDTree(ps_group, metric='euclidean')
        # 3. 批量计算密度（sklearn用query_radius，替代scipy的query_ball_point）
        # 返回值：列表的列表（每个元素是一个点的邻居索引）
        neighbor_indices_list = kdtree.query_radius(ps_group, r=r)
        # 4. 统计每个点的邻居数（密度），批量回填
        density_group = np.array([len(indices) for indices in neighbor_indices_list])
        density_all[original_indices] = density_group
    ps_hf = np.c_[ps_hf,density_all]
    '6.最后一次去噪'
    dtd = 10
    ps_fh = np.r_[ps_fh,ps_hf[ps_hf[:,6]<dtd,:5]]
    ps_hf = ps_hf[ps_hf[:,6]>=dtd,:]
    return ps_hf[:,:6],ps_fh


def cut_DGH(xyzic,hf_lf):
    '分割盾构环'
    num_DGH = len(hf_lf)
    list_DGH = []
    for i in range(num_DGH):
        xyzic_l = xyzic[xyzic[:,4]<hf_lf[i,0],:]
        list_DGH.append(xyzic_l)
        xyzic=xyzic[xyzic[:,4]>=hf_lf[i,1],:]
    list_DGH.append(xyzic)
    return list_DGH

def cut_DGH_PY(ps_fh,ps_hf,x0,z0,R=2.7,cpu=mp.cpu_count()):
    '按照二维投影分割盾构环（存在严重bug，请慎重使用）'
    # 计算弧长
    # xzrc = zs.fit_circle(ps_fh[:, 0], ps_fh[:, 2], ps_fh[:, 4], num_cpu=cpu)  # 拟合各截面
    # zs.fit_cicle_rough(ps_fh)
    # x0 = np.mean(xzrc[:, 0])
    # z0 = np.mean(xzrc[:, 1])  # 平均圆心
    # 整体拟合
    # print('RANSAC输入点云数量为', len(ps_fh))
    # model = zs.CircleLeastSquareModel()  # 类的实例化:用最小二乘生成已知模型
    # data = np.vstack([ps_fh[:, 0], ps_fh[:, 2]]).T  # 整理数据
    # result = model.fit(data)  # 拟合圆
    # x0 = result.a * -0.5
    # z0 = result.b * -0.5
    # R = 0.5 * math.sqrt(result.a ** 2 + result.b ** 2 - 4 * result.c)  # 圆心及坐标半径
    angle_fh = zs.get_angle_all(ps_fh[:, [0, 2]], x0, z0, cpu_count=cpu)  # 各点角度
    perimeter_fh = angle_fh / 360 * 2 * np.pi * R  # 各点弧度
    angle_hf = zs.get_angle_all(ps_hf[:, [0, 2]], x0, z0, cpu_count=cpu)  # 各点角度
    perimeter_hf = angle_hf / 360 * 2 * np.pi * R  # 各点弧度
    py_hf = np.c_[perimeter_hf, ps_hf[:, 1]]
    py_fh = np.c_[perimeter_fh, ps_fh[:, 1]]
    num_hf = int(np.max(ps_hf[:,5])+1+1)  # 加1是环缝数量，加2是盾构环数量
    idx_dgh = np.zeros(len(ps_fh))
    p_min = 0
    p_max = 2 * np.pi * R
    for i in tqdm(range(num_hf)):
        if i == 0:
            # 将y_min到第一条缝建立凸壳
            y_min = np.min(ps_fh[:,1])  # 最小y
            p_l = np.array([[p_min,y_min],[p_max,y_min]])  # 左侧点
            # 与右侧点集进行合并
            p_r = py_hf[ps_hf[:,5]==i,:]
            # p_lf = np.r_[p_l,p_r]
            # # 求凸壳
            # hull = spt.ConvexHull(points=p_lf, incremental=False)  # 求凸壳
            # ID = hull.vertices  # 返回凸壳的边缘点号
            # polygon = p_lf[ID, :]  # 求凸壳数组
            # ID2 = zr.inpolygon(py_fh[:,0],py_fh[:,0], polygon[:, 0], polygon[:, 1]) # 在当前凸壳内的点
            # idx_dgh[ID2] = i
        elif i == num_hf-1:
            y_max = np.max(ps_fh[:,1])  # 最大y
            p_r = np.array([[p_min,y_max],[p_max,y_max]])  # 右侧点
            # 与右侧点集进行合并
            p_l = py_hf[ps_hf[:, 5] == i-1, :]  # 右侧点
            # p_lf = np.r_[p_l, p_r]
            # # 求凸壳
            # hull = spt.ConvexHull(points=p_lf, incremental=False)  # 求凸壳
            # ID = hull.vertices  # 返回凸壳的边缘点号
            # polygon = p_lf[ID, :]  # 求凸壳数组
            # ID2 = zr.inpolygon(py_fh[:,0],py_fh[:,0], polygon[:, 0], polygon[:, 1]) # 在当前凸壳内的点
            # idx_dgh[ID2] = i
        else:  # 其他正常情况
            # 左侧边界点
            p_l = py_hf[ps_hf[:, 5] == i-1, :]  # 右侧点
            # 右侧边界点
            p_r = py_hf[ps_hf[:, 5] == i, :]  # 右侧点
        p_lf = np.r_[p_l, p_r]
        # 求凸壳
        hull = spt.ConvexHull(points=p_lf, incremental=False)  # 求凸壳
        ID = hull.vertices  # 返回凸壳的边缘点号
        polygon = p_lf[ID, :]  # 求凸壳数组
        ID2 = zr.inpolygon(py_fh[:,0],py_fh[:,1], polygon[:, 0], polygon[:, 1]) # 在当前凸壳内的点
        idx_dgh[ID2] = i
    return idx_dgh
                        
def Merge_straight_lines(lines, threshold = 10):
    '合并相同直线'
    distances = squareform(pdist(lines))  # 距离矩阵
    groups = []
    visited = set()
    for i in range(len(lines)):
        if i in visited:
            continue
        group = [i]
        visited.add(i)
        for j in range(i + 1, len(lines)):
            if j not in visited and distances[i, j] < threshold:
                group.append(j)
                visited.add(j)
        groups.append(group)
    print("按距离分组结果：")
    for idx, group in enumerate(groups):
        print(f"组 {idx}: {group}")
    return groups

def get_ZF_JCFI(xyzic,cpu=mp.cpu_count(),r=0.03,eps=0.02,min_samples=4,sigma=0.01):
    '基于JCFI提取每个盾构环的纵缝'
    #1. 计算JCFI均值与标准差
    xyzicjp = get_JCFI_noout(xyzic, r,cpu)
    mean_JCFI = np.mean(xyzicjp[:,5])
    std_JCFI = np.std(xyzicjp[:,5])
    td0 = mean_JCFI+3*std_JCFI  # 严格阈值
    print('严格JCFI阈值',td0)
    #3. 通过DBSCAN聚类并剔除非种子点
    xyzicj_td0 = xyzicjp[xyzicjp[:,5]>=td0,:]
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(xyzicj_td0[:,:3])
    labels = clustering.labels_  # 每个点的类别标签，-1 表示噪声
    xyzicjzl = np.c_[xyzicj_td0,labels]
    xyzicjzl = xyzicjzl[xyzicjzl[:,-1]>=0,:]
    l_un,num_l = np.unique(xyzicjzl[:,-1],return_counts=True)
    seed_index = []  #  种子索引
    C_len = len(np.unique(xyzicjzl[:, 4]))
    for i in l_un:
        xyzicjzl_ = xyzicjzl[xyzicjzl[:,-1]==i,:]
        num_c_ = len(np.unique(xyzicjzl_[:,4]))
        if num_c_>=0.25*C_len:
            seed_index.append(i)
    print('候选种子点索引',seed_index)
    seed_index_in = np.isin(xyzicjzl[:, -1], seed_index)
    xyzicjzl_in = xyzicjzl[seed_index_in, :]
    # zt.view_pointclouds(xyzicjzl_in[:, :3], xyzicjzl_in[:, -1], colormap='hsv')
    print('候选种子点数量',xyzicjzl_in.shape)
    num_seed_index = len(seed_index)
    #4. 对各个联通区域拟合直线pY
    kb_all = np.empty([num_seed_index, 2])  # 直线属性容器
    j = 0
    for i in seed_index:
        xyzicjzl_in_ = xyzicjzl_in[xyzicjzl_in[:,-1]==i,:]
        oy_ = xyzicjzl_in_[:,[6,1]]
        # 二维直线拟合
        kb_all[j,:] = zR.fit_2Dline_ransac(oy_,sigma=sigma)
        j+=1
    #5. 合并相同直线
    groups_lines = Merge_straight_lines(kb_all, 2)
    #6. 重新整理种子点数据
    kb_list = np.empty([len(groups_lines), 2])
    for idx, group in enumerate(groups_lines):
        if len(group)>=2:
            selected_labels = np.array(seed_index)[group]
            xyzicjzl_in_ = xyzicjzl_in[np.isin(xyzicjzl_in[:,-1],selected_labels),:]
            oy_ = xyzicjzl_in[:, [6, 1]]
            kb_list[idx,:] = zR.fit_2Dline_ransac(oy_,sigma=sigma)
        else:
            kb_list[idx, :] = kb_all[idx, :]
    print('联通区域拟合直线属性',kb_list)
    # #7. 找到直线区域平均距离大于0的点数量
    # # 点到直线的距离
    # zf_list =[]
    # td1 = mean_JCFI+1*std_JCFI  # 不严格阈值
    # oy_all = xyzicjz[:,[6,1]]
    # td2 = 0.1  # 距离阈值
    # for i in range(len(kb_list)):
    #     dis_all_ = zm.get_distance_point2line(oy_all,kb_list[i])
    #     ps_ = xyzicjz[dis_all_<td2,:]
    #     ps_ = ps_[ps_[:,5]>td1,:]
    #     num_C_ = len(np.unique(ps_[:,4]))  # 截面数量
    #     if num_C_/C_len >0.5:
    #         zf_list.append(ps_)
    # zf_array = np.vstack(zf_list)
    # 找到符合条件的下标并合并
    zf_bool = np.zeros(len(xyzicjp), dtype=bool)
    td1 = mean_JCFI + 1 * std_JCFI  # 不严格阈值
    td_dis = 0.1  # 距离阈值
    print('不严格JCFI阈值',td1)
    py_all = xyzicjp[:,[6,1]]
    JCFI_all = xyzicjp[:,5]
    for i in range(len(kb_list)):
        dis_all_ = zm.get_distance_point2line(py_all, kb_list[i])
        # 限制条件1
        valid_indices = dis_all_ < td_dis
        # 限制条件2
        condition_mask = JCFI_all > td1
        # 同时满足两个条件的位置
        final_mask = valid_indices & condition_mask
        ps_ = xyzicjp[final_mask,:]
        num_C_ = len(np.unique(ps_[:, 4]))  # 截面数量
        if num_C_ / C_len > 0.5:
            # 将满足条件的位置在zf_bool中设为True
            zf_bool = zf_bool | final_mask  # 使用或操作，累积所有满足条件的位置
    # 返回zf_bool为True的点云
    xyzic_true = xyzicjp[zf_bool, :]
    # 返回zf_bool为False的点云
    xyzic_false = xyzicjp[~zf_bool, :]
    return xyzic_true, xyzic_false

def get_ZF_C(xyzic,cpu=mp.cpu_count(),r=0.035,eps=0.02,min_samples=4,sigma=0.01,R=2.7,td_dis=0.1):
    '基于球曲率求单个盾构环的纵缝'
    '1.计算JCFI和周长'
    xyzicJpC = get_JCFI_ZF(xyzic,r=r,cpu=cpu,R=R)
    # 计算JCFI的严格阈值
    mean_JCFI = np.mean(xyzicJpC[:,5])
    std_JCFI = np.std(xyzicJpC[:,5])
    td0 = mean_JCFI+3*std_JCFI  # 严格阈值
    print('严格JCFI阈值',td0)
    # 寻找第一批候选点
    # xyzicp = np.c_[xyzic,perimeter]
    ps_td0 = xyzicJpC[xyzicJpC[:,5] >= td0, :]
    '2.DBSCAN聚类'
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(ps_td0[:,:3])
    labels = clustering.labels_  # 每个点的类别标签，-1 表示噪
    ps_l = np.c_[ps_td0,labels]
    ps_l = ps_l[ps_l[:, -1] >= 0, :]
    l_un,num_l = np.unique(ps_l[:,-1],return_counts=True)
    seed_index = []  #  种子索引
    C_len = len(np.unique(xyzic[:, 4]))  # 盾构环截面数量
    for i in l_un:
        ps_l_ = ps_l[ps_l[:,-1]==i,:]
        num_c_ = len(np.unique(ps_l_[:,4]))
        if num_c_>=0.25*C_len:
            seed_index.append(i)
    print('候选种子联通索引',seed_index)
    seed_index_in = np.isin(ps_l[:, -1], seed_index)
    ps_in = ps_l[seed_index_in, :]
    print('候选种子点数量', ps_in.shape)
    num_seed_index = len(seed_index)  # 联通区域数量
    '3.对各个联通区域拟合直线pY，合并相近直线'
    # 拟合直线
    kb_all = np.empty([num_seed_index, 2])  # 直线属性容器
    j = 0
    for i in seed_index:
        ps_in_ = ps_in[ps_in[:,-1]==i,:]
        py_ = ps_in_[:,[6,1]]
        # 二维直线拟合
        kb_all[j,:] = zR.fit_2Dline_ransac(py_,sigma=sigma)
        j+=1
    print(kb_all)
    # 合并相同直线
    groups_lines = Merge_straight_lines(kb_all, 2)
    '4.整理最后的种子点数据'
    # 重新整理种子点数据
    kb_list = np.empty([len(groups_lines), 2])
    for idx, group in enumerate(groups_lines):
        if len(group)>=2:
            selected_labels = np.array(seed_index)[group]
            ps_in_ = ps_in[np.isin(ps_in[:,-1],selected_labels),:]
            py_ = ps_in_[:, [6, 1]]
            kb_list[idx,:] = zR.fit_2Dline_ransac(py_,sigma=sigma)
        else:
            kb_list[idx, :] = kb_all[idx, :]
    print('联通区域拟合直线属性',kb_list)
    '5.输出纵缝点和衬砌点'
    # 找到符合条件的下标并合并
    zf_bool = np.zeros(len(xyzic), dtype=bool)
    mean_C = np.mean(xyzicJpC[:,7])
    std_C = np.std(xyzicJpC[:,7])
    td1 = mean_C+3*std_C  # 不严格阈值
    print('严格球曲率阈值',td1)
    py_all = xyzicJpC[:,[6,1]]
    C_all = xyzicJpC[:,7]
    for i in range(len(kb_list)):
        dis_all_ = zm.get_distance_point2line(py_all, kb_list[i])
        # 限制条件1
        valid_indices = dis_all_ < td_dis
        # 限制条件2
        condition_mask = C_all > td1
        # 同时满足两个条件的位置
        final_mask = valid_indices & condition_mask
        ps_ = xyzicJpC[final_mask,:]
        num_C_ = len(np.unique(ps_[:, 4]))  # 截面数量
        if num_C_ / C_len > 0.5:
            # 将满足条件的位置在zf_bool中设为True
            zf_bool = zf_bool | final_mask  # 使用或操作，累积所有满足条件的位置
        # np.savetxt('E:\\2025博二上学期\\基于复合指数的RMLS盾构隧道环缝和纵缝提取\\Data\\test_ps_.txt',ps_,fmt='%.05f')
    # 返回zf_bool为True的点云
    xyzic_true = xyzicJpC[zf_bool, :]
    # 返回zf_bool为False的点云
    xyzic_false = xyzicJpC[~zf_bool, :]
    # np.savetxt('E:\\2025博二上学期\\基于复合指数的RMLS盾构隧道环缝和纵缝提取\\Data\\xyzic_true.txt',xyzic_true,fmt='%.05f')
    # np.savetxt('E:\\2025博二上学期\\基于复合指数的RMLS盾构隧道环缝和纵缝提取\\Data\\xyzic_false.txt',xyzic_false,fmt='%.05f')
    return xyzic_true, xyzic_false

def get_HF_intensity_peaks(ps,length_05 = 4,dis=200):
    '251103强化版本强度值环缝提取算法'
    c_un = np.unique(ps[:,4])
    num_C = len(c_un)
    # 计算每个环的平均强度值
    i_c = np.empty(num_C)
    # 并行计算准备
    tik = zs.cut_down(num_C)  # 分块起止点
    pool = mp.Pool(processes=mp.cpu_count())  # 开启多进程池，数量为cpu
    multi_res = [pool.apply_async(zs.find_cImean_block, args=(ps, c_un, tik[i], tik[i + 1])) for i in  # points_new
                 range(mp.cpu_count())]  # 将每个block需要处理的点云区间发送到每个进程当中
    tik_ = 0  # 计数器
    for res in multi_res:
        i_c[tik[tik_]:tik[tik_ + 1]] = res.get()
        tik_ += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    '归一化特征值'
    i_c = zm.normalization(i_c,1.0)
    # 取反
    i_c_1 = 1-i_c
    '计算极低值'
    peaks, properties = find_peaks(i_c_1,height=np.mean(i_c_1)*0.5,  # 最小峰值高度
                                   distance=dis,  # 峰值间最小距离
                                   prominence=np.std(i_c_1) * 0.3)  # 峰值突出度
    c_un_maxes = c_un[peaks]  # 峰值对应的c值
    print('环缝中心截面位置',c_un_maxes)
    num_hf = len(c_un_maxes)  # 环缝数量
    # length_05 = 15  # 假定环缝半宽度
    td = 3
    hf_lf = np.empty([num_hf,2])
    for i in range(num_hf):
        # 找到左右假定搜索边界
        peaks_l_ = peaks[i]-length_05
        peaks_r_ = peaks[i]+length_05
        # 找到左右非环缝边界
        cq_l_ = peaks_l_-length_05
        cq_r_ = peaks_r_+length_05
        # --- 新增：边界检查与修正 ---
        peaks_l_ = max(0, peaks_l_)
        peaks_r_ = min(num_C-1, peaks_r_)  # 索引最大为 num_C - 1
        cq_l_ = max(0, cq_l_)
        cq_r_ = min(num_C-1, cq_r_)  # 索引最大为 num_C - 1
        # --- 结束新增 ---
        # 求左右衬砌的平均标准差和阈值
        i_c_l = i_c[cq_l_:peaks_l_]
        i_c_r = i_c[peaks_r_:cq_r_]
        mean_i_c_l = np.mean(i_c_l)
        std_i_c_l = np.std(i_c_l)
        mean_i_c_r = np.mean(i_c_r)
        std_i_c_r = np.std(i_c_r)
        td_l_ = mean_i_c_l - std_i_c_l * td
        td_r_ = mean_i_c_r - std_i_c_r * td
        # 左右待选值
        i_c_hf_l = i_c[peaks_l_:peaks[i]]
        i_c_hf_r = i_c[peaks[i]:peaks_r_]
        # 在 i_c_l 中查找最后一个小于 td_l_ 的元素的相对下标
        indices_l = np.where(i_c_hf_l < td_l_)[0]
        if len(indices_l) > 0:
            last_idx_l_rel = indices_l[0]
        else:
            last_idx_l_rel = 0
        indices_r = np.where(i_c_hf_r < td_r_)[0]
        if len(indices_r) > 0:
            first_idx_r_rel = indices_r[-1]
        else:
            first_idx_r_rel = 14
        # 整理左右下标
        idx_l_ = peaks[i] - length_05 + last_idx_l_rel
        idx_r_ = peaks[i] + first_idx_r_rel
        idx_r_ = min(idx_r_, num_C-1)
        hf_lf[i,0] = c_un[idx_l_]
        hf_lf[i,1] = c_un[idx_r_]
    print('环缝截面起止位置',hf_lf)
    # 确保 hf_lf 是整数类型，因为它们将用作索引
    hf_lf = hf_lf.astype(int)
    # 假设 ps[:, 4] 存储的是环的索引 c
    c_indices = ps[:, 4]
    # 创建一个布尔掩码，标记哪些点属于环缝
    mask_hf = np.zeros(len(ps), dtype=bool)
    for start, end in hf_lf:
        # 创建当前环缝范围的掩码，并与总掩码进行或运算
        mask_hf |= (c_indices >= start) & (c_indices <= end)
    # 使用掩码分割数据
    ps_hf = ps[mask_hf]  # 环缝部分
    ps_nf = ps[~mask_hf]  # 非环缝部分 (~ 是逻辑非运算符)
    return ps_hf, ps_nf

def Example_segmentation_longitudinal_seam(zf,eps=0.35,min_samples=2):
    '实例分割纵缝'
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(zf[:,:3])
    labels = clustering.labels_  # 每个点的类别标签，-1 表示噪声
    # 获取总的 Y 轴范围
    total_y_range = np.max(zf[:,1]) - np.min(zf[:,1])
    threshold = total_y_range / 3.0
    # 获取所有唯一的标签（排除噪声标签 -1）
    unique_labels = np.unique(labels)
    labels_to_remove = []
    for label in unique_labels:
        if label == -1:  # 跳过噪声点
            continue
        # 获取当前标签的 Y 值范围
        label_y_values = zf[labels == label, 1]
        if len(label_y_values) == 0:  # 如果该标签没有点，跳过
            labels_to_remove.append(label)
        label_y_range = np.max(label_y_values) - np.min(label_y_values)
        # 如果 Y 轴范围小于阈值，标记为需要移除
        if label_y_range < threshold:
            labels_to_remove.append(label)
    # 如果没有需要移除的标签，直接返回原标签
    if not labels_to_remove:
        return labels
    # 创建新的标签数组
    new_labels = labels.copy()
    # 对需要移除的标签进行处理
    for label_to_remove in sorted(labels_to_remove):
        # 将该标签的所有点的标签设为 -1（噪声）
        new_labels[new_labels == label_to_remove] = -1
    # 如果需要重新排序标签编号，可以这样做：
    unique_valid_labels = np.unique(new_labels[new_labels != -1])
    label_mapping = {old_label: new_idx for new_idx, old_label in enumerate(unique_valid_labels)}
    # 创建最终的标签数组
    final_labels = np.where(new_labels == -1, -1, np.array([label_mapping.get(l, -1) for l in new_labels]))
    return final_labels

def change_S_0(angle_360):
    num = len(angle_360)
    angle_360_new = np.empty(num)
    for i in range(num):
        if angle_360[i] < 270:
            angle_360_new[i] = angle_360[i] + 90
        else:
            angle_360_new[i] = angle_360[i] - 270

    return angle_360_new

def inverse_change_S_0(angle_360_new):
    'change_S_0的单体反函数'
    if angle_360_new >= 90:
        angle_360_original = angle_360_new - 90
    else:
        angle_360_original = angle_360_new + 270
    return angle_360_original

def Arc_length_along_the_specified_direction(ps,x0,z0,R):
    '求以下方向为基准的弧长和弧度'
    angle_all = change_S_0(zs.get_angle_all(ps[:, [0, 2]], x0, z0))
    perimeter_all = angle_all / 360 * 2 * np.pi * R
    return angle_all,perimeter_all

def fit_2Dline_ransac_robust(points, sigma, iters=1000, P=0.99):
    """
    使用改进的RANSAC算法拟合直线，对噪声更鲁棒。
    :param points: 二维点集, numpy array of shape (N, 2)
    :param sigma: 数据和模型之间可接受的最大垂直距离（欧氏距离）
    :param iters: 最大迭代次数
    :param P: 希望得到正确模型的概率
    :return: 最佳的直线参数 (a, b)，表示 y = ax + b。如果无法拟合，返回 (None, None)
    """
    if len(points) < 2:
        print("Error: Not enough points to fit a line.")
        return None, None

    best_a = 0
    best_b = 0
    best_inlier_count = 0
    best_inlier_mask = np.zeros(len(points), dtype=bool) # 记录最佳模型的内点索引

    # 初始化动态迭代次数
    dynamic_iters = iters
    desired_prob = P
    min_points_needed = 2  # 拟合直线需要的最少点数

    for i in range(dynamic_iters):
        # 1. 随机选择两个不相同的点
        idx1, idx2 = random.sample(range(len(points)), 2)
        p1 = points[idx1]
        p2 = points[idx2]

        # 避免选择两个完全相同的点
        if np.array_equal(p1, p2):
            continue

        # 2. 使用这两个点定义一条直线 (ax + by + c = 0)
        # 这种形式可以避免斜率为无穷大的问题
        a = p1[1] - p2[1]
        b = p2[0] - p1[0]
        c = p1[0] * p2[1] - p2[0] * p1[1]
        line_normal = np.array([a, b])
        line_normal_mag = np.linalg.norm(line_normal)

        # 如果法向量为零向量（理论上不应发生，但作为安全检查），跳过
        if line_normal_mag < 1e-10:
            continue

        # 3. 计算所有点到该直线的垂直距离
        # 点到直线 ax+by+c=0 的距离公式: |ax0 + by0 + c| / sqrt(a^2 + b^2)
        # 等价于 |[a, b] . [x0, y0] + c| / ||[a, b]||
        point_coords = points # shape (N, 2)
        distances = np.abs(np.dot(line_normal, point_coords.T) + c) / line_normal_mag

        # 4. 找出内点 (inliers)
        inlier_mask = distances < sigma
        total_inlier = np.sum(inlier_mask)

        # 5. 判断当前模型是否更好
        if total_inlier > best_inlier_count:
            best_inlier_count = total_inlier
            # 更新最佳模型参数 (转换回 y = ax + b 形式)
            if abs(b) > 1e-10: # 避免除以接近零的数（即直线非垂直）
                best_a = -a / b
                best_b = -c / b
            else: # 直线接近垂直 x = constant
                # 此时无法用 y=ax+b 表示，可以返回特殊值或处理
                # 这里我们仍然尝试用两点计算，但要小心处理垂直情况
                # 如果 x1 == x2，则直线是 x = x1
                if abs(p2[0] - p1[0]) < 1e-10:
                     # 返回一个标记，表示是垂直线，或者使用 x=const 形式
                     # 为了与原函数返回格式一致，可能需要特殊处理或警告
                     print(f"Warning: Found a near-vertical line at iteration {i}. Returning parameters based on two points.")
                     best_a = float('inf') if (p2[0] - p1[0]) == 0 else (p2[1] - p1[1]) / (p2[0] - p1[0])
                     best_b = p1[1] - best_a * p1[0] # 这在 a=inf 时可能无意义
                     # 一个更健壮的处理垂直线的方式是返回 (rho, theta) 形式
                     # 但为了保持接口一致，这里先用两点计算
                     if best_a == float('inf') or best_a == float('-inf'):
                         # 如果是垂直线，我们无法用 y=ax+b 表示
                         # 可以选择跳过或用其他方式表示，这里暂时跳过
                         print(f"Skipping vertical line model at iteration {i}.")
                         continue # 跳过这个模型
                else:
                     best_a = (p2[1] - p1[1]) / (p2[0] - p1[0])
                     best_b = p1[1] - best_a * p1[0]
            best_inlier_mask = inlier_mask.copy()

            # 6. (可选) 动态更新迭代次数 (RANSAC 核心思想)
            # 计算当前内点比例 w
            w = total_inlier / len(points)
            # 计算达到所需概率 P 所需的剩余迭代次数
            # 公式: k = log(1-P) / log(1-w^s), 其中 s 是模型需要的最少点数 (这里是2)
            if w > 0 and w < 1:
                estimated_w_s = w ** min_points_needed
                if estimated_w_s < 1:
                    new_dynamic_iters = math.log(1 - desired_prob) / math.log(1 - estimated_w_s)
                    # 取原迭代次数和新估计次数的最小值，防止过度迭代
                    dynamic_iters = min(dynamic_iters, int(new_dynamic_iters) + 100) # 加上一个小的缓冲
            # print(f"Iteration {i}: Found better model with {total_inlier} inliers. New estimated max iters: {dynamic_iters}")

        # 7. 提前终止条件：如果当前内点数已经非常多，可能已经找到了很好的模型
        if total_inlier > len(points) * 0.8: # 例如，如果超过80%的点都是内点，可以提前结束
            # print(f"Early termination at iteration {i} with {total_inlier} inliers.")
            break

    # 可选：对最佳模型的内点进行最小二乘法拟合，以获得更精确的 a, b
    # if best_inlier_count >= min_points_needed:
    #     inlier_points = points[best_inlier_mask]
    #     # 使用 numpy 的 lstsq 进行最小二乘拟合 y = ax + b
    #     # 构造矩阵 A: [x, 1] -> y
    #     A = np.vstack([inlier_points[:, 0], np.ones(len(inlier_points))]).T
    #     sol, residuals, rank, s = np.linalg.lstsq(A, inlier_points[:, 1], rcond=None)
    #     if rank >= 2: # 确保解是有效的
    #         best_a, best_b = sol
    #         print(f"Refined parameters using least squares on inliers: a={best_a}, b={best_b}")

    if best_inlier_count == 0:
        print("Warning: No good model found by RANSAC.")
        return None, None

    return best_a, best_b

def Finding_the_four_to_divide_the_shield_ring(labels_zf,perimeter_dgh,dgh,perimeter_zf,zf):
    '求分割盾构环的四至'
    num_gp = np.max(labels_zf) + 2  # 盾构环数量
    zf_p = num_gp + 1  # 起止线加纵缝数量
    # 点坐标容器
    sizhi = np.empty([zf_p,2,2])  # 数量，坐标，起止
    # 初始化
    sizhi[0, 0, :] = 0  # 初始起止弧度值
    p_max = np.max(perimeter_dgh)
    sizhi[-1, 0, :] = p_max  # 初始起止弧度值
    sizhi[:, 1, 0] = np.min(dgh[:, 1])  # 最小y
    sizhi[:, 1, 1] = np.max(dgh[:, 1])  # 最大y
    # 对纵缝从小到大进行排序
    lp = np.empty(num_gp-1)
    for i in range(num_gp-1):
        lp[i] = np.mean(perimeter_zf[labels_zf == i])
    # 对 lp[:, 1] 进行从小到大的排序并只返回排序索引
    sorted_indices = np.argsort(lp)
    # 求剩余四至
    j = 0
    for i in sorted_indices:
        p_line_ = perimeter_zf[labels_zf == i]
        y_line_ = zf[labels_zf == i,1]
        # 直线拟合
        k,b = fit_2Dline_ransac_robust(np.c_[p_line_,y_line_],sigma=0.01)
        print(j,k)
        p_max_ = (np.max(dgh[:, 1]) - b) / k
        p_min_ = (np.min(dgh[:, 1]) - b) / k  # 最小最大p
        sizhi[j+1,0,0] = p_min_
        sizhi[j+1,0,1] = p_max_
        j += 1
    # 创建新的标签映射
    new_labels_zf = np.copy(labels_zf)
    for new_label, old_label in enumerate(sorted_indices):
        new_labels_zf[labels_zf == old_label] = new_label
    return sizhi, new_labels_zf

def from_DGH_get_GP_index(perimeter_dgh,dgh,labels_zf,sizhi):
    '求管片序列'
    # 对前盾构环进行分割
    py_dgh = np.c_[perimeter_dgh, dgh[:, 1]]
    ind_gp = np.empty(len(dgh))  # 管片序列
    j = 0
    num_gp = np.max(labels_zf) + 2
    for i in range(num_gp):
        # 获取当前管片4至
        p0 = sizhi[i, :, 0]
        p1 = sizhi[i, :, 1]
        p2 = sizhi[i+1, :, 1]
        p3 = sizhi[i+1, :, 0]
        # 将这四个点组合成多边形的顶点
        polygon_vertices = np.array([p0, p1, p2, p3])
        # np.savetxt('polygon_vertices'+str(i)+'.txt', polygon_vertices,fmt='%.05f')
        # 创建一个 Path 对象，它代表了您的多边形
        polygon_path = Path(polygon_vertices)
        # 检查 py_dgh 中的每个点是否在多边形内
        is_inside = polygon_path.contains_points(py_dgh)
        # 提取在多边形内部的散点的索引
        inside_indices = np.where(is_inside)[0]
        # np.savetxt('dgh1_'+str(i)+'.txt',dgh[inside_indices,:],fmt='%.05f')
        ind_gp[inside_indices] = j
        j += 1
    return ind_gp

def fit_gp(num_gp,ind_gp,dgh):
    '管片拟合'
    args = np.empty([num_gp, 3])  # 盾构环1的管片椭圆参数
    for i in range(num_gp):
        gp_ = dgh[ind_gp==i,:]
        args[i,:] = zR.fit_circle_single(gp_[:,[0,2]])
        # arg_ = ze.fitellipse(gp_[:,[0,2]])
        # args[i, :] = arg_
    return args


def calculate_dislocation_in_angle_range(circle_params_0, circle_params_1, x0, z0, i, angle_step):
    """
    计算指定角度范围内的环间错台值（基于圆拟合参数）。
    考虑角度区间中心方向。

    Args:
        circle_params_0 (tuple): 第0环在该范围内的单个管片圆参数 (cx, cz, r)
        circle_params_1 (tuple): 第1环在该范围内的单个管片圆参数 (cx, cz, r)
        x0 (float): 基准圆心 x 坐标
        z0 (float): 基准圆心 z 坐标
        i (float): 起始角度 (经过 change_S_0 变换后)
        angle_step (float): 角度步长 (经过 change_S_0 变换后)

    Returns:
        float: 该角度范围内的环间错台值 (正值表示环1向外错台，负值表示向内)。
               如果任一环在该区间无有效圆参数，则返回 None。
    """

    if circle_params_0 is None or circle_params_1 is None:
        print(f"Warning: No valid circle parameters found for range [{i}, {angle_step}) in one or both rings.")
        return None

    cx_0, cz_0, r_0 = circle_params_0
    cx_1, cz_1, r_1 = circle_params_1

    # 检查半径是否为有效值
    if np.isnan(r_0) or np.isnan(r_1) or r_0 <= 0 or r_1 <= 0:
        print(f"Warning: Invalid radius found for range [{i}, {angle_step}). r0={r_0}, r1={r_1}")
        return None

    # 计算该角度区间的中心角度（注意：i 和 angle_step 是经过 change_S_0 变换的角度）
    # 需要先反变换回原始角度，再转为弧度
    center_angle_transformed = (i + angle_step) / 2.0
    center_angle_original_deg = inverse_change_S_0(center_angle_transformed)  # 这个函数需要处理单个值
    center_angle_radians = np.deg2rad(center_angle_original_deg)

    # 方向向量
    cos_theta = np.cos(center_angle_radians)
    sin_theta = np.sin(center_angle_radians)

    def get_radius_in_direction(circle_params, x0, z0, cos_theta, sin_theta):
        """
        对于圆，在指定方向上找到圆上点到基准圆心的距离。
        找到圆 (cx, cz, r) 上的点 P = (cx + r*cos(phi), cz + r*sin(phi))，
        使得向量 (P - (x0, z0)) 与方向 (cos_theta, sin_theta) 的夹角最小（或投影最大）。
        这等价于优化：max (P - (x0, z0)) · (cos_theta, sin_theta)
        即 max (cx + r*cos(phi) - x0)*cos_theta + (cz + r*sin(phi) - z0)*sin_theta
        即 max r*cos(phi)*cos_theta + r*sin(phi)*sin_theta + const
        即 max r*(cos(phi)*cos_theta + sin(phi)*sin_theta) = r*cos(phi - theta)
        当 phi = theta 时，cos(phi - theta) = 1 最大。
        所以，圆上在 "圆心为原点的极坐标" theta 角度上的点 P_theta = (cx + r*cos(theta), cz + r*sin(theta))
        是在方向 (cos_theta, sin_theta) 上投影最大的点。
        计算 P_theta 到 (x0, z0) 的距离。
        """
        cx, cz, r = circle_params
        if np.isnan(r) or r <= 0:
            return None

        # 计算圆上在方向 theta (相对于圆心) 的点
        x_on_circle = cx + r * cos_theta  # cos(theta) 是方向向量的x分量
        z_on_circle = cz + r * sin_theta  # sin(theta) 是方向向量的z分量

        # 计算该点到基准圆心的距离
        radius_at_direction = np.sqrt((x_on_circle - x0) ** 2 + (z_on_circle - z0) ** 2)
        return radius_at_direction

    # 计算环0在该方向上的径向距离
    radius_0_in_direction = get_radius_in_direction(circle_params_0, x0, z0, cos_theta, sin_theta)
    if radius_0_in_direction is None:
        print(
            f"Warning: Could not calculate radius for ring 0 in direction [{center_angle_original_deg} deg] (range [{i}, {angle_step})).")
        return None

    # 计算环1在该方向上的径向距离
    radius_1_in_direction = get_radius_in_direction(circle_params_1, x0, z0, cos_theta, sin_theta)
    if radius_1_in_direction is None:
        print(
            f"Warning: Could not calculate radius for ring 1 in direction [{center_angle_original_deg} deg] (range [{i}, {angle_step})).")
        return None

    # 计算错台值：环1的径向距离 - 环0的径向距离
    dislocation = radius_1_in_direction - radius_0_in_direction

    return dislocation

def get_in_ring_dislocation(dgh0,dgh1,zf0,zf1,num_int = 3600):
    '计算环间错台'
    '1.实例分割纵缝'
    labels_zf_0 = Example_segmentation_longitudinal_seam(zf0)
    print('前纵缝类别数量', max(labels_zf_0) + 1)
    labels_zf_1 = Example_segmentation_longitudinal_seam(zf1)
    print('后纵缝类别数量', max(labels_zf_0) + 1)
    '2.求共同圆心与半径'
    dghs = np.r_[dgh0,dgh1]
    xzrc = zs.fit_circle(dghs[:,0],dghs[:,2],dghs[:,4])
    x0 = np.mean(xzrc[:,0])
    z0 = np.mean(xzrc[:,1])
    R = np.mean(xzrc[:,2])
    '3.求所有数据的弧度值(以下方向为0)'
    angle_dgh_0, perimeter_dgh0 = Arc_length_along_the_specified_direction(dgh0, x0, z0, R)
    angle_dgh_1, perimeter_dgh1 = Arc_length_along_the_specified_direction(dgh1, x0, z0, R)
    angle_zf_0, perimeter_zf_0 = Arc_length_along_the_specified_direction(zf0, x0, z0, R)
    angle_zf_1, perimeter_zf_1 = Arc_length_along_the_specified_direction(zf1, x0, z0, R)
    '4.分割两个盾构环的四至'
    sizhi0,_ = Finding_the_four_to_divide_the_shield_ring(labels_zf_0, perimeter_dgh0, dgh0, perimeter_zf_0, zf0)
    sizhi1,_ = Finding_the_four_to_divide_the_shield_ring(labels_zf_1, perimeter_dgh1, dgh1, perimeter_zf_1, zf1)
    '5.盾构环转管片标记'
    ind_gp_0 = from_DGH_get_GP_index(perimeter_dgh0, dgh0, labels_zf_0, sizhi0)
    ind_gp_1 = from_DGH_get_GP_index(perimeter_dgh1, dgh1, labels_zf_1, sizhi1)
    '6.对所有管片进行椭圆拟合'
    num_gp_0 = len(np.unique(ind_gp_0))
    num_gp_1 = len(np.unique(ind_gp_1))  # 管片数量
    args_0 = fit_gp(num_gp_0, ind_gp_0, dgh0)
    args_1 = fit_gp(num_gp_1, ind_gp_1, dgh1)  # 拟合椭圆参数
    '7.错台计算'
    angle_step = 360/num_int
    angle_dislocation = np.zeros([num_int,2])
    dgh0_ind = np.c_[dgh0, ind_gp_0]
    dgh1_ind = np.c_[dgh1, ind_gp_1]
    j = 0
    for i in np.arange(0,360,angle_step):
        angle_dislocation[j,0]=inverse_change_S_0((i+i + angle_step)/2)
        dgh_0_i_ = dgh0_ind[(i < angle_dgh_0) & (angle_dgh_0 < i + angle_step), :]
        dgh_1_i_ = dgh1_ind[(i < angle_dgh_1) & (angle_dgh_1 < i + angle_step), :]
        if dgh_0_i_.size and dgh_1_i_.size:  # 如果都有点云
            result_0_ = mode(dgh_0_i_[:,-1], keepdims=True)
            ind_args_0 = result_0_.mode[0]
            result_1_ = mode(dgh_1_i_[:,-1], keepdims=True)
            ind_args_1 = result_1_.mode[0]
            dislocation_ = calculate_dislocation_in_angle_range(args_0[int(ind_args_0)],args_1[int(ind_args_1)],x0,z0,i,i + angle_step)
            angle_dislocation[j, 1] = dislocation_
        j += 1
    return angle_dislocation

def get_ring_dislocation(dgh,zf):
    '计算环内错台'
    '1.实例分割纵缝'
    labels_zf = Example_segmentation_longitudinal_seam(zf)
    print('纵缝类别数量', max(labels_zf) + 1)
    '2.求平均圆心与半径'
    xzrc = zs.fit_circle(dgh[:, 0], dgh[:, 2], dgh[:, 4])
    x0 = np.mean(xzrc[:,0])
    z0 = np.mean(xzrc[:,1])
    R = np.mean(xzrc[:,2])
    '3.求所有数据的弧度值(以下方向为0)'
    angle_dgh, perimeter_dgh = Arc_length_along_the_specified_direction(dgh, x0, z0, R)
    angle_zf, perimeter_zf = Arc_length_along_the_specified_direction(zf, x0, z0, R)
    '4.分割两个盾构环的四至'
    sizhi,labels_zf_new = Finding_the_four_to_divide_the_shield_ring(labels_zf, perimeter_dgh, dgh, perimeter_zf, zf)
    '5.盾构环转管片标记'
    ind_gp = from_DGH_get_GP_index(perimeter_dgh, dgh, labels_zf, sizhi)
    '6.对所有管片进行椭圆拟合'
    num_gp = len(np.unique(ind_gp))
    args = fit_gp(num_gp, ind_gp, dgh)
    print('拟合参数',args)
    '7.对各个纵缝找到所在平均角度'
    angle_list = np.zeros(max(labels_zf) + 1)
    for i in range(max(labels_zf) + 1):
        angle_zf_ = angle_zf[labels_zf==i]
        # angle_zf_ = zsp.inverse_change_S_0(angle_zf_)
        angle_list[i] = np.mean(angle_zf_)
    angle_list = np.sort(angle_list)  # 出现环缝的向下为正方向的角度值
    # print('所有角度值',angle_list)
    '8.环内错台计算'
    dislocation = np.zeros(max(labels_zf) + 1)
    for i in range(max(labels_zf) + 1):
        args_0_ = args[i]  # 前管片拟合参数
        args_1_ = args[i+1]  # 后管片拟合参数
        angle_ = inverse_change_S_0(angle_list[i])  # 纵缝实际角度值
        angle_rad = np.deg2rad(angle_)
        # print('当前计算角度值', angle_)
        cos_theta = np.cos(angle_rad)
        sin_theta = np.sin(angle_rad)
        # 提取圆参数
        cx_0, cz_0, r_0 = args_0_
        cx_1, cz_1, r_1 = args_1_
        # 计算前管片在该角度方向上的点到基准圆心的距离
        # 圆上在角度 angle_rad 方向的点 (相对于圆心)
        x_on_circle_0 = cx_0 + r_0 * cos_theta
        z_on_circle_0 = cz_0 + r_0 * sin_theta
        radius_0_at_angle = np.sqrt((x_on_circle_0 - x0) ** 2 + (z_on_circle_0 - z0) ** 2)
        # 计算后管片在该角度方向上的点到基准圆心的距离
        x_on_circle_1 = cx_1 + r_1 * cos_theta
        z_on_circle_1 = cz_1 + r_1 * sin_theta
        radius_1_at_angle = np.sqrt((x_on_circle_1 - x0) ** 2 + (z_on_circle_1 - z0) ** 2)
        # 计算环内错台值：后管片距离 - 前管片距离
        dislocation[i] = radius_1_at_angle - radius_0_at_angle
        if abs(dislocation[i]) >= 0.1:
            dislocation[i] = np.sqrt((x_on_circle_1 - x_on_circle_0) ** 2 + (z_on_circle_1 - z_on_circle_0) ** 2)
    print('最大错台距离',max(dislocation),'最小错台距离',min(dislocation))
    '给纵缝赋值'
    num_ps_zf = len(zf)
    dis_all = np.zeros(num_ps_zf)
    for i in range(max(labels_zf) + 1):
        dis_all[labels_zf_new==i] = dislocation[i]
    return dislocation, dis_all

def get_JCFI_mp_new(xyzic,r=0.085,cpu=mp.cpu_count(),R=2.7,dis_c=3):
    '改进JCFI算法'
    '1.计算球曲率'
    C_all = Curvature_r_mp(xyzic[:, :3], r=r/2, cpu=cpu)
    '2.建立弧长-y轴二维坐标系'
    dis_min_all, perimeter = get_dis_min_mp(xyzic,dis_c,cpu,R)
    '3.改进左右邻域密度差'
    d4_all = get_4_density_mp(perimeter,xyzic[:,1],r)
    xyziccddA = np.c_[xyzic,C_all,dis_min_all,d4_all,C_all*dis_min_all*d4_all]
    return xyziccddA

def get_4_density_mp(perimeter,y,r,cpu=mp.cpu_count()):
    '求点与前后左右密度差并行计算版'
    '准备工作'
    py = np.c_[perimeter,y]
    num_py = len(py)
    tree = cKDTree(py)  # 建立树
    '创建共享内存'
    shm = shared_memory.SharedMemory(create=True, size=py.nbytes)
    #  将数据复制到共享内存
    shared_array = np.ndarray(py.shape, dtype=py.dtype, buffer=shm.buf)
    shared_array[:] = py[:]
    print(f"共享内存创建完成: {shm.name}")
    print(f"共享内存大小: {shm.size} 字节")
    '开启并行计算'
    pool = mp.Pool(processes=cpu)
    multi_res = pool.starmap_async(get_4_density_, ((shared_array,tree,r,i) for i in
                 tqdm(range(num_py),desc='分配任务计算点与前后左右密度差',unit='个点',total=num_py)))
    d4_all = np.zeros(num_py)  # 创建容器
    j = 0  # 结果输出计步器
    for res in tqdm(multi_res.get(),total=num_py,desc='输出截面点与前后左右密度差'):
        d4_all[j] = res
        j += 1
    pool.close()  # 关闭所有进程
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    # 清理共享内存
    shm.close()
    shm.unlink()  # 重要：释放共享内存
    return d4_all


def get_4_density_(py,tree,r,i):
    '求单点与前后左右密度差'
    neighbors_indices_ = tree.query_ball_point(py[i, :], r=r / 2, p=2)  # 直径周围点索引
    neighbors_indices_ = [idx for idx in neighbors_indices_ if idx != i]  # 剔除自身索引 i
    py_ = py[neighbors_indices_, :] - py[i, :]  # 求相对于当前点的坐标
    angles_ = np.arctan2(py_[:, 1], py_[:, 0])  # 计算每个点在当前点的相对角度
    # angles_ = (angles_ + 2 * np.pi) % (2 * np.pi)  # [0,2π]
    angles_deg_ = np.degrees(angles_)  # 转换为角度
    angles_deg_ = (angles_deg_ + 360) % 360  # [0,360) 范围
    # 创建布尔掩码来筛选不同方向的点
    mask_up_ = (angles_deg_ > 85) & (angles_deg_ < 95)  # 上
    mask_left_ = ((angles_deg_ > 175) & (angles_deg_ < 185))  # 左
    mask_down_ = (angles_deg_ > 265) & (angles_deg_ < 275)  # 下
    mask_right_ = (angles_deg_ >= 0) & (angles_deg_ < 5) | (angles_deg_ > 355) & (angles_deg_ <= 360)  # 右
    # 求对应点
    num_up_ = np.sum(mask_up_)
    num_left_ = np.sum(mask_left_)
    num_down_ = np.sum(mask_down_)
    num_right_ = np.sum(mask_right_)
    # 求上下左右点密度比例
    c_ = min([num_up_, num_down_]) / max([num_up_, num_down_])
    r_ = min([num_left_, num_right_]) / max([num_left_, num_right_])
    d_both_ = c_ + r_
    return d_both_

def get_perimeter(xyzic,cpu=mp.cpu_count(),R=2.7):
    '计算弧长'
    xzrc = zs.fit_circle(xyzic[:, 0], xyzic[:, 2], xyzic[:, 4], num_cpu=cpu)  # 拟合各截面
    x0 = np.mean(xzrc[:, 0])
    z0 = np.mean(xzrc[:, 1])  # 平均圆心
    angle_all = zs.get_angle_all(xyzic[:, [0, 2]], x0, z0, cpu_count=cpu)  # 各点角度
    perimeter = angle_all / 360 * 2 * np.pi * R  # 各点弧度
    return perimeter

def get_dis_min_lf_mp(xyzic,r=0.02,cpu=mp.cpu_count()):
    '求盾构环点左右邻域点最小值'
    '1.计算弧长'
    ig = 10
    c_max = np.max(xyzic[:,4])-ig
    c_min = np.min(xyzic[:,4])+ig
    xyzic_min = xyzic[xyzic[:,4] >= c_min,:]
    xyzic_min = xyzic_min[xyzic_min[:,4] <= c_max,:]
    xzrc = zs.fit_circle(xyzic_min[:, 0], xyzic_min[:, 2], xyzic_min[:, 4], num_cpu=cpu)  # 拟合各截面
    x0 = np.mean(xzrc[:, 0])
    z0 = np.mean(xzrc[:, 1])  # 平均圆心
    R = np.mean(xzrc[:, 2])
    # 使用arctan2直接计算每个点的角度
    x_diff = xyzic[:, 0] - x0
    z_diff = xyzic[:, 2] - z0
    # 使用arctan2计算弧度，然后转换为角度
    angles_rad = np.arctan2(z_diff, x_diff)  # 返回弧度，范围 [-π, π]
    angles_deg = np.degrees(angles_rad)  # 转换为角度，范围 [-180, 180)
    # 将负角度转换为正角度范围 [0, 360)
    angles_deg = np.where(angles_deg < 0, angles_deg + 360, angles_deg)
    # 计算每个点的弧长（当前角度除以360乘以周长）
    circumference = 2 * np.pi * R  # 周长
    arc_lengths = (angles_deg / 360) * circumference  # 弧长
    '2.计算深度'
    distances = np.sqrt((xyzic[:, 0] - x0) ** 2 + (xyzic[:, 2] - z0) ** 2) - R
    '3.合并pyd'
    pyd = np.c_[arc_lengths,xyzic[:, 1],distances]
    '4.计算左右深度差'
    # 准备工作
    num_pyd = len(pyd)
    tree = cKDTree(pyd[:,:2])  # 建立树
    tik = zs.cut_down(num_pyd, cpu)  # 分块起止点
    # 创建共享内存
    shm = shared_memory.SharedMemory(create=True, size=pyd.nbytes)
    #  将数据复制到共享内存
    shared_array = np.ndarray(pyd.shape, dtype=pyd.dtype, buffer=shm.buf)
    shared_array[:] = pyd[:]
    print(f"共享内存创建完成: {shm.name}")
    print(f"共享内存大小: {shm.size} 字节")
    '开启并行计算'
    pool = mp.Pool(processes=cpu)
    # multi_res = pool.starmap_async(get_radias_depth_, ((shared_array,tree,r,i) for i in
    #              tqdm(range(num_pyd),desc='分配任务计算点径向深度差',unit='个点',total=num_pyd)))
    multi_res = [pool.apply_async(get_radias_depth_block, args=(shared_array,tree,r, tik[i], tik[i + 1])) for i in  # points_new
                 range(mp.cpu_count())]  # 将每个block需要处理的点云区间发送到每个进程当中
    dis_all = np.zeros(num_pyd)  # 创建容器
    # j = 0  # 结果输出计步器
    # for res in tqdm(multi_res.get(),total=num_pyd,desc='输出截面点与前后左右密度差'):
    #     dis_all[j] = res
    #     j += 1
    tik_ = 0  # 计数器
    for res in multi_res:
        dis_all[tik[tik_]:tik[tik_ + 1]] = res.get()
        tik_ += 1
    pool.close()  # 关闭所有进程
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    # 清理共享内存
    shm.close()
    shm.unlink()  # 重要：释放共享内存
    return dis_all

def get_radias_depth_block(pyd,tree,r,tik,tok):
    '计算每块左右深度差'
    dis_tik = np.zeros(tok-tik)
    j = 0
    for i in tqdm(range(tik,tok)):
        dis_tik[j] = get_radias_depth_(pyd,tree,r,i)
        j += 1
    return dis_tik

def get_radias_depth_(pyd,tree,r,i):
    '计算单点左右深度差'
    # 整理左侧和右侧点集
    p_l = pyd[i,0]-r
    p_r = pyd[i,0]+r
    # 计算0.02-0.04之间的点
    # 获取圆环区域点（r < dist <= 2r）
    idx_less = np.asarray(tree.query_ball_point(pyd[i, :2], r=r))
    idx_more = np.asarray(tree.query_ball_point(pyd[i, :2], r=r * 2))
    mask = ~np.isin(idx_more, idx_less)
    if mask.size < 1:
        dis = 0
    else:
        idx_ring = idx_more[mask]  # 圆环上的下标
        pyd_ring = pyd[idx_ring,:]  # 圆环上的点
        pyd_l = pyd_ring[pyd_ring[:, 0] < p_l, :]
        pyd_r = pyd_ring[pyd_ring[:, 0] > p_r, :]
        if pyd_l.size < 1 or pyd_r.size < 1:
            dis = 0
        else:
            # 计算欧氏距离的平方（避免开方，更快且 argmin 结果不变）
            dist_l = np.sum((pyd[i, :2] - pyd_l[:,:2]) ** 2, axis=1)
            # 找到最小距离的下标
            idx_min_l = np.argmin(dist_l)
            dis_l = pyd_l[idx_min_l, 2]
            dis_l = pyd[i,2]-dis_l
            # 计算欧氏距离的平方（避免开方，更快且 argmin 结果不变）
            dist_r = np.sum((pyd[i, :2] - pyd_r[:,:2]) ** 2, axis=1)
            # 找到最小距离的下标
            idx_min_r = np.argmin(dist_r)
            dis_r = pyd_r[idx_min_r, 2]
            dis_r = pyd[i, 2] - dis_r
            # 最短值
            if np.abs(dis_l)>np.abs(dis_r):
                dis = dis_r
            else:
                dis = dis_l
    # print(dis)
    return dis

def get_dis_min_mp(xyzic,dis_c=3,cpu=mp.cpu_count(),R=2.7):
    '求截面点与前后邻域点最小值并行计算版'
    num_ps = len(xyzic)  # 点云数量
    xzrc = zs.fit_circle(xyzic[:, 0], xyzic[:, 2], xyzic[:, 4], num_cpu=cpu)  # 拟合各截面
    x0 = np.mean(xzrc[:, 0])
    z0 = np.mean(xzrc[:, 1])  # 平均圆心
    angle_all = zs.get_angle_all(xyzic[:, [0, 2]], x0, z0, cpu_count=cpu)  # 各点角度
    perimeter = angle_all / 360 * 2 * np.pi * R  # 各点弧度
    xyzicp = np.c_[xyzic, perimeter]
    c_un = np.unique(xyzicp[:, 4])
    '创建共享内存'
    shm = shared_memory.SharedMemory(create=True, size=xyzicp.nbytes)
    #  将数据复制到共享内存
    shared_array = np.ndarray(xyzicp.shape, dtype=xyzicp.dtype, buffer=shm.buf)
    shared_array[:] = xyzicp[:]
    print(f"共享内存创建完成: {shm.name}")
    print(f"共享内存大小: {shm.size} 字节")
    '开启并行计算'
    pool = mp.Pool(processes=cpu)
    multi_res = pool.starmap_async(get_dis_min_cs, ((shared_array,i,dis_c,x0,z0) for i in
                 tqdm(c_un[dis_c:-dis_c],desc='分配任务计算截面点与前后邻域点距离最小值',unit='个点',total=len(c_un[dis_c:-dis_c]))))
    dis_min_all = np.zeros(num_ps)  # 容器
    j = 0
    for res in tqdm(multi_res.get(),total=len(c_un[dis_c:-dis_c]),desc='输出截面点与前后邻域点距离最小值'):
        dis_min_all[xyzic[:, 4] == c_un[j+dis_c]] = res
        j += 1
    pool.close()  # 关闭所有进程
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    # 清理共享内存
    shm.close()
    shm.unlink()  # 重要：释放共享内存
    dis_min_all = np.nan_to_num(dis_min_all,nan=0.0)
    return dis_min_all,perimeter

def get_dis_min_cs(xyzicp,i,dis_c,x0,z0):
    xyzicp_b_ = xyzicp[xyzicp[:, 4] == i - dis_c, :]  # 前截面
    xyzicp_f_ = xyzicp[xyzicp[:, 4] == i + dis_c, :]  # 后截面
    xyzicp_ = xyzicp[xyzicp[:, 4] == i, :]
    # 建立二维坐标系树
    yp_b_ = xyzicp_b_[:, [1, 5]]
    yp_f_ = xyzicp_f_[:, [1, 5]]
    yp_ = xyzicp_[:, [1, 5]]
    # 为当前截面yp_中的每个点找到在前截面yp_b_中最近的点的索引
    nbrs_b = NearestNeighbors(n_neighbors=1, algorithm='kd_tree').fit(yp_b_)
    _, indices_b = nbrs_b.kneighbors(yp_)
    nbrs_f = NearestNeighbors(n_neighbors=1, algorithm='kd_tree').fit(yp_f_)
    _, indices_f = nbrs_f.kneighbors(yp_)
    # 整理xz_b和xz_f
    xz_b = xyzicp_b_[indices_b, [0, 2]]
    xz_f = xyzicp_f_[indices_f, [0, 2]]
    xz_ = xyzicp_[:, [0, 2]]
    # 求距离
    distances_xz_b = np.sqrt(np.sum((xz_ - xz_b) ** 2, axis=1))
    distances_xz_f = np.sqrt(np.sum((xz_ - xz_f) ** 2, axis=1))
    # 求正负号
    signs_b = get_signs(x0, z0, xz_, xz_b)
    signs_f = get_signs(x0, z0, xz_, xz_f)
    # 求最小距离
    signed_distances_min = np.where(
        distances_xz_b <= distances_xz_f,
        distances_xz_b*signs_b,
        distances_xz_f*signs_f
    )
    # distances_min = np.min(np.c_[distances_xz_b, distances_xz_f], axis=1)
    return signed_distances_min

def get_signs(x0,z0,xz_,xz_BorF):
    '求正负号'
    # 假设圆心坐标为 x0, z0
    center = np.array([x0, z0])
    # 计算各点到圆心的距离
    dist_to_center_current = np.sqrt(np.sum((xz_ - center) ** 2, axis=1))
    dist_to_center_BorF = np.sqrt(np.sum((xz_BorF - center) ** 2, axis=1))
    signed_distances_xz_BorF = np.sign(dist_to_center_current - dist_to_center_BorF)
    return signed_distances_xz_BorF


