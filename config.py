"""
配置文件
该文件包含项目的所有配置参数，包括路径配置、文件名、算法参数、界面参数和颜色配置。
@Author: Met
@Date: 2026-03-12
"""
import os

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_INPUT_DIR = os.path.join(BASE_DIR, "data", "input")
DATA_OUTPUT_DIR = os.path.join(BASE_DIR, "data", "output")

# 文件名
VRP_FILE = "X-n125-k30.vrp" #VRP数据文件
MAP_FILE = "obstacles.txt" #地图文件

# 算法参数
POP_SIZE = 80 #种群大小
GENERATIONS = 300 #遗传代数
ELITE_SIZE = 6 #精英数大小
#变异率由0.6减小至0.1。
MUT_START = 0.6
MUT_END = 0.1

# 界面参数
ROWS, COLS = 101, 101
CELL_SIZE = 7
WINDOW_WIDTH = COLS * CELL_SIZE + 250
WINDOW_HEIGHT = ROWS * CELL_SIZE

# 颜色配置
COLOR_BG = (30, 30, 30)
COLOR_GRID = (50, 50, 50)
COLOR_OBSTACLE = (255, 255, 255)
COLOR_DEPOT = (255, 255, 0)
COLOR_CUST_WAIT = (50, 150, 255)
COLOR_CUST_DONE = (255, 50, 50)