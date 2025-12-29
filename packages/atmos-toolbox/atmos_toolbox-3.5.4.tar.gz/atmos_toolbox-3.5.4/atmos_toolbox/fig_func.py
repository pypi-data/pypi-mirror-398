
import numpy as np
import matplotlib.path as mplPath

#%%

def bb_2d(b_lon, b_lat, lon_w, lat_w, b_gap=1, r0=-1e-8): #radius,
    
    """
    full name: boundary_bool_2d
    """
      
    boundary = []
    for i in np.arange(0, len(b_lon), int(b_gap)):
        AAA = (b_lon[i], b_lat[i]);
        boundary.append(AAA)
    bbPath = mplPath.Path(np.array(boundary))
    
    Lon_w, Lat_w = np.meshgrid(lon_w, lat_w)
    grid = np.zeros(Lat_w.shape)
    for xaa in lon_w:
        for yaa in lat_w:
            aaa = (xaa,yaa)
            if (bbPath.contains_point(aaa, radius=r0)==1): #radius = radius
                grid[lat_w==yaa,
                     lon_w==xaa] = 1

    return grid


def extract_boundary(arr, direction='south'):
    """
    提取二维0-1数组的指定方向边界
    
    参数:
        arr: 二维numpy数组或列表，包含0和1
        direction: 字符串，指定边界方向
                  'south' - 南部边界（每列最下方的1）
                  'north' - 北部边界（每列最上方的1）
                  'east' - 东部边界（每行最右方的1）
                  'west' - 西部边界（每行最左方的1）
    
    返回:
        相同大小的数组，只保留指定边界的1值，其他位置为0
    """
    # 转换为numpy数组以便处理
    arr = np.array(arr)
    rows, cols = arr.shape
    
    # 创建全零的结果数组
    result = np.zeros_like(arr)
    
    if direction.lower() == 'south':
        # 南部边界：遍历每一列，找到每列最下方的1
        for col in range(cols):
            for row in range(rows - 1, -1, -1):
                if arr[row, col] == 1:
                    result[row, col] = 1
                    break
                    
    elif direction.lower() == 'north':
        # 北部边界：遍历每一列，找到每列最上方的1
        for col in range(cols):
            for row in range(rows):
                if arr[row, col] == 1:
                    result[row, col] = 1
                    break
                    
    elif direction.lower() == 'east':
        # 东部边界：遍历每一行，找到每行最右方的1
        for row in range(rows):
            for col in range(cols - 1, -1, -1):
                if arr[row, col] == 1:
                    result[row, col] = 1
                    break
                    
    elif direction.lower() == 'west':
        # 西部边界：遍历每一行，找到每行最左方的1
        for row in range(rows):
            for col in range(cols):
                if arr[row, col] == 1:
                    result[row, col] = 1
                    break
                    
    else:
        raise ValueError("direction必须是'south', 'north', 'east', 'west'之一")
    
    return result