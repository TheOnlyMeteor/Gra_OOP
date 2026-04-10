import numpy as np
from typing import List


class Node:
    def __init__(self, node_id: int, x: int, y: int, demand: int = 0, is_depot: bool = False):
        self.node_id = node_id
        self.x, self.y = x, y
        self.demand = demand
        self.is_depot = is_depot


class Route:
    def __init__(self, nodes: List[int], matrix: np.ndarray, depot_id: int):
        self.nodes = nodes  # 客户节点序列
        self.matrix = matrix
        self.depot_id = depot_id
        self.cost = 0.0
        self.load = 0
        self.update_stats()

    def update_stats(self, demand_list: List[int] = None):
        """重新计算路径成本和载重"""
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
        if demand_list:
            self.load = sum(demand_list[n] for n in self.nodes)

    def optimize_2opt(self):
        """行为内敛：路径自己负责内部优化"""
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
    def __init__(self, chromosome: List[int]):
        self.chromosome = chromosome  # 巨型巡游序列
        self.routes: List[Route] = []
        self.total_cost = float('inf')

    def __lt__(self, other):  # 支持直接排序
        return self.total_cost < other.total_cost