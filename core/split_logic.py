from typing import List, Tuple
import numpy as np
from .models import Route


class PrinsSplitter:
    @staticmethod
    def split(tour: List[int], matrix: np.ndarray, demands: List[int],
              capacity: int, depot_id: int) -> Tuple[float, List[Route]]:
        n = len(tour)
        if n == 0: return 0.0, []

        f = [float('inf')] * (n + 1)
        f[0] = 0.0
        predecessor = [0] * (n + 1)

        # 预缓存减少访问开销
        dist_to_depot = [matrix[depot_id][node] for node in tour]
        dist_from_depot = [matrix[node][depot_id] for node in tour]

        for i in range(1, n + 1):
            load = 0
            route_dist = 0.0
            for j in range(i, 0, -1):
                curr_node = tour[j - 1]
                load += demands[curr_node]
                if load > capacity: break

                if j < i:
                    route_dist += matrix[curr_node][tour[j]]

                cost = f[j - 1] + dist_to_depot[j - 1] + route_dist + dist_from_depot[i - 1]

                if cost < f[i] - 1e-9:
                    f[i] = cost
                    predecessor[i] = j - 1

        # 回溯构建
        routes = []
        curr = n
        while curr > 0:
            prev = predecessor[curr]
            nodes = tour[prev:curr]
            routes.append(Route(nodes, matrix, depot_id))
            curr = prev
        return f[n], routes[::-1]