import numpy as np  # 数组库
import multiprocessing as mp  # 并行计算库
import math  # 添加数学库为cuda编程做准备
from tqdm import tqdm  # 进度条

class supervoxel:
    '建立超体素'

    def __init__(self, xyz):
        '构造函数'
        self.xyz = xyz