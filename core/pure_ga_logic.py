"""
纯遗传算法逻辑文件

该文件实现了纯遗传算法使用的贪心分割器GreedySplitter，用于将染色体（巨型巡游序列）分割成多条满足容量约束的路径。

@Author: Met
@Date: 2026-03-12
"""
from typing import List, Tuple
import numpy as np
from .models import Route


class GreedySplitter:
    """贪心分割器"""

    @staticmethod
    def split(tour: List[int], matrix: np.ndarray, garbage_volume: List[int],
              capacity: int, depot_id: int) -> Tuple[float, List[Route]]:
        """
        贪心分割算法
        最基础的贪心分割：只要装不下了，就回库换一辆车
        :param tour: 客户访问序列
        :param matrix: 距离矩阵
        :param garbage_volume: 需求列表
        :param capacity: 车辆容量
        :param depot_id: 仓库ID
        :return: Tuple[float, List[Route]]: 总成本和路径列表
        """
        routes = []
        current_route_nodes = []
        current_load = 0
        total_cost = 0.0

        for node in tour:
            node_demand = garbage_volume[node]
            # 如果加上这个点就超载了，则当前车结束，结算并换新车
            if current_load + node_demand > capacity:
                if current_route_nodes:
                    route = Route(current_route_nodes, matrix, depot_id)
                    routes.append(route)
                    total_cost += route.cost
                current_route_nodes = [node]
                current_load = node_demand
            else:
                current_route_nodes.append(node)
                current_load += node_demand

        # 处理最后一条路径
        if current_route_nodes:
            route = Route(current_route_nodes, matrix, depot_id)
            routes.append(route)
            total_cost += route.cost

        return total_cost, routes