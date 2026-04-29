"""
数据加载器文件
该文件实现了DataLoader类，用于加载和解析VRP问题数据和网格地图。
主要功能包括：
1. 加载VRP文件，解析节点坐标、需求和仓库信息
2. 加载网格地图文件，用于路径规划
@Author: Met
@Date: 2026-03-12
"""
import os
import numpy as np
from core.models import Node


class DataLoader:
    """
    数据加载器
    """
    @staticmethod
    def load_vrp(path):
        """
        解析VRP文件
        :param path: VRP文件路径
        :return: Tuple[List[Node], int, int]: 节点列表、车辆容量和仓库ID
        :raise FileNotFoundError: 如果文件不存在
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"找不到文件: {path}")

        nodes = []
        cap = 0
        depot_id = 0
        section = None

        # 预存坐标和需求，最后统一创建对象
        coords = {}
        garbage_volume = {}

        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: continue

                if "CAPACITY" in line:
                    cap = int(line.split(":")[-1].strip())
                elif "NODE_COORD_SECTION" in line:
                    section = "COORD"
                elif "DEMAND_SECTION" in line:
                    section = "DEMAND"
                elif "DEPOT_SECTION" in line:
                    section = "DEPOT"
                elif "EOF" in line:
                    break
                elif section == "COORD":
                    parts = line.split()
                    if len(parts) >= 3:
                        idx = int(parts[0]) - 1
                        coords[idx] = (int(float(parts[1])), int(float(parts[2])))
                elif section == "DEMAND":
                    parts = line.split()
                    if len(parts) >= 2:
                        idx = int(parts[0]) - 1
                        garbage_volume[idx] = int(parts[1])
                elif section == "DEPOT":
                    if line != "-1" and line.isdigit():
                        depot_id = int(line) - 1

        # 转换为 Node 对象列表
        for idx in sorted(coords.keys()):
            new_node = Node(
                node_id=idx,
                x=coords[idx][0],
                y=coords[idx][1],
                garbage_volume=garbage_volume.get(idx, 0),
                is_depot=(idx == depot_id)
            )
            nodes.append(new_node)

        return nodes, cap, depot_id

    @staticmethod
    def load_grid_map(path):
        """
        读取网格地图
        :param path: 地图文件路径
        :return: np.ndarray: 网格地图数组
        """
        if not os.path.exists(path):
            return np.zeros((101, 101), dtype=int)
        return np.loadtxt(path, dtype=int)


    @staticmethod
    def export_solution_to_file(solution, output_filepath="data/output/best_solution.txt"):
        """
        将 CVRP 的最优调度方案导出到文本文件中
        :param solution: 包含最优路线的 Solution 对象
        :param output_filepath: 导出的文件路径
        """
        # 确保输出的文件夹存在
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)

        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 40 + "\n")
            f.write("          CVRP 最优车辆调度方案          \n")
            f.write("=" * 40 + "\n\n")

            if not solution or not hasattr(solution, 'routes') or not solution.routes:
                f.write("警告：未找到有效的调度路线数据！\n")
                print("导出失败：无效的 solution 对象。")
                return

            # 写入全局指标
            # 兼容不同的成本变量命名 (cost 或 distance)
            total_cost = getattr(solution, 'cost', getattr(solution, 'distance', '未知'))
            if isinstance(total_cost, (int, float)):
                f.write(f"【全局指标】\n")
                f.write(f"总使用车辆数: {len(solution.routes)} 辆\n")
                f.write(f"车队总行驶距离: {total_cost:.2f}\n\n")

            f.write("-" * 40 + "\n")
            f.write("【各车辆详细路线】\n")
            f.write("-" * 40 + "\n\n")

            # 遍历每一辆车
            for i, route in enumerate(solution.routes):
                f.write(f"▶ 车辆 {i + 1}:\n")

                # 兼容节点序列的变量命名
                route_seq = getattr(route, 'nodes',
                                    getattr(route, 'path', getattr(route, 'route', getattr(route, 'node_list', []))))

                if route_seq:
                    # 将列表 [0, 5, 8, 0] 转换为字符串 "0 -> 5 -> 8 -> 0"
                    route_str = " -> ".join(map(str, route_seq))
                    f.write(f"  行驶轨迹: {route_str}\n")
                else:
                    f.write(f"  行驶轨迹: 空\n")

                # 如果 Route 类有 load (载重) 属性，一并打印
                if hasattr(route, 'load'):
                    f.write(f"  车辆载重: {route.load}\n")

                # 如果 Route 类有单独的 cost 或 distance 属性
                route_cost = getattr(route, 'cost', getattr(route, 'distance', getattr(route, 'length', None)))
                if route_cost is not None:
                    f.write(f"  单车距离: {route_cost:.2f}\n")

                f.write("\n")

        print(f"✅ 最佳方案已成功导出至: {os.path.abspath(output_filepath)}")