import matplotlib.pyplot as plt
import os


class GAVisualizer:
    def __init__(self, title: str):
        self.title = title

    # ... plot_comparison 方法保持不变 ...
    def plot_comparison(self, solvers_dict: dict, save_path: str):
        """绘制历史进化曲线"""
        plt.figure(figsize=(10, 6))
        for label, solver in solvers_dict.items():
            plt.plot(range(1, len(solver.history) + 1), solver.history, label=label)

        plt.title(f"Evolution Curve: {self.title}")
        plt.xlabel("Generation")
        plt.ylabel("Best Cost")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(save_path)
        plt.show()

    def plot_solution_routes(self, nodes: list, solution, save_path: str, solver_name: str):
        """
        绘制详细的路线图（使用全局标号）
        nodes: Node对象列表
        solution: Solution对象
        """
        plt.figure(figsize=(14, 11))

        # 1. 建立 ID 到坐标的映射，以及 ID 到全局显示序号的映射
        # 假设内部 node_id 是 0-based，而 VRP 原始序号是 1-based
        coords = {n.node_id: (n.x, n.y) for n in nodes}
        # 这里的 display_id 是我们在图上看到的标号 (原始 1-based ID)
        display_id = {n.node_id: n.node_id + 1 for n in nodes}

        depot_node = next(n for n in nodes if n.is_depot)
        depot_xy = (depot_node.x, depot_node.y)

        # 2. 绘制所有未访问节点（作为背景）
        all_x = [n.x for n in nodes if not n.is_depot]
        all_y = [n.y for n in nodes if not n.is_depot]
        plt.scatter(all_x, all_y, c='lightgray', s=30, alpha=0.3, zorder=1)

        # 3. 绘制路径
        cmap = plt.get_cmap('tab20')

        for r_idx, route in enumerate(solution.routes):
            color = cmap(r_idx % 20)
            # 路径坐标: Depot -> 客户... -> Depot
            route_coords = [depot_xy] + [coords[nid] for nid in route.nodes] + [depot_xy]
            xs, ys = zip(*route_coords)

            # 绘制轨迹线
            plt.plot(xs, ys, color=color, linewidth=1.5, alpha=0.7, zorder=2)

            # 绘制方向小箭头
            for i in range(len(xs) - 1):
                plt.annotate('', xy=(xs[i + 1], ys[i + 1]), xytext=(xs[i], ys[i]),
                             arrowprops=dict(arrowstyle='->', color=color, lw=1, alpha=0.4))

            # 4. 【核心改动】标注全局标号
            for nid in route.nodes:
                nx, ny = coords[nid]
                # 获取该节点在 VRP 文件中的原始标号
                original_label = str(display_id[nid])

                # 绘制带背景的文字，确保清晰度
                plt.text(nx, ny + 0.6, original_label, color='black', fontsize=7,
                         ha='center', va='center', fontweight='bold',
                         bbox=dict(boxstyle='round,pad=0.1', fc='white', ec=color, alpha=0.8, lw=1))

                # 在节点位置点一个小圆点，颜色与路线一致
                plt.scatter(nx, ny, color=color, s=20, zorder=3)

        # 5. 绘制仓库并标注标号
        plt.scatter(*depot_xy, c='red', marker='s', s=180, label='Depot', zorder=5)
        plt.text(depot_xy[0], depot_xy[1] - 1.5, f"ID:{display_id[depot_node.node_id]} (Depot)",
                 color='red', fontweight='bold', ha='center', fontsize=9)

        # 6. 图表装饰
        plt.title(f"VRP Global ID Map: {solver_name}\nInstance: {self.title} | Cost: {solution.total_cost:.2f}")
        plt.xlabel("X Coordinate")
        plt.ylabel("Y Coordinate")
        plt.grid(True, linestyle=':', alpha=0.5)
        plt.tight_layout()

        plt.savefig(save_path, dpi=300)  # 提高分辨率
        print(f"路线图（全局标号版）已保存至: {save_path}")
        plt.show()