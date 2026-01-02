import ezdxf
from ezdxf import colors
from tqdm import tqdm
from ezdxf.addons import odafc
import numpy as np

def normalize_color(value):
    'RGB unit16转8'
    return int((value / 65535) * 255)


def points2dxf(xyzrgb,output=None,dxfversion='R2013'):
    '''
    点云转dxf
    :param dxfversion: AutoCAD版本号
    :param xyzrgb: 记录每个点云的坐标和颜色
    :param output: 输出路径
    :return: dxf类
    '''
    num = len(xyzrgb)  # 点云数量
    doc = ezdxf.new(dxfversion=dxfversion)  # 新建一个DXF类
    msp = doc.modelspace()  # DXF模型指针
    # 设置新的边界点位置
    extmin = (np.min(xyzrgb[:,0]), np.min(xyzrgb[:,1]), np.min(xyzrgb[:,2]))  # 最小边界
    extmax = (np.max(xyzrgb[:,0]), np.max(xyzrgb[:,1]), np.max(xyzrgb[:,2]))  # 最大边界
    msp.reset_extents(extmin, extmax)  # 重置边界
    # 遍历las点云添加.dxf点位置及颜色（真彩色）
    for i in tqdm(range(num)):
        color = colors.rgb2int((normalize_color(xyzrgb[i,3]), normalize_color(xyzrgb[i,4]), normalize_color(xyzrgb[i,5])))  # 将颜色转换为 AutoCAD 颜色
        # 将点添加到 DXF 文件中
        dxf_point = msp.add_point((xyzrgb[:,0], xyzrgb[:,1], xyzrgb[:,2]))
        # 设置附加属性
        dxf_point.dxf.linetype = 'Continuous'  # 点的线型
        dxf_point.dxf.color = 256  # AutoCAD 颜色号  # ['62']
        dxf_point.dxf.true_color = color  # 点的真彩颜色
        dxf_point.dxf.lineweight = 13  # 线宽 单位毫米
    # 保存
    if output is not None:
        doc.saveas(output)  # 保存.dxf
    return doc


def dxf2dwg(doc,output,version='R13',by='C:\\Program Files\\ODA\\ODAFileConverter 25.4.0\\ODAFileConverter.exe'):
    '''
    dxf转dwg
    :param doc: dxf文件类
    :param output: dwg输出路径
    :param version: dwg版本号
    :param by: ODA.exe路径
    '''
    odafc.win_exec_path = by  # 设置软件开源路径
    odafc.export_dwg(doc, output, replace=True, version=version)  # 保存.dwg
