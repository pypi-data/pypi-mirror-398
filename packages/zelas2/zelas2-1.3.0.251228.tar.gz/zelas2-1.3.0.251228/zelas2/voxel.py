import numpy as np  # 数组库
import multiprocessing as mp  # 并行计算库
import math  # 添加数学库为cuda编程做准备
import open3d as o3d  # 添加点云处理库
import scipy.spatial as spt  # 求凸壳用的库
from shapely.geometry import Polygon  # 求凸壳面积用的库
import time as t  # 时间库
import pyvista as pv  # 极坐标体素显示库
import seaborn as sns  # 随机颜色使用的库
from tqdm import tqdm  # 进度条
from copy import deepcopy  # 深拷贝


class voxel:
    '建立体素类'

    # 输入点云位置，体元边长，找最邻近的邻域数量
    def __init__(self, xyz, pixel=0):  # 每个点云所在体素的位置，总共的体素。体素所在的位置
        self.voxel_nei = None  # 体素邻域
        self.voxel_values = None  # 体素特征值
        self.voxel_start = None  # 体素开始位置
        self.xyz = xyz  # 存储点云位置
        self.num = len(self.xyz)  # 存储点云数量
        self.pixel = pixel  # 体素的点云分辨率
        self.reset_pixel()  # 自适应体素分辨率
        print('当前体素分辨率为', self.pixel)
        self.SpaceBoundary = np.array([self.xyz.max(axis=0), self.xyz.min(axis=0)])  # 点云的边界
        self.VoxelLength = np.empty([3])  # 体素长、宽、高的数量
        self.VoxelLengthDigit = np.empty([3])  # 体素长、宽、高的位数
        self.find_VoxelLength()  # 求长宽高 的数量
        self.points_local = np.empty([self.num, 3])  # 每个点云所在的体素位置
        self.points_local_un = None  # 精简化后的有值体素位置容器
        self.num_voxel = 0  # 有效体元的数量

    # 重新设置体元分辨率
    def reset_pixel(self):
        # 自适应体素
        if self.pixel == 0:
            area = get_area(self.xyz[:, :2])  # 求面积
            density = num_area(self.num, area)  # 求密度
            self.pixel = np.ceil(1 / np.sqrt(density) * 10) / 10  # 求体素网格边长

    # 计算体素长宽高
    def find_VoxelLength(self):
        self.voxel_start = np.floor(self.SpaceBoundary[1, :] / self.pixel)  # 体素的位置应该从哪里（XYZ）开始
        voxel_end = np.ceil(self.SpaceBoundary[0, :] / self.pixel)
        self.VoxelLength = (voxel_end - self.voxel_start + 1).astype(int)  # 刷新体元数量
        self.VoxelLengthDigit = [len(str(self.VoxelLength[0])), len(str(self.VoxelLength[1])), len(str(self.VoxelLength[2]))]  # 刷新体元长宽高的位数
        print('体素的长宽高为', self.VoxelLength)
        # self.voxel_values = np.zeros(self.VoxelLength, dtype=np.float16)  # 设置三维体素(类型设置为16位浮点型)
        self.voxel_values = np.zeros(self.VoxelLength, dtype=np.float32)  # 设置三维体素(类型设置为16位浮点型)
        print('体素已建立')

    def P2V(self, values):
        '''
        点云连接体素（默认使用并行计算），并返回下标
        :param values: 点云特征值数组
        :return: 每个体素的周围26邻域中的有值体素位置
                 其他返回在类的属性中
        '''
        for i in tqdm(range(self.num),desc='单点云强度转有值体素',unit='points'):
            # self.points_local[i, :] = np.round(self.xyz[i, :] / self.pixel) - self.voxel_start  # 遍历点属于哪个体素
            self.points_local[i, :] = np.floor(self.xyz[i, :] / self.pixel) - self.voxel_start  # 遍历点属于哪个体素
            # if self.voxel_values[int(self.points_local[i, 0]), int(self.points_local[i, 1]), int(self.points_local[i, 2])]==0:
            #     self.voxel_values[int(self.points_local[i, 0]), int(self.points_local[i, 1]), int(self.points_local[i, 2])] = values[i]  # 体素赋值 需要改进（平均值版）
            self.voxel_values[int(self.points_local[i, 0]), int(self.points_local[i, 1]), int(self.points_local[i, 2])] = values[i]  # 体素赋值
        del values  # 删除
        self.points_local = self.points_local.astype(int)  # 将点云位置进行整数化
        self.points_local_un = np.unique(self.points_local, axis=0)  # 有值体素位置精简化
        self.num_voxel = len(self.points_local_un)  # 有值体素数量
        print('体素赋值已完成')
        id_point, self.index = np.unique(self.points_local, axis=0, return_index=True)  # 体素位置升序排序按照（x,y,z），并返回下标
        self.num_voxel = len(id_point)  # 返回有效的体元数量
        # del id_point
        '''
        self.voxel_nei = nei_26_mp(self.points_local, self.VoxelLength, self.voxel_values)  # 寻找26邻域位置
        print('体素26邻域搜索已完成')
        return self.voxel_nei
        '''
    def P2V_double(self, values):
        '体素二次赋值'
        self.voxel_values = np.zeros([int(self.VoxelLength[0]), int(self.VoxelLength[1]), int(self.VoxelLength[2])])
        for i in range(self.num):
            # print(i)
            self.points_local[i, :] = np.floor(self.xyz[i, :] / self.pixel) - self.voxel_start # 遍历点属于哪个体素
            self.voxel_values[int(self.points_local[i, 0]), int(self.points_local[i, 1]), int(self.points_local[i, 2])] = values[i]  # 体素赋值
        return self.voxel_values

    def Voxel2Pixel(self):
        '计算体素转像素（值为最低点高程，矩阵思想）'
        # 点云重新赋值
        self.voxel_values = np.ones(self.VoxelLength, dtype=np.float32) * 10000
        self.P2V(self.points_local[:, 2])  # 将高程值附给体素
        pixel_values_min = np.argmin(self.voxel_values, axis=2)
        self.pixel_min_un = np.empty([self.VoxelLength[0] * self.VoxelLength[1], 3])  # 二维像素数组，值为高程最低值
        k = 0
        for i in range(self.VoxelLength[0]):
            for j in range(self.VoxelLength[1]):
                self.pixel_min_un[k, 0] = i
                self.pixel_min_un[k, 1] = j
                self.pixel_min_un[k, 2] = pixel_values_min[i, j]
                k += 1
        return self.pixel_min_un

    def P2Vm(self, values):
        '点云体素化赋值（平均值版）'
        self.voxel_values = np.zeros([int(self.VoxelLength[0]), int(self.VoxelLength[1]), int(self.VoxelLength[2])], dtype=np.float32)  # 存储总值的容器
        voxel_num = np.zeros([int(self.VoxelLength[0]), int(self.VoxelLength[1]), int(self.VoxelLength[2])], dtype=np.float32)  # 存储体素数量的容器
        for i in tqdm(range(self.num)):
            self.points_local[i, :] = np.floor(self.xyz[i, :] / self.pixel) - self.voxel_start  # 遍历点属于哪个体素
            self.voxel_values[int(self.points_local[i, 0]), int(self.points_local[i, 1]), int(self.points_local[i, 2])] += values[i]  # 体素赋值
            voxel_num[int(self.points_local[i, 0]), int(self.points_local[i, 1]), int(self.points_local[i, 2])] += 1  # 点云数量增值
        print('点云转体素已完成')
        self.points_local = self.points_local.astype(int)  # 将点云位置进行整数化
        self.points_local_un = np.unique(self.points_local, axis=0)  # 有值体素位置精简化
        self.num_voxel = len(self.points_local_un)  # 有值体素数量
        # 平均值化有值
        self.voxel_values = self.voxel_values / voxel_num
        self.voxel_values = np.float32(self.voxel_values)
        # self.voxel_values = np.float16(self.voxel_values)
        self.voxel_values = np.nan_to_num(self.voxel_values)  # nan转0
        print('体素赋值已完成')
        return self.voxel_values

    def P2Vrgbm(self, r, g, b):
        '''
        点云体素化赋值（三波段平均值版）
        :param r: 第一波段特征值
        :param g: 第二波段特征值
        :param b: 第三波段特征值
        :return:
        '''
        self.voxel_values_r = np.zeros([int(self.VoxelLength[0]), int(self.VoxelLength[1]), int(self.VoxelLength[2])], dtype=np.float16)  # 存储总值的容器
        self.voxel_values_g = deepcopy(self.voxel_values_r)
        self.voxel_values_b = deepcopy(self.voxel_values_r)  # 深拷贝特征容器
        voxel_num = np.zeros([int(self.VoxelLength[0]), int(self.VoxelLength[1]), int(self.VoxelLength[2])], dtype=np.int16)  # 存储体素数量的容器
        for i in tqdm(range(self.num), desc='点云体素化三波段赋值', unit='个点'):
            self.points_local[i, :] = np.floor(self.xyz[i, :] / self.pixel) - self.voxel_start  # 遍历点属于哪个体素
            self.voxel_values_r[int(self.points_local[i, 0]), int(self.points_local[i, 1]), int(self.points_local[i, 2])] += r[i]  # 体素赋值
            self.voxel_values_g[int(self.points_local[i, 0]), int(self.points_local[i, 1]), int(self.points_local[i, 2])] += g[i]  # 体素赋值
            self.voxel_values_b[int(self.points_local[i, 0]), int(self.points_local[i, 1]), int(self.points_local[i, 2])] += b[i]  # 体素赋值
            voxel_num[int(self.points_local[i, 0]), int(self.points_local[i, 1]), int(self.points_local[i, 2])] += 1  # 点云数量增值
        print('点云转体素已完成')
        self.points_local = self.points_local.astype(int)  # 将点云位置进行整数化
        self.points_local_un = np.unique(self.points_local, axis=0)  # 有值体素位置精简化
        self.num_voxel = len(self.points_local_un)  # 有值体素数量
        # 平均值化有值
        self.voxel_values_r = np.float16(self.voxel_values_r)
        self.voxel_values_r = self.voxel_values_r / voxel_num
        self.voxel_values_r = np.nan_to_num(self.voxel_values_r)  # nan转0
        self.voxel_values_b = np.float16(self.voxel_values_b)
        self.voxel_values_b = self.voxel_values_b / voxel_num
        self.voxel_values_b = np.nan_to_num(self.voxel_values_b)  # nan转0
        self.voxel_values_g = np.float16(self.voxel_values_g)
        self.voxel_values_g = self.voxel_values_g / voxel_num
        self.voxel_values_g = np.nan_to_num(self.voxel_values_g)  # nan转0
        print('体素赋值已完成')

    def find_newPoint_local(self, xyz_):
        '''
        查询某一批点云的所在体素的位置
        :param xyz_: 某一批点云的三维坐标
        :return: 这批点云所在的体素位置
        '''
        points_local_new = np.empty([len(xyz_), 3])  # 存储当前点云所在体素的位置
        for i in range(len(xyz_)):
            points_local_new[i, :] = np.floor(xyz_[i, :3] / self.pixel) - self.voxel_start  # 遍历点属于哪个体素
        return points_local_new

    def V2P(self, v_local_un):
        '体素转点云'
        lwd_321 = v_local_un[:, 0] * (10 ** self.VoxelLengthDigit[-2]) + v_local_un[:, 1] + v_local_un[:, 2] * (10 ** (self.VoxelLengthDigit[-1] * (-1)))
        p_lwd_321 = self.points_local[:, 0] * (10 ** self.VoxelLengthDigit[-2]) + self.points_local[:, 1] + self.points_local[:, 2] * (10 ** (self.VoxelLengthDigit[-1] * (-1)))
        points_index = np.isin(p_lwd_321, lwd_321)  # 提取点云的下标 by:Zelas
        return points_index

    def WatchVoxel_RGB(self, edges=True, dp=1):
        '显示RGB体素'
        self.points_local_un_rgb = np.empty([len(self.points_local_un), 3])  # 每个有值体素的三波段值
        for i in tqdm(range(len(self.points_local_un)), desc='赋值有值体素的特征', unit='个体素'):
            self.points_local_un_rgb[i, :] = [self.voxel_values_r[int(self.points_local_un[i, 0]), int(self.points_local_un[i, 1]), int(self.points_local_un[i, 2])], self.voxel_values_g[int(self.points_local_un[i, 0]), int(self.points_local_un[i, 1]), int(self.points_local_un[i, 2])],
                                              self.voxel_values_b[int(self.points_local_un[i, 0]), int(self.points_local_un[i, 1]), int(self.points_local_un[i, 2])]]
        voxel_8ps = Calculate8Points_mp_starmap_async(self.points_local_un, self.num_voxel, dp=dp)  # 求每个体素的8个顶点
        voxel_8ps_2D = np.reshape(voxel_8ps, (-1, 3))  # 数据降维
        cells_hex = np.arange(self.num_voxel * 8).reshape([self.num_voxel, 8])  # 顶点索引排序
        grid = pv.UnstructuredGrid({pv.CellType.HEXAHEDRON: cells_hex}, voxel_8ps_2D)  # 建立体素网格
        plotter = pv.Plotter()  # 创建绘图窗口
        plotter.background_color = 'white'  # 设置背景颜色为白色
        grid.cell_data['colors'] = self.points_local_un_rgb  # 将体素RGB传给网格体
        plotter.add_mesh(grid, scalars='colors', rgb=True, show_edges=edges, show_scalar_bar=False)  # 添加体素网格，并设置颜色映射
        plotter.show_grid(color='black', xtitle='R Axis', ytitle='C Axis', ztitle='L Axis', n_xlabels=4, n_ylabels=4, n_zlabels=4)  # 显示网格线
        plotter.show()  # 显示绘图

    def WatchVoxel(self, cmap='gray', edges=True, grid_color='black', dp=1):
        '显示笛卡尔坐标系体素'
        self.points_local_un_value = np.empty(len(self.points_local_un))  # 每个有值体素的值
        for i in range(len(self.points_local_un)):
            self.points_local_un_value[i] = self.voxel_values[int(self.points_local_un[i, 0]), int(self.points_local_un[i, 1]), int(self.points_local_un[i, 2])]
        # voxel_8ps = Calculate8Points_mp_0(self.points_local_un,self.num_voxel, dp=self.pixel)  # 求每个体素的8个顶点
        voxel_8ps = Calculate8Points_mp_0(self.points_local_un, self.num_voxel, dp=dp)  # 求每个体素的8个顶点
        voxel_8ps_2D = np.reshape(voxel_8ps, (-1, 3))  # 数据降维
        cells_hex = np.arange(self.num_voxel * 8).reshape([self.num_voxel, 8])  # 顶点索引排序
        grid = pv.UnstructuredGrid({pv.CellType.HEXAHEDRON: cells_hex}, voxel_8ps_2D)  # 建立体素网格
        # color = np.c_[self.points_local_un_value, self.points_local_un_value, self.points_local_un_value]
        # grid.plot(scalars=color, show_edges=True, cmap=cmap)  # 显示体素
        plotter = pv.Plotter()  # 创建绘图窗口
        plotter.background_color = 'white'  # 设置背景颜色为白色
        plotter.add_mesh(grid, scalars=self.points_local_un_value, show_edges=edges, cmap=cmap, show_scalar_bar=False)  # 添加体素网格，并设置颜色映射
        print('已显示体素')
        plotter.show_grid(color=grid_color, xtitle='R Axis', ytitle='C Axis', ztitle='L Axis', n_xlabels=5, n_ylabels=5, n_zlabels=5)  # 显示网格线
        # 手动添加坐标轴刻度标签
        # plotter.add_text("1", position='x', position_x=1, position_y=-1)
        plotter.show()  # 显示绘图

    def WatchVoxel_bright(self, num_L, L_un,dp=1):
        '显示笛卡尔坐标系体素(单体化显示)'
        # 颜色赋值
        colors = np.array(sns.color_palette('bright', n_colors=num_L))
        colors = np.sum(colors, axis=1)
        # colors = np.arange(1,num_L+1)
        # 对有值体素的容器进行赋值
        self.points_local_un = np.unique(self.points_local, axis=0)  # 有值体素位置精简化
        self.points_local_un_value = np.empty(len(self.points_local_un))  # 建立体素容器的值
        # self.points_local_un_colors = np.empty([len(self.points_local_un),3])  # 建立体素颜色显示容器
        self.points_local_un_colors = np.empty([len(self.points_local_un)])  # 建立体素颜色显示容器
        for i in range(len(self.points_local_un)):  # 赋值
            self.points_local_un_value[i] = self.voxel_values[int(self.points_local_un[i, 0]), int(self.points_local_un[i, 1]), int(self.points_local_un[i, 2])]
            # self.points_local_un_colors[i,:] = colors[int(self.points_local_un_value[i])==L_un,:]
            self.points_local_un_colors[i] = colors[self.points_local_un_value[i] == L_un]  # L_un = np.unique(label_points) num_L = len(L_un)
        voxel_8ps = Calculate8Points_mp_starmap_async(self.points_local_un, self.num_voxel, dp=dp)  # 求每个体素的8个顶点
        voxel_8ps_2D = np.reshape(voxel_8ps, (-1, 3))  # 数据降维
        cells_hex = np.arange(self.num_voxel * 8).reshape([self.num_voxel, 8])  # 顶点索引排序
        grid = pv.UnstructuredGrid({pv.CellType.HEXAHEDRON: cells_hex}, voxel_8ps_2D)  # 建立体素网格
        plotter = pv.Plotter()  # 创建绘图窗口
        plotter.background_color = 'white'  # 设置背景颜色为白色
        plotter.add_mesh(grid, scalars=self.points_local_un_colors, show_edges=True, cmap='tab20', show_scalar_bar=False)  # 添加体素网格，并设置颜色映射
        plotter.show()  # 显示绘图

    def WatchVoxel_Background_Monomer(self, num_L, L_un, dimidiate=256,edge=False):
        '''
        显示体素，小于阈值的显示强度值，大于等于阈值的显示单体化
        :param num_L: 单体化数量
        :param L_un: 单体化标签
        :param dimidiate: 阈值，默认256
        '''
        # 对有值体素的容器进行赋值
        self.points_local_un = np.unique(self.points_local, axis=0)  # 有值体素位置精简化
        self.points_local_un_value = np.empty(len(self.points_local_un))  # 建立体素容器的值
        for i in range(len(self.points_local_un)):  # 赋值
            self.points_local_un_value[i] = self.voxel_values[int(self.points_local_un[i, 0]), int(self.points_local_un[i, 1]), int(self.points_local_un[i, 2])]
        points_local_un_gray = self.points_local_un[self.points_local_un_value < dimidiate, :]  # 单独灰度体素位置
        points_local_un_color = self.points_local_un[self.points_local_un_value >= dimidiate, :]  # 显示单体化体素位置
        num_voxel_gray = len(points_local_un_gray)
        num_voxel_color = len(points_local_un_color)  # 两种体素数量
        plotter = pv.Plotter()  # 创建绘图窗口
        plotter.background_color = 'white'  # 设置背景颜色为白色
        # 建立普通灰度体素显示
        voxel_8ps = Calculate8Points_mp_0(points_local_un_gray, num_voxel_gray, dp=self.pixel)  # 求每个体素的8个顶点
        voxel_8ps_2D = np.reshape(voxel_8ps, (-1, 3))  # 数据降维
        cells_hex = np.arange(num_voxel_gray * 8).reshape([num_voxel_gray, 8])  # 顶点索引排序
        grid = pv.UnstructuredGrid({pv.CellType.HEXAHEDRON: cells_hex}, voxel_8ps_2D)  # 建立体素网格
        points_local_un_value_other = self.points_local_un_value[self.points_local_un_value < dimidiate]
        plotter.add_mesh(grid, scalars=points_local_un_value_other, show_edges=edge, cmap='gray', show_scalar_bar=False)  # 添加体素网格，并设置颜色映射
        # 建立单体化显示
        # 颜色赋值
        colors = np.array(sns.color_palette('bright', n_colors=num_L))
        colors = np.sum(colors, axis=1)
        # 对有值体素的容器进行赋值
        points_local_un_color_value = self.points_local_un_value[self.points_local_un_value >= dimidiate]  # 单体化特征值
        color_other = np.empty(num_voxel_color)  # 新建单体化颜色数组
        for i in range(num_voxel_color):  # 颜色赋值
            color_other[i] = colors[points_local_un_color_value[i] == L_un]
        voxel_8ps = Calculate8Points_mp_starmap_async(points_local_un_color, num_voxel_color, dp=self.pixel)  # 求每个体素的8个顶点
        voxel_8ps_2D = np.reshape(voxel_8ps, (-1, 3))  # 数据降维
        cells_hex = np.arange(num_voxel_color * 8).reshape([num_voxel_color, 8])  # 顶点索引排序
        grid = pv.UnstructuredGrid({pv.CellType.HEXAHEDRON: cells_hex}, voxel_8ps_2D)  # 建立体素网格
        plotter.add_mesh(grid, scalars=color_other, show_edges=edge, cmap='tab20', show_scalar_bar=False)  # 添加体素网格，并设置颜色映射
        plotter.show()  # 显示绘图

    def WatchVoxel_Highsingleclass(self, HLT=256,edge=False):
        '高亮显示单类体素（设置单类体素的强度值为256）'
        # 对有值体素的容器进行赋值
        self.points_local_un = np.unique(self.points_local, axis=0)  # 有值体素位置精简化
        self.points_local_un_value = np.empty(len(self.points_local_un))  # 建立体素容器的值
        for i in tqdm(range(len(self.points_local_un)),desc='重新赋值各个有值体素',unit='个'):  # 赋值
            self.points_local_un_value[i] = self.voxel_values[int(self.points_local_un[i, 0]), int(self.points_local_un[i, 1]), int(self.points_local_un[i, 2])]
        points_local_un_256 = self.points_local_un[self.points_local_un_value == HLT, :]  # 单独显示的体素位置
        points_local_un_other = self.points_local_un[self.points_local_un_value != HLT, :]  # 其他显示的体素位置
        num_voxel_256 = len(points_local_un_256)
        num_voxel_other = len(points_local_un_other)
        # 首先建立高光显示体素
        voxel_8ps = Calculate8Points_mp_0(points_local_un_256, num_voxel_256, dp=self.pixel)  # 求每个体素的8个顶点
        voxel_8ps_2D = np.reshape(voxel_8ps, (-1, 3))  # 数据降维
        cells_hex = np.arange(num_voxel_256 * 8).reshape([num_voxel_256, 8])  # 顶点索引排序
        grid = pv.UnstructuredGrid({pv.CellType.HEXAHEDRON: cells_hex}, voxel_8ps_2D)  # 建立体素网格
        # color = [255,128,0]  # 橙色RGB
        # colors = np.tile(color, (num_voxel_256, 1))  # 数组扩展
        plotter = pv.Plotter()  # 创建绘图窗口
        plotter.background_color = 'white'  # 设置背景颜色为白色
        plotter.add_mesh(grid, color='r', show_edges=edge)  # 添加体素网格，并设置颜色映射
        # 然后建立普通灰度体素显示
        voxel_8ps = Calculate8Points_mp_0(points_local_un_other, num_voxel_other, dp=self.pixel)  # 求每个体素的8个顶点
        voxel_8ps_2D = np.reshape(voxel_8ps, (-1, 3))  # 数据降维
        cells_hex = np.arange(num_voxel_other * 8).reshape([num_voxel_other, 8])  # 顶点索引排序
        grid = pv.UnstructuredGrid({pv.CellType.HEXAHEDRON: cells_hex}, voxel_8ps_2D)  # 建立体素网格
        points_local_un_value_other = self.points_local_un_value[self.points_local_un_value != HLT]
        plotter.add_mesh(grid, scalars=points_local_un_value_other, show_edges=edge, cmap='gray', show_scalar_bar=False)  # 添加体素网格，并设置颜色映射
        plotter.show()  # 显示绘图


def Calculate8Points_mp_0(points_local_un, num, dp=0.5):
    '并行计算出每个有值体素8个点的坐标（笛卡尔显示专用）'
    # 准备工作
    voxel_8ps = np.empty([num, 8, 3], dtype=np.float32)  # 存储每个容器显示的8个点
    num_cpu = mp.cpu_count()  # 线程数
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    tik = cut_down(num, num_cpu)  # 分块函数
    tik_b = 0  # 分块输出计时器
    # 并行计算
    multi_res = [pool.apply_async(Calculate8Points_Block_0, args=(points_local_un, dp, tik[i], tik[i + 1])) for i in
                 range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    for res in multi_res:
        voxel_8ps[tik[tik_b]:tik[tik_b + 1], :, :] = res.get()  # 将每个进程得到的结果分block的发送到容器当中
        tik_b += 1
    # 后续处理
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    return voxel_8ps


def Calculate8Points_mp_starmap_async(points_local_un, num, dp=0.5):
    '基于starmap_async并行计算每个有值体素8个点的坐标（笛卡尔显示专用）'
    # 准备工作
    voxel_8ps = np.empty([num, 8, 3], dtype=np.float32)  # 存储每个容器显示的8个点
    num_cpu = mp.cpu_count()  # 线程数
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    # 并行计算
    multi_res = pool.starmap_async(Calculate8Points_, ((points_local_un[i, :], dp) for i in
                                                       tqdm(range(num), desc='分配任务计算单个体素包围盒', unit='个有值体素', total=num)))
    j = 0
    for res in tqdm(multi_res.get(), total=num, desc='导出单个体素包围盒', unit='个有值体素'):
        voxel_8ps[j, :] = res
        j += 1
    pool.close()  # 关闭所有进程
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    return voxel_8ps


def Calculate8Points_(points_local_un, dp):
    '计算一个有值体素的包围盒'
    voxel_8ps_ = np.empty([8, 3], dtype=np.float32)  # 分块容器
    voxel_8ps_[:4, 2] = dp * points_local_un[2]
    voxel_8ps_[4:, 2] = dp * (points_local_un[2] + 1)
    # 求x范围
    voxel_8ps_[0, 0] = voxel_8ps_[4, 0] = voxel_8ps_[1, 0] = voxel_8ps_[5, 0] = dp * points_local_un[0]
    voxel_8ps_[2, 0] = voxel_8ps_[6, 0] = voxel_8ps_[3, 0] = voxel_8ps_[7, 0] = dp * (points_local_un[0] + 1)
    # 求y范围
    voxel_8ps_[0, 1] = voxel_8ps_[4, 1] = voxel_8ps_[3, 1] = voxel_8ps_[7, 1] = dp * points_local_un[1]
    voxel_8ps_[1, 1] = voxel_8ps_[5, 1] = voxel_8ps_[2, 1] = voxel_8ps_[6, 1] = dp * (points_local_un[1] + 1)
    return voxel_8ps_


def Calculate8Points_Block_0(points_local_un, dp, tik, tok):
    '分块计算出每个有值体素8个点的坐标（笛卡尔显示专用）'
    num_ = tok - tik  # 每个block的处理数量
    j = 0  # 循环计数器
    voxel_8ps_ = np.empty([num_, 8, 3], dtype=np.float32)  # 分块容器
    for j in range(num_):
        # 求z范围
        voxel_8ps_[j, :4, 2] = dp * points_local_un[tik + j, 2]
        voxel_8ps_[j, 4:, 2] = dp * (points_local_un[tik + j, 2] + 1)
        # 求x范围
        voxel_8ps_[j, 0, 0] = voxel_8ps_[j, 4, 0] = voxel_8ps_[j, 1, 0] = voxel_8ps_[j, 5, 0] = dp * points_local_un[tik + j, 0]
        voxel_8ps_[j, 2, 0] = voxel_8ps_[j, 6, 0] = voxel_8ps_[j, 3, 0] = voxel_8ps_[j, 7, 0] = dp * (points_local_un[tik + j, 0] + 1)
        # 求y范围
        voxel_8ps_[j, 0, 1] = voxel_8ps_[j, 4, 1] = voxel_8ps_[j, 3, 1] = voxel_8ps_[j, 7, 1] = dp * points_local_un[tik + j, 1]
        voxel_8ps_[j, 1, 1] = voxel_8ps_[j, 5, 1] = voxel_8ps_[j, 2, 1] = voxel_8ps_[j, 6, 1] = dp * (points_local_un[tik + j, 1] + 1)
        # 刷新计数器
        j += 1
    print('已完成第', tik, '至第', tok, '的有值体素')
    return voxel_8ps_


# 求点云的平面密度
def num_area(num, area):
    return num / area


# 求面积（平面面积以及侧面积）
def get_area(xy):
    hull = spt.ConvexHull(points=xy, incremental=False)  # 求凸壳
    ID = hull.vertices  # 返回凸壳的边缘点号
    polygon = xy[ID, :]  # 求凸壳数组
    area = Polygon(polygon).area  # 求多边形面积
    return area


def nei_26_mp(id_point, num_v, binary, cpu=mp.cpu_count()):
    '''
    并行计算体素的26邻域有值体素函数
    :param id_point: 点云所在体素位置数组 numpy[数量，3]
    :param num_v: 体素长宽高 numpy[1,3]
    :param binary: 三维体素 voxel.voxel_values numpy[长，宽，高]
    :param cpu: 并行计算分块数，默认为cpu的最大物理线程数 Int
    :return: 每个体素的周围26邻域中的有值体素位置 嵌套数组，参考voxel.voxel_nei
    '''
    # 函数准备
    num = len(id_point)
    tik = cut_down(num, cpu)  # 计算每个块的起止点
    a = [0 for x in range(num)]
    j = 0  # 分块输出计数器
    pool = mp.Pool(processes=cpu)  # 开启多进程池，数量为cpu
    # 并行处理
    multi_res = [pool.apply_async(nei_26, args=(id_point[tik[i]:tik[i + 1], :], num_v, binary)) for i in
                 range(cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    for res in multi_res:
        a[tik[j]:tik[j + 1]] = res.get()  # 将每个进程得到的结果分block的发送到容器当中
        j += 1
        print('已完成进度', j, '/', cpu)
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    return a


def nei_26(id_point, num_v, binary):
    '''
    # 非并行26邻域有值体素搜索函数
    :param id_point: 点云所在体素位置数组
    :param num_v: 体素长宽高
    :param binary: 三维体素
    :return: 每个体素的周围26邻域中的有值体素位置
    '''
    a = []  # 符合条件的邻域存储容器
    num = len(id_point)  # 输入点的数量
    min_n = 0
    for i in range(num):
        x = id_point[i, 0]
        y = id_point[i, 1]
        z = id_point[i, 2]  # 点云所在体素下标
        # 求此体素26邻域
        neighbour = [[x + 1, y, z], [x, y + 1, z], [x - 1, y, z], [x, y - 1, z], [x, y, z - 1], [x, y, z + 1],
                     [x + 1, y + 1, z], [x - 1, y + 1, z], [x - 1, y - 1, z], [x + 1, y - 1, z], [x + 1, y, z + 1],
                     [x, y + 1, z + 1], [x - 1, y, z - 1], [x, y - 1, z - 1], [x, y + 1, z - 1], [x, y - 1, z + 1],
                     [x + 1, y, z - 1], [x - 1, y, z + 1], [x + 1, y + 1, z + 1], [x - 1, y - 1, z - 1],
                     [x - 1, y + 1, z + 1], [x + 1, y - 1, z + 1], [x + 1, y + 1, z - 1], [x - 1, y - 1, z + 1],
                     [x - 1, y + 1, z - 1], [x + 1, y - 1, z - 1]]  # size=list
        '''
        # 求此体素的80邻域
        neighbour = [[x + 1, y, z], [x, y + 1, z], [x - 1, y, z], [x, y - 1, z], [x, y, z - 1], [x, y, z + 1],
                         [x + 1, y + 1, z], [x + 1, y, z + 1], [x, y + 1, z + 1], [x - 1, y - 1, z], [x - 1, y, z - 1],
                         [x, y - 1, z - 1], [x + 1, y + 1, z + 1], [x - 1, y - 1, z - 1], [x - 1, y + 1, z + 1],
                         [x + 1, y - 1, z + 1], [x + 1, y + 1, z - 1], [x - 1, y - 1, z + 1], [x - 1, y + 1, z - 1],
                         [x + 1, y - 1, z - 1], [x + 1, y - 1, z], [x - 1, y + 1, z], [x + 1, y, z - 1],
                         [x - 1, y, z + 1],
                         [x, y + 1, z - 1], [x, y - 1, z + 1], [x + 2, y, z], [x + 2, y + 1, z], [x + 2, y - 1, z],
                         [x + 2, y, z + 1], [x + 2, y, z - 1], [x - 2, y, z], [x - 2, y + 1, z], [x - 2, y - 1, z],
                         [x - 2, y, z + 1], [x - 2, y, z - 1], [x, y + 2, z], [x + 1, y + 2, z], [x - 1, y + 2, z],
                         [x, y + 2, z + 1], [x, y + 2, z - 1], [x, y - 2, z], [x + 1, y - 2, z], [x - 1, y - 2, z],
                         [x, y - 2, z + 1], [x, y - 2, z - 1], [x, y, z + 2], [x + 1, y, z + 2], [x - 1, y, z + 2],
                         [x, y + 1, z + 2], [x, y - 1, z + 2], [x, y, z - 2], [x + 1, y, z - 2], [x - 1, y, z - 2],
                         [x, y + 1, z - 2], [x, y - 1, z - 2], [x - 1, y - 1, z + 2], [x - 1, y - 1, z - 2],
                         [x - 1, y + 1, z + 2], [x - 1, y + 1, z - 2], [x + 1, y - 1, z + 2], [x + 1, y - 1, z - 2],
                         [x + 1, y + 1, z + 2], [x + 1, y + 1, z - 2], [x - 1, y - 2, z + 1], [x - 1, y - 2, z - 1],
                         [x + 1, y - 2, z + 1], [x + 1, y - 2, z - 1], [x - 1, y + 2, z + 1], [x - 1, y + 2, z - 1],
                         [x + 1, y + 2, z + 1], [x + 1, y + 2, z - 1], [x - 2, y - 1, z + 1], [x - 2, y - 1, z - 1],
                         [x - 2, y + 1, z + 1], [x - 2, y + 1, z - 1],
                         [x + 2, y - 1, z + 1], [x + 2, y - 1, z - 1], [x + 2, y + 1, z + 1], [x + 2, y + 1, z - 1]]
        '''
        neighbour = np.array(neighbour)  # 类型转换 list->numpy
        # 限制条件太少，找到的最邻近太多太多了(解决验证中）
        neighbour = neighbour[neighbour[:, 0] < num_v[0]]
        neighbour = neighbour[neighbour[:, 0] >= min_n]
        neighbour = neighbour[neighbour[:, 1] < num_v[1]]
        neighbour = neighbour[neighbour[:, 1] >= min_n]
        neighbour = neighbour[neighbour[:, 2] < num_v[2]]
        # neighbour = neighbour[neighbour[:, 2] >= min_n]
        for j in range(len(neighbour)):  # binary(neighbour(1,r),neighbour(2,r),neighbour(3,r))~=0
            b_x = int(neighbour[j, 0])
            b_y = int(neighbour[j, 1])
            b_z = int(neighbour[j, 2])
            if binary[b_x, b_y, b_z] == 0:
                neighbour[j, :] = [-1, -1, -1]
        neighbour = neighbour[neighbour[:, 2] >= min_n]
        a.append(neighbour)
    return a

def Nei_12(x,y,z):
    '适配纵缝提取的12邻域'
    neighbour = np.array([[x,y+1,z],[x,y-1,z],[x-1,y-1,z],[x-2,y-1,z],[x-1,y,z],[x-2,y,z],[x-1,y+1,z],[x-2,y+1,z],[x-4, y+1, z], [x-5, y+1, z],[x-4, y-1, z], [x-5, y-1, z]])
    return neighbour

def Nei_6(x, y, z):
    '6邻域数组函数'
    neighbour = np.array([[x + 1, y, z], [x, y + 1, z], [x - 1, y, z], [x, y - 1, z], [x, y, z - 1], [x, y, z + 1]])
    return neighbour


def Nei_14(x, y, z):
    '14邻域数组函数'
    neighbour = np.array([[x + 1, y, z], [x, y + 1, z], [x - 1, y, z]
                             , [x, y - 1, z], [x, y, z - 1], [x, y, z + 1]
                             , [x - 1, y + 1, z], [x - 1, y - 1, z], [x + 1, y - 1, z]
                             , [x - 1, y, z - 1], [x - 1, y, z - 1], [x, y - 1, z - 1], [x, y + 1, z - 1], [x + 1, y, z - 1]])
    return neighbour


def Nei_18(x, y, z):
    '18邻域数组函数'
    neighbour = np.array([[x + 1, y, z], [x, y + 1, z], [x - 1, y, z], [x, y - 1, z], [x, y, z - 1], [x, y, z + 1], [x + 1, y + 1, z], [x - 1, y + 1, z], [x - 1, y - 1, z], [x + 1, y - 1, z], [x + 1, y, z + 1],
                          [x, y + 1, z + 1], [x - 1, y, z - 1], [x, y - 1, z - 1], [x, y + 1, z - 1], [x, y - 1, z + 1],
                          [x + 1, y, z - 1], [x - 1, y, z + 1]])
    return neighbour


def Nei_26(x, y, z):
    '26邻域数组函数'
    neighbour = np.array([[x + 1, y, z], [x, y + 1, z], [x - 1, y, z], [x, y - 1, z], [x, y, z - 1], [x, y, z + 1],
                          [x + 1, y + 1, z], [x - 1, y + 1, z], [x - 1, y - 1, z], [x + 1, y - 1, z], [x + 1, y, z + 1],
                          [x, y + 1, z + 1], [x - 1, y, z - 1], [x, y - 1, z - 1], [x, y + 1, z - 1], [x, y - 1, z + 1],
                          [x + 1, y, z - 1], [x - 1, y, z + 1], [x + 1, y + 1, z + 1], [x - 1, y - 1, z - 1],
                          [x - 1, y + 1, z + 1], [x + 1, y - 1, z + 1], [x + 1, y + 1, z - 1], [x - 1, y - 1, z + 1],
                          [x - 1, y + 1, z - 1], [x + 1, y - 1, z - 1]])
    return neighbour


def Nei_56(x, y, z):
    '56邻域数组函数'
    neighbour = np.array([[x + 1, y, z], [x, y + 1, z], [x - 1, y, z], [x, y - 1, z], [x, y, z - 1], [x, y, z + 1],
                          [x + 1, y + 1, z], [x - 1, y + 1, z], [x - 1, y - 1, z], [x + 1, y - 1, z], [x + 1, y, z + 1],
                          [x, y + 1, z + 1], [x - 1, y, z - 1], [x, y - 1, z - 1], [x, y + 1, z - 1], [x, y - 1, z + 1],
                          [x + 1, y, z - 1], [x - 1, y, z + 1], [x + 1, y + 1, z + 1], [x - 1, y - 1, z - 1],
                          [x - 1, y + 1, z + 1], [x + 1, y - 1, z + 1], [x + 1, y + 1, z - 1], [x - 1, y - 1, z + 1],
                          [x - 1, y + 1, z - 1], [x + 1, y - 1, z - 1], [x, y, z - 2], [x + 1, y, z - 2], [x, y + 1, z - 2], [x - 1, y, z - 2], [x, y - 1, z - 2], [x, y, z - 2], [x + 1, y, z - 2], [x, y + 1, z - 2], [x - 1, y, z - 2], [x, y - 1, z - 2],
                          [x - 2, y, z], [x - 2, y + 1, z], [x - 2, y - 1, z], [x - 2, y, z + 1], [x - 2, y, z - 1], [x, y - 2, z], [x - 1, y - 2, z], [x + 1, y - 2, z], [x, y - 2, z + 1], [x, y - 2, z - 1],
                          [x, y, z + 2], [x + 1, y, z + 2], [x, y + 1, z + 2], [x - 1, y, z + 2], [x, y - 1, z + 2], [x, y, z - 2], [x + 1, y, z - 2], [x, y + 1, z - 2], [x - 1, y, z - 2], [x, y - 1, z - 2],
                          [x + 2, y, z], [x + 2, y + 1, z], [x + 2, y - 1, z], [x + 2, y, z + 1], [x + 2, y, z - 1], [x, y + 2, z], [x - 1, y + 2, z], [x + 1, y + 2, z], [x, y + 2, z + 1], [x, y + 2, z - 1]
                          ])
    return neighbour


def Nei_80(x, y, z):
    '80邻域数组函数'
    neighbour = np.array([[x + 1, y, z], [x, y + 1, z], [x - 1, y, z], [x, y - 1, z], [x, y, z - 1], [x, y, z + 1], [x + 1, y + 1, z], [x + 1, y, z + 1], [x, y + 1, z + 1], [x - 1, y - 1, z], [x - 1, y, z - 1], [x, y - 1, z - 1], [
        x + 1, y + 1, z + 1], [x - 1, y - 1, z - 1], [x - 1, y + 1, z + 1], [x + 1, y - 1, z + 1], [x + 1, y + 1, z - 1], [x - 1, y - 1, z + 1], [x - 1, y + 1, z - 1], [x + 1, y - 1, z - 1], [x + 1, y - 1, z], [x - 1, y + 1, z], [x + 1, y, z - 1], [x - 1, y, z + 1], [
                              x, y + 1, z - 1], [x, y - 1, z + 1], [x + 2, y, z], [x + 2, y + 1, z], [x + 2, y - 1, z], [x + 2, y, z + 1], [x + 2, y, z - 1], [x - 2, y, z], [x - 2, y + 1, z], [x - 2, y - 1, z], [x - 2, y, z + 1], [x - 2, y, z - 1], [
                              x, y + 2, z], [x + 1, y + 2, z], [x - 1, y + 2, z], [x, y + 2, z + 1], [x, y + 2, z - 1], [x, y - 2, z], [x + 1, y - 2, z], [x - 1, y - 2, z], [x, y - 2, z + 1], [x, y - 2, z - 1], [
                              x, y, z + 2], [x + 1, y, z + 2], [x - 1, y, z + 2], [x, y + 1, z + 2], [x, y - 1, z + 2], [x, y, z - 2], [x + 1, y, z - 2], [x - 1, y, z - 2], [x, y + 1, z - 2], [x, y - 1, z - 2], [
                              x - 1, y - 1, z + 2], [x - 1, y - 1, z - 2], [x - 1, y + 1, z + 2], [x - 1, y + 1, z - 2], [x + 1, y - 1, z + 2], [x + 1, y - 1, z - 2], [x + 1, y + 1, z + 2], [x + 1, y + 1, z - 2], [x - 1, y - 2, z + 1], [x - 1, y - 2, z - 1], [
                              x + 1, y - 2, z + 1], [x + 1, y - 2, z - 1], [x - 1, y + 2, z + 1], [x - 1, y + 2, z - 1], [x + 1, y + 2, z + 1], [x + 1, y + 2, z - 1], [x - 2, y - 1, z + 1], [x - 2, y - 1, z - 1], [x - 2, y + 1, z + 1], [x - 2, y + 1, z - 1], [
                              x + 2, y - 1, z + 1], [x + 2, y - 1, z - 1], [x + 2, y + 1, z + 1], [x + 2, y + 1, z - 1]])
    return neighbour


def Nei_124(x, y, z):
    '124邻域数组函数'
    neighbour = np.array(
        [[x, y + 1, z], [x, y + 2, z], [x, y - 1, z], [x, y - 2, z], [x + 1, y + 1, z], [x + 1, y + 2, z], [x + 1, y - 1, z], [x + 1, y - 2, z], [x + 1, y, z], [x + 2, y + 1, z], [x + 2, y + 2, z], [x + 2, y - 1, z], [x + 2, y - 2, z], [x + 2, y, z], [x - 1, y + 1, z], [x - 1, y + 2, z],
         [x - 1, y - 1, z], [x - 1, y - 2, z], [x - 1, y, z], [x - 2, y + 1, z], [x - 2, y + 2, z], [x - 2, y - 1, z], [x - 2, y - 2, z], [x - 2, y, z], [
             x, y + 1, z + 1], [x, y + 2, z + 1], [x, y - 1, z + 1], [x, y - 2, z + 1], [x + 1, y + 1, z + 1], [x + 1, y + 2, z + 1], [x + 1, y - 1, z + 1], [x + 1, y - 2, z + 1], [x + 1, y, z + 1], [x + 2, y + 1, z + 1], [x + 2, y + 2, z + 1], [x + 2, y - 1, z + 1], [x + 2, y - 2, z + 1],
         [x + 2, y, z + 1], [x - 1, y + 1, z + 1], [x - 1, y + 2, z + 1], [x - 1, y - 1, z + 1], [x - 1, y - 2, z + 1], [x - 1, y, z + 1], [x - 2, y + 1, z + 1], [x - 2, y + 2, z + 1], [x - 2, y - 1, z + 1], [x - 2, y - 2, z + 1], [x - 2, y, z + 1], [
             x, y + 1, z + 2], [x, y + 2, z + 2], [x, y - 1, z + 2], [x, y - 2, z + 2], [x + 1, y + 1, z + 2], [x + 1, y + 2, z + 2], [x + 1, y - 1, z + 2], [x + 1, y - 2, z + 2], [x + 1, y, z + 2], [x + 2, y + 1, z + 2], [x + 2, y + 2, z + 2], [x + 2, y - 1, z + 2], [x + 2, y - 2, z + 2],
         [x + 2, y, z + 2], [x - 1, y + 1, z + 2], [x - 1, y + 2, z + 2], [x - 1, y - 1, z + 2], [x - 1, y - 2, z + 2], [x - 1, y, z + 2], [x - 2, y + 1, z + 2], [x - 2, y + 2, z + 2], [x - 2, y - 1, z + 2], [x - 2, y - 2, z + 2], [x - 2, y, z + 2], [
             x, y + 1, z - 1], [x, y + 2, z - 1], [x, y - 1, z - 1], [x, y - 2, z - 1], [x + 1, y + 1, z - 1], [x + 1, y + 2, z - 1], [x + 1, y - 1, z - 1], [x + 1, y - 2, z - 1], [x + 1, y, z - 1], [x + 2, y + 1, z - 1], [x + 2, y + 2, z - 1], [x + 2, y - 1, z - 1], [x + 2, y - 2, z - 1],
         [x + 2, y, z - 1], [x - 1, y + 1, z - 1], [x - 1, y + 2, z - 1], [x - 1, y - 1, z - 1], [x - 1, y - 2, z - 1], [x - 1, y, z - 1], [x - 2, y + 1, z - 1], [x - 2, y + 2, z - 1], [x - 2, y - 1, z - 1], [x - 2, y - 2, z - 1], [x - 2, y, z - 1], [
             x, y + 1, z - 2], [x, y + 2, z - 2], [x, y - 1, z - 2], [x, y - 2, z - 2], [x + 1, y + 1, z - 2], [x + 1, y + 2, z - 2], [x + 1, y - 1, z - 2], [x + 1, y - 2, z - 2], [x + 1, y, z - 2], [x + 2, y + 1, z - 2], [x + 2, y + 2, z - 2], [x + 2, y - 1, z - 2], [x + 2, y - 2, z - 2],
         [x + 2, y, z - 2], [x - 1, y + 1, z - 2], [x - 1, y + 2, z - 2], [x - 1, y - 1, z - 2], [x - 1, y - 2, z - 2], [x - 1, y, z - 2], [x - 2, y + 1, z - 2], [x - 2, y + 2, z - 2], [x - 2, y - 1, z - 2], [x - 2, y - 2, z - 2], [x - 2, y, z - 2], [
             x, y, z + 1], [x, y, z + 2], [x, y, z - 1], [x, y, z - 2]])
    return neighbour


def FindNeiLabels(points_local_un, binary, VoxelLengthDigit, points_local, num_Nei=26):
    """
    区域增长划定连通的体素标签
    :param points_local_un:所有有值体素的位置
    :param binary:三维体素
    :param VoxelLengthDigit:体素长宽高位数
    :param points_local:体素中每个点云在体素上的位置
    :param num_Nei:搜索的邻域数量，默认为26，实际上可以挑选6/26/128邻域等
    :return:
    """
    '1.寻找每个体素的有效邻域体素'
    # 准备工作
    un_321 = points_local_un[:, 0] * (10 ** VoxelLengthDigit[-2]) + points_local_un[:, 1] + points_local_un[:, 2] * (10 ** (VoxelLengthDigit[-1] * (-1)))  # 有值体素标签
    limit_box = np.array(binary.shape)  # 给出默认体素尺寸限制
    # 先找points_local_un的6/18/26/56/80/128邻域
    FunName_FindNei = 'Nei_' + str(num_Nei)  # 函数名
    FindNei = globals()[FunName_FindNei]  # 使用 globals() 函数获取函数引用
    num_un = len(points_local_un)  # 有值体素数量
    a = []  # 有值体素的26邻域嵌套数组
    for i in range(num_un):
        print('当前体素', i)
        x = points_local_un[i, 0]
        y = points_local_un[i, 1]
        z = points_local_un[i, 2]  # 遍历到当前体素位置
        neighbour = FindNei(x, y, z)  # 函数引用-求邻域
        # 找到“正常”的邻域
        neighbour = neighbour[neighbour[:, 0] < limit_box[0]]
        neighbour = neighbour[neighbour[:, 0] >= 0]
        neighbour = neighbour[neighbour[:, 1] < limit_box[1]]
        neighbour = neighbour[neighbour[:, 1] >= 0]
        neighbour = neighbour[neighbour[:, 2] < limit_box[2]]
        neighbour = neighbour[neighbour[:, 2] >= 0]
        # 清除无值邻域
        for j in range(len(neighbour)):  # binary(neighbour(1,r),neighbour(2,r),neighbour(3,r))~=0
            print('当前邻域', j)
            b_x = int(neighbour[j, 0])
            b_y = int(neighbour[j, 1])
            b_z = int(neighbour[j, 2])
            if binary[b_x, b_y, b_z] == 0:
                neighbour[j, :] = [-1, -1, -1]
        neighbour = neighbour[neighbour[:, 2] >= 0]
        a.append(neighbour)
    '2.各类别区域增长划分标签'
    labels = np.zeros(num_un)  # 建立空标签数组  默认为0
    arange_ = np.arange(num_un)  # 随机挑选一个有值体素
    label_ = 1  # 标签自增工具
    for i in range(num_un):  # 对每个有值体素进行遍历
        if labels[i] == 0:  # 如果没有标签记录
            labels[i] = label_  # 给一个起始便签
            vessel = a[i]  # 新便签起始邻域
            '''
            i_ = binary[points_local_un[i, 0], points_local_un[i, 1], points_local_un[i, 2]]  # 当前体素特征值
            # 读取此区域特征值范围  (后续可以修改)
            classes_ = np.argmin(np.absolute(binary_limit[:, 0] - i_))  # 判断属于哪类
            i_max_ = binary_limit[classes_, 0] + binary_limit[classes_, 1] * n
            i_min_ = binary_limit[classes_, 0] - binary_limit[classes_, 1] * n  # 最大最小特征阈值
            '''
            while len(vessel) > 0:  # 当还有没处理的邻域时
                v_321_0_ = vessel[0, 0] * (10 ** VoxelLengthDigit[-2]) + vessel[0, 1] + vessel[0, 2] * (10 ** (VoxelLengthDigit[-1] * (-1)))  # 容器开始的标签
                index_ = np.isin(un_321, v_321_0_)  # 所在的un下标
                # if labels[index_] == 0 and i_min_ <= binary[vessel[0, 0], vessel[0, 1], vessel[0, 2]] <= i_max_:  # 如果是没分类的体素并且特征值合适
                if labels[index_] == 0:  # 如果是没分类的体素
                    index_ = int(arange_[index_])  # 当前邻域容器的下标
                    vessel = np.vstack([vessel, a[index_]])  # 增加容器
                    labels[index_] = label_  # 赋予便签
                vessel = np.delete(vessel, 0, axis=0)  # 删除已用的邻域
                print('总进度', np.round(i / num_un, 2), '标签', label_, '剩余待处理体素', len(vessel))
            label_ += 1  # 标签增加
    '3：体素标签转所有点云标签'
    # 单个点在un上的位置，然后将标签赋值
    p_lwd_321 = points_local[:, 0] * (10 ** VoxelLengthDigit[-2]) + points_local[:, 1] + points_local[:, 2] * (10 ** (VoxelLengthDigit[-1] * (-1)))  # 点在体素坐标的匹配标签
    labels_points = np.empty(len(p_lwd_321))  # 每个点云的标签容器
    for i in range(len(p_lwd_321)):  # 遍历点云
        labels_points[i] = labels[np.where(un_321 == p_lwd_321[i])]  # 对每个点云赋值标签
    return labels, labels_points  # 返回每个体素的标签和每个点云的标签


def FindZFvoxel(points_local_un, binary, VoxelLengthDigit, num_Nei=26):
    '搜索径向接缝体素'
    # 寻找每个体素有效的邻域体素
    # 准备工作
    un_321 = points_local_un[:, 0] * (10 ** VoxelLengthDigit[-2]) + points_local_un[:, 1] + points_local_un[:, 2] * (10 ** (VoxelLengthDigit[-1] * (-1)))  # 有值体素标签
    limit_box = np.array(binary.shape)  # 给出默认体素尺寸限制
    # 先找points_local_un的6/18/26/56/80/128邻域
    FunName_FindNei = 'Nei_' + str(num_Nei)  # 函数名
    FindNei = globals()[FunName_FindNei]  # 使用 globals() 函数获取函数引用
    num_un = len(points_local_un)  # 有值体素数量
    a = []  # 有值体素的8邻域嵌套数组
    for i in range(num_un):
        # print('当前体素', i)
        x = points_local_un[i, 0]
        y = points_local_un[i, 1]
        z = points_local_un[i, 2]  # 遍历到当前体素位置
        neighbour = FindNei(x, y, z)  # 函数引用-求邻域
        # 找到“正常”的邻域
        neighbour = neighbour[neighbour[:, 0] < limit_box[0]]
        neighbour = neighbour[neighbour[:, 0] >= 0]
        neighbour = neighbour[neighbour[:, 1] < limit_box[1]]
        neighbour = neighbour[neighbour[:, 1] >= 0]
        neighbour = neighbour[neighbour[:, 2] < limit_box[2]]
        neighbour = neighbour[neighbour[:, 2] >= 0]
        # 清除无值邻域
        for j in range(len(neighbour)):  # binary(neighbour(1,r),neighbour(2,r),neighbour(3,r))~=0
            print('当前邻域', j)
            b_x = int(neighbour[j, 0])
            b_y = int(neighbour[j, 1])
            b_z = int(neighbour[j, 2])
            if binary[b_x, b_y, b_z] == 0:
                neighbour[j, :] = [-1, -1, -1]
        neighbour = neighbour[neighbour[:, 2] >= 0]
        # 判断是否是凸起型体素 左右体素是否有下沉体素  (可以将交错缝提取出来,4*5)
        if y-1 >= 0 and binary[x, y - 1, z] > 0 and y+1 < limit_box[1] and binary[x, y + 1, z] == 0:
            if x - 4 >= 0 and binary[x - 3, y - 1, z] * binary[x - 4, y - 1, z] > 0:
                a.append(neighbour)
                print('a+:',neighbour)
        elif y-1 >= 0 and binary[x, y - 1, z] == 0 and y+1 < limit_box[1] and binary[x, y + 1, z] > 0:
            if x - 4 >= 0 and binary[x - 3, y + 1, z] * binary[x - 4, y + 1, z] > 0:
                a.append(neighbour)
                print('a+:', neighbour)
    return np.unique(np.vstack(a),axis=0)


def find_subarray_rows(big_array, small_array):
  """
  判断大二维数组中是否存在包含小二维数组所有行的子数组，其中大小数组都是三列。

  Args:
    big_array: 大二维数组，三列。
    small_array: 小二维数组，三列。

  Returns:
    如果大二维数组中存在包含小二维数组所有行的子数组，则返回 True，否则返回 False。
  """
  for i in range(big_array.shape[0] - small_array.shape[0] + 1):
    if np.array_equal(big_array[i:i + small_array.shape[0]], small_array):
      return True
  return False


def FindConnectedSeed(seed_voxel_local, points_local_un, binary, VoxelLengthDigit, points_local, num_Nei=26):
    '''
    基于种子体素连通区域增长
    :param seed_voxel_local: 种子体素位置
    :param points_local_un:所有有值体素的位置
    :param binary: 三维体素
    :param VoxelLengthDigit: 体素长宽高位数
    :param points_local: 体素中每个点云在体素上的位置
    :param num_Nei: 搜索的邻域数量，默认为26，实际上可以挑选6/18/26/128邻域等
    :return: 每个体素的标签和每个点云的标签，其中0为无用位置
    '''
    '1.寻找每个体素的有效邻域体素'
    # 先找points_local_un的6/18/26/56/80/128邻域
    limit_box = np.array(binary.shape)  # 给出默认体素尺寸限制
    FunName_FindNei = 'Nei_' + str(num_Nei)  # 函数名
    FindNei = globals()[FunName_FindNei]  # 使用 globals() 函数获取函数引用
    num_un = len(points_local_un)  # 有值体素数量
    a = []  # 有值体素的邻域嵌套数组
    for i in range(num_un):
        print('当前体素', i)
        x = points_local_un[i, 0]
        y = points_local_un[i, 1]
        z = points_local_un[i, 2]  # 遍历到当前体素位置
        neighbour = FindNei(x, y, z)  # 函数引用-求邻域
        # 找到“正常”的邻域
        neighbour = neighbour[neighbour[:, 0] < limit_box[0]]
        neighbour = neighbour[neighbour[:, 0] >= 0]
        neighbour = neighbour[neighbour[:, 1] < limit_box[1]]
        neighbour = neighbour[neighbour[:, 1] >= 0]
        neighbour = neighbour[neighbour[:, 2] < limit_box[2]]
        neighbour = neighbour[neighbour[:, 2] >= 0]
        # 清除无值邻域
        for j in range(len(neighbour)):  # binary(neighbour(1,r),neighbour(2,r),neighbour(3,r))~=0
            print('当前邻域', j)
            b_x = int(neighbour[j, 0])
            b_y = int(neighbour[j, 1])
            b_z = int(neighbour[j, 2])
            if binary[b_x, b_y, b_z] == 0:
                neighbour[j, :] = [-1, -1, -1]
        neighbour = neighbour[neighbour[:, 2] >= 0]
        a.append(neighbour)
    '2:种子体素区域增长并划分标签'
    labels = np.zeros(num_un)  # 建立空标签数组  默认为0
    arange_ = np.arange(num_un)  # 自增标签
    label_ = 1  # 标签自增工具
    num_seed = len(seed_voxel_local)  # 种子体素数量
    seed_321 = seed_voxel_local[:, 0] * (10 ** VoxelLengthDigit[-2]) + seed_voxel_local[:, 1] + seed_voxel_local[:, 2] * (10 ** (VoxelLengthDigit[-1] * (-1)))  # 种子体素标签
    un_321 = points_local_un[:, 0] * (10 ** VoxelLengthDigit[-2]) + points_local_un[:, 1] + points_local_un[:, 2] * (10 ** (VoxelLengthDigit[-1] * (-1)))  # 有值体素标签
    for i in range(num_seed):  # 对种子点进行循环
        seed_321_ = seed_321[i]  # 当前种子体素下标
        # ind = np.isin(un_321,seed_321)  # 当前种子体素下标
        ind = np.where(np.isin(un_321, seed_321_))[0]  # 当前种子体素下标
        if labels[ind] == 0:  # 如果还没有给标签
            labels[ind] = label_  # 给一个起始便签
            vessel = a[ind[0]]  # 新便签起始邻域
            while len(vessel) > 0:  # 种子体素还有邻域时
                v_321_0_ = vessel[0, 0] * (10 ** VoxelLengthDigit[-2]) + vessel[0, 1] + vessel[0, 2] * (10 ** (VoxelLengthDigit[-1] * (-1)))  # 容器开始的标签
                index_ = np.isin(un_321, v_321_0_)  # 所在的un下标
                if labels[index_] == 0:  # 如果是没分类的体素
                    index_ = int(arange_[index_])  # 当前邻域容器的下标
                    vessel = np.vstack([vessel, a[index_]])  # 增加容器
                    labels[index_] = label_  # 赋予便签
                vessel = np.delete(vessel, 0, axis=0)  # 删除已用的邻域
                print('总进度', np.round(i / num_seed, 2), '标签', label_, '剩余待处理体素', len(vessel))
            label_ += 1  # 标签增加
    '3：体素标签转所有点云标签'
    p_lwd_321 = points_local[:, 0] * (10 ** VoxelLengthDigit[-2]) + points_local[:, 1] + points_local[:, 2] * (10 ** (VoxelLengthDigit[-1] * (-1)))  # 点在体素坐标的匹配标签
    labels_points = np.empty(len(p_lwd_321))  # 每个点云的标签容器
    for i in range(len(p_lwd_321)):  # 遍历点云
        labels_points[i] = labels[np.where(un_321 == p_lwd_321[i])]  # 对每个点云赋值标签
    return labels, labels_points  # 返回每个体素的标签和每个点云的标签


def FindNeiSameLabel(points_local_un, binary, VoxelLengthDigit, binary_limit, points_local, limit_box=None):
    '''区域增长划定相同的体素标签
    :param points_local: 体素中每个点云在体素上的位置
    :param binary_limit: 每个类别的特征值限制数组 [特征均值_i,特征方差_i]*n ,i=1:n
    :param points_local_un: 所有有值体素的位置
    :param binary: 三维体素
    :param VoxelLengthDigit：体素长宽高位数
    :param limit_box: 体素空间限制要求
    返回每个有值体素的所在标签
    '''
    '1.寻找每个体素的有效邻域体素'
    # 准备工作
    un_321 = points_local_un[:, 0] * (10 ** VoxelLengthDigit[-2]) + points_local_un[:, 1] + points_local_un[:, 2] * (10 ** (VoxelLengthDigit[-1] * (-1)))  # 有值体素标签
    if limit_box is None:
        limit_box = np.array(binary.shape)  # 给出默认体素尺寸限制
    # 先找points_local_un的26邻域
    num_un = len(points_local_un)  # 有值体素数量
    a = []  # 有值体素的26邻域嵌套数组
    for i in range(num_un):
        x = points_local_un[i, 0]
        y = points_local_un[i, 1]
        z = points_local_un[i, 2]  # 遍历到当前体素位置
        # 求此体素26邻域
        neighbour = np.array([[x + 1, y, z], [x, y + 1, z], [x - 1, y, z], [x, y - 1, z], [x, y, z - 1], [x, y, z + 1],
                              [x + 1, y + 1, z], [x - 1, y + 1, z], [x - 1, y - 1, z], [x + 1, y - 1, z], [x + 1, y, z + 1],
                              [x, y + 1, z + 1], [x - 1, y, z - 1], [x, y - 1, z - 1], [x, y + 1, z - 1], [x, y - 1, z + 1],
                              [x + 1, y, z - 1], [x - 1, y, z + 1], [x + 1, y + 1, z + 1], [x - 1, y - 1, z - 1],
                              [x - 1, y + 1, z + 1], [x + 1, y - 1, z + 1], [x + 1, y + 1, z - 1], [x - 1, y - 1, z + 1],
                              [x - 1, y + 1, z - 1], [x + 1, y - 1, z - 1]])
        # 找到“正常”的邻域
        neighbour = neighbour[neighbour[:, 0] < limit_box[0]]
        neighbour = neighbour[neighbour[:, 0] >= 0]
        neighbour = neighbour[neighbour[:, 1] < limit_box[1]]
        neighbour = neighbour[neighbour[:, 1] >= 0]
        neighbour = neighbour[neighbour[:, 2] < limit_box[2]]
        neighbour = neighbour[neighbour[:, 2] >= 0]
        # 清除无值邻域
        for j in range(len(neighbour)):  # binary(neighbour(1,r),neighbour(2,r),neighbour(3,r))~=0
            b_x = int(neighbour[j, 0])
            b_y = int(neighbour[j, 1])
            b_z = int(neighbour[j, 2])
            if binary[b_x, b_y, b_z] == 0:
                neighbour[j, :] = [-1, -1, -1]
        neighbour = neighbour[neighbour[:, 2] >= 0]
        a.append(neighbour)
    '2.各类别区域增长划分标签'
    labels = np.zeros(num_un)  # 建立空标签数组  默认为0
    n = 2  # 特征值标准差阈值
    # 随机挑选一个有值体素
    arange_ = np.arange(num_un)
    # start = np.random.choice(arange_)  # 种子点的开始位置
    label_ = 1  # 标签自增工具
    for i in range(num_un):  # 对每个有值体素进行遍历
        if labels[i] == 0:  # 如果没有标签记录
            labels[i] = label_  # 给一个起始便签
            vessel = a[i]  # 新便签起始邻域
            i_ = binary[points_local_un[i, 0], points_local_un[i, 1], points_local_un[i, 2]]  # 当前体素特征值
            # 读取此区域特征值范围  (后续可以修改)
            classes_ = np.argmin(np.absolute(binary_limit[:, 0] - i_))  # 判断属于哪类
            i_max_ = binary_limit[classes_, 0] + binary_limit[classes_, 1] * n
            i_min_ = binary_limit[classes_, 0] - binary_limit[classes_, 1] * n  # 最大最小特征阈值
            while len(vessel) > 0:
                v_321_0_ = vessel[0, 0] * (10 ** VoxelLengthDigit[-2]) + vessel[0, 1] + vessel[0, 2] * (10 ** (VoxelLengthDigit[-1] * (-1)))  # 容器开始的标签
                index_ = np.isin(un_321, v_321_0_)  # 所在的un下标
                if labels[index_] == 0 and i_min_ <= binary[vessel[0, 0], vessel[0, 1], vessel[0, 2]] <= i_max_:  # 如果是没分类的体素并且特征值合适
                    # vessel = np.append(vessel, a[index_])  # 增加容器
                    index_ = int(arange_[index_])
                    vessel = np.vstack([vessel, a[index_]])  # 增加容器
                    labels[index_] = label_  # 赋予便签
                vessel = np.delete(vessel, 0, axis=0)  # 删除已用
                print('总进度', np.round(i / num_un, 2), '标签', label_, '剩余待处理体素', len(vessel))
            label_ += 1  # 标签增加
    '3：体素标签转所有点云标签'
    # 单个点在un上的位置，然后将标签赋值
    p_lwd_321 = points_local[:, 0] * (10 ** VoxelLengthDigit[-2]) + points_local[:, 1] + points_local[:, 2] * (10 ** (VoxelLengthDigit[-1] * (-1)))  # 点在体素坐标的匹配标签
    labels_points = np.empty(len(p_lwd_321))
    for i in range(len(p_lwd_321)):
        # labels_points[i] = labels[np.int16(np.array(np.where(un_321 == p_lwd_321[i])))]
        labels_points[i] = labels[np.where(un_321 == p_lwd_321[i])]
    return labels, labels_points


def Nei_search(points_local_un, binary, VoxelLengthDigit, voxel_begin=None, limit_box=None, limit_I=None):
    '''相同类别的邻域搜索（暂定）
    :param points_local_un: 所有有值体素的位置
    :param binary: 三维体素
    :param voxel_begin：种子点体素
    :param limit_box: 体素空间限制要求
    '''
    # 准备工作
    un_321 = points_local_un[:, 0] * (10 ** VoxelLengthDigit[-2]) + points_local_un[:, 1] + points_local_un[:, 2] * (10 ** (VoxelLengthDigit[-1] * (-1)))
    if limit_box is None:
        limit_box = np.array(binary.shape)
    # 先找points_local_un的26邻域
    num_un = len(points_local_un)
    # a = [0 for x in range(num_un)]  # 有值体素的26邻域嵌套数组
    a = []  # 有值体素的26邻域嵌套数组
    for i in range(num_un):
        x = points_local_un[i, 0]
        y = points_local_un[i, 1]
        z = points_local_un[i, 2]  # 遍历到当前体素位置
        # 求此体素26邻域
        neighbour = np.array([[x + 1, y, z], [x, y + 1, z], [x - 1, y, z], [x, y - 1, z], [x, y, z - 1], [x, y, z + 1],
                              [x + 1, y + 1, z], [x - 1, y + 1, z], [x - 1, y - 1, z], [x + 1, y - 1, z], [x + 1, y, z + 1],
                              [x, y + 1, z + 1], [x - 1, y, z - 1], [x, y - 1, z - 1], [x, y + 1, z - 1], [x, y - 1, z + 1],
                              [x + 1, y, z - 1], [x - 1, y, z + 1], [x + 1, y + 1, z + 1], [x - 1, y - 1, z - 1],
                              [x - 1, y + 1, z + 1], [x + 1, y - 1, z + 1], [x + 1, y + 1, z - 1], [x - 1, y - 1, z + 1],
                              [x - 1, y + 1, z - 1], [x + 1, y - 1, z - 1]])
        # 找到“正常”的邻域
        neighbour = neighbour[neighbour[:, 0] < limit_box[0]]
        neighbour = neighbour[neighbour[:, 0] >= 0]
        neighbour = neighbour[neighbour[:, 1] < limit_box[1]]
        neighbour = neighbour[neighbour[:, 1] >= 0]
        neighbour = neighbour[neighbour[:, 2] < limit_box[2]]
        neighbour = neighbour[neighbour[:, 2] >= 0]
        # 清除无值邻域
        for j in range(len(neighbour)):  # binary(neighbour(1,r),neighbour(2,r),neighbour(3,r))~=0
            b_x = int(neighbour[j, 0])
            b_y = int(neighbour[j, 1])
            b_z = int(neighbour[j, 2])
            if binary[b_x, b_y, b_z] == 0:
                neighbour[j, :] = [-1, -1, -1]
        neighbour = neighbour[neighbour[:, 2] >= 0]
        a.append(neighbour)
    '连通区域增长(此区域需要自定义设计)'
    # 挑选种子点
    arange_ = np.arange(num_un)
    if voxel_begin is None:
        start = np.random.choice(arange_)  # 种子点的开始位置
    else:
        vb_321 = voxel_begin[0] * (10 ** VoxelLengthDigit[-2]) + voxel_begin[1] + voxel_begin[2] * (10 ** (VoxelLengthDigit[-1] * (-1)))
        index_ = np.isin(un_321, vb_321)
        start = int(arange_[index_])
    b = a[start]  # 随机点的起始邻域
    binary[points_local_un[start, 0], points_local_un[start, 1], points_local_un[start, 2]] = np.nan  # 起始点脱离循环
    connect = points_local_un[start]  # 连通区域标记容器
    while len(b) > 0:  # 当邻域容器依然有值时
        # 判断当前元素的值（可更改）
        if binary[b[0, 0], b[0, 1], b[0, 2]] == 1.0:
            connect = np.vstack([connect, b[0, :]])  # 添加整理符合条件的体素
            binary[b[0, 0], b[0, 1], b[0, 2]] = np.nan  # 脱离循环
            # 3列合并到1列
            b_321_ = b[0, 0] * (10 ** VoxelLengthDigit[-2]) + b[0, 1] + b[0, 2] * (10 ** (VoxelLengthDigit[-1] * (-1)))
            # b_new = a[un_321 == b_321_]
            a_index_ = np.isin(un_321, b_321_)
            a_index_ = arange_[a_index_]
            b_new = a[int(a_index_)]
            b = np.delete(b, 0, axis=0)
            b = np.vstack([b, b_new])
        else:
            b = np.delete(b, 0, axis=0)
        print('当前容器内剩余体素数量', len(b))
    return connect


def find_nei26_single(p2v_id, num_v, binary, threshold=0):
    '求单体元26邻域'
    min_v = 0  # 体素的最小边界
    x = p2v_id[0]
    y = p2v_id[1]
    z = p2v_id[2]  # 点云所在体素下标
    # 求此体素26邻域
    neighbour = [[x + 1, y, z], [x, y + 1, z], [x - 1, y, z], [x, y - 1, z], [x, y, z - 1], [x, y, z + 1],
                 [x + 1, y + 1, z], [x - 1, y + 1, z], [x - 1, y - 1, z], [x + 1, y - 1, z], [x + 1, y, z + 1],
                 [x, y + 1, z + 1], [x - 1, y, z - 1], [x, y - 1, z - 1], [x, y + 1, z - 1], [x, y - 1, z + 1],
                 [x + 1, y, z - 1], [x - 1, y, z + 1], [x + 1, y + 1, z + 1], [x - 1, y - 1, z - 1],
                 [x - 1, y + 1, z + 1], [x + 1, y - 1, z + 1], [x + 1, y + 1, z - 1], [x - 1, y - 1, z + 1],
                 [x - 1, y + 1, z - 1], [x + 1, y - 1, z - 1]]
    neighbour = np.array(neighbour)  # 类型转换
    # 找到“正常”的邻域
    neighbour = neighbour[neighbour[:, 0] < num_v[0]]
    neighbour = neighbour[neighbour[:, 0] >= min_v]
    neighbour = neighbour[neighbour[:, 1] < num_v[1]]
    neighbour = neighbour[neighbour[:, 1] >= min_v]
    neighbour = neighbour[neighbour[:, 2] < num_v[2]]
    for j in range(len(neighbour)):  # binary(neighbour(1,r),neighbour(2,r),neighbour(3,r))~=0
        b_x = int(neighbour[j, 0])
        b_y = int(neighbour[j, 1])
        b_z = int(neighbour[j, 2])
        if threshold == 0 and binary[b_x, b_y, b_z] == threshold:  # 如果未设置阈值
            neighbour[j, :] = [-1, -1, -1]
        elif binary[b_x, b_y, b_z] > threshold or binary[b_x, b_y, b_z] == 0:  # 如果设置阈值
            neighbour[j, :] = [-1, -1, -1]
    neighbour = neighbour[neighbour[:, 2] >= min_v]
    return neighbour


def cut_down(num, Piece=mp.cpu_count()):
    '建立并行计算断点'
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


def find_arctan_block(xzc_point, xzc_c, tik0, tik1):
    ' 并行计算每个点的反正切'
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


def find_belong_block(angle, single_a, tik0, tik1):
    '计算每个点云属于哪个环块'
    belong_ = np.empty(tik1 - tik0)
    j = 0  # 计数器
    for i in range(tik0, tik1):
        belong_[j] = np.floor(angle[i] / single_a)  # 点云归属标签赋值
        j += 1
    print('已完成', tik0, '-', tik1, '的环块归属')
    return belong_


def Split_ring_mp(xzc_point, xzc_c, n=10160, num_cpu=mp.cpu_count()):
    '将圆环分成n份(点云以及圆环)并行计算'
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


def XYZ2ρθY_1(xyzic, xzrc, n=3000):
    '240522单点笛卡尔坐标系转成圆柱体坐标系'
    xzr = xzrc[xzrc[:, -1] == xyzic[-1], :3]  # 圆心位置
    R2 = (xyzic[0] - xzr[0, 0]) ** 2 + (xyzic[2] - xzr[0, 1]) ** 2  # 点到圆心的距离
    ρ = np.sqrt(R2)
    y = xyzic[1]
    # 求角度
    # d_yx_[j, 0] = (xzc_point[i, 1] - xz_c[0, 1])
    # d_yx_[j, 1] = (xzc_point[i, 0] - xz_c[0, 0])
    d_z = xyzic[2] - xzr[0, 1]
    d_x = xyzic[0] - xzr[0, 0]
    angle = np.arctan2(d_z, d_x)  # 求反正切值
    # 将角度分解
    single_a = np.pi * 2 / n  # 求每个块的过渡
    θ = np.floor(angle / single_a)  # 点云归属标签赋值
    ρθY = np.array([ρ, θ, y])
    return ρθY


def XYZ2ρθY(xyzic, xzrc, n=3000):
    '笛卡尔坐标系转成圆柱体坐标系'
    Y = xyzic[:, 1]  # y轴坐标为起点
    c = xzrc[:, 3]  # 所有圆环名
    ρ = np.empty([len(xyzic)])  # 新建一个存储点云p的容器
    '准备添加并行化'
    for i in range(len(xyzic)):
        xyz_ = xyzic[i, :3]  # 当前点的空间位置
        c_i = xyzic[i, -1]  # 当前点圆环名
        xzr_ = xzrc[c == c_i, :3]  # 圆心位置
        R2 = (xyz_[0] - xzr_[0, 0]) ** 2 + (xyz_[2] - xzr_[0, 1]) ** 2  # 点到圆心的距离
        # dis[i] = np.abs(R2 - xzr_[0, -1] ** 2)
        ρ[i] = np.sqrt(R2)  # 点云到中轴线的距离
    θ = np.empty([len(xyzic)])  # 新建一个存储点云θ的容器
    # 求角度
    xzc_point = np.c_[xyzic[:, 0], xyzic[:, 2], xyzic[:, -1]]
    xzc_c = np.c_[xzrc[:, :2], xzrc[:, -1]]
    θ = Split_ring_mp(xzc_point, xzc_c, n=n)
    ρθY = np.c_[ρ, θ, Y]
    # 归一化
    θ_min = np.min(ρθY[:, 1])  # 角度向量化后的最小值
    ρθY[:, 1] = ρθY[:, 1] - θ_min  # 使所有的角度都大于0
    Y_min = np.min(ρθY[:, -1])  # Y轴后的最小值
    ρθY[:, -1] = ρθY[:, -1] - Y_min  # Y轴归0
    return ρθY, θ_min, Y_min


class voxel_ρθY:
    '建立空间圆柱坐标系体素'

    def __init__(self, ρθY, pixel=np.array([0.004, 1, 0.004])):
        '建立构造函数'
        # 输入圆柱坐标以及默认的体元分辨率
        self.points_local_un_value = None  # 精简化后的有值体素强度值容器
        self.points_local_un = None  # 精简化后的有值体素位置容器
        self.VoxelLengthDigit = None  # 体元数量位数
        self.VoxelLength = None  # 体素长宽高容器
        self.pixel = pixel  # 体素的点云分辨率
        self.voxel_values = None  # 体素特征值
        self.num = len(ρθY)  # 点云数量
        self.ρθY = ρθY  # 将矫正后的坐标放入进去（记得之前要矫正）
        self.SpaceBoundary = self.ρθY.max(axis=0)  # 求点云的最大边界
        # self.SpaceBoundary = np.array([self.ρθY.max(axis=0), self.ρθY.min(axis=0)])  # 点云的边界
        self.find_VoxelLength()  # 求体素长宽高
        self.points_local = np.empty([self.num, 3])  # 每个点云所在的体素位置

    def find_VoxelLength(self):
        '求体素体积'
        self.VoxelLength = np.int16(np.ceil(self.SpaceBoundary / self.pixel) + 1)  # 求体素的长宽高
        print('体素的长宽高为', self.VoxelLength)
        self.VoxelLengthDigit = [len(str(self.VoxelLength[0])), len(str(self.VoxelLength[1])),
                                 len(str(self.VoxelLength[2]))]  # 刷新体元长宽高的位数

    def P2V(self, values):
        '点云体素化并赋值'
        print('最大特征值', np.max(values), '最小特征值', np.min(values))
        self.voxel_values = np.zeros([int(self.VoxelLength[0]), int(self.VoxelLength[1]), int(self.VoxelLength[2])])
        for i in range(self.num):
            self.points_local[i, :] = np.floor(self.ρθY[i, :] / self.pixel)  # 遍历点属于哪个体素
            # if self.voxel_values[int(self.points_local[i, 0]), int(self.points_local[i, 1]), int(self.points_local[i, 2])] == 0:
            self.voxel_values[int(self.points_local[i, 0]), int(self.points_local[i, 1]), int(self.points_local[i, 2])] = values[i]  # 体素赋值
        self.points_local = self.points_local.astype(int)  # 将点云位置进行整数化
        self.points_local_un = np.unique(self.points_local, axis=0)  # 有值体素位置精简化
        print('有值极坐标体素的数量',len(self.points_local_un))
        self.points_local_un_value = np.zeros(len(self.points_local_un))  # 每个有值体素的值
        for i in range(len(self.points_local_un)):
            self.points_local_un_value[i] = self.voxel_values[int(self.points_local_un[i, 0]), int(self.points_local_un[i, 1]), int(self.points_local_un[i, 2])]
        print('最大体素值',np.max(self.points_local_un_value),'最小体素值',np.min(self.points_local_un_value))
        return self.voxel_values

    def P2Vm(self, values):
        '点云体素化赋值（平均值版）'
        print('开始进行极体素化赋值')
        self.voxel_values = np.zeros([int(self.VoxelLength[0]), int(self.VoxelLength[1]), int(self.VoxelLength[2])])  # 存储总值的容器
        voxel_num = np.zeros([int(self.VoxelLength[0]), int(self.VoxelLength[1]), int(self.VoxelLength[2])], dtype=np.float32)  # 存储体素数量的容器
        for i in range(self.num):
            self.points_local[i, :] = np.floor(self.ρθY[i, :] / self.pixel)  # 遍历点属于哪个体素
            self.voxel_values[int(self.points_local[i, 0]), int(self.points_local[i, 1]), int(self.points_local[i, 2])] += values[i]  # 体素赋值
            voxel_num[int(self.points_local[i, 0]), int(self.points_local[i, 1]), int(self.points_local[i, 2])] += 1  # 点云数量增值
        self.points_local = self.points_local.astype(int)  # 将点云位置进行整数化
        self.points_local_un = np.unique(self.points_local, axis=0)  # 有值体素位置精简化
        self.points_local_un_value = np.empty(len(self.points_local_un))  # 每个有值体素的值
        for i in range(len(self.points_local_un)):
            self.points_local_un_value[i] = self.voxel_values[int(self.points_local[i, 0]), int(self.points_local[i, 1]), int(self.points_local[i, 2])]

        # 平均值化有值
        self.voxel_values = self.voxel_values / voxel_num
        self.voxel_values = np.nan_to_num(self.voxel_values)  # nan转0
        print('极体素化赋值已完成')
        return self.voxel_values

    def P2V_double(self, values):
        '体素二次赋值'
        voxel_values = np.zeros([int(self.VoxelLength[0]), int(self.VoxelLength[1]), int(self.VoxelLength[2])])
        for i in range(self.num):
            # print(i)
            self.points_local[i, :] = np.round(self.ρθY[i, :] / self.pixel)  # 遍历点属于哪个体素
            voxel_values[int(self.points_local[i, 0]), int(self.points_local[i, 1]), int(self.points_local[i, 2])] = values[i]  # 体素赋值
        return voxel_values

    def find_newPoint_local(self, ρθY_):
        '查询某一批点云的最新体素位置'
        # points_local_new = np.empty([len(ρθY_), 3])  # 存储当前点云所在体素的位置
        points_local_new = np.empty([ρθY_.shape[0], 3])  # 存储当前点云所在体素的位置
        for i in range(ρθY_.shape[0]):
            points_local_new[i, :] = np.round(ρθY_[i, :3] / self.pixel)  # 遍历点属于哪个体素
        return points_local_new

    def watch_voxel(self, r=2.75, n=0, color=0, cmap='gray',edge=True,colorbar=True):
        '体素显示函数'
        '''
        colors = np.empty(self.VoxelLength, dtype=object)  # 体素颜色容器
        points_local_un = np.unique(self.points_local, axis=0)  # 简化有值体素
        for i in range(len(points_local_un)):
            colors[points_local_un[i, 0], points_local_un[i, 1], points_local_un[i, 2]] = 'red'  # 赋值为红色
        fig = plt.figure(figsize=plt.figaspect(0.5))  # 新建一个显示窗口
        ax = fig.gca(projection='3d')
        ax.voxels(colors, facecolors=colors)
        plt.tight_layout()
        plt.show()
        '''
        len_voxel = len(self.points_local_un)  # 有值体素数量
        girth = r * np.pi * 2  # 周长
        if n == 0:
            n = np.ceil(girth / self.pixel[0])  # 将圆分成多少份
        voxel_8ps = Calculate8Points_mp(self.points_local_un, dp=self.pixel[0], n=n)  # 求每个体素的8个顶点
        # voxel_8ps = voxel_8ps[self.points_local_un[:,0] >= (np.max(self.points_local_un[:,0])-4),:,:]
        voxel_8ps_2D = np.reshape(voxel_8ps, (-1, 3))  # 数据降维
        cells_hex = np.arange(len_voxel * 8).reshape([len_voxel, 8])  # 顶点索引排序
        grid = pv.UnstructuredGrid({pv.CellType.HEXAHEDRON: cells_hex}, voxel_8ps_2D)  # 建立体素网格
        if color == 0:
            color = self.points_local_un_value
        # grid.plot(scalars=color, show_edges=edge, cmap=cmap)  # 显示体素
        plotter = pv.Plotter()  # 创建绘图窗口
        plotter.background_color = 'white'  # 设置背景颜色为白色
        plotter.add_mesh(grid, scalars=color, show_edges=edge, cmap=cmap, show_scalar_bar=colorbar,lighting=False)  # 添加体素网格，并设置颜色映射
        print('已显示体素')
        plotter.show()  # 显示绘图
        return

    def θy2P(self, θy):
        '体素θy转点云'
        input_21 = θy[:, 0] + θy[:, 1] * (10 ** (self.VoxelLengthDigit[-1] * (-1)))
        base_21 = self.points_local[:, 1] + self.points_local[:, 2] * (10 ** (self.VoxelLengthDigit[-1] * (-1)))
        points_index = np.isin(base_21, input_21)  # 提取点云的下标 by:Zelas
        return points_index

    def V2P(self, v_local_un):
        '体素转点云'
        lwd_321 = v_local_un[:, 0] * (10 ** self.VoxelLengthDigit[-2]) + v_local_un[:, 1] + v_local_un[:, 2] * (10 ** (self.VoxelLengthDigit[-1] * (-1)))
        p_lwd_321 = self.points_local[:, 0] * (10 ** self.VoxelLengthDigit[-2]) + self.points_local[:, 1] + self.points_local[:, 2] * (10 ** (self.VoxelLengthDigit[-1] * (-1)))
        points_index = np.isin(p_lwd_321, lwd_321)  # 提取点云的下标 by:Zelas
        return points_index


def watch_o3d_voxel(xyzrgb, size=0.05):
    '（已弃用）显示体素（注意rgb的值域∈【0，1】）'
    xyz_o3d = o3d.geometry.PointCloud()  # 建立open3d点云类容器
    xyz_o3d.points = o3d.utility.Vector3dVector(xyzrgb[:, :3])  # 赋予点坐标
    xyz_o3d.colors = o3d.utility.Vector3dVector(xyzrgb[:, 3:])  # 赋予点颜色
    voxel_grid = o3d.geometry.VoxelGrid.create_from_point_cloud(xyz_o3d, voxel_size=size)  # 体素化
    o3d.visualization.draw_geometries([voxel_grid])  # 显示体素


def Calculate8Points_mp(points_local_un, dp=0.05, n=1130):
    '并行计算出每个有值体素8个点的坐标（极坐标显示专用）'
    # 准备工作
    num = len(points_local_un)  # 有值体素数量
    voxel_8ps = np.empty([num, 8, 3], dtype=np.float32)  # 存储每个容器显示的8个点
    do = 2 * np.pi / n  # 每份角度
    num_cpu = mp.cpu_count()  # 线程数
    pool = mp.Pool(processes=num_cpu)  # 开启多进程池，数量为cpu
    tik = cut_down(num, num_cpu)  # 分块函数
    tik_b = 0  # 分块输出计时器
    # 并行计算
    multi_res = [pool.apply_async(Calculate8Points_Block, args=(points_local_un, dp, do, tik[i], tik[i + 1])) for i in
                 range(num_cpu)]  # 将每个block需要处理的点云区间发送到每个进程当中
    for res in multi_res:
        voxel_8ps[tik[tik_b]:tik[tik_b + 1], :, :] = res.get()  # 将每个进程得到的结果分block的发送到容器当中
        tik_b += 1
    # 后续处理
    pool.close()  # 禁止进程池再接收任务
    pool.join()  # 当所有进程全部计算完毕后，退出并行计算
    return voxel_8ps


def Calculate8Points_Block(points_local_un, dp, do, tik, tok):
    '分块计算出每个有值体素8个点的坐标（极坐标显示专用）'
    num_ = tok - tik  # 每个block的处理数量
    j = 0  # 循环计数器
    voxel_8ps_ = np.empty([num_, 8, 3], dtype=np.float32)  # 分块容器
    for j in range(num_):
        # 求y范围
        voxel_8ps_[j, :4, 1] = dp * points_local_un[tik + j, 2]
        voxel_8ps_[j, 4:, 1] = dp * (points_local_un[tik + j, 2] + 1)
        # 求x范围
        dp0 = dp * points_local_un[tik + j, 0]  # 起始极径
        dp1 = dp * (points_local_un[tik + j, 0] + 1)  # 终止极径
        x00 = dp0 * np.cos(do * points_local_un[tik + j, 1])
        x01 = dp1 * np.cos(do * points_local_un[tik + j, 1])
        x10 = dp0 * np.cos(do * (points_local_un[tik + j, 1] + 1))
        x11 = dp1 * np.cos(do * (points_local_un[tik + j, 1] + 1))  # x坐标
        voxel_8ps_[j, 0, 0] = voxel_8ps_[j, 4, 0] = x00
        voxel_8ps_[j, 1, 0] = voxel_8ps_[j, 5, 0] = x01
        voxel_8ps_[j, 2, 0] = voxel_8ps_[j, 6, 0] = x11
        voxel_8ps_[j, 3, 0] = voxel_8ps_[j, 7, 0] = x10
        # 确定z值
        z00 = dp0 * np.sin(do * points_local_un[tik + j, 1])
        z01 = dp1 * np.sin(do * points_local_un[tik + j, 1])
        z10 = dp0 * np.sin(do * (points_local_un[tik + j, 1] + 1))
        z11 = dp1 * np.sin(do * (points_local_un[tik + j, 1] + 1))
        voxel_8ps_[j, 0, 2] = voxel_8ps_[j, 4, 2] = z00
        voxel_8ps_[j, 1, 2] = voxel_8ps_[j, 5, 2] = z01
        voxel_8ps_[j, 2, 2] = voxel_8ps_[j, 6, 2] = z11
        voxel_8ps_[j, 3, 2] = voxel_8ps_[j, 7, 2] = z10
        # 刷新计数器
        j += 1
    print('已完成第', tik, '至第', tok, '的有值体素')
    return voxel_8ps_


class Pixelation:
    '下采样类，正在开发中'

    def __init__(self, xy, xyz=None, dx=0, dy=0, threads=mp.cpu_count()):  # 输入下采样数据，下采样横像素尺寸，下采样纵像素尺寸
        '下采样'
        """
        xy:点云平面坐标
        xyz：点云三维坐标
        dx，dy：像素
        threads:多线程数量，默认为CPU最大线程数
        """
        self.PlaneLengthDigit = None  # 像素长宽的位数
        self.PlaneLength = None  # 像素长宽
        self.pixel_start = None  # 像素起始位置
        self.xy = xy  # 数据传递
        self.dx = dx  # 1
        self.dy = dy  # 像素尺寸大小  # 0.004
        # self.pixel = pixel
        self.num = len(xy)  # 数据数量
        self.num_threads = threads  # 并行计算使用的线程数
        t1 = t.time()
        if self.dx + self.dy == 0 and xyz is not None:  # 如果没有初始像素
            self.AdaptiveSideLength(xyz)  # 则给出一个边长
            print('自适应体素求法用时', t.time() - t1, 's')
        self.PlaneBoundary = np.array([self.xy.min(axis=0), self.xy.max(axis=0)])  # 点云的边界
        self.img = None  # 图片容器
        self.find_PlaneLength()  # 建立图片容器
        self.points_local = np.empty([self.num, 2])  # 每个点云的像素位置

    def find_PlaneLength(self):
        '建立像素容器'
        self.pixel_start = np.floor(self.PlaneBoundary[0, :] / [self.dx, self.dy])  # 像素起始位置
        pixel_end = np.ceil(self.PlaneBoundary[1, :] / [self.dx, self.dy])  # 像素结束位置
        self.PlaneLength = (pixel_end - self.pixel_start + 1).astype(int)  # 刷新像素长宽
        self.PlaneLengthDigit = [len(str(self.PlaneLength[0])), len(str(self.PlaneLength[1]))]  # 像素长宽的位数
        print('下采样的长宽为', self.PlaneLength)
        self.img = np.zeros(self.PlaneLength, dtype=np.float32)  # 设置三维体素(类型设置为32位浮点型)

    def AdaptiveSideLength(self, xyz):
        '自适应边长：求平均点间距'
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(xyz)
        distances = pcd.compute_nearest_neighbor_distance()
        self.dx = self.dy = np.mean(distances)
        print('平均点间距为', self.dx)

    def P2G(self, intensity):
        '强度值下采样平均值版'
        # self.voxel_values = np.zeros([int(self.VoxelLength[0]), int(self.VoxelLength[1]), int(self.VoxelLength[2])])  # 存储总值的容器
        pixel_num = np.zeros([int(self.PlaneLength[0]), int(self.PlaneLength[1])], dtype=np.int16)  # 存储像素数量的容器
        for i in range(self.num):
            self.points_local[i, :] = np.round(self.xy[i, :] / [self.dx, self.dy]) - self.pixel_start  # 遍历点属于哪个像素
            self.img[int(self.points_local[i, 0]), int(self.points_local[i, 1])] += intensity[i]  # 像素赋值
            pixel_num[int(self.points_local[i, 0]), int(self.points_local[i, 1])] += 1  # 点云数量增值
        print('点云转体素已完成')
        self.points_local = self.points_local.astype(int)  # 将点云位置进行整数化
        self.points_local_un = np.unique(self.points_local, axis=0)  # 有值像素位置精简化
        print('有值像素数量',len(self.points_local_un))
        # 平均值化有值
        self.img = self.img / pixel_num
        self.img = np.nan_to_num(self.img)  # nan转0
        print('体素赋值已完成')
        return self.img

    def haplochromatization(self):
        '像素单体化'
        '1:寻找每个像素的有效邻域'
        # 准备工作
        un_21 = self.points_local_un[:, 0] * (10 ** self.PlaneLengthDigit[0]) + self.points_local_un[:, 1]  # 有值像素标签
        # 先找points_local_un的8邻域
        num_un = len(self.points_local_un)  # 有值像素数量
        a = []  # 有值像素的8邻域嵌套数组
        limit_box = np.array(self.img.shape)  # 给出默认像素尺寸限制
        for i in tqdm(range(num_un),colour='green',desc='寻找有值像素8邻域',unit="pixel"):
            x = self.points_local_un[i, 0]
            y = self.points_local_un[i, 1]  # 遍历到当前像素位置
            # 求此像素8邻域
            neighbour = np.array([[x + 1, y - 1], [x + 1, y], [x + 1, y + 1], [x, y - 1], [x, y + 1], [x - 1, y - 1],
                                  [x - 1, y], [x - 1, y + 1]])
            # 找到“正常”的邻域
            neighbour = neighbour[neighbour[:, 0] < limit_box[0]]
            neighbour = neighbour[neighbour[:, 0] >= 0]
            neighbour = neighbour[neighbour[:, 1] < limit_box[1]]
            neighbour = neighbour[neighbour[:, 1] >= 0]
            # 清除无值邻域
            for j in range(len(neighbour)):  # binary(neighbour(1,r),neighbour(2,r))~=0
                b_x = int(neighbour[j, 0])
                b_y = int(neighbour[j, 1])
                if self.img[b_x, b_y] == 0:
                    neighbour[j, :] = [-1, -1]
            neighbour = neighbour[neighbour[:, 1] >= 0]
            a.append(neighbour)
        '2：对联通区域进行增长'
        labels = np.zeros(num_un)  # 建立空标签数组  默认为0
        arange_ = np.arange(num_un)  # 每一个有值像素下标
        label_ = 1  # 标签自增工具
        finished_pixel = 1  # 已处理完的像素计数器
        # for i in tqdm(range(num_un),colour='green',desc='联通区域增长 当前标签'+str(label_),unit="pixel"):  # 对每个有值像素进行遍历
        for i in range(num_un):
            if labels[i] == 0:  # 如果没有标签记录
                labels[i] = label_  # 给一个起始便签
                vessel = a[i]  # 新便签起始邻域
                while len(vessel) > 0:  # 如果存在有值邻域
                    p_21_0_ = vessel[0, 0] * (10 ** self.PlaneLengthDigit[0]) + vessel[0, 1]  # 容器开始的标签
                    index_ = np.isin(un_21, p_21_0_)  # 所在的un下标
                    if labels[index_] == 0:
                        index_ = int(arange_[index_])
                        vessel = np.vstack([vessel, a[index_]])  # 增加容器
                        labels[index_] = label_  # 赋予便签
                        vessel = np.delete(vessel, 0, axis=0)  # 删除已用
                        finished_pixel += 1  # 完成一个像素
                        print('总进度', np.round(finished_pixel / num_un, 2), '标签', label_, '剩余待处理像素', len(vessel))
                    else:
                        vessel = np.delete(vessel, 0, axis=0)  # 删除已用
                        print('总进度', np.round(finished_pixel / num_un, 2), '标签', label_, '剩余待处理像素', len(vessel))
                label_ += 1  # 标签增加
        '3:像素标签转点云标签'
        # 单个点在un上的位置，然后将标签赋值
        p_lwd_21 = self.points_local[:, 0] * (10 ** self.PlaneLengthDigit[0]) + self.points_local[:, 1]  # 点在体素坐标的匹配标签
        labels_points = np.empty(len(p_lwd_21))
        for i in range(len(p_lwd_21)):
            labels_points[i] = labels[np.where(un_21 == p_lwd_21[i])]
        return labels, labels_points  # labels:每个像素的标签,labels_points：每个点云的标签

    def SemanticSegmentation(self, binary_limit):
        '图像语义分割'
        # binary_limit: 每个类别的特征值限制数组[特征均值_i, 特征方差_i] * n, i = 1:n
        '1:寻找每个像素的有效邻域'
        # 准备工作
        un_321 = self.points_local_un[:, 0] * (10 ** self.PlaneLengthDigit[0]) + self.points_local_un[:, 1]  # 有值体素标签
        # 先找points_local_un的8邻域
        num_un = len(self.points_local_un)  # 有值像素数量
        a = []  # 有值像素的8邻域嵌套数组
        limit_box = np.array(self.img.shape)  # 给出默认像素尺寸限制
        for i in range(num_un):
            x = self.points_local_un[i, 0]
            y = self.points_local_un[i, 1]  # 遍历到当前像素位置
            # 求此像素8邻域
            neighbour = np.array([[x + 1, y - 1], [x + 1, y], [x + 1, y + 1], [x, y - 1], [x, y + 1], [x - 1, y - 1],
                                  [x - 1, y], [x - 1, y + 1]])
            # 找到“正常”的邻域
            neighbour = neighbour[neighbour[:, 0] < limit_box[0]]
            neighbour = neighbour[neighbour[:, 0] >= 0]
            neighbour = neighbour[neighbour[:, 1] < limit_box[1]]
            neighbour = neighbour[neighbour[:, 1] >= 0]
            # 清除无值邻域
            for j in range(len(neighbour)):  # binary(neighbour(1,r),neighbour(2,r))~=0
                b_x = int(neighbour[j, 0])
                b_y = int(neighbour[j, 1])
                if self.img[b_x, b_y] == 0:
                    neighbour[j, :] = [-1, -1]
            neighbour = neighbour[neighbour[:, 1] >= 0]
            a.append(neighbour)
        '2.各类别区域增长划分标签'
        labels = np.zeros(num_un)  # 建立空标签数组  默认为0
        n = 2  # 特征值标准差阈值
        # 随机挑选一个有值体素
        arange_ = np.arange(num_un)
        # start = np.random.choice(arange_)  # 种子点的开始位置
        label_ = 1  # 标签自增工具
        for i in range(num_un):  # 对每个有值体素进行遍历
            if labels[i] == 0:  # 如果没有标签记录
                labels[i] = label_  # 给一个起始便签
                vessel = a[i]  # 新便签起始邻域
                i_ = self.img[self.points_local_un[i, 0], self.points_local_un[i, 1], self.points_local_un[i, 2]]  # 当前体素特征值  存在bug
                # 读取此区域特征值范围  (后续可以修改)
                classes_ = np.argmin(np.absolute(binary_limit[:, 0] - i_))  # 判断属于哪类
                i_max_ = binary_limit[classes_, 0] + binary_limit[classes_, 1] * n
                i_min_ = binary_limit[classes_, 0] - binary_limit[classes_, 1] * n  # 最大最小特征阈值
                while len(vessel) > 0:
                    v_321_0_ = vessel[0, 0] * (10 ** self.PlaneLengthDigit[0]) + vessel[0, 1]  # 容器开始的标签
                    index_ = np.isin(un_321, v_321_0_)  # 所在的un下标
                    if labels[index_] == 0 and i_min_ <= self.img[vessel[0, 0], vessel[0, 1]] <= i_max_:  # 如果是没分类的像素并且特征值合适
                        # vessel = np.append(vessel, a[index_])  # 增加容器
                        index_ = int(arange_[index_])
                        vessel = np.vstack([vessel, a[index_]])  # 增加容器
                        labels[index_] = label_  # 赋予便签
                    vessel = np.delete(vessel, 0, axis=0)  # 删除已用
                    print('总进度', np.round(i / num_un, 2), '标签', label_, '剩余待处理体素', len(vessel))
                label_ += 1  # 标签增加
        '3：体素标签转所有点云标签'
        # 单个点在un上的位置，然后将标签赋值
        p_lwd_321 = self.points_local[:, 0] * (10 ** self.PlaneLengthDigit[0]) + self.points_local[:, 1]  # 点在体素坐标的匹配标签
        labels_points = np.empty(len(p_lwd_321))
        for i in range(len(p_lwd_321)):
            # labels_points[i] = labels[np.int16(np.array(np.where(un_321 == p_lwd_321[i])))]
            labels_points[i] = labels[np.where(un_321 == p_lwd_321[i])]
        return labels, labels_points  # labels:每个像素的标签,labels_points：每个点云的标签


class voxel3:
    '建立体素类（笛卡尔坐标系但体素长宽高尺寸不一致）'

    # 输入点云位置，体元边长，找最邻近的邻域数量
    def __init__(self, xyz, rr_x=1, rr_y=1, rr_z=1):  # 每个点云所在体素的位置，总共的体素。体素所在的位置
        self.xyz = xyz  # 存储点云位置
        self.num = len(self.xyz)  # 存储点云数量
        self.rr = [rr_x, rr_y, rr_z]  # 体素的点云分辨率
        print('体素三轴分辨率为', self.rr)
        self.SpaceBoundary = np.array([self.xyz.max(axis=0), self.xyz.min(axis=0)])  # 点云的边界
        self.find_VoxelLength()  # 求长宽高 的数量
        self.points_local = np.empty([self.num, 3])  # 每个点云所在的体素位置
        self.num_voxel = 0  # 有效体元的数量

    def find_VoxelLength(self):
        '初始化体素框架'
        self.voxel_start = np.floor(self.SpaceBoundary[1, :] / self.rr)  # 体素的位置应该从哪里（XYZ）开始
        voxel_end = np.ceil(self.SpaceBoundary[0, :] / self.rr)  # 体素结束位置
        self.VoxelLength = (voxel_end - self.voxel_start + 1).astype(int)  # 刷新体元数量
        self.VoxelLengthDigit = [len(str(self.VoxelLength[0])), len(str(self.VoxelLength[1])), len(str(self.VoxelLength[2]))]  # 刷新体元长宽高的位数
        print('体素的长宽高为', self.VoxelLength)
        self.voxel_values = np.zeros(self.VoxelLength, dtype=np.float32)  # 设置三维体素(类型设置为32位浮点型)
        print('体素框架已建立')

    def P2V(self, values):
        '点云特征转体素特征（建立有值体素）'
        for i in range(self.num):
            self.points_local[i, :] = np.floor(self.xyz[i, :] / self.rr) - self.voxel_start  # 遍历点属于哪个体素
            self.voxel_values[int(self.points_local[i, 0]), int(self.points_local[i, 1]), int(self.points_local[i, 2])] = values[i]  # 体素赋值
        self.points_local = self.points_local.astype(int)  # 将点云位置进行整数化
        self.points_local_un = np.unique(self.points_local, axis=0)  # 有值体素位置精简化
        self.num_voxel = len(self.points_local_un)  # 有值体素数量
        print('体素赋值已完成')

    def Voxel2Pixel(self):
        '计算体素转像素（值为最低点高程，矩阵思想）'
        # 点云重新赋值
        self.voxel_values = np.ones(self.VoxelLength, dtype=np.float32) * 10000
        self.P2V(self.points_local[:, 2])  # 将高程值附给体素
        pixel_values_min = np.argmin(self.voxel_values, axis=2)
        self.pixel_min_un = np.empty([self.VoxelLength[0] * self.VoxelLength[1], 3])
        k = 0
        for i in tqdm(range(self.VoxelLength[0])):
            for j in range(self.VoxelLength[1]):
                self.pixel_min_un[k, 0] = i
                self.pixel_min_un[k, 1] = j
                self.pixel_min_un[k, 2] = pixel_values_min[i, j]
                k += 1
        return self.pixel_min_un

    def V2P(self, v_local_un):
        '体素转点云'
        lwd_321 = v_local_un[:, 0] * (10 ** self.VoxelLengthDigit[-2]) + v_local_un[:, 1] + v_local_un[:, 2] * (10 ** (self.VoxelLengthDigit[-1] * (-1)))
        p_lwd_321 = self.points_local[:, 0] * (10 ** self.VoxelLengthDigit[-2]) + self.points_local[:, 1] + self.points_local[:, 2] * (10 ** (self.VoxelLengthDigit[-1] * (-1)))
        points_index = np.isin(p_lwd_321, lwd_321)  # 提取点云的下标 by:Zelas
        return points_index
