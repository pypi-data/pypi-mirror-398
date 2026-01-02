import numpy as np
from numpy.ma.core import indices
from sklearn.neighbors import KDTree
import multiprocessing as mp
from tqdm import tqdm


def getPCA_R_mp(xyz,tree,r_min=0.05,r_max=0.2,dr=0.02,cpu=mp.cpu_count()):
    '求每个点的最小半径'
    num = len(xyz)
    r_all = np.empty(num)

    pool = mp.Pool(processes=cpu)  # 开启多进程池，数量为cpu
    multi_res = pool.starmap_async(getPCA_R, ((i,xyz,tree,r_min,r_max,dr) for i in
                 tqdm(range(num),desc='分配任务计算单个点的适应半径',unit='个点',total=num)))
    j = 0
    for res in tqdm(multi_res.get(),total=num,desc='输出单个点的适应半径'):
        r_all[j] = res[0]
        j += 1
    pool.close()  # 关闭所有进程
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    return r_all

def getPCA_R(i,xyz,tree,r_min,r_max,dr):
    xyz_ = xyz[i, :]  # 当前点
    min_entropy = float('inf')
    optimal_r = r_min
    indices_best = []
    for r_ in np.arange(r_min, r_max, dr):
        indices= tree.query_radius([xyz_], r_)  # 查询半径为0.2内的点
        indices = indices[0]
        indices = indices[indices != i]  # 不包含自己
        xyz_i_r_ = xyz[indices, :]  # 在半径范围内的点
        num_ = len(xyz_i_r_)  # 寻找点的数量
        if num_ >= 2:
            # 构建协方差矩阵并计算特征值
            centered_points = xyz_i_r_ - np.mean(xyz_i_r_, axis=0)
            cov_matrix = np.cov(centered_points, rowvar=False)
            eigenvalues = np.linalg.eigvalsh(cov_matrix)
            eigenvalues = np.sort(eigenvalues)[::-1]  # 降序排序
            # 计算局部维度特征
            L_lambda = (eigenvalues[0] - eigenvalues[1]) / eigenvalues[0]
            P_lambda = (eigenvalues[1] - eigenvalues[2]) / eigenvalues[0]
            S_lambda = eigenvalues[2] / eigenvalues[0]
            # 计算信息熵
            entropy = -L_lambda * np.log(L_lambda) - P_lambda * np.log(P_lambda) - S_lambda * np.log(S_lambda)
            # 最小熵准则
            if entropy < min_entropy:
                min_entropy = entropy
                optimal_r = r_
                indices_best = indices
    return optimal_r,indices

def PCA_new(xyz,r_min=0.05,r_max=0.2,dr=0.02,cpu=mp.cpu_count()):
    '改进PCA算法 ＤＯＩ：１０．１６２５１／ｊ．ｃｎｋｉ．１００９－２３０７．２０２１．１１．０１２．'
    tree = KDTree(xyz)  # 创建树
    # 1.对每个点求最小半径
    r_all = getPCA_R_mp(xyz,tree,r_min,r_max,dr,cpu)
    # 2.计算亲和度
    Affinity = getAffinity_mp(xyz,tree,r_all)
    # 3.计算改进PCA
    return Affinity

def PCA_new_mp(xyz,r_min=0.05,r_max=0.2,dr=0.02,cpu=mp.cpu_count(),k=10):
    '''
    改进PCA算法（全程并行计算版）
    :param xyz: 点云坐标
    :param r_min: 最小半径
    :param r_max: 最大半径
    :param dr: 半径迭代步长
    :param cpu: 并行线程数量
    :param k: K邻域数量
    :return: np.array([L1,L2,L3,VECTOR])*len(xyz)
    '''
    # 准备工作
    num = len(xyz)  # 点云数量
    L123V = np.empty([num,6])  # 前三个为特征值，后三个为最小特征向量
    tree = KDTree(xyz)  # 创建树
    pool = mp.Pool(processes=cpu)  # 开启多进程池，数量为cpu
    Ve = np.empty([num,3])
    Vr = np.empty([num,3])
    # 并行计算
    multi_res = pool.starmap_async(PCA_new_, ((i,xyz,tree,r_min,r_max,dr,k) for i in
                 tqdm(range(num),desc='分配任务计算每个点的PCA',unit='个点',total=num)))
    j = 0
    for res in tqdm(multi_res.get(),total=num,desc='输出单个点的特征值和最小特征向量'):
        Ve[j, :] = res[0]
        Vr[j, :] = res[1]
        j += 1
    pool.close()  # 关闭所有进程
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    return Ve,Vr

def PCA_new_(i,xyz,tree,r_min=0.05,r_max=0.2,dr=0.02,k=10):
    '单点改进PCA算法'
    _,indices = getPCA_R(i, xyz, tree, r_min, r_max, dr)  # 求最适合的半径和下标
    # 计算亲和度和PCA改进矩阵
    xyz_ = xyz[i, :]  # 当前点
    xyz_J = xyz[indices, :]  # 所有J点
    distances = np.linalg.norm(xyz_J - xyz_, axis=1)  # 计算欧式距离
    distance_i_, _ = tree.query([xyz_], k=k + 1)  # 计算I点的第k个点的距离
    num_J = len(xyz_J)
    Ai = np.empty(num_J)  # 一排的亲和度
    centroid = np.mean(xyz_J, axis=0)  # 点云质心
    C = np.zeros([3,3])  # 特征矩阵
    for j in range(num_J):
        xyz_J_ = xyz_J[j, :]
        distance_j_, _ = tree.query([xyz_J_], k=k + 1)  # 计算J点的第k个点的距离
        Aij = np.exp(- (distances[j] ** 2) / (distance_i_[0, -1] * distance_j_[0, -1]))  # 当前两点的亲和度
        Ai[j] = Aij
        # 计算特征值和特征向量
        pj_p = xyz_J_ - centroid  # 临近点减质心
        Cj = Ai[j]*np.outer(pj_p, pj_p)  # 求元素矩阵
        C += Cj
    # 矩阵分解
    eigenvalues, eigenvectors = np.linalg.eig(C)  # 求出矩阵的特征值和特征向量
    sort = eigenvalues.argsort()[::-1]
    eigenvalues = eigenvalues[sort]
    eigenvectors = eigenvectors[:, sort]
    return eigenvalues,eigenvectors[:,-1]  # 返回特征值和最小的特征向量

def getAffinity(xyz,tree,r_all,k=10):
    '单线程计算亲和度'
    num = len(xyz)  # 点的数量
    Affinity = []  # 亲和度容器
    for i in tqdm(range(num),desc='计算两点之间的亲和度',unit='个点',total=num):
        xyz_ = xyz[i,:]  # 当前点
        indices = tree.query_radius([xyz_], r_all[i])  # 需要计算的J点们的下标
        indices = indices[0]
        indices = indices[indices != i]  # 不包含自己
        xyz_J = xyz[indices,:]  # 所有J点
        distances = np.linalg.norm(xyz_J - xyz_, axis=1) # 计算欧式距离
        distance_i_, _ = tree.query([xyz_], k=k + 1)  # 计算I点的第k个点的距离
        num_J = len(xyz_J)
        Ai = np.empty(num_J)  # 一排的亲和度
        for j in range(num_J):
            xyz_J_ = xyz_J[j,:]
            distance_j_, _ = tree.query([xyz_J_], k=k + 1)  # 计算J点的第k个点的距离
            Aij = np.exp(- (distances[j] ** 2) / (distance_i_[0,-1] * distance_j_[0,-1]))  # 当前两点的亲和度
            Ai[j] = Aij
        Affinity.append(Ai)
    return Affinity

def getAffinity_mp(xyz,tree,r_all,k=10,cpu=mp.cpu_count()):
    '并行计算点到点的亲和度'
    # 准备工作
    num = len(xyz)  # 点的数量
    Affinity = []  # 亲和度容器
    pool = mp.Pool(processes=cpu)  # 开启多进程池，数量为cpu
    # 并行计算
    multi_res = pool.starmap_async(getAffinity_, ((i,xyz,tree,r_all,k) for i in
                 tqdm(range(num),desc='分配任务计算每个点的亲和点',unit='个点',total=num)))
    j = 0
    for res in tqdm(multi_res.get(),total=num,desc='输出单个点的适应半径'):
        Affinity.append(res)
        j += 1
    pool.close()  # 关闭所有进程
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    return Affinity
def getAffinity_(i,xyz,tree,r_all,k):
    xyz_ = xyz[i, :]  # 当前点
    indices = tree.query_radius([xyz_], r_all[i])  # 需要计算的J点们的下标
    indices = indices[0]
    indices = indices[indices != i]  # 不包含自己
    xyz_J = xyz[indices, :]  # 所有J点
    distances = np.linalg.norm(xyz_J - xyz_, axis=1)  # 计算欧式距离
    distance_i_, _ = tree.query([xyz_], k=k + 1)  # 计算I点的第k个点的距离
    num_J = len(xyz_J)
    Ai = np.empty(num_J)  # 一排的亲和度
    for j in range(num_J):
        xyz_J_ = xyz_J[j, :]
        distance_j_, _ = tree.query([xyz_J_], k=k + 1)  # 计算J点的第k个点的距离
        Aij = np.exp(- (distances[j] ** 2) / (distance_i_[0, -1] * distance_j_[0, -1]))  # 当前两点的亲和度
        Ai[j] = Aij
    return Ai

