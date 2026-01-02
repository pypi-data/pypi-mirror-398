from __future__ import division
# 这是一个关于私人用途的代码原文件库
import numpy as np
from numpy import *
import sys  # maxint
import matplotlib.pyplot as plt
import pyvista as pv
import polars as pl
from PIL import Image
import plyfile as pf
import os
from scipy.interpolate import griddata
import math

# C-均值聚类
def FCM_train(X, n_centers, m, max_iter=100, theta=1e-5, seed=0):
    rng = np.random.RandomState(seed)
    N, D = np.shape(X)
    # 随机初始化关系矩阵
    U = rng.uniform(size=(N, n_centers))
    # 保证每行和为1
    U = U / np.sum(U, axis=1, keepdims=True)
    # 开始迭代
    for i in range(max_iter):
        print(i)
        U_old = U.copy()
        centers = FCM_getCenters(U, X, m)
        U = FCM_getU(X, centers, m)
        # 两次关系的距离矩阵过小，结束训练
        if np.linalg.norm(U - U_old) < theta:
            break
    return centers, U


def FCM_getCenters(U, X, m):
    N, D = np.shape(X)
    N, C = np.shape(U)
    um = U ** m
    tile_X = np.tile(np.expand_dims(X, 1), [1, C, 1])
    tile_um = np.tile(np.expand_dims(um, 1), [1, 1, D])
    temp = tile_X * tile_um
    new_C = np.sum(temp, axis=0) / np.expand_dims(np.sum(um, axis=0), axis=-1)
    return new_C


def FCM_getU(X, Centers, m):
    N, D = np.shape(X)
    C, D = np.shape(Centers)
    temp = FCM_dist(X, Centers) ** float(2 / (m - 1))
    tile_temp = np.tile(np.expand_dims(temp, 1), [1, C, 1])
    denominator_ = np.expand_dims(temp, -1) / tile_temp
    return 1 / np.sum(denominator_, axis=-1)

def FCM_dist(X, Centers):
    N, D = np.shape(X)
    C, D = np.shape(Centers)
    tile_x = np.tile(np.expand_dims(X, 1), [1, C, 1])
    tile_centers = np.tile(np.expand_dims(Centers, axis=0), [N, 1, 1])
    dist = np.sum((tile_x - tile_centers) ** 2, axis=-1)
    return np.sqrt(dist)

def qhull2D(sample):
    link = lambda a, b: concatenate((a, b[1:]))
    edge = lambda a, b: concatenate(([a], [b]))

    def dome(sample, base):
        h, t = base
        dists = dot(sample - h, dot(((0, -1), (1, 0)), (t - h)))
        outer = repeat(sample, dists > 0, 0)
        if len(outer):
            pivot = sample[argmax(dists)]
            return link(dome(outer, edge(h, pivot)),
                        dome(outer, edge(pivot, t)))
        else:
            return base

    if len(sample) > 2:
        axis = sample[:, 0]
        base = take(sample, [argmin(axis), argmax(axis)], 0)
        return link(dome(sample, base), dome(sample, base[::-1]))
    else:
        return sample


def minBoundingRect(hull_points_2d):
    # print "Input convex hull points: "
    # print hull_points_2d

    # Compute edges (x2-x1,y2-y1)
    edges = zeros((len(hull_points_2d) - 1, 2))  # empty 2 column array
    for i in range(len(edges)):
        edge_x = hull_points_2d[i + 1, 0] - hull_points_2d[i, 0]
        edge_y = hull_points_2d[i + 1, 1] - hull_points_2d[i, 1]
        edges[i] = [edge_x, edge_y]
    # print "Edges: \n", edges

    # Calculate edge angles   atan2(y/x)
    edge_angles = zeros((len(edges)))  # empty 1 column array
    for i in range(len(edge_angles)):
        edge_angles[i] = math.atan2(edges[i, 1], edges[i, 0])
    # print "Edge angles: \n", edge_angles

    # Check for angles in 1st quadrant
    for i in range(len(edge_angles)):
        edge_angles[i] = abs(edge_angles[i] % (math.pi / 2))  # want strictly positive answers
    # print "Edge angles in 1st Quadrant: \n", edge_angles

    # Remove duplicate angles
    edge_angles = unique(edge_angles)
    # print "Unique edge angles: \n", edge_angles

    # Test each angle to find bounding box with smallest area
    min_bbox = (0, sys.maxsize, 0, 0, 0, 0, 0, 0)  # rot_angle, area, width, height, min_x, max_x, min_y, max_y  sys.maxint
    print("Testing", len(edge_angles), "possible rotations for bounding box... \n")
    for i in range(len(edge_angles)):

        # Create rotation matrix to shift points to baseline
        # R = [ cos(theta)      , cos(theta-PI/2)
        #       cos(theta+PI/2) , cos(theta)     ]
        R = array([[math.cos(edge_angles[i]), math.cos(edge_angles[i] - (math.pi / 2))], [math.cos(edge_angles[i] + (math.pi / 2)), math.cos(edge_angles[i])]])
        # print "Rotation matrix for ", edge_angles[i], " is \n", R

        # Apply this rotation to convex hull points
        rot_points = dot(R, transpose(hull_points_2d))  # 2x2 * 2xn
        # print "Rotated hull points are \n", rot_points

        # Find min/max x,y points
        min_x = nanmin(rot_points[0], axis=0)
        max_x = nanmax(rot_points[0], axis=0)
        min_y = nanmin(rot_points[1], axis=0)
        max_y = nanmax(rot_points[1], axis=0)
        # print "Min x:", min_x, " Max x: ", max_x, "   Min y:", min_y, " Max y: ", max_y

        # Calculate height/width/area of this bounding rectangle
        width = max_x - min_x
        height = max_y - min_y
        area = width * height
        # print "Potential bounding box ", i, ":  width: ", width, " height: ", height, "  area: ", area

        # Store the smallest rect found first (a simple convex hull might have 2 answers with same area)
        if (area < min_bbox[1]):
            min_bbox = (edge_angles[i], area, width, height, min_x, max_x, min_y, max_y)
        # Bypass, return the last found rect
        # min_bbox = ( edge_angles[i], area, width, height, min_x, max_x, min_y, max_y )

    # Re-create rotation matrix for smallest rect
    angle = min_bbox[0]
    R = array([[math.cos(angle), math.cos(angle - (math.pi / 2))], [math.cos(angle + (math.pi / 2)), math.cos(angle)]])
    # print "Projection matrix: \n", R

    # Project convex hull points onto rotated frame
    proj_points = dot(R, transpose(hull_points_2d))  # 2x2 * 2xn
    # print "Project hull points are \n", proj_points

    # min/max x,y points are against baseline
    min_x = min_bbox[4]
    max_x = min_bbox[5]
    min_y = min_bbox[6]
    max_y = min_bbox[7]
    # print "Min x:", min_x, " Max x: ", max_x, "   Min y:", min_y, " Max y: ", max_y

    # Calculate center point and project onto rotated frame
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    center_point = dot([center_x, center_y], R)
    # print "Bounding box center point: \n", center_point

    # Calculate corner points and project onto rotated frame
    corner_points = zeros((4, 2))  # empty 2 column array
    corner_points[0] = dot([max_x, min_y], R)
    corner_points[1] = dot([min_x, min_y], R)
    corner_points[2] = dot([min_x, max_y], R)
    corner_points[3] = dot([max_x, max_y], R)
    # print "Bounding box corner points: \n", corner_points

    # print "Angle of rotation: ", angle, "rad  ", angle * (180/math.pi), "deg"

    return (angle, min_bbox[1], min_bbox[2], min_bbox[3], center_point, corner_points)  # rot_angle, area, width, height, center_point, corner_points


def Get_MBR(points):
    '求平面包围盒'
    hull_points = qhull2D(points)  # Find convex hull 查找凸包
    hull_points = hull_points[::-1]  # Reverse order of points, to match output from other qhull implementations 颠倒点的顺序，以匹配其他qhull实现的输出
    print('凸包点: \n', hull_points, "\n")
    (rot_angle, area, width, height, center_point, corner_points) = minBoundingRect(hull_points)  # Find minimum area bounding rectangle 查找最小面积边界矩形
    print("Minimum area bounding box 最小面积边界框:")
    print("Rotation angle 旋转角:", rot_angle, "rad  (", rot_angle * (180 / math.pi), "deg )")
    print("Width 宽度:", width, " Height 长度:", height, "  Area 面积:", area)
    print("Center point 中心点: \n", center_point)  # numpy array
    print("Corner points 转角点: \n", corner_points, "\n")  # numpy array
    RectangleProperties = np.array([width, height, area])  # 合并矩形属性
    return corner_points, RectangleProperties, center_point


def Get_KB(x1, y1, x2, y2):
    '通过两点式求二维直线的截距和斜率'
    # 计算斜率
    slope = (y2 - y1) / (x2 - x1)
    # 计算截距
    intercept = y1 - slope * x1
    print(f"斜率：{slope}")
    print(f"截距：{intercept}")
    return slope, intercept


def get_cm_all():
    '获得plt和pv支持的colormap列表'
    colormaps = plt.colormaps()  # 列出所有colormap的名字
    j = 0
    for i in colormaps:
        print('colormap', j, ':', i)
        j += 1
    return colormaps


def view_pointclouds(xyz,i,i_name='intensity',colormap='gray',save_path=None):
    '基于pyvista显示点云'
    points = pv.PolyData(xyz)  # 建立pv类
    points[i_name] = i  # 将特征填入类
    # 显示点云
    # 创建一个plotter对象
    plotter = pv.Plotter()
    # 显示点云
    plotter.add_points(points, cmap=colormap, show_scalar_bar=False)
    plotter.background_color = 'white'
    # 添加坐标轴
    plotter.add_axes()
    # 添加坐标轴的刻度
    # plotter.show_grid(color='black', xlabel='X (m)', ylabel='Y (m)', zlabel='Z (m)')  # 显示网格线
    # 显示坐标轴刻度和标签，隐藏网格线
    plotter.show_bounds(
        grid=False,
        location='outer',
        ticks='inside',
        all_edges=False,
        xlabel='X (m)',
        ylabel='Y (m)',
        zlabel='Z (m)'
    )
    plotter.show()
    if save_path:
        # --- 离屏 Plotter 用于截图 ---
        plotter_offscreen = pv.Plotter(off_screen=True)  # 创建离屏 Plotter
        plotter_offscreen.add_points(points, cmap=colormap, show_scalar_bar=False)
        plotter_offscreen.background_color = 'white'
        plotter_offscreen.add_axes()
        # plotter_offscreen.show_grid(color='black', xlabel='X (m)', ylabel='Y (m)', zlabel='Z (m)')
        # 显示坐标轴刻度和标签，隐藏网格线
        plotter_offscreen.show_bounds(
            grid=False,
            location='outer',
            ticks='inside',
            all_edges=False,
            xlabel='X (m)',
            ylabel='Y (m)',
            zlabel='Z (m)'
        )
        arr = plotter_offscreen.screenshot(filename=None, return_img=True)
        img = Image.fromarray(arr, 'RGB')
        dpi = 1200
        img.save(save_path, dpi=(dpi, dpi))
        print(f"图片已保存为: {save_path} (分辨率: {dpi} DPI)")
    # 显示图形



def ReadByPolars(path_file,sep=' '):
    '通过polars读取txt点云'
    xyzi = np.array(pl.read_csv(path_file, has_header=False, separator=sep))  # 读取点云
    return xyzi


def resize_image(input_image_path, output_image_path, new_width, new_height):
    '''
    对图像进行分辨率的修改（https://blog.csdn.net/m0_59799878/article/details/131571082）
    :param input_image_path:读取图像路径
    :param output_image_path:输出图像路径
    :param new_width:输出图像分辨率宽
    :param new_height:输出图像分辨率高
    :return:
    '''
    image = Image.open(input_image_path)
    resized_image = image.resize((new_width, new_height))
    resized_image.save(output_image_path)

def ply2np(input,output=None):
    '读取ply点云并转为numpy格式后存储'
    ply = pf.PlyData.read(input)  # 读取ply
    pcd_ply = ply.elements[0]  # 获取数据属性
    num_names = len(pcd_ply.properties)  # 属性数量
    print('ply点云属性数量',num_names)
    # pcd = []
    for i in range(num_names):  # 对属性数据进行整理
        name_ = pcd_ply.properties[i].name  # 属性名
        print('第',i,'列名称',name_)
        data_ = pcd_ply.data[name_]  # 属性对应数据
        data_ = data_.astype(np.float64)  # 转为numpy
        if i == 0:
            pcd = data_
        else:
            pcd = np.c_[pcd,data_]  # 合并numpy
    print('ply点云数量',len(pcd))
    if output is not None:
        np.savetxt(output,pcd,fmt='%.08f')  # 输出numpy
        print('点云文件已保存在',output)
    return pcd

def fix_plt_CHN():
    '解决matplotlib中文显示乱码问题'
    import matplotlib as mpl
    mpl.rcParams['font.family'] = 'SimHei'  # 设置默认字体为 SimHei
    mpl.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def largeCsmall(xyz_l,xyz_s):
    '输出大点云-小点云的点云'
    label_l = xyz_l[:,0]*10+xyz_l[:,1]+xyz_l[:,2]*0.1
    label_s = xyz_s[:,0]*10+xyz_s[:,1]+xyz_s[:,2]*0.1
    id = np.isin(label_l,label_s,invert=True)  # 返回不在的下标
    return xyz_l[id,:]

def AccuracyEvaluation(standard_vehicle,standard_non_vehicle,experiment_vehicle,experiment_non_vehicle):
    '''
    点云精度评价
    :param standard_vehicle: 标准的是点云
    :param standard_non_vehicle: 标准非点云
    :param experiment_vehicle: 测试是点云
    :param experiment_non_vehicle: 测试非点云
    :return: 精度评价结果
    '''
    # 整理前三列数据
    SYV = standard_vehicle[:,2]*100+standard_vehicle[:,1]*10+standard_vehicle[:,0]
    print('标准真数量', len(SYV))
    SNV = standard_non_vehicle[:,2]*100+standard_non_vehicle[:,1]*10+standard_non_vehicle[:,0]
    print('标准假数量', len(SNV))
    EYV = experiment_vehicle[:,2]*100+experiment_vehicle[:,1]*10+experiment_vehicle[:,0]
    print('测试真数量', len(EYV))
    ENV = experiment_non_vehicle[:,2]*100+experiment_non_vehicle[:,1]*10+experiment_non_vehicle[:,0]
    print('测试假数量', len(ENV))
    # 计算True Positives (TP), True Negatives (TN), False Positives (FP), False Negatives (FN)
    # TT = np.isin(EYV, SYV)
    TP = np.sum(np.isin(EYV, SYV))  # 实验提取为车辆且标准为车辆的数量
    print(f"测试为真且标准为真的数量: {TP:.2f}")
    FP = np.sum(np.isin(SNV, EYV))  # 实验提取为车辆但标准为非车辆的数量
    # np.savetxt('FP.txt',standard_non_vehicle[np.isin(SNV, EYV),:],fmt='%.05f')
    print(f"测试为真但标准为假的数量: {FP:.2f}")
    TN = np.sum(np.isin(ENV, SNV))  # 实验提取为非车辆且标准为非车辆的数量
    print(f"测试为假且标准为假的数量: {TN:.2f}")
    FN = np.sum(np.isin(ENV, SYV))  # 实验提取为非车辆但标准为车辆的数量
    print(f"测试为假但标准为真的数量: {FN:.2f}")
    # 计算指标
    type_I_error = FP / (FP + TN)  # 一类误差（Type I Error，假阳性率）
    type_II_error = FN / (FN + TP)  # 二类误差（Type II Error，假阴性率）
    total_error = (FP + FN) / (TP + TN + FP + FN)  # 总误差（Total Error）
    completeness = TP / (TP + FN)  # 完备性（召回率）（Completeness，也称Recall）
    correctness = TP / (TP + FP)  # 正确性（精确率）（Correctness，也称Precision）
    accuracy = (TP + TN) / (TP + TN + FP + FN)  # 准确率（Accuracy）
    quality = TP / (TP + FP + FN)  # 质量（Quality）
    expected_accuracy = ((TP + FN) * (TP + FP) + (TN + FP) * (TN + FN)) / (TP + TN + FP + FN)**2
    kappa = (accuracy - expected_accuracy) / (1 - expected_accuracy)  # kappa
    F1 = 2 * (correctness * completeness) / (correctness + completeness)   # F1指数
    print(f"一类错误 (Type I Error): {type_I_error:.4f}")
    print(f"二类错误 (Type II Error): {type_II_error:.4f}")
    print(f"总错误率 (Total Error): {total_error:.4f}")
    print(f"完备性 (Completeness): {completeness:.4f}")
    print(f"正确性 (Correctness): {correctness:.4f}")
    print(f"准确率 (Accuracy): {accuracy:.4f}")
    print(f"质量 (Quality): {quality:.4f}")
    print(f"卡帕系数 (Kappa coefficient): {kappa:.4f}")   # 存在问题
    print(f"F1指数 (F1 score): {F1:.4f}")
    return np.array([type_I_error,type_II_error,total_error,completeness,correctness,accuracy,quality,kappa,F1])

def read_all_txt(file_path,name=None,sep=' ',limit=5):
    '批量读取文件名带相同字符串的然后合并输出'
    # 获取所有文件名带有 'name' 的 txt 文件
    files = [f for f in os.listdir(file_path) if f.endswith('.txt') and name in f]
    # 使用 Polars 合并所有文件
    j = 0
    for file in files:
        data = ReadByPolars(os.path.join(file_path, file),sep)
        data = data[:,:limit]
        if j==0:
            output = data
        else:
            output = np.r_[output,data]
        j += 1
    return output

def find_first0(arr):
    '找到数组中第一个为0的下标'
    # 找到所有0的位置
    zero_indices = np.where(arr == 0)
    # 第一个0的位置
    first_zero = zero_indices[0][0] if zero_indices[0].size > 0 else -1
    return first_zero

def find_last0(arr):
    '找到数组中最后一个为0的下标'
    # 找到所有0的位置
    zero_indices = np.where(arr == 0)
    # 最后一个0的位置
    last_zero = zero_indices[0][-1] if zero_indices[0].size > 0 else -1
    return last_zero

def ground_ps2DEM(xyz,pixel=1):
    '地面点转DEM,并返回网格坐标'
    x = xyz[:,0]
    y = xyz[:,1]
    z = xyz[:,2]
    # 创建网格
    gird_x,gird_y = np.mgrid[min(x):max(x):pixel,min(y):max(y):pixel]
    gird_z = griddata((x,y),z,(gird_x,gird_y),method='cubic')  # 双三次卷积插值生成DEM
    return gird_z,gird_x,gird_y

def get_buildDSM(xyz,gird_x,gird_y):
    '在建立DEM网格的情况下建立建筑物DSM'
    x = xyz[:,0]
    y = xyz[:,1]
    z = xyz[:,2]
    # 创建DSM网格
    gird_z = griddata((x, y), z, (gird_x, gird_y), method='cubic')  # 双三次卷积插值生成DSM
    return gird_z

def find_continuous_segments(arr):
    """
    找到一维数组中所有连续整数段的起始和终止数
    :param arr: 一维整数数组（已排序）
    :return: 列表，每个元素为 (起始数, 终止数)
    """
    if not arr:
        return []

    segments = []  # 存储所有连续段
    start = arr[0]  # 当前连续段的起始数

    for i in range(1, len(arr)):
        if arr[i] != arr[i - 1] + 1:  # 检测中断点
            segments.append((start, arr[i - 1]))  # 保存当前连续段
            start = arr[i]  # 开始新的连续段

    # 添加最后一个连续段
    segments.append((start, arr[-1]))
    return np.array(segments, dtype=int)

def Read_bin(file,dtype=np.float32,len1=5):
    '读取.bin点云'
    # 读取时需指定数据类型和形状
    loaded_data = np.fromfile(file, dtype=dtype).reshape(-1, len1)  # 假设点云是N×3结构
    return loaded_data
