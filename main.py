import config as cfg
import os

from gui.renderer import SimulationApp
from utils.data_loader import DataLoader
from utils.path_finding import PathFinder
from utils.visualizer import GAVisualizer
from core.ga_engine import GASolver
from core.pure_ga_engine import PureGASolver


class VRPExperiment:
    """实验管理类：负责运行不同算法并对比"""

    def __init__(self):
        # 1. 初始化数据
        vrp_path = os.path.join(cfg.DATA_INPUT_DIR, cfg.VRP_FILE)
        self.nodes, capacity, self.depot_id = DataLoader.load_vrp(vrp_path)
        self.grid = DataLoader.load_grid_map(os.path.join(cfg.DATA_INPUT_DIR, cfg.MAP_FILE))
        #距离矩阵计算
        finder = PathFinder(self.grid)
        self.matrix = finder.dijkstra_matrix(self.nodes)
        #求解器配置
        self.customers = [n.node_id for n in self.nodes if not n.is_depot]
        self.demands = [n.demand for n in self.nodes]
        cfg.CAPACITY = capacity #动态注入文件读取的容量

    def run(self):
        # 2. 创建不同的求解器对象
        improved_solver = GASolver(self.matrix, self.demands, cfg.CAPACITY,
                                   self.customers, self.depot_id, cfg)
        pure_solver = PureGASolver(self.matrix, self.demands, cfg.CAPACITY,
                                   self.customers, self.depot_id, cfg)

        # 3. 运行进化
        print("正在运行实验...")
        improved_solver.generate_initial_population()
        pure_solver.generate_initial_population()
        #进化过程
        for gen in range(1, cfg.GENERATIONS + 1):
            improved_solver.evolve(gen)
            pure_solver.evolve(gen)
            if gen % 50 == 0 or gen == 1:
                print(
                    f"Gen {gen:3d} | Best Cost: {improved_solver.population[0].total_cost:.2f} | Cache: {len(improved_solver.fitness_cache)}"
                )
                print(f"Progress: {gen}/{cfg.GENERATIONS} generations complete.")

        # 4. 使用可视化对象进行展示
        viz = GAVisualizer(cfg.VRP_FILE)

        # A.绘制进化对比曲线
        viz.plot_comparison({
            "Improved GA": improved_solver,
            "Pure GA": pure_solver
        },os.path.join(cfg.DATA_OUTPUT_DIR,"fitness_comparison.png"))

        # B.绘制改进版的最优路线图
        viz.plot_solution_routes(
            self.nodes,
            improved_solver.best_solution,
            os.path.join(cfg.DATA_OUTPUT_DIR,"routes_improved.png"),
            "improved GA"
        )

        # C.绘制对照组的最优路线图
        viz.plot_solution_routes(
            self.nodes,
            pure_solver.best_solution,
            os.path.join(cfg.DATA_OUTPUT_DIR,"routes_pure.png"),
            "pure GA"
        )
        # 5. 打印对比总结
        self._print_summary(improved_solver,pure_solver)

        #结果展示
        best_sol = improved_solver.population[0]
        print(f"\n求解完成！最优成本：{best_sol.total_cost:.2f},使用车辆数: {len(best_sol.routes)}")
        app = SimulationApp(self.nodes,self.grid,best_sol)
        app.run()



    def _print_summary(self, s1, s2):
        print("\n" + "=" * 40)
        print(f"实验总结:")
        print(f"改进版最终成本: {s1.best_solution.total_cost:.2f}")
        print(f"对照组最终成本: {s2.best_solution.total_cost:.2f}")
        improvement = (s2.best_solution.total_cost - s1.best_solution.total_cost) / s2.best_solution.total_cost
        print(f"相对精度提升: {improvement * 100:.2f}%")
        print("=" * 40)



if __name__ == "__main__":
    exp = VRPExperiment()
    exp.run()