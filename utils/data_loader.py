# utils/data_loader.py
import os
import numpy as np
from core.models import Node


class DataLoader:
    @staticmethod
    def load_vrp(path):
        """解析VRP文件"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"找不到文件: {path}")

        nodes = []
        cap = 0
        depot_id = 0
        section = None

        # 预存坐标和需求，最后统一创建对象
        coords = {}
        demands = {}

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
                        demands[idx] = int(parts[1])
                elif section == "DEPOT":
                    if line != "-1" and line.isdigit():
                        depot_id = int(line) - 1

        # 转换为 Node 对象列表
        for idx in sorted(coords.keys()):
            new_node = Node(
                node_id=idx,
                x=coords[idx][0],
                y=coords[idx][1],
                demand=demands.get(idx, 0),
                is_depot=(idx == depot_id)
            )
            nodes.append(new_node)

        return nodes, cap, depot_id

    @staticmethod
    def load_grid_map(path):
        """读取地图"""
        if not os.path.exists(path):
            return np.zeros((101, 101), dtype=int)
        return np.loadtxt(path, dtype=int)