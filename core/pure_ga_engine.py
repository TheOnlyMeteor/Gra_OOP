"""
纯遗传算法求解器（对照组）

该文件实现了纯遗传算法求解器PureGASolver，作为改进版遗传算法的对照组。
主要功能包括：
1. 随机初始化种群（不使用启发式算法）
2. 评估解（仅进行贪心分割，不进行局部优化）
3. 进化过程（精英保留、锦标赛选择、OX交叉、变异）
@Author: Met
@Date: 2026-03-12
"""
import random

from .base_solver import BaseGASolver
from .models import Solution
from .pure_ga_logic import GreedySplitter


class PureGASolver(BaseGASolver):
    """纯遗传算法求解器（对照组）"""

    def __init__(self, matrix, garbage_volume, capacity, customers, depot_id, cfg):
        """初始化求解器
        
        Args:
            matrix: 距离矩阵
            garbage_volume: 需求列表
            capacity: 车辆容量
            customers: 客户列表
            depot_id: 仓库ID
            cfg: 配置对象
        """
        super().__init__(cfg)
        self.matrix = matrix
        self.garbage_volume = garbage_volume
        self.capacity = capacity
        self.customers = customers
        self.depot_id = depot_id
        self.cfg = cfg
        self.population = []

    def generate_initial_population(self):
        """随机初始化种群（不使用启发式算法）
        
        100% 随机生成初始种群，作为对照组
        """
        for _ in range(self.cfg.POP_SIZE):
            tour = random.sample(self.customers, len(self.customers))
            self.population.append(Solution(tour))

    def evaluate_solution(self, sol: Solution):
        """评估解决方案
        
        仅进行贪心分割，不进行任何局部优化
        
        Args:
            sol: 要评估的解决方案
        """
        # 仅使用贪心分割
        cost, routes = GreedySplitter.split(
            sol.chromosome, self.matrix, self.garbage_volume,
            self.cfg.CAPACITY, self.depot_id
        )
        sol.routes = routes
        sol.total_cost = cost
        # 注意：这里不写回染色体，因为没有进行局部路径修改

    def evolve(self, gen):
        """
        执行一代进化
        :param gen: 当前进化代数
        """
        # 1. 评估全员
        for sol in self.population:
            self.evaluate_solution(sol)

        # 2. 排序
        self.population.sort(key=lambda x: x.total_cost)

        # 3. 精英保留
        next_gen = self.population[:self.cfg.ELITE_SIZE]

        # 4. 进化过程（保持与实验组相同的交叉和变异概率）
        rate = self.cfg.MUT_START - (self.cfg.MUT_START - self.cfg.MUT_END) * (gen / self.cfg.GENERATIONS)

        while len(next_gen) < self.cfg.POP_SIZE:
            p1, p2 = self._tournament_select(), self._tournament_select()
            child_chromo = self._ox_crossover(p1.chromosome, p2.chromosome)
            child_chromo = self._mutate(child_chromo, rate)
            next_gen.append(Solution(child_chromo))

        self.population = next_gen
        self.population.sort(key=lambda x: x.total_cost)
        self.record_history()

    def _tournament_select(self):
        """
        锦标赛选择
        随机选择两个个体，返回适应度较好的一个
        :return: Solution: 选择的个体
        """
        a, b = random.sample(self.population, 2)
        return a if a.total_cost < b.total_cost else b

    def _ox_crossover(self, p1, p2):
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

    def _mutate(self, chromo, rate):
        """
        变异操作
        :param chromo: 染色体
        :param rate: 变异概率
        :return: List[int]: 变异后的染色体
        """
        if random.random() < rate:
            # 简单的交换变异
            i, j = random.sample(range(len(chromo)), 2)
            chromo[i], chromo[j] = chromo[j], chromo[i]
        return chromo