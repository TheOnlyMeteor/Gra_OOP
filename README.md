# 面向垃圾运输网络的线路优化系统

基于遗传算法的容量约束车辆路径问题 (CVRP) 求解系统，用于优化垃圾清运车辆的路线规划。

## 特性

- **双算法对比引擎**：基础遗传算法 (Pure GA) 作为对照组，改进遗传算法 (IGA) 作为实验组
- **MVC 架构 GUI**：基于 Tkinter 的图形界面，支持数据 CRUD、算法调度、结果可视化
- **路径规划**：Dijkstra 距离矩阵 + A* 避障寻路（支持障碍地图）
- **动画仿真**：Pygame 多车同时行驶动画，可交互控制路线显隐
- **批量实验**：无 GUI 命令行脚本，自动统计多次运行的最优/平均/标准差
- **图表导出**：收敛曲线对比、车辆满载率、线路规划图谱（SVG/PNG）

## 项目结构

```
CVRP_pro/
├── main.py                 # 程序入口，启动 Tkinter GUI
├── config.py               # 全局配置（算法参数、路径、颜色）
├── controllers.py          # MVC-Controller，统筹数据与算法
├── system_ui.py            # MVC-View，Tkinter 主窗口（4 个标签页）
├── core/
│   ├── models.py           # 数据模型：Node / Route / Solution
│   ├── base_solver.py      # 遗传算法抽象基类
│   ├── pure_ga_engine.py   # 基础 GA 求解器（对照组）
│   └── ga_engine.py        # 改进 GA 求解器（实验组）
├── utils/
│   ├── data_loader.py      # VRP 文件解析与结果导出
│   └── path_finding.py     # Dijkstra 矩阵 + A* 寻路
├── gui/
│   └── renderer.py         # Pygame 动画仿真
├── data/
│   ├── input/              # VRP 算例与障碍地图
│   └── output/             # 输出图表与路线文件
└── run_exp*.py             # 批量实验脚本
```

## 环境要求

- Python 3.8+
- 依赖包：

```bash
pip install numpy matplotlib pygame
```

> Tkinter 通常随 Python 一起安装，无需额外配置。

## 快速开始

### GUI 模式

```bash
python main.py
```

主界面包含四个标签页：

| 标签页 | 功能 |
|---|---|
| 垃圾点信息管理 | 增删改节点、CSV 导入导出 |
| 线路规划与调度 | 设置种群规模/迭代代数，启动双算法对比 |
| 运输效率评估 | 收敛曲线图 + 车辆满载率柱状图 + 动画仿真入口 |
| 线路对比图谱 | 基础 GA vs 改进 GA 的路线规划并排对比 |

### 批量实验模式

```bash
python run_exp.py
```

无 GUI 运行，对指定算例连续多次测试，输出统计结果到 `data/output/` 目录下的 CSV 文件。

## 配置说明

编辑 `config.py` 可调整以下参数：

| 参数 | 默认值 | 说明 |
|---|---|---|
| `VRP_FILE` | `A-n80-k10.vrp` | 默认加载的 VRP 算例 |
| `MAP_FILE` | `obstacles_dev.txt` | 障碍地图文件 |
| `POP_SIZE` | 80 | 种群大小 |
| `GENERATIONS` | 300 | 进化代数 |
| `ELITE_SIZE` | 6 | 精英保留数量 |
| `MUT_START` | 0.6 | 初始变异率 |
| `MUT_END` | 0.1 | 最终变异率（线性衰减） |
| `ROWS/COLS` | 101×101 | 地图网格尺寸 |

## 算法说明

### 基础 GA（Pure GA）

- 100% 随机初始化种群
- 贪心分割：按容量约束顺序装车
- 锦标赛选择 + OX 交叉 + 交换变异

### 改进 GA（IGA）

- **混合初始化**：50% 最近邻启发式 + 50% 随机
- **Prins 动态规划分割**：将巨型巡游序列最优分割为多路径
- **路径内优化**：2-opt 局部搜索
- **路径间优化**：不同车辆间交换节点以减少总成本
- **Lamarckian 进化**：优化后的路径写回染色体
- **适应度缓存**：避免重复评估相同染色体

## 输入数据格式

### VRP 文件

采用标准 CVRPLIB 格式，包含以下节：

```
CAPACITY : 100
NODE_COORD_SECTION
1 10 20
2 30 40
...
DEMAND_SECTION
1 0
2 15
...
DEPOT_SECTION
1
-1
EOF
```

### 障碍地图文件

纯文本矩阵（0 = 可通行，1 = 障碍物），尺寸由 `config.py` 中 `ROWS/COLS` 定义。

## 输出文件

所有输出位于 `data/output/`：

| 文件 | 说明 |
|---|---|
| `evolution.svg/png` | 两种算法收敛曲线对比图 |
| `route_map.svg/png` | 双算法路线规划并排对比图 |
| `Final_Best_Routes.txt` | 最优调度方案的详细文本报告 |
| `batch_experiment_results.csv` | 批量实验统计结果 |

## 许可证

本项目用于学术研究与毕业设计。
