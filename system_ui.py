"""
垃圾运输优化管理系统界面 (MVC - View)
包含CRUD交互、双算法报表对比、以及高精度的双算法线路图谱对比展示。
@Author: Met
@Date: 2026-03-12
"""
import multiprocessing
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def start_pygame_renderer(nodes_data, grid_map_data, solution_data):
    from gui.renderer import SimulationApp
    sim = SimulationApp(nodes_data, grid_map_data, solution_data)
    sim.run()

class SystemMainWindow(tk.Tk):
    def __init__(self, controller):
        """
        初始化系统主窗口
        :param controller: 系统控制器实例
        """
        super().__init__()
        self.controller = controller
        self.title("面向垃圾运输网络的线路优化系统 v2.0")
        self.geometry("1100x750")  # 稍微加大窗口以适应并排的大图

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 初始化系统的四大模块
        self.init_data_tab()
        self.init_optimize_tab()
        self.init_dashboard_tab()
        self.init_map_tab()  # 新增：线路对比图谱模块

        self.controller.load_system_data()
        self.refresh_data_table()

    # ================= 模块一：CRUD与文件导入 =================
        # ================= 模块一：CRUD与文件导入 =================
    def init_data_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=" 📍 垃圾点信息管理 ")

        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, pady=10, padx=10)

        ttk.Button(toolbar, text="➕ 新增节点", command=self.add_node).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="✏️ 修改选中", command=self.edit_node).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="🗑️ 删除选中", command=self.delete_node).pack(side=tk.LEFT, padx=5)

        ttk.Label(toolbar, text=" | ").pack(side=tk.LEFT)
        ttk.Button(toolbar, text="📂 导入CSV", command=self.import_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="💾 导出CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)

        ttk.Button(toolbar, text="✅ 应用更改并重排网络", command=self.apply_changes).pack(side=tk.RIGHT, padx=5)

        columns = ("ID", "节点类型", "X坐标", "Y坐标", "预计产生垃圾量(kg)")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=18)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def refresh_data_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in self.controller.get_garbage_points_data():
            self.tree.insert("", tk.END, values=row)

    def add_node(self):
        # 新增时，临时赋予一个当前最大长度+1的ID
        new_id = len(self.tree.get_children()) + 1
        self._open_node_dialog("新增垃圾点", None, None, new_id)

    def edit_node(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要修改的节点！")
            return
        item = self.tree.item(selected[0])['values']
        # 修改时，原封不动传入它本来的 ID
        self._open_node_dialog("修改垃圾点", item, selected[0], item[0])

    def delete_node(self):
        selected = self.tree.selection()
        if selected and messagebox.askyesno("确认", "确定要删除该节点吗？"):
            self.tree.delete(selected[0])

    def _open_node_dialog(self, title, init_data=None, item_id=None, assigned_id=1):
        top = tk.Toplevel(self)
        top.title(title)
        top.geometry("320x250")

        ttk.Label(top, text="节点 ID:").grid(row=0, column=0, pady=5, padx=10)
        ttk.Label(top, text=str(assigned_id), foreground="gray").grid(row=0, column=1, sticky="w")

        ttk.Label(top, text="节点类型:").grid(row=1, column=0, pady=10, padx=10)
        type_var = tk.StringVar(value=init_data[1] if init_data else "垃圾收运点")
        ttk.Combobox(top, textvariable=type_var, values=["垃圾处理车场", "垃圾收运点"], state="readonly").grid(
            row=1, column=1)

        ttk.Label(top, text="X 坐标:").grid(row=2, column=0, pady=5)
        x_entry = ttk.Entry(top)
        x_entry.insert(0, str(init_data[2]) if init_data else "0")
        x_entry.grid(row=2, column=1)

        ttk.Label(top, text="Y 坐标:").grid(row=3, column=0, pady=5)
        y_entry = ttk.Entry(top)
        y_entry.insert(0, str(init_data[3]) if init_data else "0")
        y_entry.grid(row=3, column=1)

        ttk.Label(top, text="垃圾量(kg):").grid(row=4, column=0, pady=5)
        demand_entry = ttk.Entry(top)
        demand_entry.insert(0, str(init_data[4]) if init_data else "10")
        demand_entry.grid(row=4, column=1)

        def save():
            try:
                x, y, d = int(x_entry.get()), int(y_entry.get()), int(demand_entry.get())
                if x < 0 or y < 0 or d < 0:
                    raise ValueError

                # 传入固定的 assigned_id，杜绝了"待分配"字符串
                values = (assigned_id, type_var.get(), x, y, d)
                if item_id:
                    self.tree.item(item_id, values=values)
                else:
                    self.tree.insert("", tk.END, values=values)
                top.destroy()
            except ValueError:
                messagebox.showerror("错误", "坐标和垃圾量必须是大于等于0的整数！")

        ttk.Button(top, text="保存修改", command=save).grid(row=5, column=0, columnspan=2, pady=15)

    # def apply_changes(self):
    #     """
    #     应用更改并重算网络
    #     将表格中的数据更新到控制器，并重新计算距离矩阵
    #     """
    #     data = [self.tree.item(child)["values"] for child in self.tree.get_children()]
    #
    #     # 有且仅有一个车场
    #     depot_count = sum(1 for item in data if item[1] == "垃圾处理车场")
    #     if depot_count != 1:
    #         messagebox.showerror("业务验证失败",
    #                              f"系统中必须有且仅有 1 个【垃圾处理车场】！当前有 {depot_count} 个。请修改节点类型。")
    #         return
    #
    #     self.controller.update_nodes_from_ui(data)
    #
    #     # 更新完毕后，立即重绘数据表，利用 Controller 返回的干净连续的 IDs 更新前端
    #     self.refresh_data_table()
    #     messagebox.showinfo("成功", "更改已应用！系统已为您自动重排节点ID，底层连通图与距离矩阵重建完成。")
    def apply_changes(self):
        """
        应用更改并重算网络
        将表格中的数据更新到控制器，并在更新前进行严格的业务逻辑校验
        """
        data = [self.tree.item(child)["values"] for child in self.tree.get_children()]

        # 1. 业务验证：车场唯一性拦截
        depot_count = sum(1 for item in data if item[1] == "垃圾处理车场")
        if depot_count != 1:
            messagebox.showerror("业务验证失败",
                                 f"系统中必须有且仅有 1 个【垃圾处理车场】！当前有 {depot_count} 个。请修改节点类型。")
            return

        # 2. 逻辑验证：单点垃圾量不可大于单车最大载重拦截
        vehicle_capacity = self.controller.capacity
        for item in data:
            if item[1] == "垃圾收运点" and int(item[4]) > vehicle_capacity:
                messagebox.showerror("容量逻辑错误",
                                     f"显示 ID 为 {item[0]} 的垃圾量 ({item[4]}kg) 超出了单辆车的最大额定载重 ({vehicle_capacity}kg)！\n\n"
                                     "这会导致底层 Prins 动态规划算法无法完成切分计算，引发程序崩溃。\n"
                                     "请将该大型垃圾点拆分为多个节点，或调小垃圾量后再试。")
                return

        # 所有验证通过，将干净的数据推送到控制层处理
        self.controller.update_nodes_from_ui(data)

        # 更新完毕后，立即重绘数据表，利用 Controller 返回的干净连续的 IDs 更新前端
        self.refresh_data_table()
        messagebox.showinfo("成功", "更改已成功应用！系统已自动为您重排底层连续节点 ID，连通图与距离代价矩阵重建完成。")

    # def apply_changes(self):
    #
    #     data = [self.tree.item(child)["values"] for child in self.tree.get_children()]
    #     self.controller.update_nodes_from_ui(data)
    #     self.refresh_data_table()
    #     messagebox.showinfo("成功", "更改已应用，距离网络重算完成！")

    # def init_data_tab(self):
    #     """
    #     初始化数据管理标签页
    #     创建垃圾点信息管理界面，包括CRUD操作和文件导入导出功能
    #     """
    #     frame = ttk.Frame(self.notebook)
    #     self.notebook.add(frame, text=" 垃圾点信息管理 ")
    #
    #     toolbar = ttk.Frame(frame)
    #     toolbar.pack(fill=tk.X, pady=10, padx=10)
    #
    #     ttk.Button(toolbar, text="➕ 新增节点", command=self.add_node).pack(side=tk.LEFT, padx=5)
    #     ttk.Button(toolbar, text="✏️ 修改选中", command=self.edit_node).pack(side=tk.LEFT, padx=5)
    #     ttk.Button(toolbar, text="🗑️ 删除选中", command=self.delete_node).pack(side=tk.LEFT, padx=5)
    #
    #     ttk.Label(toolbar, text=" | ").pack(side=tk.LEFT)
    #     ttk.Button(toolbar, text="📂 导入CSV", command=self.import_csv).pack(side=tk.LEFT, padx=5)
    #     ttk.Button(toolbar, text="💾 导出CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)
    #
    #     ttk.Button(toolbar, text="✅ 应用更改并重算网络", command=self.apply_changes).pack(side=tk.RIGHT, padx=5)
    #
    #     columns = ("ID", "节点类型", "X坐标", "Y坐标", "垃圾量(kg)")
    #     self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=18)
    #     for col in columns:
    #         self.tree.heading(col, text=col)
    #         self.tree.column(col, anchor=tk.CENTER)
    #     self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    # def refresh_data_table(self):
    #     """
    #     刷新数据表格
    #     从控制器获取最新的垃圾点数据并更新表格显示
    #     """
    #     for item in self.tree.get_children():
    #         self.tree.delete(item)
    #     for row in self.controller.get_garbage_points_data():
    #         self.tree.insert("", tk.END, values=row)
    #
    # def add_node(self):
    #     """
    #     新增垃圾点
    #     打开新增垃圾点对话框
    #     """
    #     self.__open_node_dialog("新增垃圾点", None)
    #
    # def edit_node(self):
    #     """
    #     修改选中的垃圾点
    #     打开修改垃圾点对话框，编辑选中的节点信息
    #     """
    #     selected = self.tree.selection()
    #     if not selected:
    #         messagebox.showwarning("提示", "请先选择要修改的节点！")
    #         return
    #     item = self.tree.item(selected[0])['values']
    #     self.__open_node_dialog("修改垃圾点", item, selected[0])
    #
    # def delete_node(self):
    #     """
    #     删除选中的垃圾点
    #     删除表格中选中的节点
    #     """
    #     selected = self.tree.selection()
    #     if selected and messagebox.askyesno("确认", "确定要删除该节点吗？"):
    #         self.tree.delete(selected[0])

    def __open_node_dialog(self, title, init_data=None, item_id=None):
        """
        打开节点编辑对话框
        :param title: 对话框标题
        :param init_data: 初始数据，默认为None
        :param item_id: 节点ID，默认为None
        """
        top = tk.Toplevel(self)
        top.title(title)
        top.geometry("300x250")

        ttk.Label(top, text="节点类型:").grid(row=0, column=0, pady=10, padx=10)
        type_var = tk.StringVar(value=init_data[1] if init_data else "垃圾收运点")
        ttk.Combobox(top, textvariable=type_var, values=["垃圾处理车场", "垃圾收运点"]).grid(row=0, column=1)

        ttk.Label(top, text="X坐标:").grid(row=1, column=0, pady=10)
        x_entry = ttk.Entry(top)
        x_entry.insert(0, str(init_data[2]) if init_data else "0")
        x_entry.grid(row=1, column=1)

        ttk.Label(top, text="Y坐标:").grid(row=2, column=0, pady=10)
        y_entry = ttk.Entry(top)
        y_entry.insert(0, str(init_data[3]) if init_data else "0")
        y_entry.grid(row=2, column=1)

        ttk.Label(top, text="垃圾量(kg):").grid(row=3, column=0, pady=10)
        garbage_volume_entry = ttk.Entry(top)
        garbage_volume_entry.insert(0, str(init_data[4]) if init_data else "10")
        garbage_volume_entry.grid(row=3, column=1)

        def save():
            try:
                x, y, d = int(x_entry.get()), int(y_entry.get()), int(garbage_volume_entry.get())
                values = (item_id, type_var.get(), x, y, d)
                if item_id:
                    self.tree.item(item_id, values=values)
                else:
                    self.tree.insert("", tk.END, values=values)
                top.destroy()
            except ValueError:
                messagebox.showerror("错误", "坐标和垃圾量必须是整数！")

        ttk.Button(top, text="保存", command=save).grid(row=4, column=0, columnspan=2, pady=20)



    def import_csv(self):
        """
        导入CSV数据
        从CSV文件导入垃圾点数据
        """
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if path:
            self.controller.import_from_csv(path)
            self.refresh_data_table()
            messagebox.showinfo("成功", "导入成功，矩阵已重算。")

    def export_csv(self):
        """
        导出CSV数据
        将垃圾点数据导出到CSV文件
        """
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if path:
            self.controller.export_to_csv(path)
            messagebox.showinfo("成功", "数据导出成功！")

    # ================= 模块二：调度规划 =================
    def init_optimize_tab(self):
        """
        初始化调度规划标签页
        创建线路规划与调度界面，包括算法参数设置和执行控制
        """
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=" ⚙️ 线路规划与调度 ")

        param_lf = ttk.LabelFrame(frame, text="算法引擎参数")
        param_lf.pack(fill=tk.X, padx=20, pady=20)

        ttk.Label(param_lf, text="种群规模:").grid(row=0, column=0, padx=10, pady=10)
        self.pop_entry = ttk.Entry(param_lf)
        self.pop_entry.insert(0, "80")
        self.pop_entry.grid(row=0, column=1)

        ttk.Label(param_lf, text="迭代代数:").grid(row=0, column=2, padx=10, pady=10)
        self.gen_entry = ttk.Entry(param_lf)
        self.gen_entry.insert(0, "300")
        self.gen_entry.grid(row=0, column=3)

        ctrl_frame = ttk.Frame(frame)
        ctrl_frame.pack(pady=20)
        self.btn_run = ttk.Button(ctrl_frame, text="🚀 启动对比分析引擎 (基础 vs 改进)", command=self.start_optimization)
        self.btn_run.pack()

        self.progress_var = tk.DoubleVar()
        ttk.Progressbar(frame, variable=self.progress_var, maximum=100).pack(fill=tk.X, padx=50, pady=10)

        self.status_label = ttk.Label(frame, text="系统就绪，等待执行...", font=("Arial", 11))
        self.status_label.pack(pady=5)

    def start_optimization(self):
        """
        启动优化算法
        读取算法参数并启动异步优化过程
        """
        pop, gen = int(self.pop_entry.get()), int(self.gen_entry.get())
        self.btn_run.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.controller.run_optimization_async(pop, gen, self.update_progress, self.on_optimization_finish)

    def update_progress(self, percent, cost, stage_str):
        """
        更新进度信息
        :param percent: 进度百分比
        :param cost: 当前最优成本
        :param stage_str: 当前阶段描述
        """
        self.progress_var.set(percent)
        self.status_label.config(text=f"[{stage_str}] 进度: {percent}% | 当前最优成本: {cost:.2f}")

    def on_optimization_finish(self):
        """
        优化完成处理
        恢复按钮状态，更新状态信息，并绘制结果图表
        """
        self.btn_run.config(state=tk.NORMAL)
        self.status_label.config(text="✅ 计算完成！请查看【效率评估】与【对比图谱】。")
        self.draw_dashboard()
        self.draw_route_maps()  # 触发绘制路线图

    # ================= 模块三：报表对比 =================
    def init_dashboard_tab(self):
        """
        初始化报表对比标签页
        创建运输效率评估界面，包括结果展示和图表绘制
        """
        self.dash_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dash_frame, text=" 📊 运输效率评估 ")

        self.stat_label = ttk.Label(self.dash_frame, text="暂无评估数据...", font=("Arial", 11, "bold"))
        self.stat_label.pack(pady=5)

        self.canvas_frame = ttk.Frame(self.dash_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.btn_sim = ttk.Button(self.dash_frame, text="启动改进组最佳路径动态仿真", state=tk.DISABLED,
                                  command=self.launch_sim)
        self.btn_sim.pack(pady=10)

    def draw_dashboard(self):
        """
        绘制仪表盘图表
        绘制算法性能对比和车辆负载率图表
        """
        # 清除画布上的所有组件
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        # 从控制器获取评估指标数据
        m = self.controller.get_evaluation_metrics()
        # 如果没有数据，直接返回
        if not m: return

        # 计算优化提升率
        imp = ((m['total_cost_pure'] - m['total_cost_improved']) / m['total_cost_pure']) * 100
        # 构建评估结果文本
        text = (
            f"【优化结果评估】 基础GA成本: {m['total_cost_pure']:.2f} | 改进后系统成本: {m['total_cost_improved']:.2f}\n"
            f"系统相对优化提升率: {imp:.2f}% | 共调派垃圾车: {m['vehicle_count']} 辆")
        # 更新状态标签
        self.stat_label.config(text=text)
        # 启用仿真按钮
        self.btn_sim.config(state=tk.NORMAL)

        # 创建1行2列的图表布局
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

        # 绘制算法收敛性能对比图表
        # 绘制基础GA的收敛曲线（灰色虚线）
        ax1.plot(m['history_pure'], color='gray', linestyle='--', label='对照组 (基础GA)')
        # 绘制改进GA的收敛曲线（蓝色实线）
        ax1.plot(m['history_improved'], color='blue', linewidth=2, label='实验组 (系统改进型GA)')
        # 设置图表标题
        ax1.set_title("算法收敛性能对比分析", fontdict={'family': 'SimHei'})
        # 设置X轴标签
        ax1.set_xlabel("迭代代数", fontdict={'family': 'SimHei'})
        # 设置Y轴标签
        ax1.set_ylabel("规划成本 (距离)", fontdict={'family': 'SimHei'})
        # 添加图例
        ax1.legend(prop={'family': 'SimHei'})
        # 添加网格线
        ax1.grid(True, alpha=0.3)

        # 绘制车辆满载率评估图表
        # 解包车辆ID和负载率数据
        vehicles, rates = zip(*m['load_rates']) if m['load_rates'] else ([], [])
        # 绘制柱状图
        bars = ax2.bar(vehicles, rates, color='teal', alpha=0.7)
        # 设置图表标题
        ax2.set_title("各清运车辆满载率评估 (%)", fontdict={'family': 'SimHei'})
        # 设置Y轴范围，确保能显示所有数据
        ax2.set_ylim(0, max(110, max(rates) + 10) if rates else 110)
        # 添加100%容量线作为参考
        ax2.axhline(100, color='red', linestyle=':', label='标准容量线')
        # 添加图例
        ax2.legend(prop={'family': 'SimHei'})

        # 在每个柱状图上添加百分比标签
        for bar in bars:
            yval = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2.0, yval + 1, f'{yval:.1f}%', ha='center', va='bottom',
                     fontsize=8)

        # 调整图表布局
        plt.tight_layout()
        # 创建Matplotlib画布并绑定到Tkinter窗口
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        # 绘制图表
        canvas.draw()
        # 将画布添加到窗口中
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def launch_sim(self):
        # 1. 提取节点和解决方案（这两个已经验证没问题了）
        nodes_data = self.controller.nodes
        solution_data = self.controller.best_solution

        # 2. 【核心修复】：自动嗅探网格地图的真实变量名，绝不盲猜报错！
        import numpy as np
        if hasattr(self.controller, 'grid_map'):
            grid_map_data = self.controller.grid_map
        elif hasattr(self.controller, 'grid'):
            grid_map_data = self.controller.grid
        elif hasattr(self.controller, 'map_data'):
            grid_map_data = self.controller.map_data
        elif hasattr(self.controller, 'obstacle_map'):
            grid_map_data = self.controller.obstacle_map
        elif hasattr(self.controller, 'matrix'):
            # 有些写法是直接把最短代价矩阵 matrix 传给渲染器
            grid_map_data = self.controller.matrix
        else:
            # 【终极兜底】：如果上面全都没猜中，打印出你真实的变量名供我们排查，
            # 并临时生成一个 101x101 的空地图，确保程序绝对不崩溃、窗口绝对能打开！
            print("==================================================")
            print("找不到地图变量！请看这里，你的 Controller 实际拥有的变量是：")
            print(list(self.controller.__dict__.keys()))
            print("==================================================")
            grid_map_data = np.zeros((101, 101)).tolist()

        # 3. 启动独立进程
        import multiprocessing
        sim_process = multiprocessing.Process(
            target=start_pygame_renderer,
            args=(nodes_data, grid_map_data, solution_data)
        )
        sim_process.start()

    # ================= 新增模块四：线路对比图谱 =================
    def init_map_tab(self):
        """
        初始化线路对比图谱标签页
        创建线路对比图谱界面，用于展示两种算法的线路规划结果
        """
        self.map_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.map_frame, text=" 🗺️ 线路对比图谱 ")

        self.map_info_label = ttk.Label(self.map_frame, text="暂无图谱数据，请先进行规划调度...", font=("Arial", 11))
        self.map_info_label.pack(pady=10)

        self.map_canvas_frame = ttk.Frame(self.map_frame)
        self.map_canvas_frame.pack(fill=tk.BOTH, expand=True)

    def draw_route_maps(self):
        """
        同时绘制两个算法的具体线路图
        类似于 visualizer 的风格，展示基础GA和改进GA的线路规划结果
        """
        # 清除画布上的所有组件
        for widget in self.map_canvas_frame.winfo_children():
            widget.destroy()

        # 检查是否有解决方案数据
        if not self.controller.best_solution or not self.controller.pure_solution:
            return

        # 更新标签文本，显示图表标题
        self.map_info_label.config(text="全网垃圾收运车辆轨迹详细图谱对比", font=("SimHei", 12, "bold"))

        # 创建1行2列的图表布局，设置图表大小
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # 绘制基础算法图纸
        self.__plot_single_route(
            ax=ax1,  # 左侧子图
            nodes=self.controller.nodes,  # 节点列表
            solution=self.controller.pure_solution,  # 基础GA解决方案
            title=f"对照组策略: 基础GA分配图 (成本: {self.controller.pure_solution.total_cost:.2f})"  # 图表标题，包含成本信息
        )

        # 绘制改进算法图纸
        self.__plot_single_route(
            ax=ax2,  # 右侧子图
            nodes=self.controller.nodes,  # 节点列表
            solution=self.controller.best_solution,  # 改进GA解决方案
            title=f"实验组策略: 改进GA智能分配图 (成本: {self.controller.best_solution.total_cost:.2f})"  # 图表标题，包含成本信息
        )

        # 调整图表布局
        plt.tight_layout()
        # 创建Matplotlib画布并绑定到Tkinter窗口
        canvas = FigureCanvasTkAgg(fig, master=self.map_canvas_frame)
        # 绘制图表
        canvas.draw()
        # 将画布添加到窗口中
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def __plot_single_route(self, ax, nodes, solution, title):
        """
        核心画图封装：绘制单个算法的线路图
        :param ax: 绘图轴对象
        :param nodes: 节点列表
        :param solution: 解决方案对象
        :param title: 图表标题
        """
        # 创建节点ID到坐标的映射字典，方便快速查找节点坐标
        coords = {n.node_id: (n.x, n.y) for n in nodes}
        # 创建节点ID到显示ID的映射字典（显示ID从1开始，更符合人类阅读习惯）
        display_id = {n.node_id: n.node_id + 1 for n in nodes}  # 全局标号

        # 找到车场节点（唯一的is_depot为True的节点）
        depot_node = next(n for n in nodes if n.is_depot)
        # 获取车场坐标
        depot_xy = (depot_node.x, depot_node.y)

        # 1. 绘制背景节点 (浅灰色)
        # 提取所有非车场节点的X坐标
        all_x = [n.x for n in nodes if not n.is_depot]
        # 提取所有非车场节点的Y坐标
        all_y = [n.y for n in nodes if not n.is_depot]
        # 绘制背景节点，使用浅灰色，设置透明度和层级（zorder=1确保在底层）
        ax.scatter(all_x, all_y, c='lightgray', s=30, alpha=0.3, zorder=1)

        # 2. 遍历各辆车的路径
        # 获取颜色映射，用于为不同车辆分配不同颜色
        cmap = plt.get_cmap('tab20')
        # 遍历每条路线
        for r_idx, route in enumerate(solution.routes):
            # 为当前路线选择颜色（循环使用tab20颜色，最多支持20种不同颜色）
            color = cmap(r_idx % 20)

            # 构建完整路径：车场 -> 客户节点1 -> 客户节点2 -> ... -> 车场
            route_coords = [depot_xy] + [coords[nid] for nid in route.nodes] + [depot_xy]
            # 解包路径坐标为X和Y列表，便于绘制线条
            xs, ys = zip(*route_coords)

            # 绘制轨迹连线，设置颜色、线宽和透明度
            ax.plot(xs, ys, color=color, linewidth=1.5, alpha=0.7, zorder=2)

            # 绘制方向小箭头，指示车辆行驶方向
            for i in range(len(xs) - 1):
                # 从当前点到下一个点绘制箭头
                ax.annotate('', xy=(xs[i + 1], ys[i + 1]), xytext=(xs[i], ys[i]),
                            arrowprops=dict(arrowstyle='->', color=color, lw=1, alpha=0.6))

            # 绘制各个节点的标号和圆点
            for nid in route.nodes:
                # 获取节点坐标
                nx, ny = coords[nid]
                # 在节点上方添加标号，带白色背景框，提高可读性
                ax.text(nx, ny + 1.2, str(display_id[nid]), color='black', fontsize=8,
                        ha='center', va='center', fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.1', fc='white', ec=color, alpha=0.8, lw=1))
                # 绘制节点圆点，使用与路线相同的颜色
                ax.scatter(nx, ny, color=color, s=25, zorder=3)

        # 3. 绘制车场 Depot
        # 绘制红色方形车场标记，设置较大的大小和最高层级（zorder=5确保在最上层）
        ax.scatter(*depot_xy, c='red', marker='s', s=150, zorder=5)
        # 在车场下方添加标签，显示车场ID
        ax.text(depot_xy[0], depot_xy[1] - 2.5, f"车场 ({display_id[depot_node.node_id]})",
                color='red', fontweight='bold', ha='center', fontsize=10)

        # 图表修饰
        # 设置图表标题，使用中文字体
        ax.set_title(title, fontdict={'family': 'SimHei', 'size': 12})
        # 设置X轴标签，使用中文字体
        ax.set_xlabel("地图 X 坐标", fontdict={'family': 'SimHei'})
        # 设置Y轴标签，使用中文字体
        ax.set_ylabel("地图 Y 坐标", fontdict={'family': 'SimHei'})
        # 添加网格线，提高可读性
        ax.grid(True, linestyle=':', alpha=0.5)