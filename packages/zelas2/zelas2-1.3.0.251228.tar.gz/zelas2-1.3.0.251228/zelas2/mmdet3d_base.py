import os
import numpy as np
import zelas2.TheHeartOfTheMilitaryGod as zt
import random
import mmengine
import zelas2.shield as zs

def get_pts_paths(folder_path, end='las'):
    """
    读取当前文件夹下所有点云数据的绝对路径并保存到一个数组中

    Args:
        folder_path (str): 文件夹路径

    Returns:
        list: 所有las点云数据的绝对路径列表
    """
    las_paths = []
    for filename in os.listdir(folder_path):
        if filename.endswith(end):
            print(os.path.join(folder_path, filename))
            las_paths.append(os.path.join(folder_path, filename))
    return las_paths

def cut_points(xyzi,output_dir,name,chunk_size=160,old_max_i=65535):
    '将大点云分割成小点云,并重置xy坐标系'
    min_x = np.min(xyzi[:, 0])
    max_x = np.max(xyzi[:, 0])
    min_y = np.min(xyzi[:, 1])
    max_y = np.max(xyzi[:, 1])

    num_chunks_x = int(np.ceil((max_x - min_x) / chunk_size))
    num_chunks_y = int(np.ceil((max_y - min_y) / chunk_size))

    for i in range(num_chunks_x):
        for j in range(num_chunks_y):
            chunk_min_x = min_x + i * chunk_size
            chunk_max_x = chunk_min_x + chunk_size
            chunk_min_y = min_y + j * chunk_size
            chunk_max_y = chunk_min_y + chunk_size

            xyzi_ = xyzi[xyzi[:,0]>=chunk_min_x,:]
            xyzi_ = xyzi_[xyzi_[:,0]<chunk_max_x,:]
            xyzi_ = xyzi_[xyzi_[:,1]>=chunk_min_y,:]
            xyzi_ = xyzi_[xyzi_[:,1]<chunk_max_y,:]
            '重置坐标系'
            center_x = (chunk_min_x + chunk_max_x) / 2
            center_y = (chunk_min_y + chunk_max_y) / 2

            xyzi_[:, 0] = xyzi_[:, 0] - center_x
            xyzi_[:, 1] = xyzi_[:, 1] - center_y
            xyzi_[:, 3] = xyzi_[:, 3] / old_max_i
            output_path = output_dir+'\\'+name+str(i)+str(j)+'.txt'
            np.savetxt(output_path,xyzi_,fmt='%.05f')
            print('已经输出',output_path,'点云')

def cut_points_NS(xyzi,output_dir,name,chunk_size=125,old_max_i=65535):
    '将大点云分割成小点云,并重置xy坐标系,左下角为原点'
    # 求原始点云四至
    min_x = np.min(xyzi[:, 0])
    max_x = np.max(xyzi[:, 0])
    min_y = np.min(xyzi[:, 1])
    max_y = np.max(xyzi[:, 1])
    # 求分割边长
    num_chunks_x = int(np.ceil((max_x - min_x) / chunk_size))
    num_chunks_y = int(np.ceil((max_y - min_y) / chunk_size))
    # 分割坐标系+重置坐标系
    for i in range(num_chunks_x):
        for j in range(num_chunks_y):
            # 每块数据的四至
            chunk_min_x = min_x + i * chunk_size
            chunk_max_x = chunk_min_x + chunk_size
            chunk_min_y = min_y + j * chunk_size
            chunk_max_y = chunk_min_y + chunk_size
            # 找到这块数据
            xyzi_ = xyzi[xyzi[:,0]>=chunk_min_x,:]
            xyzi_ = xyzi_[xyzi_[:,0]<chunk_max_x,:]
            xyzi_ = xyzi_[xyzi_[:,1]>=chunk_min_y,:]
            xyzi_ = xyzi_[xyzi_[:,1]<chunk_max_y,:]
            '重置坐标系'
            # center_x = (chunk_min_x + chunk_max_x) / 2
            # center_y = (chunk_min_y + chunk_max_y) / 2
            xyzi_[:, 0] = xyzi_[:, 0] - chunk_min_x
            xyzi_[:, 1] = xyzi_[:, 1] - chunk_min_y
            xyzi_[:, 3] = xyzi_[:, 3] / old_max_i
            # 输出点云
            output_path = output_dir+'\\'+name+str(i)+str(j)+'.txt'
            np.savetxt(output_path,xyzi_,fmt='%.05f')
            print('已经输出',output_path,'点云')


def reset_z_intensity(xyzil,old_max_i=65535):
    '重置z坐标和强度值'
    xyzil[:,3] = xyzil[:,3]/old_max_i  # 重置强度值

    center_z = np.min(xyzil[:,2])  # 获取最低高程值
    xyzil[:,2] = xyzil[:,2] - center_z  # 矫正高程值，使得都大于0
    return xyzil

def reset_y(xyzil):
    '重置y坐标'
    y_mid = np.min(xyzil[:,1])+np.ptp(xyzil[:,1])/2
    xyzil[:,1] = xyzil[:,1] - y_mid
    return xyzil

def reset_newXYZI(xyzil,old_max_i=255,x0=0.049966401000506665,z0=1.31217610795099):
    '重置圆柱体3D坐标以及强度值'
    # z0 = np.mean(xyzil[:,2])  # 求z中心
    xyzil[:, 3] = xyzil[:, 3] / old_max_i  # 重置强度值
    if x0*z0 ==0:
        # 拟合圆中心
        model = zs.CircleLeastSquareModel()  # 类的实例化:用最小二乘生成已知模型
        data = np.vstack([xyzil[:, 0], xyzil[:, 2]]).T  # 整理数据
        result = model.fit(data)  # 拟合圆
        x0 = result.a * -0.5
        z0 = result.b * -0.5
    # ps_0 = zs.fit_cicle_rough(xyzil[:,:5])
    # xzrc = zs.fit_circle(ps_0[:,0],ps_0[:,2],ps_0[:,4],t=0.15)
    # x0 = np.mean(xzrc[:, 0])
    # z0 = np.mean(xzrc[:, 1])
    y0 = np.mean(xyzil[:,1])
    # 刷新坐标
    print('新圆心',x0,y0,z0)
    xyzil[:, 0] = xyzil[:, 0] - x0
    xyzil[:, 1] = xyzil[:, 1] - y0
    xyzil[:, 2] = xyzil[:, 2] - z0
    return xyzil

def reset_newRAYI(xyzil,x0=0.049966401000506665,z0=1.31217610795099,R=2.7):
    '将XYZ坐标转为极体素坐标'
    x = xyzil[:, 0]
    y = xyzil[:, 1]
    z = xyzil[:, 2]
    # 中心化
    x_c = x - x0
    z_c = z - z0
    # 极径
    r = np.sqrt(x_c**2 + z_c**2)-R
    # 弧长（绕Y轴，x-z平面）
    theta = np.arctan2(z_c, x_c)  # 注意顺序：atan2(z, x)
    arc = theta * R
    # 调整y
    y_adj = y - np.min(y)
    # 构造新数组
    new_xyzil = xyzil.copy()
    new_xyzil[:, 0] = r
    new_xyzil[:, 2] = y_adj
    new_xyzil[:, 1] = arc
    return new_xyzil


def swap_yz_coordinates(data):
    """
    Swap Y and Z coordinates in point cloud data

    Parameters:
    data: numpy array with shape (N, 3) or (N, M) where first 3 columns are X, Y, Z

    Returns:
    result[:, 2] = y_coords  # Put original Y values into Z column
    """
    # Extract X, Y, Z coordinates
    # x_coords = data[:, 0].copy()  # X remains unchanged
    z_coords = data[:, 2].copy()  # Z values (original)
    y_coords = data[:, 1].copy()  # Y values (original)

    # Create new array with swapped Y-Z
    result = data.copy()
    result[:, 1] = z_coords  # Put original Z values into Y column
    result[:, 2] = y_coords  # Put original Y values into Z column
    return result

def np2bin_batch(input,otput):
    'numpy点云批量转为.bin格式'
    # 获取点云路径
    files = [f for f in os.listdir(input) if f.endswith('.txt')]
    # 批量转为.bin
    for file in files:
        xyzil_ = zt.ReadByPolars(os.path.join(input, file))
        xyzi_ = xyzil_[:,:4]
        xyzi_ = np.float32(xyzi_)
        print('已经读取点云',os.path.join(input, file))
        name_ = os.path.splitext(file)[0] + '.bin'
        with open(os.path.join(otput,name_), 'wb') as f:
            f.write(xyzi_.tobytes())
        print('已经输出点云',os.path.join(otput, name_))

def np2label_batch(input,otput):
    'numpy点云标签批量生成.bin格式标签'
    files = [f for f in os.listdir(input) if f.endswith('.txt')]
    '标签批量转为.bin'
    for file in files:
        xyzil_ = zt.ReadByPolars(os.path.join(input, file))
        print('已经读取点云',os.path.join(input, file))
        L = np.int32(xyzil_[:,4])
        print(np.unique(L))
        name_ = os.path.splitext(file)[0] + '.label'
        with open(os.path.join(otput,name_), 'wb') as f:
            f.write(L.tobytes())
        print('已经输出逐点级标签',os.path.join(otput, name_))

def np2ImageSets_batch(input_path,train_file,val_file,test_file,p=np.array([7,2,1])):
    '生成训练集、验证集和测试集.txt'
    '批量读取las'
    files = [f for f in os.listdir(input_path) if f.endswith('.bin')]
    random.shuffle(files)  # 打乱数据集
    p_sum = np.sum(p)
    total_length = len(files)
    part1_length = np.floor(total_length * p[0] / p_sum).astype(int)
    part2_length = np.floor(total_length * p[1] / p_sum).astype(int)
    # part3_length = total_length - part1_length - part2_length
    part1 = files[:part1_length]
    part2 = files[part1_length:part1_length + part2_length]
    part3 = files[part1_length + part2_length:]
    # 将训练集和验证集\测试集的文件名写入对应的 .txt 文件
    with open(train_file, 'w') as train_f:
        for file in part1:
            train_f.write(f"{file}\n")
    with open(val_file, 'w') as val_f:
        for file in part2:
            val_f.write(f"{file}\n")
    with open(test_file, 'w') as test_f:
        for file in part3:
            test_f.write(f"{file}\n")

def create_pkl(ImageSets_path,out_file,data_set='Custom'):
    '通过数据集生成mmdet3d所能接受的仿seg_kitti的.pkl'
    data_infos = dict()
    data_infos['metainfo'] = dict(DATASET=data_set)
    data_list = []
    # 读取ImageSets里面的txt
    with open(ImageSets_path, 'r') as f:
        # 读取所有行并去除每行的换行符
        samples = [line.strip() for line in f.readlines()]
    num_samples = len(samples)
    for i in range(num_samples):
        data_list.append({
            'lidar_points': {
                'lidar_path':
                    'points'+'/'+samples[i],
                'num_pts_feats':
                    4
            },
            'pts_semantic_mask_path':
                'semantic_mask'+'/'+os.path.splitext(samples[i])[0] + '.label',
            'sample_id':
                str(i)
        })
    data_infos.update(dict(data_list=data_list))
    # 保存.pkl
    mmengine.dump(data_infos, out_file)