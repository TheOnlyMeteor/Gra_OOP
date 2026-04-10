import random

from .base_solver import BaseGASolver
from .models import Solution
from .pure_ga_logic import GreedySplitter


class PureGASolver(BaseGASolver):
    def __init__(self, matrix, demands, capacity, customers, depot_id, cfg):
        super().__init__(cfg)
        self.matrix = matrix
        self.demands = demands
        self.capacity = capacity
        self.customers = customers
        self.depot_id = depot_id
        self.cfg = cfg
        self.population = []

    def generate_initial_population(self):
        """对照组：100% 随机初始化，不使用任何启发式算法"""
        for _ in range(self.cfg.POP_SIZE):
            tour = random.sample(self.customers, len(self.customers))
            self.population.append(Solution(tour))

    def evaluate_solution(self, sol: Solution):
        """对照组：仅进行贪心分割，不进行任何局部优化"""
        # 仅使用贪心分割
        cost, routes = GreedySplitter.split(
            sol.chromosome, self.matrix, self.demands,
            self.cfg.CAPACITY, self.depot_id
        )
        sol.routes = routes
        sol.total_cost = cost
        # 注意：这里不写回染色体，因为没有进行局部路径修改

    def evolve(self, gen):
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
        a, b = random.sample(self.population, 2)
        return a if a.total_cost < b.total_cost else b

    def _ox_crossover(self, p1, p2):
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
        if random.random() < rate:
            # 简单的交换变异
            i, j = random.sample(range(len(chromo)), 2)
            chromo[i], chromo[j] = chromo[j], chromo[i]
        return chromo