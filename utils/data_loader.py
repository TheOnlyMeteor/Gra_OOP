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