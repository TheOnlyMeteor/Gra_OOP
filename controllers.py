"""
系统控制器文件 (MVC - Controller)
负责统筹数据加载、CRUD操作、调度算法引擎、计算评估指标。
@Author: Met
@Date: 2026-03-12
"""
import os
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

    # def update_nodes_from_ui(self, ui_data_list):
    #     self.nodes = []
    #     # 无论UI如何增删，底层严格按照顺序 0 到 N-1 重新洗牌索引
    #     for item in ui_data_list:
    #         # item[0] 是显示ID（UI显示的ID），需要转换为底层索引
    #         display_id = int(item[0])
    #         actual_node_id = display_id - 1  # 显示ID是 node_id + 1
    #
    #         is_depot = (item[1] == "垃圾处理车场")
    #         # 强制车场的垃圾需求为 0，防止算法引擎容量计算错乱
    #         garbage_volume = int(item[4]) if not is_depot else 0
    #
    #         # 使用 actual_node_id 而不是 enumerate 的 idx
    #         new_node = Node(node_id=actual_node_id, x=int(item[2]), y=int(item[3]), garbage_volume=garbage_volume, is_depot=is_depot)
    #         self.nodes.append(new_node)
    #         if is_depot:
    #             self.depot_id = actual_node_id
    #
    #     # 按 node_id 排序，确保 nodes 列表的顺序与 node_id 一致
    #     self.nodes.sort(key=lambda n: n.node_id)
    #     # 重新验证 depot_id
    #     for n in self.nodes:
    #         if n.is_depot:
    #             self.depot_id = n.node_id
    #             break
    #
    #     self.recalculate_matrix()
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
                progress_callback(int((gen / (generations * 2)) * 100), pure_solver.best_solution.total_cost,
                                  "基础遗传算法评估中...")

            improved_solver = GASolver(self.matrix, garbage_volumes, self.capacity, customers, self.depot_id, cfg)
            improved_solver.generate_initial_population()
            for gen in range(1, generations + 1):
                improved_solver.evolve(gen)
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
        if not self.best_solution: return None
        load_rates = [(f"V{i + 1}", (r.load / self.capacity) * 100) for i, r in enumerate(self.best_solution.routes)]
        return {
            "total_cost_improved": self.best_solution.total_cost,
            "total_cost_pure": self.pure_solution.total_cost,
            "vehicle_count": len(self.best_solution.routes),
            "load_rates": load_rates,
            "history_improved": self.improved_history,
            "history_pure": self.pure_history
        }

    def get_routes_data_for_sim(self):
        """
        提取用于独立进程仿真的纯数据。
        自动检测 Route 类中用于存储节点序列的变量名。
        """
        if not getattr(self, 'best_solution', None) or not self.best_solution.routes:
            return []

        routes_data = []
        for route in self.best_solution.routes:
            # 自动适配你在 models.py 中给路线定义的实际属性名
            if hasattr(route, 'nodes'):
                routes_data.append(route.nodes)
            elif hasattr(route, 'route'):
                routes_data.append(route.route)
            elif hasattr(route, 'node_list'):
                routes_data.append(route.node_list)
            elif hasattr(route, 'path'):
                routes_data.append(route.path)
            else:
                # 如果都不是，直接打印出 Route 类所有的变量名，方便咱们排查
                print("请检查 models.py 中 Route 类的变量名！当前 Route 的属性有：", route.__dict__.keys())
                break

        return routes_data