# """
# 系统控制器文件 (MVC - Controller)
# 负责统筹数据加载、CRUD操作、调度算法引擎(双算法对比)、计算评估指标。
# @Author: Met
# @Date: 2026-03-12
# """
# import os
# import csv
# import threading
# from config import *
# from core.models import Node
# from utils.data_loader import DataLoader
# from utils.path_finding import PathFinder
# from core.ga_engine import GASolver
# from core.pure_ga_engine import PureGASolver
#
# class SystemController:
#     def __init__(self):
#         """
#         初始化系统控制器
#         初始化系统所需的各种属性和状态
#         """
#         self.nodes = []  # 节点列表
#         self.capacity = 0  # 车辆容量
#         self.depot_id = 0  # 车场节点ID
#         self.grid = None  # 网格地图
#         self.matrix = None  # 距离矩阵
#         self.best_solution = None  # 改进版最优解
#         self.pure_solution = None  # 基础版最优解
#         self.improved_history = []  # 改进版算法历史记录
#         self.pure_history = []  # 基础版算法历史记录
#         self.is_running = False  # 算法运行状态
#
#     def load_system_data(self):
#         """
#         加载初始数据与地图
#         从配置文件指定的路径加载VRP数据和网格地图，并计算距离矩阵
#         """
#         vrp_path = os.path.join(DATA_INPUT_DIR, VRP_FILE)
#         map_path = os.path.join(DATA_INPUT_DIR, MAP_FILE)
#
#         self.nodes, self.capacity, self.depot_id = DataLoader.load_vrp(vrp_path)
#         self.grid = DataLoader.load_grid_map(map_path)
#         self.recalculate_matrix()
#
#     def recalculate_matrix(self):
#         """
#         重新计算距离矩阵
#         在CRUD修改节点后调用，使用Dijkstra算法计算所有节点之间的最短路径
#         """
#         finder = PathFinder(self.grid)
#         self.matrix = finder.dijkstra_matrix(self.nodes)
#
#     # ================= CRUD与文件导入导出模块 =================
#     def get_garbage_points_data(self):
#         """
#         为 UI 层提供垃圾点视图数据
#         :return: list: 包含垃圾点信息的列表，每个元素为 (node_id, type_str, x, y, garbage_volume)
#         """
#         data = []
#         for n in self.nodes:
#             type_str = "垃圾处理车场" if n.is_depot else "垃圾收运点"
#             data.append((n.node_id, type_str, n.x, n.y, n.garbage_volume))
#         return data
#
#     def update_nodes_from_ui(self, ui_data_list):
#         """
#         接收UI层传递的新数据列表，重建系统节点并重算矩阵
#         :param ui_data_list: UI层传递的数据列表，每个元素为 (node_id, type_str, x, y, garbage_volume)
#         """
#         self.nodes = []
#         for idx, item in enumerate(ui_data_list):
#             # item 格式: (node_id, type_str, x, y, garbage_volume)
#             is_depot = (item[1] == "垃圾处理车场")
#             garbage_volume = int(item[4]) if not is_depot else 0
#             new_node = Node(node_id=idx, x=int(item[2]), y=int(item[3]), garbage_volume=garbage_volume, is_depot=is_depot)
#             self.nodes.append(new_node)
#             if is_depot:
#                 self.depot_id = idx
#
#         self.recalculate_matrix() # 核心：修改数据后必须重算矩阵！
#
#     def import_from_csv(self, filepath):
#         """
#         从CSV导入数据
#         :param filepath: CSV文件路径
#         """
#         new_ui_data = []
#         with open(filepath, 'r', encoding='utf-8') as f:
#             reader = csv.reader(f)
#             next(reader) # 跳过表头
#             for idx, row in enumerate(reader):
#                 if len(row) >= 4:
#                     new_ui_data.append((idx, row[0], int(row[1]), int(row[2]), int(row[3])))
#         self.update_nodes_from_ui(new_ui_data)
#
#     def export_to_csv(self, filepath):
#         """
#         导出数据到CSV
#         :param filepath: CSV文件路径
#         """
#         with open(filepath, 'w', newline='', encoding='utf-8') as f:
#             writer = csv.writer(f)
#             writer.writerow(['节点类型', 'X坐标', 'Y坐标', '预计垃圾量(kg)'])
#             for n in self.nodes:
#                 type_str = "垃圾处理车场" if n.is_depot else "垃圾收运点"
#                 writer.writerow([type_str, n.x, n.y, n.garbage_volume])
#
#     # ================= 调度引擎模块 (双算法运行) =================
#     def run_optimization_async(self, pop_size, generations, progress_callback, finish_callback):
#         """
#         异步执行两种算法，用于论文对比
#         :param pop_size: 种群规模
#         :param generations: 迭代代数
#         :param progress_callback: 进度回调函数，接收 (percent, cost, stage_str) 参数
#         :param finish_callback: 完成回调函数
#         """
#         # 检查是否已经有算法在运行
#         if self.is_running: return
#         # 设置运行状态为True，防止重复执行
#         self.is_running = True
#
#         # 定义异步任务函数
#         def _task():
#             # 提取客户节点ID列表（排除车场）
#             customers = [n.node_id for n in self.nodes if not n.is_depot]
#             # 提取所有节点的垃圾量（包括车场，车场垃圾量为0）
#             garbage_volumes = [n.garbage_volume for n in self.nodes]
#
#             # 动态更新配置参数
#             import config as cfg
#             cfg.POP_SIZE = pop_size  # 设置种群规模
#             cfg.GENERATIONS = generations  # 设置迭代代数
#             cfg.CAPACITY = self.capacity  # 设置车辆容量
#
#             # 1. 运行基础版 GA (对照组)
#             # 初始化基础版遗传算法求解器
#             pure_solver = PureGASolver(self.matrix, garbage_volumes, self.capacity, customers, self.depot_id, cfg)
#             # 生成初始种群
#             pure_solver.generate_initial_population()
#             # 迭代进化
#             for gen in range(1, generations + 1):
#                 # 执行一代进化
#                 pure_solver.evolve(gen)
#                 # 计算进度（基础GA占总进度的前50%）
#                 progress = int((gen / (generations * 2)) * 100) # 占前50%进度
#                 # 调用进度回调函数，更新UI
#                 progress_callback(progress, pure_solver.best_solution.total_cost, "基础遗传算法评估中...")
#
#             # 2. 运行改进版 GA (实验组)
#             # 初始化改进版遗传算法求解器
#             improved_solver = GASolver(self.matrix, garbage_volumes, self.capacity, customers, self.depot_id, cfg)
#             # 生成初始种群
#             improved_solver.generate_initial_population()
#             # 迭代进化
#             for gen in range(1, generations + 1):
#                 # 执行一代进化
#                 improved_solver.evolve(gen)
#                 # 计算进度（改进GA占总进度的后50%）
#                 progress = 50 + int((gen / (generations * 2)) * 100) # 占后50%进度
#                 # 调用进度回调函数，更新UI
#                 progress_callback(progress, improved_solver.best_solution.total_cost, "改进启发式引擎优化中...")
#
#             # 保存结果供报表读取
#             self.best_solution = improved_solver.best_solution  # 保存改进版最优解
#             self.improved_history = improved_solver.history  # 保存改进版算法历史记录
#             self.pure_solution = pure_solver.best_solution  # 保存基础版最优解
#             self.pure_history = pure_solver.history  # 保存基础版算法历史记录
#
#             # 重置运行状态
#             self.is_running = False
#             # 调用完成回调函数，通知UI计算完成
#             finish_callback()
#
#         # 创建并启动后台线程执行任务
#         threading.Thread(target=_task, daemon=True).start()
#
#     def get_evaluation_metrics(self):
#         """
#         获取图表所需数据
#         :return:
#             dict: 包含评估指标的字典，包括:
#                 - total_cost_improved: 改进版算法的总成本
#                 - total_cost_pure: 基础版算法的总成本
#                 - vehicle_count: 车辆数量
#                 - load_rates: 各车辆的负载率
#                 - history_improved: 改进版算法的历史记录
#                 - history_pure: 基础版算法的历史记录
#             None: 如果没有最优解
#         """
#         if not self.best_solution: return None
#
#         load_rates = []
#         for i, r in enumerate(self.best_solution.routes):
#             load_rate = (r.load / self.capacity) * 100
#             load_rates.append((f"V{i+1}", load_rate))
#
#         return {
#             "total_cost_improved": self.best_solution.total_cost,
#             "total_cost_pure": self.pure_solution.total_cost,
#             "vehicle_count": len(self.best_solution.routes),
#             "load_rates": load_rates,
#             "history_improved": self.improved_history,
#             "history_pure": self.pure_history
#         }

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