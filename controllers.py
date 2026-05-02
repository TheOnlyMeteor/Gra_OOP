"""
系统控制器文件 (MVC - Controller)
负责统筹数据加载、CRUD操作、调度算法引擎、计算评估指标。
@Author: Met
@Date: 2026-03-12
"""
import csv
import threading
from config import *
from core.models import Node
from utils.data_loader import DataLoader
from utils.path_finding import PathFinder
from core.ga_engine import GASolver
from core.pure_ga_engine import PureGASolver

class SystemController:
    def __init__(self):
        self.nodes = []
        self.capacity = 0
        self.depot_id = 0
        self.grid = None
        self.matrix = None

        self.best_solution = None
        self.pure_solution = None
        self.improved_history = []
        self.pure_history = []
        self.is_running = False

    def load_system_data(self):
        vrp_path = os.path.join(DATA_INPUT_DIR, VRP_FILE)
        map_path = os.path.join(DATA_INPUT_DIR, MAP_FILE)
        self.nodes, self.capacity, self.depot_id = DataLoader.load_vrp(vrp_path)
        self.grid = DataLoader.load_grid_map(map_path)
        self.recalculate_matrix()

    def recalculate_matrix(self):
        finder = PathFinder(self.grid)
        self.matrix = finder.dijkstra_matrix(self.nodes)

    # ================= CRUD与文件导入导出模块 =================
    def get_garbage_points_data(self):
        data = []
        for n in self.nodes:
            type_str = "垃圾处理车场" if n.is_depot else "垃圾收运点"
            # UI 显示的 ID 为底层逻辑 ID + 1
            data.append((n.node_id + 1, type_str, n.x, n.y, n.garbage_volume))
        return data

    def update_nodes_from_ui(self, ui_data_list):
        """
        接收UI层传递的新数据列表，重建系统节点并重算矩阵。
        修复：彻底抛弃UI传来的显示ID，严格按照 0 到 N-1 重新生成连续ID。
        """
        self.nodes = []

        # 使用 enumerate 自动生成 0, 1, 2... 的严格连续序列
        for idx, item in enumerate(ui_data_list):
            actual_node_id = idx  # 核心修复：无视 item[0]，强制底层 ID 连续

            is_depot = (item[1] == "垃圾处理车场")
            # 强制车场的垃圾需求为 0，防止算法引擎容量计算错乱
            garbage_volume = int(item[4]) if not is_depot else 0

            # 实例化节点
            new_node = Node(node_id=actual_node_id, x=int(item[2]), y=int(item[3]),
                            garbage_volume=garbage_volume, is_depot=is_depot)
            self.nodes.append(new_node)

            # 记录最新分配的车场ID
            if is_depot:
                self.depot_id = actual_node_id

        # 因为通过 enumerate 按顺序追加，天然有序，不需要做 sort() 操作了
        # 核心：修改数据后必须重算矩阵
        self.recalculate_matrix()

    def import_from_csv(self, filepath):
        new_ui_data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)
            for idx, row in enumerate(reader):
                if len(row) >= 4:
                    new_ui_data.append((idx + 1, row[0], int(row[1]), int(row[2]), int(row[3])))
        self.update_nodes_from_ui(new_ui_data)

    def export_to_csv(self, filepath):
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['节点类型', 'X坐标', 'Y坐标', '预计垃圾量(kg)'])
            for n in self.nodes:
                type_str = "垃圾处理车场" if n.is_depot else "垃圾收运点"
                writer.writerow([type_str, n.x, n.y, n.garbage_volume])

    # ================= 调度引擎模块 =================
    def run_optimization_async(self, pop_size, generations, progress_callback, finish_callback):
        if self.is_running: return
        self.is_running = True

        def _task():
            customers = [n.node_id for n in self.nodes if not n.is_depot]
            garbage_volumes = [n.garbage_volume for n in self.nodes]

            import config as cfg
            cfg.POP_SIZE = pop_size
            cfg.GENERATIONS = generations
            cfg.CAPACITY = self.capacity

            pure_solver = PureGASolver(self.matrix, garbage_volumes, self.capacity, customers, self.depot_id, cfg)
            pure_solver.generate_initial_population()
            for gen in range(1, generations + 1):
                pure_solver.evolve(gen)
                if gen == 1:
                    print(f"PGA={pure_solver.best_solution.total_cost}")
                progress_callback(int((gen / (generations * 2)) * 100), pure_solver.best_solution.total_cost,
                                  "基础遗传算法评估中...")

            improved_solver = GASolver(self.matrix, garbage_volumes, self.capacity, customers, self.depot_id, cfg)
            improved_solver.generate_initial_population()
            for gen in range(1, generations + 1):
                improved_solver.evolve(gen)
                if gen == 1:
                    print(f"IGA={improved_solver.best_solution.total_cost}")
                progress_callback(50 + int((gen / (generations * 2)) * 100), improved_solver.best_solution.total_cost,
                                  "改进启发式引擎优化中...")

            self.best_solution = improved_solver.best_solution
            self.improved_history = improved_solver.history
            self.pure_solution = pure_solver.best_solution
            self.pure_history = pure_solver.history
            DataLoader.export_solution_to_file(self.best_solution,"data/output/Final_Best_Routes.txt")
            self.is_running = False
            finish_callback()
        threading.Thread(target=_task, daemon=True).start()


    def get_evaluation_metrics(self):
        """
        获取评估指标信息进行展示
        :return: 评估信息
        """
        if not self.best_solution or not self.pure_solution: return None

        # 新增一个辅助计算函数：遍历路线中的节点，去源数据里累加真实垃圾量
        def calculate_load_rate(route):
            # 根据路线中的节点ID，从 self.nodes 中查出真实的垃圾量并累加
            actual_load = sum(self.nodes[nid].garbage_volume for nid in route.nodes)
            return (actual_load / self.capacity) * 100
        # 计算实验组（改进GA）的满载率
        load_rates = [(f"V{i + 1}", (r.load / self.capacity) * 100) for i, r in
                               enumerate(self.best_solution.routes)]

        # 计算对照组（基础GA）的满载率
        load_rates_pure = [(f"V{i + 1}", calculate_load_rate(r)) for i, r in enumerate(self.pure_solution.routes)]
        print(f"PGA车辆满载率:{load_rates_pure}")
        print(f"IGA车辆满载率:{load_rates}")
        return {
            "total_cost_improved": self.best_solution.total_cost,
            "total_cost_pure": self.pure_solution.total_cost,
            "vehicle_count": len(self.best_solution.routes),
            "load_rates": load_rates,
            "history_improved": self.improved_history,
            "history_pure": self.pure_history
        }
