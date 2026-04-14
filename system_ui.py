"""
垃圾运输优化管理系统界面 (MVC - View)
包含：数据管理视图、线路规划视图、效率评估仪表盘
@Author: Met
@Date: 2026-03-12
"""
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class SystemMainWindow(tk.Tk):
    """系统主窗口"""

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.title("城市垃圾运输网络调度优化系统 v1.0")
        self.geometry("900x650")

        # 创建选项卡控件 (Notebook)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 初始化子模块
        self.init_data_tab()
        self.init_optimize_tab()
        self.init_dashboard_tab()

        # 加载数据
        self.controller.load_system_data()
        self.refresh_data_table()

    def init_data_tab(self):
        """模块一：垃圾点信息管理"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=" 📍 垃圾点信息管理 ")

        # 工具栏
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, pady=5)
        ttk.Label(toolbar, text="系统已连接数据源...", foreground="green").pack(side=tk.LEFT, padx=5)

        # 数据表格
        columns = ("ID", "节点类型", "X坐标", "Y坐标", "预计产生垃圾量(kg)")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER, width=150)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)

    def refresh_data_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in self.controller.get_garbage_points_data():
            self.tree.insert("", tk.END, values=row)

    def init_optimize_tab(self):
        """模块二：线路规划与调度策略"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=" ⚙️ 线路规划与调度 ")

        # 参数设置区
        param_lf = ttk.LabelFrame(frame, text="启发式算法参数设置")
        param_lf.pack(fill=tk.X, padx=20, pady=20)

        ttk.Label(param_lf, text="种群规模 (POP_SIZE):").grid(row=0, column=0, padx=10, pady=10)
        self.pop_entry = ttk.Entry(param_lf)
        self.pop_entry.insert(0, "80")
        self.pop_entry.grid(row=0, column=1)

        ttk.Label(param_lf, text="迭代代数 (GENERATIONS):").grid(row=0, column=2, padx=10, pady=10)
        self.gen_entry = ttk.Entry(param_lf)
        self.gen_entry.insert(0, "300")
        self.gen_entry.grid(row=0, column=3)

        # 控制区
        ctrl_frame = ttk.Frame(frame)
        ctrl_frame.pack(pady=20)
        self.btn_run = ttk.Button(ctrl_frame, text="🚀 启动智能调度引擎", command=self.start_optimization)
        self.btn_run.pack(side=tk.LEFT, padx=10)

        # 进度状态区
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=50, pady=10)

        self.status_label = ttk.Label(frame, text="等待执行...", font=("Arial", 12))
        self.status_label.pack(pady=5)

    def start_optimization(self):
        pop = int(self.pop_entry.get())
        gen = int(self.gen_entry.get())

        self.btn_run.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.status_label.config(text="正在构建垃圾清运网络路线...")

        # 传入回调函数更新界面
        self.controller.run_optimization_async(
            pop_size=pop,
            generations=gen,
            progress_callback=self.update_progress,
            finish_callback=self.on_optimization_finish
        )

    def update_progress(self, percent, current_cost):
        self.progress_var.set(percent)
        self.status_label.config(text=f"计算中... 进度: {percent}% | 当前最优成本: {current_cost:.2f}")

    def on_optimization_finish(self):
        self.btn_run.config(state=tk.NORMAL)
        self.status_label.config(text="✅ 调度优化完成！请前往【运输效率评估】查看报表。")
        self.draw_dashboard()  # 更新图表

    def init_dashboard_tab(self):
        """模块三：运输效率评估报表"""
        self.dash_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dash_frame, text=" 📊 运输效率评估 ")

        # 顶部统计文字
        self.stat_label = ttk.Label(self.dash_frame, text="暂无评估数据，请先运行线路规划。", font=("Arial", 12, "bold"))
        self.stat_label.pack(pady=10)

        # 画布容器
        self.canvas_frame = ttk.Frame(self.dash_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        # 底部仿真按钮
        self.btn_sim = ttk.Button(self.dash_frame, text="🎬 启动车辆路径动态仿真", state=tk.DISABLED,
                                  command=self.launch_sim)
        self.btn_sim.pack(pady=10)

    def draw_dashboard(self):
        """使用 Matplotlib 绘制车辆满载率和成本收敛曲线"""
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        metrics = self.controller.get_evaluation_metrics()
        if not metrics: return

        self.stat_label.config(
            text=f"总体评估：共需调派垃圾车 {metrics['vehicle_count']} 辆，网络总运输成本(距离)为 {metrics['total_cost']:.2f}")
        self.btn_sim.config(state=tk.NORMAL)

        # 创建画板 (1行2列)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4))

        # 图1：算法收敛曲线
        ax1.plot(metrics['evolution_history'], color='b', label='Best Cost')
        ax1.set_title("算法收敛与优化趋势", fontdict={'family': 'SimHei'})  # 支持中文
        ax1.set_xlabel("迭代代数 (Generations)", fontdict={'family': 'SimHei'})
        ax1.set_ylabel("行驶总成本", fontdict={'family': 'SimHei'})
        ax1.grid(True, linestyle='--', alpha=0.6)

        # 图2：垃圾车满载率柱状图
        vehicles = [v[0] for v in metrics['load_rates']]
        rates = [v[1] for v in metrics['load_rates']]
        bars = ax2.bar(vehicles, rates, color='orange')
        ax2.set_title("清运车辆满载率评估 (%)", fontdict={'family': 'SimHei'})
        ax2.set_ylim(0, 110)
        ax2.axhline(100, color='r', linestyle='--', label='容量上限')
        ax2.legend(prop={'family': 'SimHei'})
        # 在柱子上标注具体数值
        for bar in bars:
            yval = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2.0, yval + 1, f'{yval:.1f}%', ha='center', va='bottom',
                     fontsize=8)

        plt.tight_layout()

        # 嵌入 Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def launch_sim(self):
        """打开原有的 Pygame 仿真界面"""
        from gui.renderer import SimulationApp
        # 初始化仿真App并运行（注意：Pygame会接管主线程，关闭后可返回Tkinter）
        app = SimulationApp(self.controller.nodes, self.controller.grid, self.controller.best_solution)
        app.run()