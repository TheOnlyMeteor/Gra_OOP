from typing import List, Tuple
import numpy as np
from .models import Route


class GreedySplitter:
    @staticmethod
    def split(tour: List[int], matrix: np.ndarray, demands: List[int],
              capacity: int, depot_id: int) -> Tuple[float, List[Route]]:
        """最基础的贪心分割：只要装不下了，就回库换一辆车"""
        routes = []
        current_route_nodes = []
        current_load = 0
        total_cost = 0.0

        for node in tour:
            node_demand = demands[node]
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