"""
系统控制器文件 (MVC - Controller)
负责统筹数据加载、调度算法引擎、计算评估指标，并为 UI 层提供面向对象的接口。
@Author: Met
@Date: 2026-03-12
"""
import os
import threading
from config import *
from utils.data_loader import DataLoader
from utils.path_finding import PathFinder
from core.ga_engine import GASolver


class SystemController:
    def __init__(self):
        self.nodes = []
        self.capacity = 0
        self.depot_id = 0
        self.grid = None
        self.matrix = None
        self.best_solution = None
        self.solver = None
        self.is_running = False

    def load_system_data(self):
        """加载垃圾点网络数据与地图"""
        vrp_path = os.path.join(DATA_INPUT_DIR, VRP_FILE)
        map_path = os.path.join(DATA_INPUT_DIR, MAP_FILE)

        self.nodes, self.capacity, self.depot_id = DataLoader.load_vrp(vrp_path)
        self.grid = DataLoader.load_grid_map(map_path)

        finder = PathFinder(self.grid)
        self.matrix = finder.dijkstra_matrix(self.nodes)

    def get_garbage_points_data(self):
        """为 UI 层提供垃圾点视图数据"""
        data = []
        for n in self.nodes:
            # 业务化命名转换：is_depot -> 是否为车场，garbage_volume -> 预计垃圾量
            type_str = "垃圾处理车场" if n.is_depot else "垃圾收运点"
            data.append((n.node_id + 1, type_str, n.x, n.y, n.garbage_volume))
        return data

    def run_optimization_async(self, pop_size, generations, progress_callback, finish_callback):
        """使用多线程异步执行算法，避免阻塞 GUI 界面"""
        if self.is_running: return
        self.is_running = True

        def _task():
            customers = [n.node_id for n in self.nodes if not n.is_depot]
            garbage_volume = [n.garbage_volume for n in self.nodes]

            # 动态覆盖配置
            import config as cfg
            cfg.POP_SIZE = pop_size
            cfg.GENERATIONS = generations
            cfg.CAPACITY = self.capacity

            self.solver = GASolver(self.matrix, garbage_volume, self.capacity, customers, self.depot_id, cfg)
            self.solver.generate_initial_population()

            for gen in range(1, generations + 1):
                self.solver.evolve(gen)
                # 计算进度百分比并回调给 UI 更新进度条
                progress = int((gen / generations) * 100)
                progress_callback(progress, self.solver.best_solution.total_cost)

            self.best_solution = self.solver.best_solution
            self.is_running = False
            finish_callback()  # 通知 UI 计算完成

        # 启动后台线程
        threading.Thread(target=_task, daemon=True).start()

    def get_evaluation_metrics(self):
        """获取运输效率评估指标（为图表提供数据）"""
        if not self.best_solution: return None

        load_rates = []
        route_costs = []
        for i, r in enumerate(self.best_solution.routes):
            load_rate = (r.load / self.capacity) * 100
            load_rates.append((f"Vehicle {i + 1}", load_rate))
            route_costs.append(r.cost)

        return {
            "total_cost": self.best_solution.total_cost,
            "vehicle_count": len(self.best_solution.routes),
            "load_rates": load_rates,  # 车辆满载率
            "evolution_history": self.solver.history  # 进化收敛数据
        }