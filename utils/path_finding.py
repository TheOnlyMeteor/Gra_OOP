import heapq
import numpy as np

class PathFinder:
    def __init__(self, grid):
        self.grid = grid
        self.moves = [(0,1,1.0),(0,-1,1.0),(1,0,1.0),(-1,0,1.0),(1,1,1.414),(1,-1,1.414),(-1,1,1.414),(-1,-1,1.414)]

    def dijkstra_matrix(self, nodes):
        num = len(nodes)
        matrix = np.zeros((num, num))
        for i in range(num):
            dists = self._dijkstra((nodes[i].x, nodes[i].y))
            for j in range(num):
                matrix[i][j] = dists[nodes[j].x][nodes[j].y]
        return matrix

    def _dijkstra(self, start):
        dists = np.full(self.grid.shape, float('inf'))
        dists[start] = 0
        pq = [(0, start[0], start[1])]
        while pq:
            d, x, y = heapq.heappop(pq)
            if d > dists[x, y]: continue
            for dx, dy, c in self.moves:
                nx, ny = x+dx, y+dy
                if 0 <= nx < self.grid.shape[0] and 0 <= ny < self.grid.shape[1] and self.grid[nx,ny] == 0:
                    if d+c < dists[nx, ny]:
                        dists[nx, ny] = d+c
                        heapq.heappush(pq, (d+c, nx, ny))
        return dists

    # utils/path_finding.py

    def get_a_star_path(self, start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
        """A* 寻路算法实现"""
        if start == end: return [start]

        open_set = []
        # (f_score, count, current_pos)
        heapq.heappush(open_set, (0, 0, start))
        came_from = {}

        g_score = {start: 0}
        f_score = {start: self._heuristic(start, end)}
        count = 0

        while open_set:
            curr = heapq.heappop(open_set)[2]

            if curr == end:
                return self._reconstruct_path(came_from, curr)

            for dx, dy, cost in self.moves:
                neighbor = (curr[0] + dx, curr[1] + dy)

                if 0 <= neighbor[0] < self.grid.shape[0] and 0 <= neighbor[1] < self.grid.shape[1]:
                    if self.grid[neighbor[0], neighbor[1]] == 1: continue  # 障碍物

                    temp_g = g_score[curr] + cost
                    if temp_g < g_score.get(neighbor, float('inf')):
                        came_from[neighbor] = curr
                        g_score[neighbor] = temp_g
                        f_score[neighbor] = temp_g + self._heuristic(neighbor, end)
                        count += 1
                        heapq.heappush(open_set, (f_score[neighbor], count, neighbor))
        return []  # 没找到路

    def _heuristic(self, p1, p2):
        return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5

    def _reconstruct_path(self, came_from, current):
        total_path = [current]
        while current in came_from:
            current = came_from[current]
            total_path.append(current)
        return total_path[::-1]