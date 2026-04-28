"""
CVRP 算法批量自动化测试脚本 (无 GUI 版)
用于生成论文第五章所需的“多次运行统计数据 (最优、平均、标准差)”
"""
import os
import time
import statistics
import csv
import config as cfg
from utils.data_loader import DataLoader
from utils.path_finding import PathFinder
from core.ga_engine import GASolver
from core.pure_ga_engine import PureGASolver


def run_batch_test(vrp_filename, num_runs=10):
    print(f"\n{'=' * 50}")
    print(f"🚀 开始测试算例: {vrp_filename} (连续运行 {num_runs} 次)")
    print(f"{'=' * 50}")

    # 1. 加载算例与构建全0地图矩阵 (脱离 UI，纯算力模式)
    vrp_path = os.path.join(cfg.DATA_INPUT_DIR, vrp_filename)
    if not os.path.exists(vrp_path):
        print(f"❌ 找不到算例文件: {vrp_path}")
        return None

    nodes, capacity, depot_id = DataLoader.load_vrp(vrp_path)
    # 使用一个不存在的地图文件路径，触发 DataLoader 自动生成全 0 空白地图
    grid = DataLoader.load_grid_map("dummy_map_for_test.txt")
    finder = PathFinder(grid)
    matrix = finder.dijkstra_matrix(nodes)

    customers = [n.node_id for n in nodes if not n.is_depot]
    garbage_volumes = [n.garbage_volume for n in nodes]

    # 强制统一超参数
    cfg.CAPACITY = capacity
    # cfg.POP_SIZE = 100      # 确保这里和你的 config.py 一致
    # cfg.GENERATIONS = 100   # 确保这里和你的 config.py 一致

    # 数据记录容器
    pure_costs, pure_times = [], []
    iga_costs, iga_times = [], []

    # 2. 连续运行十次
    for i in range(num_runs):
        print(f"▶ 正在执行第 {i + 1}/{num_runs} 次测试...")

        # --- 测试标准遗传算法 (Pure GA) ---
        start_time = time.time()
        pure_solver = PureGASolver(matrix, garbage_volumes, capacity, customers, depot_id, cfg)
        pure_solver.generate_initial_population()
        for gen in range(1, cfg.GENERATIONS + 1):
            pure_solver.evolve(gen)
        run_time = time.time() - start_time
        pure_costs.append(pure_solver.best_solution.total_cost)
        pure_times.append(run_time)

        # --- 测试改进遗传算法 (IGA) ---
        start_time = time.time()
        iga_solver = GASolver(matrix, garbage_volumes, capacity, customers, depot_id, cfg)
        iga_solver.generate_initial_population()
        for gen in range(1, cfg.GENERATIONS + 1):
            iga_solver.evolve(gen)
        run_time = time.time() - start_time
        iga_costs.append(iga_solver.best_solution.total_cost)
        iga_times.append(run_time)

        print(f"  └─ 完成! 传统GA成本: {pure_costs[-1]:.2f} | 改进IGA成本: {iga_costs[-1]:.2f}")

    # 3. 统计计算 (保留两位小数)
    stats = {
        "算例": vrp_filename,
        "测试次数": num_runs,
        "GA_Best": round(min(pure_costs), 2),
        "GA_Avg": round(statistics.mean(pure_costs), 2),
        "GA_Std": round(statistics.stdev(pure_costs), 2) if num_runs > 1 else 0.0,
        "GA_Time": round(statistics.mean(pure_times), 2),

        "IGA_Best": round(min(iga_costs), 2),
        "IGA_Avg": round(statistics.mean(iga_costs), 2),
        "IGA_Std": round(statistics.stdev(iga_costs), 2) if num_runs > 1 else 0.0,
        "IGA_Time": round(statistics.mean(iga_times), 2)
    }

    # 计算优化提升率
    improvement = ((stats["GA_Avg"] - stats["IGA_Avg"]) / stats["GA_Avg"]) * 100
    stats["提升率(%)"] = round(improvement, 2)

    return stats


def main():
    # 在这里填入你想测试的算例文件名（确保这些文件在 data/input/ 目录下）
    # 你可以先拿两个试试水，如果跑得快，再把大算例加进来
    test_instances = [
        # "A-n80-k10.vrp",
        # "X-n125-k30.vrp",
        "X-n261-k13.vrp"  # 如果这个跑太久，测试阶段可以先注释掉
    ]

    all_results = []

    # 执行批量测试
    for vrp in test_instances:
        result = run_batch_test(vrp, num_runs=10)  # 设定连跑 10 次
        if result:
            all_results.append(result)

    # 导出到 CSV 报表
    os.makedirs("data/output", exist_ok=True)
    csv_file = "data/output/batch_experiment_results.csv"

    if all_results:
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
            writer.writeheader()
            writer.writerows(all_results)

        print(f"\n🎉 恭喜！所有算例测试完毕。")
        print(f"📊 汇总数据已成功导出至: {csv_file}")
        print("💡 你可以直接用 Excel 打开这个文件，把数据复制到论文的表格里！")


if __name__ == "__main__":
    main()