"""
模型定义文件
该文件定义了CVRP问题的核心模型类，包括：
1. Node: 表示客户或仓库节点
2. Route: 表示一条配送路径
3. Solution: 表示一个完整的解决方案
@Author: Met
@Date: 2026-03-12
"""
import numpy as np
from typing import List


class Node:
    """表示客户或仓库节点"""
    def __init__(self, node_id: int, x: int, y: int, garbage_volume: int = 0, is_depot: bool = False):
        """
        初始化节点
        :param node_id: 节点ID
        :param x: x坐标
        :param y: y坐标
        :param garbage_volume: 需求（默认为0）
        :param is_depot: 是否为仓库（默认为False）
        """
        self.node_id = node_id
        self.x, self.y = x, y
        self.garbage_volume = garbage_volume
        self.is_depot = is_depot


class Route:
    """表示一条配送路径"""

    def __init__(self, nodes: List[int], matrix: np.ndarray, depot_id: int):
        """
        初始化路径
        :param nodes: 客户节点序列
        :param matrix: 距离矩阵
        :param depot_id: 仓库ID
        """
        self.nodes = nodes  # 客户节点序列
        self.matrix = matrix
        self.depot_id = depot_id
        self.cost = 0.0
        self.load = 0
        self.update_stats()

    def update_stats(self, garbage_volume_list: List[int] = None):
        """
        重新计算路径成本和载重
        :param garbage_volume_list: 需求列表（可选）
        """
        if not self.nodes:
            self.cost, self.load = 0.0, 0
            return

        # 计算成本
        c = self.matrix[self.depot_id][self.nodes[0]]
        for i in range(len(self.nodes) - 1):
            c += self.matrix[self.nodes[i]][self.nodes[i + 1]]
        c += self.matrix[self.nodes[-1]][self.depot_id]
        self.cost = c

        # 计算载重
        if garbage_volume_list:
            self.load = sum(garbage_volume_list[n] for n in self.nodes)

    def optimize_2opt(self):
        """
        使用2-opt算法优化路径
        2-opt算法通过交换路径中的两个节点顺序来减少路径长度
        """
        n = len(self.nodes)
        if n < 2: return

        best_nodes = self.nodes[:]
        improved = True
        while improved:
            improved = False
            for i in range(n):
                for j in range(i + 1, n):
                    # 确定A, B, C, D四个点
                    a = self.depot_id if i == 0 else best_nodes[i - 1]
                    b = best_nodes[i]
                    c = best_nodes[j]
                    d = self.depot_id if j == n - 1 else best_nodes[j + 1]

                    # 距离差值计算 (First Improvement)
                    if self.matrix[a][c] + self.matrix[b][d] < self.matrix[a][b] + self.matrix[c][d] - 1e-9:
                        best_nodes[i:j + 1] = best_nodes[i:j + 1][::-1]
                        improved = True
                        break
                if improved: break
        self.nodes = best_nodes
        self.update_stats()


class Solution:
    """表示一个完整的解决方案"""

    def __init__(self, chromosome: List[int]):
        """
        初始化解决方案
        :param chromosome: 巨型巡游序列
        """
        self.chromosome = chromosome  # 巨型巡游序列
        self.routes: List[Route] = []
        self.total_cost = float('inf')

    def __lt__(self, other):
        """
        支持直接排序，根据总成本比较
        :param other: 另一个Solution对象
        :return: bool: 如果当前解决方案的成本小于另一个，则返回True
        """
        return self.total_cost < other.total_cost