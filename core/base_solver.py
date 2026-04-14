"""
基础求解器类
该文件定义了遗传算法求解器的抽象基类BaseGASolver，提供了求解器的基本结构和方法。
@Author: Met
@Date: 2026-03-12
"""
from abc import ABC, abstractmethod
from typing import List
from .models import Solution

class BaseGASolver(ABC):
    """遗传算法求解器的抽象基类"""

    def __init__(self, cfg):
        """
        初始化求解器
        :param cfg: 配置对象，包含算法参数
        """
        self.cfg = cfg
        self.population: List[Solution] = []
        self.history: List[float] = [] # 记录每一代的最优成本

    @abstractmethod
    def evolve(self, gen_idx: int):
        """
        子类必须实现的进化逻辑
        :param gen_idx: 当前进化代数
        """
        pass

    def record_history(self):
        """
        记录当前代的最优解（假设种群已排序）
        """
        if self.population:
            self.history.append(self.population[0].total_cost)

    @property
    def best_solution(self) -> Solution:
        """
        获取当前种群中的最优解
        :return: Solution: 当前最优解对象
        """
        return self.population[0] if self.population else None