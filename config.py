import os

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_INPUT_DIR = os.path.join(BASE_DIR, "data", "input")
DATA_OUTPUT_DIR = os.path.join(BASE_DIR, "data", "output")

# 文件名
VRP_FILE = "A-n80-k10.vrp"
MAP_FILE = "obstacles_dev.txt"

# 算法参数
POP_SIZE = 80
GENERATIONS = 300
ELITE_SIZE = 6
MUT_START = 0.6
MUT_END = 0.1

# 界面参数
ROWS, COLS = 101, 101
CELL_SIZE = 8
WINDOW_WIDTH = COLS * CELL_SIZE + 250
WINDOW_HEIGHT = ROWS * CELL_SIZE

# 颜色配置
COLOR_BG = (30, 30, 30)
COLOR_GRID = (50, 50, 50)
COLOR_OBSTACLE = (255, 255, 255)
COLOR_DEPOT = (255, 255, 0)
COLOR_CUST_WAIT = (50, 150, 255)
COLOR_CUST_DONE = (255, 50, 50)