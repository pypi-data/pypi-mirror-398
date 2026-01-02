#coding=utf-8
import numpy as np  # numpy库
import math  # 添加数学库
import matplotlib.pyplot as plt  # 显示库
import open3d as o3d  # open3d库
from mpl_toolkits.mplot3d import Axes3D  # 空间三维画图
import scipy.spatial as spt  # 求凸壳用的库
from shapely.geometry import Polygon  # 求凸壳面积用的库
from sklearn.mixture import GaussianMixture  # GMM库
import time as s  # 时间库
import multiprocessing as mp  # 添加多线程库
from astropy.modeling import models, fitting  # 添加单高斯拟合函数

# 求面积（平面面积以及侧面积）
def get_area(xy):
    hull = spt.ConvexHull(points=xy, incremental=False)  # 求凸壳
    ID = hull.vertices  # 返回凸壳的边缘点号
    polygon = xy[ID, :]  # 求凸壳数组
    area = Polygon(polygon).area  # 求多边形面积
    return area

# 求每个点所占的平均面积
def mean2Ddensity(num, Area):
    density = math.sqrt(Area/num)
    print('平面平均点间距为:', density)
    return density

# https://www.cnblogs.com/wt714/p/12545129.html
# 对强度值数集进行归一化
def normalization(intensity, threshold=1):
    max_i = max(intensity)
    min_i = min(intensity)
    new_intensity = (intensity-min_i)/(max_i - min_i)*threshold
    return new_intensity

def normalization2(arr_i,max_i=1,min_i=0):
    '特征值标准化映射算法'
    # 获取数组的最小值和最大值
    min_val = np.min(arr_i)
    max_val = np.max(arr_i)
    # 使用线性插值进行映射
    mapped_array = ((arr_i - min_val) / (max_val - min_val)) * (max_i - min_i) + min_i
    return mapped_array

#求两个航带之间的最邻近点,并返回求最邻近加权后的同点强度值
def kntree_point_num(knxyz, xyz,kn_i,i,max_n=5):
    c_o3d = o3d.geometry.PointCloud()  # 建立open3d类，准备进行最邻近
    o3d_xyz = np.column_stack((knxyz[:, 0], knxyz[:, 1], knxyz[:, 2])).astype(np.float32)
    c_o3d.points = o3d.utility.Vector3dVector(o3d_xyz)  # 将点云和容器进行连接
    pcd_tree = o3d.geometry.KDTreeFlann(c_o3d)  # 对第二行带建立kntree
    i_new = []  # 新强度值存储容器
    for i in range(len(xyz)):  # 对整个点云进行遍历
        [_, idx_kn, dis_kn] = pcd_tree.search_knn_vector_3d(xyz[i, :], max_n)
        i_kn = kn_i[idx_kn]  # 存储最邻近的几个点的强度值
        dis_t = 1/np.array(dis_kn)  # 反距离加权法计算每个点的权值
        i_new_singel = np.dot(i_kn, dis_t)/sum(dis_t)  # 数乘求出最后的新的强度值
        i_new.append(i_new_singel)  # 将新的强度值集合到容器中
    return np.array(i_new)  # 返回数组类型的点云强度值

# 建立频率域直方图
def histogram(i1, i2, i3,bin=300,d=True):
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 解决中文无法显示的问题
        plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
        plt.subplot(311)  # 3行1列第一幅图
        plt.hist(sorted(i1), bins=bin,density=d)  # bins表示分为5条直方，可以根据需求修改
        plt.xlabel('intensity')
        plt.ylabel('frequency')
        #plt.xlim( 0, 50 )
        plt.subplot(312)  # 3行1列第二幅图
        plt.hist(sorted(i2), bins=bin, density=d)  # density为True表示频率，否则是频数，可根据需求修改
        plt.xlabel('intensity')
        plt.ylabel('frequency')
        #plt.xlim(0, 50)
        plt.subplot(313)  # 3行1列第三幅图
        plt.hist(sorted(i3), bins=bin, density=d)  # density为True表示频率，否则是频数，可根据需求修改
        plt.xlabel('intensity')
        plt.ylabel('frequency')
        #plt.xlim(0, 50)
        plt.show()

# 点云强度值噪声剔除函数
def NoiseElimination(xyzi, max_i):
    id = []  # 一个删除点云下标的容器
    for i in range(len(xyzi)):  # 对点云进行遍历
        if xyzi[i, 3] > max_i: # 判断是否超过阈值
            id.append(i)  # 记录点云下标
    print('剔除强度粗差',len(id),'个点')
    xyzi = np.delete(xyzi, id, axis=0)  # 删除符合条件的点云
    return xyzi  # 返回处理后的点云

# 以强度值为基础，映射到RBG，进行三维散点图的显示
def i32rgb(xyz,i1,i2,i3,max_i=255):  # 输入点云位置，以及映射的三个点云强度值
    fig = plt.figure() # 新建一个窗口
    ax = Axes3D(fig) # 明确为三维散点图
    if max(i1)+max(i2)+max(i3) >3: # 如果没有进行归一化,那么进行归一化
        i1 /= max_i
        i2 /= max_i
        i3 /= max_i
    rgb = np.c_[i1, i2, i3]  # 将三强度值附给rgb三个通道
    ax.scatter(xyz[:,0], xyz[:,1], xyz[:,2], c=rgb)  # 显示点云
    plt.show() # 显示窗口

# 高斯混合模型(输入点云分类特征、总的类别数)加上显示
def use_gmm(data,classes):
    # 显示初始条件的分布散点图
    if np.shape(data)[-1] == 2:
        plt.figure()
        plt.scatter(data[:, 0],data[:, 1])
        plt.show()
    elif np.shape(data)[-1] == 3:
        fig = plt.figure()
        ax = Axes3D(fig)
        ax.scatter(data[:, 0],data[:, 1],data[:, 2])
        plt.show()
    # 进行高斯混合模型分解
    gmm = GaussianMixture(classes)
    gmm.fit(data)
    labels = gmm.predict(data)  # 判断每个点云所属的类别
    # 显示分类后的分布散点图（无法保证类别，暂时忽略）
    return labels

# 求点云的平面密度
def num_area(num,area):
    return num/area

# 求RMSE
def get_RMSE(data):
    sum_d = sum(data)
    n = len(data)
    return sum_d/n

# 建立断点
def cut_down(num, Piece=mp.cpu_count()):
    tik = []
    if num <= Piece:
        tik.append(0)
        print('点云数量过少，不能分块')
    else:
        n_pool = math.ceil(num / Piece)  # 每个池处理的最大点云数量
        print('每个block的tik位置为', n_pool)
        for i in range(0, Piece):
            tik.append(i * n_pool)
    tik.append(num)
    return tik  # 输出每个断点位置

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

def get_ρθ_block(xyzic, xzrc, Ts, Te, n):
    '分块求圆心距和角度函数'
    # 准备工作
    single_a = np.pi * 2 / n  # 求每个块的过渡
    ρθ_ = np.empty([Te-Ts, 2])
    j = 0  # 计数器
    for i in range(Ts, Te):
        # 求p
        xyz_ = xyzic[i, :3]  # 当前点的空间位置
        c_i = xyzic[i, -1]  # 当前点圆环名
        xzr_ = xzrc[xzrc[:, -1] == c_i, :3]  # 圆心位置
        R2 = (xyz_[0] - xzr_[0, 0]) ** 2 + (xyz_[2] - xzr_[0, 1]) ** 2  # 点到圆心的距离
        ρθ_[j, 0] = np.sqrt(R2)  # 点云到中轴线的距离
        # 求角度
        angle_ = np.arctan2((xyzic[i, 2] - xzr_[0, 1]), (xyzic[i, 0] - xzr_[0, 0]))  # 求反正切值
        ρθ_[j, 1] = np.floor(angle_ / single_a)  # 点云归属标签赋值
        # 其他
        j += 1
    print('极坐标系转换已完成', Te/len(xyzic)*100, '%')
    return ρθ_

def get_ρθ_block2(xyzic, xyzc, Ts, Te, n):
    '分块只求ρθ的函数'
    # 准备工作
    single_a = np.pi * 2 / n  # 求每个块的过渡
    ρθ_ = np.empty([Te - Ts, 2])
    j = 0  # 计数器
    for i in range(Ts, Te):
        # 求圆心距
        xyz_ = xyzic[i, :3]  # 当前点的空间位置
        c_i = xyzic[i, -1]  # 当前点圆环名
        c_xyz_ = xyzc[xyzc[:, -1]==c_i, :3]  # 圆心位置
        R2 = (xyz_[0] - c_xyz_[0, 0]) ** 2 + (xyz_[2] - c_xyz_[0, 2]) ** 2  # 点到圆心的距离
        ρθ_[j, 0] = np.sqrt(R2)  # 点云到中轴线的距离
        # 求角度
        angle_ = np.arctan2((xyzic[i, 2] - c_xyz_[0, 2]), (xyzic[i, 0] - c_xyz_[0, 0]))  # 求反正切值
        ρθ_[j, 1] = np.floor(angle_ / single_a)  # 点云归属标签赋值
        # ρθ_[j, 1] = angle_
        j += 1  # 计数器更新
    print('极坐标属性添加已完成', Te / len(xyzic) * 100, '%')
    return ρθ_

def XYZ2ρθ_mp(xyzic,xyzc,num_cpu=mp.cpu_count(),n=4250):
    '中轴线刷新后的并行计算 笛卡尔坐标系转成圆柱体坐标系(非体素化准备)'
    num = len(xyzic)  # 点云数量
    tik = cut_down(num)  # 并行计算分块
    ρθ = np.empty([num, 2])  # 新建一个存储点云ρθ的容器
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    # 开始进行并行计算
    multi_res = [pool.apply_async(get_ρθ_block2, args=(xyzic, xyzc, tik[i], tik[i + 1], n)) for i in
                 range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    tik_ = 0  # 计数器
    for res in multi_res:
        ρθ[tik[tik_]:tik[tik_ + 1], :] = res.get()
        tik_ += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    # print(np.max(ρθ[:, 1]),np.min(ρθ[:, 1]))
    # 归零化
    min_ρθ = ρθ.min(0)  # 求最小值
    ρθ[:, 0] -= min_ρθ[0]
    ρθ[:, 1] -= min_ρθ[1]
    return ρθ

def XYZ2ρθY_mp(xyzic,xzrc,num_cpu=mp.cpu_count(),n=3000):
    '并行计算 笛卡尔坐标系转成圆柱体坐标系（体素化准备）'
    # 准备工作
    num = len(xyzic)  # 点云数量
    tik = cut_down(num)  # 并行计算分块
    ρθY = np.empty([num, 3])  # 新建一个存储点云ρθ的容器
    ρθY[:, -1] = xyzic[:, 1]  # 传Y
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    # 开始进行并行计算
    multi_res = [pool.apply_async(get_ρθ_block, args=(xyzic, xzrc, tik[i], tik[i + 1], n)) for i in
                 range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    tik_ = 0  # 计数器
    for res in multi_res:
        ρθY[tik[tik_]:tik[tik_ + 1], :2] = res.get()
        tik_ += 1
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    # 归0化
    min_ρθY = ρθY.min(0)  # 求最小值
    ρθY[:,0] -= min_ρθY[0]
    ρθY[:, 1] -= min_ρθY[1]
    ρθY[:, 2] -= min_ρθY[2]  # 三列归零
    return ρθY

def XYZ2ρθY(xyzic,xzrc,n=3000):
    '笛卡尔坐标系转成圆柱体坐标系'
    Y = xyzic[:, 1]  # y轴坐标为起点
    c = xzrc[:, -1]  # 所有圆环名
    ρ = np.empty([len(xyzic)])  # 新建一个存储点云p的容器
    '准备添加并行化'
    for i in range(len(xyzic)):
        xyz_ = xyzic[i, :3]  # 当前点的空间位置
        c_i = xyzic[i, -1]  # 当前点圆环名
        xzr_ = xzrc[c == c_i, :3]  # 圆心位置
        # print(i,xyz_,xzr_)
        R2 = (xyz_[0] - xzr_[0, 0]) ** 2 + (xyz_[2] - xzr_[0, 1]) ** 2  # 点到圆心的距离
        # dis[i] = np.abs(R2 - xzr_[0, -1] ** 2)
        ρ[i] = np.sqrt(R2)  # 点云到中轴线的距离

    θ = np.empty([len(xyzic)])  # 新建一个存储点云θ的容器
    # 求角度
    xzc_point = np.c_[xyzic[:,0],xyzic[:,2],xyzic[:,-1]]
    xzc_c = np.c_[xzrc[:,:2],xzrc[:,-1]]
    θ = Split_ring_mp(xzc_point,xzc_c,n=n)
    ρθY = np.c_[ρ,θ,Y]
    # 归一化
    θ_min = np.min(ρθY[:, 1])  # 角度向量化后的最小值
    ρθY[:, 1] = ρθY[:, 1] - θ_min  # 使所有的角度都大于0
    Y_min = np.min(ρθY[:, -1])  # Y轴后的最小值
    ρθY[:, -1] = ρθY[:, -1] - Y_min  # Y轴归0
    return ρθY

def FitGaussian1D(data,bins=20):
    '''
    单高斯模型拟合
    :param data: 需要拟合的数据（一维）
    :param bins: 按照data的值域分成多少份，默认为20份
    :return:
    Fx.mean.value：拟合后高斯分布的均值；
    Fx.stddev.value：拟合后高斯分布的标准差
    '''
    y_hist,x_hist = np.histogram(data, bins)  # 使用numpy粗拟合，得到直方图曲线点
    x_hist = (x_hist[1:] + x_hist[:-1]) / 2  # 刷新值域断点
    model_Gaussian1D = models.Gaussian1D(amplitude=np.max(y_hist), mean=np.mean(data), stddev=np.std(data))  # 建立高斯模型
    model_Fit = fitting.LevMarLSQFitter()  # 建立拟合模型
    Fx = model_Fit(model_Gaussian1D, x_hist, y_hist)  # 模型求解
    '''
    x = np.linspace(0, 255, int(255/bins))
    y = Fx(x)
    plt.plot(x, y)
    plt.show()
    '''
    return Fx.mean.value,Fx.stddev.value

def get_distance_point2line(points, line_ab):
    """
    点到直线的距离（平面斜率截距式）
    Args:
        points: [x0, y0]*n
        line_ab: [k, b]
    """
    k, b = line_ab
    distance = abs(k * points[:,0] - points[:,1] + b) / math.sqrt(k**2 + 1)
    # distance = abs(k * point[0] - point[1] + b) / math.sqrt(k ** 2 + 1)
    return distance
