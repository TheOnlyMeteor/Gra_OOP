"""
改进版遗传算法求解器

该文件实现了改进版的遗传算法求解器GASolver，继承自BaseGASolver。
主要功能包括：
1. 混合初始化种群（NN启发式 + 随机）
2. 评估解（包含分割、局部搜索优化）
3. 进化过程（精英保留、锦标赛选择、OX交叉、变异）
4. 不同路径间的节点交换优化
5. 适应度缓存机制
@Author: Met
@Date: 2026-03-12
"""
import random
from typing import List, Dict, Tuple
from .models import Solution, Route
from .split_logic import PrinsSplitter
from .base_solver import BaseGASolver


class GASolver(BaseGASolver):
    """改进版遗传算法求解器"""
    def __init__(self, matrix, demands, capacity, customers, depot_id, cfg):
        """
        初始化求解器
        :param matrix: 距离矩阵
        :param demands: 需求列表
        :param capacity: 车辆容量
        :param customers: 客户列表
        :param depot_id: 仓库ID
        :param cfg: 配置对象
        """
        super().__init__(cfg)
        self.matrix = matrix
        self.demands = demands
        self.capacity = capacity
        self.customers = customers
        self.depot_id = depot_id
        self.cfg = cfg
        self.population: List[Solution] = []
        self.fitness_cache: Dict[Tuple[int, ...], Tuple[float, List[Route], List[int]]] = {}

    def generate_initial_population(self):
        """
        混合初始化种群（NN启发式 + 随机）
        前一半个体使用最近邻启发式生成，后一半使用随机生成
        """
        for i in range(self.cfg.POP_SIZE):
            if i < self.cfg.POP_SIZE // 2:
                tour = self.__nn_heuristic()
            else:
                tour = random.sample(self.customers, len(self.customers))
            self.population.append(Solution(tour))

    def __nn_heuristic(self):
        """
        最近邻启发式算法生成初始解
        :return: List[int]: 生成的客户访问序列
        """
        unvisited = set(self.customers)
        curr = random.choice(list(unvisited))
        tour = [curr]
        unvisited.remove(curr)
        while unvisited:
            curr = min(unvisited, key=lambda x: self.matrix[curr][x])
            tour.append(curr)
            unvisited.remove(curr)
        return tour

    def evaluate_solution(self, sol: Solution):
        """
        评估解决方案
        包含分割、局部搜索优化和结果写回
        :param sol: 要评估的解决方案
        """
        key = tuple(sol.chromosome)
        if key in self.fitness_cache:
            sol.total_cost, sol.routes, sol.chromosome = self.fitness_cache[key]
            return

        # 1. Split
        cost, routes = PrinsSplitter.split(sol.chromosome, self.matrix, self.demands,
                                           self.cfg.CAPACITY, self.depot_id)

        # 2. Local Search (Intra-route)
        for r in routes:
            r.optimize_2opt()
            r.update_stats(self.demands)  # 更新载重

        # 3. Local Search (Inter-route - 务实地写在这里提升速度)
        self.__inter_route_swap(routes)

        # 4. 写回属性
        sol.routes = routes
        sol.total_cost = sum(r.cost for r in routes)
        sol.chromosome = [n for r in routes for n in r.nodes]  # Lamarckian

        # 5. 存入缓存
        self.fitness_cache[key] = (sol.total_cost, sol.routes, sol.chromosome)

    def __inter_route_swap(self, routes: List[Route]):
        """
        不同路径间的节点交换优化
        尝试在不同路径之间交换节点，以减少总成本
        :param routes: 路径列表
        """
        for _ in range(1):  # 仅做一次Full Pass平衡时间
            improved = False
            for i in range(len(routes)):
                for idx_i, u in enumerate(routes[i].nodes):
                    for j in range(i + 1, len(routes)):
                        for idx_j, v in enumerate(routes[j].nodes):
                            # 容量约束
                            if routes[i].load - self.demands[u] + self.demands[v] > self.cfg.CAPACITY: continue
                            if routes[j].load - self.demands[v] + self.demands[u] > self.cfg.CAPACITY: continue

                            r1, r2 = routes[i].nodes, routes[j].nodes
                            u_p = self.depot_id if idx_i == 0 else r1[idx_i - 1]
                            u_n = self.depot_id if idx_i == len(r1) - 1 else r1[idx_i + 1]
                            v_p = self.depot_id if idx_j == 0 else r2[idx_j - 1]
                            v_n = self.depot_id if idx_j == len(r2) - 1 else r2[idx_j + 1]

                            old_d = self.matrix[u_p][u] + self.matrix[u][u_n] + self.matrix[v_p][v] + self.matrix[v][
                                v_n]
                            new_d = self.matrix[u_p][v] + self.matrix[v][u_n] + self.matrix[v_p][u] + self.matrix[u][
                                v_n]

                            if new_d < old_d - 1e-9:
                                r1[idx_i], r2[idx_j] = v, u
                                routes[i].update_stats(self.demands)
                                routes[j].update_stats(self.demands)
                                improved = True
                                break
                        if improved: break
                if improved: break

    def evolve(self, gen):
        """
        执行一代进化
        :param gen: 当前进化代数
        """
        rate = self.cfg.MUT_START - (self.cfg.MUT_START - self.cfg.MUT_END) * (gen / self.cfg.GENERATIONS)

        # 1. 评估
        for sol in self.population:
            self.evaluate_solution(sol)

        # 2. 排序与精英保留
        self.population.sort()
        next_gen = self.population[:self.cfg.ELITE_SIZE]

        # 3. 繁殖
        while len(next_gen) < self.cfg.POP_SIZE:
            p1 = self.__tournament()
            p2 = self.__tournament()
            child_chromo = self.__ox_crossover(p1.chromosome, p2.chromosome)
            child_chromo = self.__mutate(child_chromo, rate)
            next_gen.append(Solution(child_chromo))

        self.population = next_gen
        self.population.sort() #使用模型内置的__lt__排序
        self.record_history() #统一记录历史

    def __tournament(self):
        """
        锦标赛选择
        随机选择两个个体，返回适应度较好的一个
        :return: Solution: 选择的个体
        """
        a, b = random.sample(self.population, 2)
        return a if a.total_cost < b.total_cost else b

    def __ox_crossover(self, p1, p2):
        """
        OX交叉操作
        :param p1: 父代1的染色体
        :param p2: 父代2的染色体
        :return: List[int]: 生成的子代染色体
        """
        size = len(p1)
        a, b = sorted(random.sample(range(size), 2))
        child = [-1] * size
        child[a:b] = p1[a:b]
        p2_fill = [n for n in p2 if n not in set(child)]
        idx = 0
        for i in range(size):
            if child[i] == -1:
                child[i] = p2_fill[idx]
                idx += 1
        return child

    def __mutate(self, chromo, rate):
        """
        变异操作
        :param chromo: 染色体
        :param rate: 变异概率
        :return: List[int]: 变异后的染色体
        """
        if random.random() < rate:
            if random.random() < 0.6:  # 逆转
                a, b = sorted(random.sample(range(len(chromo)), 2))
                chromo[a:b] = chromo[a:b][::-1]
            else:  # 交换
                i, j = random.sample(range(len(chromo)), 2)
                chromo[i], chromo[j] = chromo[j], chromo[i]
        return chromo