import numpy as np
from scipy.ndimage import distance_transform_cdt

def dfs(grid, row, col, visited, label):
    # 定义八个方向的移动
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]
    
    # 标记当前位置已访问
    visited[row][col] = True
    
    # 标记当前位置为指定标签
    grid[row][col] = label
    
    # 初始化当前连通区域中1的数量
    count = 1
    
    # 遍历当前位置的八个相邻位置
    for dr, dc in directions:
        r = row + dr
        c = col + dc
        
        # 检查相邻位置是否有效，并且是未访问过的1
        if 0 <= r < grid.shape[0] and 0 <= c < grid.shape[1] and grid[r][c] == 1 and not visited[r][c]:
            # 递归调用DFS
            count += dfs(grid, r, c, visited, label)
    
    return count

def mark_cont_area(grid, min_points):
    '''

    Parameters
    ----------
    grid : consists of 0 and 1.

    '''
    rows, cols = grid.shape
    visited = np.zeros((rows, cols), dtype=bool)
    label = 100  # 需要大于1，且下面也要跟随变化
    
    # 遍历整个矩阵
    for i in range(rows):
        for j in range(cols):
            # 如果当前位置是未访问过的1，则进行DFS，并标记连续区域
            if grid[i][j] == 1 and not visited[i][j]:
                ones_count = dfs(grid, i, j, visited, label)
                if ones_count < min_points:
                    # 连通区域中1的数量少于阈值，将其标记为0
                    grid[grid == label] = 0
                label += 1
    
    # 重新分配标签，使得标签按照间隔为1的自然数排列
    new_label = 1
    for i in range(100, label):
        if np.any(grid == i):
            grid[grid == i] = new_label
            new_label += 1
    
    return grid


def fill_only1gap(matrix):
    rows, cols = matrix.shape
    helper_matrix = np.zeros((rows, cols), dtype=int)

    # 遍历原始矩阵
    for i in range(rows):
        for j in range(cols):
            # 检查左右相邻位置
            if j > 0 and j < cols - 1 and matrix[i][j-1] == 1 and matrix[i][j+1] == 1:
                helper_matrix[i][j] = 1
            # 检查上下相邻位置
            elif i > 0 and i < rows - 1 and matrix[i-1][j] == 1 and matrix[i+1][j] == 1:
                helper_matrix[i][j] = 1
    
    # 将原始矩阵与辅助矩阵逐元素相加
    result_matrix = matrix + helper_matrix
    
    # 将结果矩阵中大于1的元素设为1
    result_matrix[result_matrix > 1] = 1
    
    return result_matrix




def expand_mask_mh(mask, k):
    """
    使用曼哈顿距离 (taxicab) 将不规则区域向外扩张 k 个格点。

    参数
    ----
    mask : 2D numpy array
        0/1 或 bool 类型的二维数组，1/True 为区域，0/False 为背景。
    k : int
        向外扩张的格点数（曼哈顿距离）。
    
    返回
    ----
    expanded_mask : 2D numpy array (uint8)
        扩张后的 0/1 mask。
    """
    
    mask = np.asarray(mask)
    
    if mask.ndim != 2:
        raise ValueError("mask 必须是二维数组")
    
    if k < 0:
        raise ValueError("k 必须是非负整数")
    
    # outside=True 表示区域外的点
    outside = (mask == 0)

    # 曼哈顿距离变换（城市街区距离）
    dist = distance_transform_cdt(outside, metric='taxicab')

    # 在外部区域中，距离 <= k 的加入区域
    grown_part = (dist > 0) & (dist <= k)

    expanded = mask.astype(bool) | grown_part

    return expanded.astype(np.uint8)
