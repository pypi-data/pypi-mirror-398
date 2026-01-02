from __future__ import division
import matplotlib.pyplot as plt  # 显示库
import numpy as np  # 添加数组库
import laspy  # 打开las用的库
import scipy.spatial as spt  # 求凸壳用的库
from mpl_toolkits.mplot3d import Axes3D  # 空间三维画图
from shapely.geometry import Polygon  # 求凸壳面积用的库
from matplotlib.path import Path  # 求点在凸壳内用的库
import time as s  # 时间库
from collections import Counter  # 统计每个元素出现次数库
from math import *  # 添加数学库
import open3d as o3d  # 点云库
import multiprocessing as mp  # 添加多进程（并行计算）库
import zelas2.Multispectral as p1
from sklearn.neighbors import KDTree  # 添加机器学习的skl.KDT的函数组
from tqdm import tqdm  # 进度条库


# 获得点云凸壳以及面积大小
def get_convexhull(self):
    hull = spt.ConvexHull(points=self.xy, incremental=False)  # 求凸壳
    ID = hull.vertices  # 返回凸壳的边缘点号
    polygon = self.xy[ID, :]  # 求凸壳数组
    area = Polygon(polygon).area  # 求多边形面积
    print('点云面积为:', area)
    return polygon, area


# 求相同位置的两个点云之间的高程差值
def deta_z(xyz1, xyz2, n=125):
    xyzd = np.empty([len(xyz1), 4])  # 新建一个和xyz1同形状的空数组再加一列
    xyz_o3d = o3d.geometry.PointCloud()  # 创建open3d类
    xyz2_np = np.column_stack((xyz2[:, 0], xyz2[:, 1], xyz2[:, 2])).astype(np.float32)  # 数据类型转换
    xyz_o3d.points = o3d.utility.Vector3dVector(xyz2_np)  # 将点云与o3d点云容器融合
    pcd_tree = o3d.geometry.KDTreeFlann(xyz_o3d)  # 对xyz1建立kntree
    for i in range(len(xyz1)):
        # [judge, id_com11, _] = pcd_tree.search_hybrid_vector_3d(xyz1[i, :], max_r, N_num) # 找最近点，有最大搜索半径限制
        [_, id_com2, dis] = pcd_tree.search_knn_vector_3d(xyz1[i, :], n)  # 找最近点，无视距离
        dis = list(dis)  # 向量列表化
        if dis[0] == 0:  # 如果是同一个点
            xyzd[i, :] = [xyz1[i, 0], xyz1[i, 1], xyz1[i, 2], 0]
        else:  # 如果没找到同一个点
            z1 = 0
            z2 = 0
            for j in range(n):
                z11 = xyz2[id_com2[j], 2]/dis[j]
                z22 = 1 / dis[j]
                z1 += z11
                z2 += z22
            zi = z1 / z2

            xyzd[i, :] = [xyz1[i, 0], xyz1[i, 1], xyz1[i, 2], abs(zi-xyz1[i, 2])]
    return xyzd


# 返回判断二维离散点是否在凸壳内的下标
def inpolygon(xq, yq, xv, yv):
    """
    reimplement inpolygon in matlab
    :type xq: np.ndarray
    :type yq: np.ndarray
    :type xv: np.ndarray
    :type yv: np.ndarray
    """
    # 合并xv和yv为顶点数组
    vertices = np.vstack((xv, yv)).T
    # 定义Path对象
    path = Path(vertices)
    # 把xq和yq合并为test_points
    test_points = np.hstack([xq.reshape(xq.size, -1), yq.reshape(yq.size, -1)])
    # 得到一个test_points是否严格在path内的mask，是bool值数组
    _in = path.contains_points(test_points)
    # 得到一个test_points是否在path内部或者在路径上的mask
    _in_on = path.contains_points(test_points, radius=-1e-10)
    # 得到一个test_points是否在path路径上的mask
    _on = _in ^ _in_on
    return _in_on  # 返回一个布尔类型数组
    # return _in_on, _on

# xyz2在xyz1里面的点云，返回下标以及重叠区面积
def overlapping_area(xy1, xy2):
    hull = spt.ConvexHull(points=xy1, incremental=False)  # 求凸壳
    ID = hull.vertices  # 返回凸壳的边缘点号
    polygon = xy1[ID, :]  # 求凸壳数组
    ID2 = inpolygon(xy2[:, 0], xy2[:, 1], polygon[:, 0], polygon[:, 1])  # 求xyz哪些点在凸壳当中
    xy2inxy1 = xy2[ID2, :]  # 求xy2在凸壳内的点数组
    hull2in1 = spt.ConvexHull(points=xy2inxy1, incremental=False)  # 求凸壳
    ID3 = hull2in1.vertices  # 返回重叠区域的凸壳点号
    p_xy2inxy1 = xy2inxy1[ID3, :]  # 重叠区域凸壳数组
    area = Polygon(p_xy2inxy1).area  # 求多边形面积
    return ID2, area,  # 返回xy2在xy1内的点云下标以及重叠区域面积


# 输入起始点的二维坐标和终点的二维坐标（两点式）
def GeneralEquation(first_x, first_y, second_x, second_y):
    # 一般式 Ax+By+C=0
    A = second_y - first_y
    B = first_x - second_x
    C = second_x * first_y - first_x * second_y
    return A, B, C  # 返回一般式的三个参数

# 输入相邻航带的点云以及重叠区域的凸壳、最后添加保存路径
def FrameOverlappingArea(xyz1, xyz2, convexhull, savepath, black=0):
    x1 = xyz1[:, 0]
    x2 = xyz2[:, 0]
    y1 = xyz1[:, 1]
    y2 = xyz2[:, 1]
    z1 = xyz1[:, 2]
    z2 = xyz2[:, 2]  # 单独提取 x y z
    x = np.hstack((x1, x2))
    y = np.hstack((y1, y2))
    z = np.hstack((z1, z2))  # 合并同类项
    if black == 0:
        cm = plt.cm.get_cmap('turbo')  # 设置colorbar的颜色条带
    else:
        cm = plt.cm.get_cmap('Greys_r')  # 设置colorbar的颜色条带为黑白_r
    sc = plt.scatter(x, y, c=z, vmin=min(z), vmax=max(z), s=5, cmap=cm, marker=".")  # 二维点x，y，最小亮度展示，最大亮度展示，点半径，使用的colormap色系，使用的点类型
    cbar = plt.colorbar(sc)  # 画出colorbar
    rectangle = plt.plot(convexhull[:, 0], convexhull[:, 1], 'w')  # 以白色展示出来凸壳位置
    plt.xlabel("x axis (meter)")
    plt.ylabel("y axis (meter)")  # 添加 x y 坐标轴标签
    cbar.ax.set_ylabel('elevation (meter)')  # 添加colorbar y轴标签
    # legend = plt.legend(rectangle, 'overlapping area', loc='upper left', edgecolor='black', facecolor='w', title='overlapping area')
    # plt.gca().add_artist(legend)
    plt.title('Overlapping area of adjacent navigation belts', pad=20)  # pad:调节和图框的距离
    plt.savefig(savepath, bbox_inches='tight', dpi=600)  # 保存路径，不留白，分辨率设置成600
    # plt.show()

# 输入为二维数组凸壳集合
def RegressionLine(convexhull):

    x = convexhull[:, 0]  # 提取x坐标集
    y = convexhull[:, 1]  # 提取y坐标集
    plt.plot(x, y, 'ro')  # 显示凸壳点集
    # plt.show()
    x_max = max(x)  # 找到最大x
    id_x_max = np.argmax(x)  # 找到最大x所在下标
    y_x_max = convexhull[id_x_max, 1]  # 返回最大x下标的y

    y_max = max(y)  # 找到最大y
    id_y_max = np.argmax(y)  # 找到最大y所在下标
    x_y_max = convexhull[id_y_max, 0]  # 返回最大y下标的x

    x_min = min(x)  # 找到最小x
    id_x_min = np.argmin(x)  # 找到最小x所在下标
    y_x_min = convexhull[id_x_min, 1]  # 返回最小x下标的y

    y_min = min(y)  # 找到最小y
    id_y_min = np.argmin(y)  # 找到最小y所在下标
    x_y_min = convexhull[id_y_min, 0]  # 返回最小y下标的x

    f1_a, f1_b, f1_c = GeneralEquation(x_y_min, y_min, x_max, y_x_max)  # 一般式 Ax+By+C=0
    fix1 = []
    for i in range(len(convexhull)):  # 将凸壳所有点带入到方程中，对方程的z进行修正
        z1 = f1_a * convexhull[i, 0] + f1_b * convexhull[i, 1] + f1_c
        if z1 < 0:
            f1_c -= z1
            fix1 = convexhull[i, :]  # 找到引起修改c的关键点
    x1_a = sum(x) / len(x)
    y1_a = (-f1_c - f1_a * x1_a) / f1_b  # 再找到一个点
    f1_x = [x1_a, fix1[0]]  # x坐标集合
    f1_y = [y1_a, fix1[1]]  # y坐标集合
    plt.plot(f1_x, f1_y)  # 找到两个点连一条线进行绘图

    f2_a, f2_b, f2_c = GeneralEquation(x_min, y_x_min, x_y_max, y_max)
    fix2 = []
    for i in range(len(convexhull)):
        z2 = f2_a * convexhull[i, 0] + f2_b * convexhull[i, 1] + f2_c
        if z2 > 0:
            f2_c -= z2
            fix2 = convexhull[i, :]
    x2_a = sum(x) / len(x)
    y2_a = (-f2_c - f2_a * x2_a) / f2_b
    f2_x = [x2_a, fix2[0]]
    f2_y = [y2_a, fix2[1]]
    plt.plot(f2_x, f2_y)
    plt.show()  # f1在上，f2在下，显示窗口

    dis_long = dis_p2p(x_y_min, y_min, x_max, y_x_max)  # 返回长
    dis_width = dis_p2p(x_max, y_x_max, x_y_max, y_max)  # 返回宽
    return f1_a, f1_b, f1_c, f2_a, f2_b, f2_c, dis_long, dis_width  # 返回两条线的6个参数，以及边长

# 返回两点之间的距离
def dis_p2p(x1, y1, x2, y2):
    d_x = abs(x1 - x2)  # 求△x
    d_y = abs(y1 - y2)  # 求△y
    dis = sqrt((d_x ** 2) + (d_y ** 2))  # 求平面两点的直线距离
    return dis

# 求点到直线的距离，输入一般式的三个参数和点的平面坐标
def dis_p2l(fa, fb, fc, x, y):
    dis = (abs(fa * x + fb * y + fc)) / ((fa ** 2 + fb ** 2) ** 0.5)
    return dis  # 返回距离

# 信息熵计算 ：输入点云高程数组
def entropy_las(z):
    count_z = list(dict(Counter(z)).values())
    num_z = len(z)
    entropy = 0
    for i in range(len(count_z)):
        entropy += (-(count_z[i] / num_z) * log(count_z[i] / num_z))
    return entropy  # 返回熵值

# PCA函数，默认降序排序
def pca(xyz_n, sort=True):
    # 直接从深蓝学院作业照搬，所有参仅供参考
    data_T = xyz_n.T  # 数组转置
    s = np.array(data_T)  # 获取数组的行列数
    n = s.shape[0]  # 获取行数（x,y,z）
    m = s.shape[1]  # 获取列数（点云数）
    mean = [0] * 3  # 定义一个平均值空数组

    for i in range(n):  # 进行行数循环
        mean[i] = np.mean(data_T[i, :])  # 求出每行的平均值
        for j in range(m):  # 进行列数循环
            data_T[i, j] -= mean[i]  # 减去平均值
    dataTT = data_T.T  # 转置修改后的数组
    # print(data_T.shape,dataTT.shape)
    c = 1 / m * np.matmul(data_T, dataTT)  # 协方差c
    eigenvalues, eigenvectors = np.linalg.eig(c)  # 求出矩阵的特征值和特征向量
    # 判断是否排序
    if sort:
        sort = eigenvalues.argsort()[::-1]
        eigenvalues = eigenvalues[sort]
        eigenvectors = eigenvectors[:, sort]

    return eigenvalues, eigenvectors  # 返回特征值和特征向量（注意是3*3的）

# 计算单个点云的曲率
def curvature_(eigenvalues,job):
    job = int(job)
    c = eigenvalues[job] / sum(eigenvalues)
    return c

def Vl(eigenvalues):
    '线状\面状\球状特征'
    '线状特征'
    numerator = np.sqrt(eigenvalues[0])-np.sqrt(eigenvalues[1])
    denominator = np.sqrt(eigenvalues[0])
    α1D = numerator/denominator
    '面状特征'
    numerator = np.sqrt(eigenvalues[1])-np.sqrt(eigenvalues[2])
    denominator = np.sqrt(eigenvalues[0])
    α2D = numerator/denominator
    '球状特征'
    α3D = np.sqrt(eigenvalues[2])/np.sqrt(eigenvalues[0])
    '判断特征最大值下标'
    vl = np.argmax([α1D,α2D,α3D])
    return vl

# 求所有点云的曲率大小
def curvature(xyz, n=15):
    xyz_32 = np.column_stack((xyz[:, 0], xyz[:, 1], xyz[:, 2])).astype(np.float32)
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(xyz_32)
    pcd_tree = o3d.geometry.KDTreeFlann(pcd)
    # id_kntree = np.empty((len(xyz), n), dtype=int)  # 新建一个用来存储下标的新数组
    curvature_all = np.empty(len(pcd.points))
    # gpu = torch.device("cuda")
    # print('欢迎有泽使用', torch.cuda.get_device_name(0), '可用cuda数为', torch.cuda.device_count())
    for i in range(len(pcd.points)):
        [_, idx, _] = pcd_tree.search_knn_vector_3d(pcd.points[i], n)  # 求每个点最近的n个点
        # print("求单个最邻近用时", s.time() - t, "秒")
        # id_kntree[i, :] = idx  # 求出每个点最邻近的n个点的下标
        xyz_n = xyz[idx, :]
        cv, _ = pca(xyz_n)  # 求每个点的特征值和特征向量
        c = curvature_(cv,job=-1)  # 求出当前点的曲率
        curvature_all[i] = c
    return curvature_all  # 返回所有数组的曲率值组成一个数组

# 计算每一个块的曲率
def curvature_block(xyz, start, end, n, job):
    xyz_32 = np.column_stack((xyz[:, 0], xyz[:, 1], xyz[:, 2])).astype(np.float32)
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(xyz_32)
    pcd_tree = o3d.geometry.KDTreeFlann(pcd)
    curvature_all = np.empty(end-start)
    for i in range(start, end):
        [_, idx, _] = pcd_tree.search_knn_vector_3d(pcd.points[i], n)  # 求每个点最近的n个点
        # id_kntree[i, :] = idx  # 求出每个点最邻近的n个点的下标
        xyz_n = xyz[idx, :]
        cv, _ = pca(xyz_n)  # 求每个点的特征值和特征向量
        c = curvature_(cv,job)  # 求出当前点的曲率
        # print(c)
        curvature_all[i-start] = c
    print('已完成第', start, '至第', end, '的点云')
    return curvature_all

# 多线程计算曲率，输入：点云坐标，最邻近点数量（默认15），开启的进程数（默认全开）
def curvature_mp(xyz, n=15, cpu=mp.cpu_count(), job=-1): # 如果job=0，那么就是求特征值法向量，如果job=-1，那就是求曲率
    pool = mp.Pool(processes=cpu)  # 开启多进程池，数量为cpu
    num = len(xyz)  # 返回点云数量
    # start, end = block(num, cpu)  # 返回每个block的起始点云下标和终止点云下标
    tik = cut_down(num, cpu)  # 去除bug后的分块函数
    j = 0  # 分块输出计数器
    curvature_all = np.empty(shape=len(xyz))  # 新建一个容器：整个点云的曲率数集
    multi_res = [pool.apply_async(curvature_block, args=(xyz, tik[i], tik[i+1], n, job)) for i in range(cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    for res in multi_res:
        curvature_all[tik[j]:tik[j+1]] = res.get()  # 将每个进程得到的结果分block的发送到容器当中
        j += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    return curvature_all  # 返回全部点云曲率集

def get_Vl_mp(xyz,n=15,cpu=mp.cpu_count()):
    '异步并行计算求Vl'
    # 准备工作
    num = len(xyz)
    Vl_all = np.empty(num)  # 存储Vl的容器
    tree = KDTree(xyz)  # 创建树
    pool = mp.Pool(processes=cpu)  # 开启多进程池，数量为cpu
    # 并行计算
    multi_res = pool.starmap_async(get_Vl, ((xyz[i,:],n,tree) for i in
                 tqdm(range(num),desc='分配任务计算单个方向向量',unit='个点',total=num)))
    j = 0
    for res in tqdm(multi_res.get(),total=num,desc='输出Vl特征结果'):
        # Vl_all[j] = res
        xyz_ = xyz[res, :]
        cv, _ = pca(xyz_)
        Vl_all[j] = Vl(cv)  # 求类别
        j += 1
    pool.close()  # 关闭所有进程
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    return Vl_all

def get_Vl(xyz,n,tree):
    '求单个点的Vl特征'
    # print(i)
    dis,ind = tree.query(xyz.reshape(1, -1), k=n)
    # xyz_ = xyz[ind,:]
    # cv, _ = pca(xyz_)  # 求每个点的特征值和特征向量
    # Vl_ = Vl(cv)  # 求类别
    return ind.reshape(-1)


def noise_elimination_mp(xyz, K=50,sigma=15,processes=mp.cpu_count()):
    '点云噪声剔除(并行计算)'
    # 并行计算准备
    num = len(xyz)  # 点云数量
    tree = KDTree(xyz)  # 建立KD树
    multi_res = np.empty(num)  # 创建并行结果容器
    pool = mp.Pool(processes)  # 开启多进程池，数量为cpu
    results = pool.starmap_async(noise_elimination_single, ((xyz[i,:],tree,K) for i in
                 tqdm(range(num),desc='并行计算任务分配',unit='个点',total=num)))  # 任务分配
    j = 0  # 计步器
    for res in tqdm(results.get(),total=num,desc='并行计算结果导出',unit='个点'):  # 结果提取
        multi_res[j] = res
        j += 1
    pool.close()  # 关闭所有进程
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    # 判断噪点的最大阈值
    max_distance = np.mean(multi_res) + sigma * np.std(multi_res)
    idx = multi_res <= max_distance
    return idx

def noise_elimination_single(xyz,tree,K):
    '点云噪声剔除 单进程'
    dist,ind = tree.query(xyz.reshape(1, -1),K)
    k_dist = np.sum(dist)  # 50邻域距离总和
    return k_dist

def surface_density_mp(xyz,r,cpu=mp.cpu_count()):
    '单点点云(表面)密度(并行)'
    t0 = s.time()  # 起始时间
    tree = KDTree(xyz[:,:2])  # 建立二维KDtree
    pool = mp.Pool(processes=cpu)  # 开启多进程池，数量为cpu
    num = len(xyz)  # 返回点云数量
    tik = cut_down(num, cpu)  # 返回每个block的起始点云下标和终止点云下标
    j = 0  # 分块输出计数器
    density_all = np.empty(shape=num)  # 新建一个容器：整个点云的曲率数集
    multi_res = [pool.apply_async(surface_density, args=(xyz, tik[i], tik[i+1],tree,r)) for i in
                 range(cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    for res in multi_res:
        density_all[tik[j]:tik[j+1]] = res.get()  # 将每个进程得到的结果分block的发送到容器当中
        j += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    t = s.time()  # 结束时间
    print('求单点二维密度用时：',t-t0,'s')
    return density_all

def dot_density_mp(xyz,r=2,cpu=mp.cpu_count()):
    '单点点云(球)密度(并行)'
    t0=s.time()  # 起始时间
    xyz_32 = np.float32(xyz)  # 格式转换成浮点32位
    # pcd = o3d.geometry.PointCloud()  # 新建容器
    # pcd.points = o3d.utility.Vector3dVector(xyz_32)  # 容器连接点云
    # pcd_tree = o3d.geometry.KDTreeFlann(pcd)  # 建立kdtree
    pool = mp.Pool(processes=cpu)  # 开启多进程池，数量为cpu
    num = len(xyz)  # 返回点云数量
    tik = cut_down(num, cpu)  # 返回每个block的起始点云下标和终止点云下标
    j = 0  # 分块输出计数器
    density_all = np.empty(shape=num)  # 新建一个容器：整个点云的曲率数集
    multi_res = [pool.apply_async(dot_density, args=(xyz_32, tik[i], tik[i+1], r)) for i in
                 range(cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    for res in multi_res:
        density_all[tik[j]:tik[j+1]] = res.get()  # 将每个进程得到的结果分block的发送到容器当中
        j += 1
    t = s.time()  # 结束时间
    print('求单点三维密度用时：',t-t0,'s')
    return density_all

# 按密度对点云进行冗余剔除（并行）
def ebydis(xyzi,cpu=mp.cpu_count(),n=50):
    t0=s.time()  # 起始时间
    pool = mp.Pool(processes=cpu)  # 开启多进程池，数量为cpu
    num = len(xyzi)  # 返回点云数量
    # start, end = block(num, cpu)  # 返回每个block的起始点云下标和终止点云下标
    tik = cut_down(num, cpu)  # 返回每个block的起始点云下标和终止点云下标
    j = 0  # 分块输出计数器
    dis_all = np.empty(shape=num)  # 新建一个容器：整个点云的曲率数集
    multi_res = [pool.apply_async(ebydis_single, args=(xyzi, tik[i], tik[i+1], n)) for i in
                 range(cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    for res in multi_res:
        dis_all[tik[j]:tik[j+1]] = res.get()  # 将每个进程得到的结果分block的发送到容器当中
        j += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    mean=np.mean(dis_all)  # 求平均距离平均值
    var=np.var(dis_all)  # 求距离方差
    max_dis = np.max(dis_all)  # 求最大距离
    t = s.time()  # 结束时间

    return dis_all,mean,var,max_dis,t-t0

def surface_density(xyz,start,end,tree,r):
    '求单点表面密度'
    num = end-start  # 点云数
    density_all = np.empty(shape=num)  # 新建一个距离容器
    xy_ = np.empty([1, 2])  # kdtree搜索位置容器
    for i in range(start, end):  # 开始循环
        xy_[0, :] = [xyz[i,0], xyz[i,1]]
        num_ = tree.query_radius(xy_, r=r, count_only=True)-1  # 搜索平面与此像素最近
        density_all[i-start]= num_/(np.pi*(r**2))
    return density_all

def dot_density(xyz,start,end,r=1):
    '单点点云(球)密度'
    # xyz_32 = np.float32(xyz)  # 格式转换成浮点32位
    pcd = o3d.geometry.PointCloud()  # 新建容器
    pcd.points = o3d.utility.Vector3dVector(xyz)  # 容器连接点云
    pcd_tree = o3d.geometry.KDTreeFlann(pcd)  # 建立kdtree
    # 遍历每一个点，找到单位面积内点的个数
    num = end-start  # 点云数
    density_all = np.empty(shape=num)  # 新建一个距离容器
    for i in range(start, end):  # 开始循环
        k,_,_=pcd_tree.search_radius_vector_3d(pcd.points[i], r)  # 单位球内点的个数
        density_ = k/(4/3*np.pi*r**3)  # 球密度
        density_all[i-start]=density_  # 放入到容器中
    return density_all

# 按密度对点云进行冗余剔除（非并行）
def ebydis_single(xyzi,start,end,n=50):
    xyz_32 = np.column_stack((xyzi[:, 0], xyzi[:, 1], xyzi[:, 2])).astype(np.float32)  # 格式转换
    pcd = o3d.geometry.PointCloud()  # 新建容器
    pcd.points = o3d.utility.Vector3dVector(xyz_32)  # 容器连接点云
    pcd_tree = o3d.geometry.KDTreeFlann(pcd)  # 建立kdtree
    # 遍历每一个点，找到50邻域的平均距离
    num = end-start  # 点云数
    dis_all = np.empty(shape=num)  # 新建一个距离容器
    for i in range(start,end):  # 开始循环
        [_,_,dis]=pcd_tree.search_knn_vector_3d(pcd.points[i],n) # 返回寻找点数量、下标、距离
        avg_dis = np.sum(np.array(dis))/n  # 求平均距离
        dis_all[i-start]=avg_dis  # 平均距离容器赋值
    '''
    # 输出一个直方图，然后为剔除做准备
    plt.hist(dis_all,histtype='bar', rwidth=0.8)
    # plt.legend()
    plt.xlabel('平均距离')
    plt.ylabel('点云数量')
    plt.title(u'点云50邻域平均距离直方图', FontProperties=font)
    plt.show()
    '''
    return dis_all

# 二维直线拟合
def linefit(x,y):
    m = len(x)  # x的个数
    sumx = np.sum(x)  # 对x序列求和
    sumy = np.sum(y)  # 对y序列求和
    sumx2 = np.sum(x**2)  # 对x序列求平方和
    sumxy = np.sum(x*y)  # 对x*y求序列和
    matirx1 = np.mat([[m, sumx], [sumx, sumx2]])  # 法向量系数矩阵
    matirx2 = np.array([sumy, sumxy])  # 值向量
    return np.matmul(np.linalg.inv(matirx1), matirx2)  # 求法向量 ab


# 寻找相同点云和不同点云
def D_Finder(xyz1,xyz2,cpu = mp.cpu_count()):
    '''
    # 添加标签
    id_0 = np.zeros(len(xyz1))
    id_1 = np.ones(len(xyz2))
    # 合并数据
    xyzd1 = np.c_[xyz1,id_0]
    xyzd2 = np.c_[xyz2,id_1]
    xyz = np.vstack([xyzd1,xyzd2])  # 合并点云
    ab_xyz = np.sort(xyz,axis=0)  # 按列排序
    '''
    # 对python重叠点云搜索最邻近
    xyz1_32 = np.column_stack((xyz1[:, 0], xyz1[:, 1], xyz1[:, 2])).astype(np.float32)  # 格式转换
    xyz2_32 = np.column_stack((xyz2[:, 0], xyz2[:, 1], xyz2[:, 2])).astype(np.float32)  # 格式转换
    pcd1 = o3d.geometry.PointCloud()  # 新建容器
    pcd1.points = o3d.utility.Vector3dVector(xyz1_32)  # 容器连接点云
    pcd1_tree = o3d.geometry.KDTreeFlann(pcd1)  # 建立kdtree
    start1, end1 = block(len(xyz1), cpu)  # 返回每个block的起始点云下标和终止点云下标
    same = []
    dif = []
    dis_all = np.empty(len(xyz2))
    for i in range(len(xyz2)):
        [_, _, dis] = pcd1_tree.search_knn_vector_3d(xyz2_32[i], 1)
        dis_all[i] = np.array(dis)
        if np.array(dis) < 0.003:
        # if np.array(dis) == 0:
            same.append(xyz2[i])
        else:
            dif.append(xyz2[i])
    same = np.array(same)
    dif = np.array(dif)
    return same , dif, dis_all


# 建立断点
def cut_down(num, Piece=mp.cpu_count()):
    tik = []
    if num <= Piece:
        tik.append(0)
        print('点云数量过少，不能分块')
    else:
        n_pool = ceil(num / Piece)  # 每个池处理的最大点云数量
        print('每个block的tik位置为', n_pool)
        for i in range(0, Piece):
            tik.append(i * n_pool)
    tik.append(num)
    return tik  # 输出每个断点位置


# 删除临近点核心代码，多线程
def del_nei_mp(com_xyz1,com_xyz2,dis11,dis22,num_cpu=mp.cpu_count(),num_n=1,max_r=0.27,d_c = 0.00159 + 0.03):
    # 准备工作
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    num = len(com_xyz2)
    tik = cut_down(num,num_cpu)  # 分块数组
    j = 0 # 分块计时器
    # 开始
    multi_res = [pool.apply_async(del_nei_block, args=(com_xyz1,com_xyz2,num_n,max_r,tik[i],tik[i+1],d_c,dis11,dis22)) for i in
                 range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    for res in multi_res:
        if j==0:
            [id_del1_1,id_del2_1] = res.get()  # 将每个进程得到的结果分block的发送到容器当中
            j += 1
        else:
            [id_del1_,id_del2_] = res.get()  # 将每个进程得到的结果分block的发送到容器当中
            id_del1_1 = np.append(id_del1_1,id_del1_)
            # del id_del1_
            id_del2_1 = np.append(id_del2_1,id_del2_)
            # del id_del2_
            j += 1
    # 结束
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    # 整理数据
    id_del1 = np.unique(id_del1_1)
    id_del2 = np.unique(id_del2_1)
    com_xyz1 = np.delete(com_xyz1,id_del1,axis=0)
    com_xyz2 = np.delete(com_xyz2, id_del2, axis=0)
    return com_xyz1,com_xyz2

def del_nei_block(com_xyz11,com_xyz22,num_n,max_r,a,b,d_c,dis11,dis22):
    # 准备工作
    com_xyz1 = np.column_stack((com_xyz11[:, 0], com_xyz11[:, 1], com_xyz11[:, 2])).astype(np.float32)
    view1 = o3d.geometry.PointCloud()
    view1.points = o3d.utility.Vector3dVector(com_xyz1)  # 将点云和容器进行连接
    pcd_tree = o3d.geometry.KDTreeFlann(view1)  # 对第一航带建立kntree
    com_xyz2 = np.column_stack((com_xyz22[:, 0], com_xyz22[:, 1], com_xyz22[:, 2])).astype(np.float32)
    view2 = o3d.geometry.PointCloud()
    view2.points = o3d.utility.Vector3dVector(com_xyz2)  # 将点云和容器进行连接
    pcd_tree2 = o3d.geometry.KDTreeFlann(view2)  # 对第一航带建立kntree
    id_del_com1 = []
    id_del_com2 = []  # 存储删除点容器
    # 开始循环
    for i in range(a,b):  # 以第二航带为参考，寻找第一航带的临近点云
        [judge, id_com11, _] = pcd_tree.search_hybrid_vector_3d(com_xyz22[i, :], max_r, num_n)  # 返回最邻近点云点号
        if judge == 1:  # 如果找到了最近的点
            # c1 = curvature_1[id_com11]
            # print(id_com11)
            id_1 = id_com11[0]
            [_, idx, _] = pcd_tree.search_knn_vector_3d(view1.points[id_1], 15)  # 求每个点最近的n个点
            xyz_n = com_xyz11[idx, :]
            cv, _ = pca(xyz_n)  # 求每个点的特征值和特征向量
            c1 = curvature_(cv,-1)  # 求出当前点的曲率
            # c2 = curvature_2[i]  # 求出两点云曲率
            [_, idx, _] = pcd_tree2.search_knn_vector_3d(view2.points[i], 15)  # 求每个点最近的n个点
            xyz_n = com_xyz22[idx, :]
            cv, _ = pca(xyz_n)  # 求每个点的特征值和特征向量
            c2 = curvature_(cv,-1)  # 求出当前点的曲率

            d_ci = np.abs(c1-c2)  # 曲率差值
            if c1 - c2 > d_c:  # 如果c1的曲率大于等于c2 超过平均值+一倍标准差
                id_del_com2.append(i)
            elif c2 - c1 >= d_c:  # 如果c2的曲率大于等于c1 超过平均值+一倍标准差
                id_del_com1.append(id_com11)
            elif com_xyz22[i, 0] is not None and com_xyz11[id_com11, 0] is not None:  # 如果相对距离存在
                if dis11[id_com11] > dis22[i]:  # 如果第一航带相对距离更大
                    id_del_com2.append(i)
                elif dis11[id_com11] <= dis22[i]:  # 如果第二航带相对距离不小于第一航带
                    id_del_com1.append(id_com11)
    # 整理数据
    id_del1 = np.array(id_del_com1)
    id_del2 = np.array(id_del_com2)
    return id_del1,id_del2










