from abc import ABC, abstractmethod
from typing import List
from .models import Solution

class BaseGASolver(ABC):
    def __init__(self, cfg):
        self.cfg = cfg
        self.population: List[Solution] = []
        self.history: List[float] = [] # 记录每一代的最优成本

    @abstractmethod
    def evolve(self, gen_idx: int):
        """子类必须实现的进化逻辑"""
        pass

    def record_history(self):
        """记录当前代的最优解（假设种群已排序）"""
        if self.population:
            self.history.append(self.population[0].total_cost)

    @property
    def best_solution(self) -> Solution:
        return self.population[0] if self.population else None