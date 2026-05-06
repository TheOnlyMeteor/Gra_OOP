"""
垃圾运输优化管理系统界面 (MVC - View)
包含CRUD交互、双算法报表对比、以及高精度的双算法线路图谱对比展示。
@Author: Met
@Date: 2026-03-12
"""
import os
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from gui.renderer import SimulationApp

# ========== 绿色环保主题配色 ==========
COLORS = {
    "primary":      "#1B5E20",
    "secondary":    "#43A047",
    "light":        "#E8F5E9",
    "accent":       "#EF6C00",
    "danger":       "#C62828",
    "edit":         "#1565C0",
    "dark_text":    "#263238",
    "mid_text":     "#78909C",
    "white":        "#FFFFFF",
    "bg":           "#EEF1F5",
    "card":         "#FFFFFF",
    "border":       "#E0E0E0",
    "tab_bar_bg":   "#DCE3E8",
}

# 标签页配置
TAB_CONFIG = [
    ("垃圾点信息管理", "data"),
    ("线路规划与调度", "optimize"),
    ("运输效率评估",   "dashboard"),
    ("线路对比图谱",   "map"),
]


def start_pygame_renderer(nodes_data, grid_map_data, solution_data):
    sim = SimulationApp(nodes_data, grid_map_data, solution_data)
    sim.run()


class SystemMainWindow(tk.Tk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._active_tab = 0

        self.title("面向垃圾运输网络的线路优化系统 v2.2")
        self.geometry("1120x780")
        self.minsize(1050, 650)
        self.configure(bg=COLORS["bg"])

        self._setup_theme()
        self._build_header()
        self._build_tab_bar()
        self._build_content_area()

        self.init_data_tab()
        self.init_optimize_tab()
        self.init_dashboard_tab()
        self.init_map_tab()

        self._switch_tab(0)

        self.controller.load_system_data()
        self.refresh_data_table()

    # ================= 主题系统 =================
    def _setup_theme(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(".", font=("Microsoft YaHei", 10), background=COLORS["bg"])

        # ---- Frame ----
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("Card.TFrame", background=COLORS["card"],
                        relief="flat", borderwidth=0)

        # ---- Label ----
        style.configure("TLabel", background=COLORS["bg"],
                        foreground=COLORS["dark_text"])
        style.configure("Title.TLabel",
                        font=("Microsoft YaHei", 15, "bold"),
                        foreground=COLORS["primary"],
                        background=COLORS["bg"])
        style.configure("Subtitle.TLabel",
                        font=("Microsoft YaHei", 10),
                        foreground=COLORS["mid_text"],
                        background=COLORS["bg"])

        # ---- LabelFrame ----
        style.configure("Card.TLabelframe",
                        background=COLORS["card"],
                        borderwidth=1,
                        relief="solid",
                        bordercolor=COLORS["border"])
        style.configure("Card.TLabelframe.Label",
                        font=("Microsoft YaHei", 11, "bold"),
                        foreground=COLORS["primary"],
                        background=COLORS["card"])

        # ---- 按钮 ----
        for name, bg, active_bg, disabled_bg, bold in [
            ("Primary.TButton", COLORS["secondary"], "#2E7D32", "#A5D6A7", True),
            ("Danger.TButton",  COLORS["danger"],   "#B71C1C", "#EF9A9A", False),
            ("Accent.TButton",  COLORS["accent"],   "#E65100", "#FFCC80", True),
            ("Edit.TButton",    COLORS["edit"],     "#0D47A1", "#90CAF9", False),
        ]:
            style.configure(name,
                            font=("Microsoft YaHei", 10,
                                  "bold" if bold else "normal"),
                            background=bg,
                            foreground=COLORS["white"],
                            borderwidth=0,
                            padding=[18, 7])
            style.map(name,
                      background=[("active", active_bg),
                                  ("disabled", disabled_bg)],
                      foreground=[("disabled", COLORS["white"])])

        style.configure("TButton",
                        font=("Microsoft YaHei", 10),
                        padding=[18, 7])

        # ---- Treeview ----
        style.configure("Treeview",
                        background=COLORS["white"],
                        fieldbackground=COLORS["white"],
                        foreground=COLORS["dark_text"],
                        rowheight=34,
                        font=("Microsoft YaHei", 10))
        style.configure("Treeview.Heading",
                        font=("Microsoft YaHei", 10, "bold"),
                        background=COLORS["primary"],
                        foreground=COLORS["white"],
                        padding=[10, 7])
        style.map("Treeview",
                  background=[("selected", COLORS["secondary"])],
                  foreground=[("selected", COLORS["white"])])

        # ---- Progressbar ----
        style.configure("TProgressbar",
                        background=COLORS["secondary"],
                        troughcolor=COLORS["border"],
                        thickness=8)

        # ---- Entry / Combobox ----
        style.configure("TEntry", fieldbackground=COLORS["white"],
                        padding=[8, 5])
        style.configure("TCombobox", fieldbackground=COLORS["white"],
                        padding=[4, 2])

    # ================= 顶部标题栏 =================
    def _build_header(self):
        header = tk.Frame(self, bg=COLORS["primary"], height=52)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        inner = tk.Frame(header, bg=COLORS["primary"])
        inner.pack(expand=True)

        tk.Label(inner,
                 text="♻  面向垃圾运输网络的线路优化系统",
                 font=("Microsoft YaHei", 15, "bold"),
                 fg=COLORS["white"],
                 bg=COLORS["primary"]).pack(side=tk.LEFT, padx=4)

        tk.Label(inner,
                 text="  |  CVRP Genetic Algorithm Solver v2.2",
                 font=("Microsoft YaHei", 9),
                 fg="#A5D6A7",
                 bg=COLORS["primary"]).pack(side=tk.LEFT, padx=(10, 0))

    # ================= 自定义 Tab Bar =================
    def _build_tab_bar(self):
        bar_height = 44
        self.tab_bar = tk.Frame(self, bg=COLORS["tab_bar_bg"], height=bar_height)
        self.tab_bar.pack(fill=tk.X, padx=10, pady=(10, 0))
        self.tab_bar.pack_propagate(False)

        inner = tk.Frame(self.tab_bar, bg=COLORS["tab_bar_bg"])
        inner.pack(fill=tk.BOTH, expand=True)

        self.tab_labels = []
        self.tab_indicators = []

        for i, (text, _key) in enumerate(TAB_CONFIG):
            inner.columnconfigure(i, weight=1, uniform="tab")

            tab_item = tk.Frame(inner, bg=COLORS["tab_bar_bg"], cursor="hand2")
            tab_item.grid(row=0, column=i, sticky="")

            lbl = tk.Label(tab_item, text=text,
                           font=("Microsoft YaHei", 12),
                           fg=COLORS["mid_text"],
                           bg=COLORS["tab_bar_bg"],
                           padx=12, pady=8,
                           cursor="hand2")
            lbl.pack()

            indicator = tk.Frame(tab_item, bg=COLORS["tab_bar_bg"], height=3)
            indicator.pack(fill=tk.X)

            lbl.bind("<Button-1>", lambda e, idx=i: self._switch_tab(idx))
            lbl.bind("<Enter>", lambda e, l=lbl, idx=i: self._on_tab_hover(l, idx, True))
            lbl.bind("<Leave>", lambda e, l=lbl, idx=i: self._on_tab_hover(l, idx, False))

            self.tab_labels.append(lbl)
            self.tab_indicators.append(indicator)

    def _on_tab_hover(self, label, idx, entering):
        if idx == self._active_tab:
            return
        if entering:
            label.config(fg=COLORS["primary"])
        else:
            label.config(fg=COLORS["mid_text"])

    def _switch_tab(self, idx):
        self._active_tab = idx
        for i, (lbl, ind) in enumerate(zip(self.tab_labels, self.tab_indicators)):
            if i == idx:
                lbl.config(fg=COLORS["primary"],
                           font=("Microsoft YaHei", 12, "bold"))
                ind.config(bg=COLORS["primary"])
            else:
                lbl.config(fg=COLORS["mid_text"],
                           font=("Microsoft YaHei", 12))
                ind.config(bg=COLORS["tab_bar_bg"])

        for key in self.tab_frames:
            self.tab_frames[key].pack_forget()
        self.tab_frames[TAB_CONFIG[idx][1]].pack(fill=tk.BOTH, expand=True)

    # ================= 内容区域 =================
    def _build_content_area(self):
        self.content_area = tk.Frame(self, bg=COLORS["bg"])
        self.content_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.tab_frames = {}
        for _text, key in TAB_CONFIG:
            frame = ttk.Frame(self.content_area)
            self.tab_frames[key] = frame

    # ================= 标签页一：垃圾点信息管理 =================
    def init_data_tab(self):
        frame = self.tab_frames["data"]

        # 标题区
        title_bar = ttk.Frame(frame)
        title_bar.pack(fill=tk.X, padx=20, pady=(18, 8))
        ttk.Label(title_bar, text="垃圾收运点数据管理",
                  style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Label(title_bar, text="支持增删改节点 / CSV 导入导出",
                  style="Subtitle.TLabel").pack(side=tk.LEFT, padx=(14, 0))

        # 工具栏
        toolbar_card = ttk.Frame(frame, style="Card.TFrame")
        toolbar_card.pack(fill=tk.X, padx=20, pady=(0, 12))
        toolbar_card.columnconfigure(0, weight=1)

        left_grp = ttk.Frame(toolbar_card, style="Card.TFrame")
        left_grp.grid(row=0, column=0, sticky="w", padx=14, pady=10)

        ttk.Button(left_grp, text=" 新增节点 ", style="Primary.TButton",
                   command=self.add_node).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(left_grp, text=" 修改选中 ", style="Edit.TButton",
                   command=self.edit_node).pack(side=tk.LEFT, padx=6)
        ttk.Button(left_grp, text=" 删除选中 ", style="Danger.TButton",
                   command=self.delete_node).pack(side=tk.LEFT, padx=6)

        tk.Frame(left_grp, bg=COLORS["border"], width=1,
                 height=26).pack(side=tk.LEFT, padx=14)

        ttk.Button(left_grp, text=" 导入 CSV ", command=self.import_csv).pack(
            side=tk.LEFT, padx=6)
        ttk.Button(left_grp, text=" 导出 CSV ", command=self.export_csv).pack(
            side=tk.LEFT, padx=6)

        right_grp = ttk.Frame(toolbar_card, style="Card.TFrame")
        right_grp.grid(row=0, column=1, sticky="e", padx=14, pady=10)

        ttk.Button(right_grp, text=" 应用更改并重排网络 ", style="Accent.TButton",
                   command=self.apply_changes).pack()

        # 数据表格
        columns = ("ID", "节点类型", "X坐标", "Y坐标", "预计产生垃圾量(kg)")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings",
                                 height=16)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER, width=140)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 12))

        ttk.Label(frame, text="提示：选中行后可使用上方按钮进行修改或删除",
                  style="Subtitle.TLabel").pack(pady=(0, 10))

    # ---- CRUD 操作方法 ----
    def refresh_data_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in self.controller.get_garbage_points_data():
            self.tree.insert("", tk.END, values=row)

    def add_node(self):
        new_id = len(self.tree.get_children()) + 1
        self._open_node_dialog("新增垃圾点", None, None, new_id)

    def edit_node(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要修改的节点！")
            return
        item = self.tree.item(selected[0])['values']
        self._open_node_dialog("修改垃圾点", item, selected[0], item[0])

    def delete_node(self):
        selected = self.tree.selection()
        if selected and messagebox.askyesno("确认", "确定要删除该节点吗？"):
            self.tree.delete(selected[0])

    def _open_node_dialog(self, title, init_data=None, item_id=None,
                          assigned_id=1):
        top = tk.Toplevel(self)
        top.title(title)
        top.geometry("360x300")
        top.configure(bg=COLORS["bg"])
        top.resizable(False, False)

        content = ttk.Frame(top)
        content.pack(fill=tk.BOTH, expand=True, padx=24, pady=24)

        fields = [
            ("节点 ID:", str(assigned_id), True),
            ("节点类型:", init_data[1] if init_data else "垃圾收运点", False),
            ("X 坐标:", str(init_data[2]) if init_data else "0", False),
            ("Y 坐标:", str(init_data[3]) if init_data else "0", False),
            ("垃圾量(kg):", str(init_data[4]) if init_data else "10", False),
        ]

        entries = {}
        for i, (label, val, readonly) in enumerate(fields):
            ttk.Label(content, text=label).grid(
                row=i, column=0, pady=7, padx=(0, 8), sticky="e")
            if readonly:
                ttk.Label(content, text=val,
                          foreground=COLORS["mid_text"]).grid(
                    row=i, column=1, sticky="w", padx=4)
            elif i == 1:
                var = tk.StringVar(value=val)
                ttk.Combobox(content, textvariable=var,
                             values=["垃圾处理车场", "垃圾收运点"],
                             state="readonly", width=20).grid(
                    row=i, column=1, padx=4)
                entries["type"] = var
            else:
                e = ttk.Entry(content, width=22)
                e.insert(0, val)
                e.grid(row=i, column=1, padx=4)
                entries[label] = e

        def save():
            try:
                x = int(entries["X 坐标:"].get())
                y = int(entries["Y 坐标:"].get())
                d = int(entries["垃圾量(kg):"].get())
                if x < 0 or y < 0 or d < 0:
                    raise ValueError
                values = (assigned_id, entries["type"].get(), x, y, d)
                if item_id:
                    self.tree.item(item_id, values=values)
                else:
                    self.tree.insert("", tk.END, values=values)
                top.destroy()
            except ValueError:
                messagebox.showerror("错误",
                                     "坐标和垃圾量必须是大于等于0的整数！")

        ttk.Button(content, text="保存修改", style="Primary.TButton",
                   command=save).grid(row=5, column=0, columnspan=2,
                                      pady=(20, 0))

    def apply_changes(self):
        data = [self.tree.item(child)["values"]
                for child in self.tree.get_children()]

        depot_count = sum(1 for item in data if item[1] == "垃圾处理车场")
        if depot_count != 1:
            messagebox.showerror("业务验证失败",
                                 f"系统中必须有且仅有 1 个【垃圾处理车场】！"
                                 f"当前有 {depot_count} 个。请修改节点类型。")
            return

        vehicle_capacity = self.controller.capacity
        for item in data:
            if item[1] == "垃圾收运点" and int(item[4]) > vehicle_capacity:
                messagebox.showerror("容量逻辑错误",
                                     f"显示 ID 为 {item[0]} 的垃圾量 ({item[4]}kg) "
                                     f"超出了单辆车的最大额定载重 ({vehicle_capacity}kg)！")
                return

        self.controller.update_nodes_from_ui(data)
        self.refresh_data_table()
        messagebox.showinfo("成功", "更改已成功应用！")

    def import_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if path:
            self.controller.import_from_csv(path)
            self.refresh_data_table()
            messagebox.showinfo("成功", "导入成功，矩阵已重算。")

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if path:
            self.controller.export_to_csv(path)
            messagebox.showinfo("成功", "数据导出成功！")

    # ================= 标签页二：线路规划与调度 =================
    def init_optimize_tab(self):
        frame = self.tab_frames["optimize"]

        title_bar = ttk.Frame(frame)
        title_bar.pack(fill=tk.X, padx=20, pady=(18, 8))
        ttk.Label(title_bar, text="算法参数配置与调度执行",
                  style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Label(title_bar, text="设置参数后启动双算法对比引擎",
                  style="Subtitle.TLabel").pack(side=tk.LEFT, padx=(14, 0))

        # 参数卡片
        card = ttk.LabelFrame(frame, text=" 遗传算法引擎参数 ",
                              style="Card.TLabelframe")
        card.pack(fill=tk.X, padx=20, pady=(6, 14))

        inner = ttk.Frame(card)
        inner.pack(padx=28, pady=20)

        ttk.Label(inner, text="种群规模",
                  font=("Microsoft YaHei", 11)).grid(
            row=0, column=0, padx=(0, 6), pady=8, sticky="e")
        self.pop_entry = ttk.Entry(inner, width=8,
                                   font=("Microsoft YaHei", 11))
        self.pop_entry.insert(0, "80")
        self.pop_entry.grid(row=0, column=1, padx=(0, 20))

        ttk.Label(inner, text="迭代代数",
                  font=("Microsoft YaHei", 11)).grid(
            row=0, column=2, padx=(0, 6), pady=8, sticky="e")
        self.gen_entry = ttk.Entry(inner, width=8,
                                   font=("Microsoft YaHei", 11))
        self.gen_entry.insert(0, "300")
        self.gen_entry.grid(row=0, column=3)

        ttk.Label(inner,
                  text="建议范围：种群 60-120  /  代数 200-500。"
                       "数值越大精度越高但耗时更长。",
                  foreground=COLORS["mid_text"],
                  font=("Microsoft YaHei", 9)).grid(
            row=1, column=0, columnspan=4, pady=(8, 0), sticky="w")

        # 执行按钮
        ctrl_card = ttk.Frame(frame, style="Card.TFrame")
        ctrl_card.pack(fill=tk.X, padx=20, pady=(0, 12))

        self.btn_run = ttk.Button(ctrl_card,
                                  text="启动对比分析引擎 "
                                       "(基础 GA vs 改进 GA)",
                                  style="Primary.TButton",
                                  command=self.start_optimization)
        self.btn_run.pack(padx=20, pady=16)

        # 进度条
        prog_frame = ttk.Frame(frame)
        prog_frame.pack(fill=tk.X, padx=20, pady=(2, 6))
        self.progress_var = tk.DoubleVar()
        ttk.Progressbar(prog_frame, variable=self.progress_var, maximum=100,
                        style="TProgressbar").pack(fill=tk.X)

        self.status_label = ttk.Label(frame, text="系统就绪，等待执行...",
                                      font=("Microsoft YaHei", 10))
        self.status_label.pack(pady=(0, 12))

    def start_optimization(self):
        pop = int(self.pop_entry.get())
        gen = int(self.gen_entry.get())
        self.btn_run.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.controller.run_optimization_async(
            pop, gen, self.update_progress, self.on_optimization_finish)

    def update_progress(self, percent, cost, stage_str):
        self.progress_var.set(percent)
        self.status_label.config(
            text=f"[{stage_str}]  进度: {percent}%  |  "
                 f"当前最优成本: {cost:.2f}",
            foreground=COLORS["accent"])

    def on_optimization_finish(self):
        self.btn_run.config(state=tk.NORMAL)
        self.status_label.config(
            text="计算完成！请查看【运输效率评估】与【线路对比图谱】标签页。",
            foreground=COLORS["primary"])
        self.draw_dashboard()
        self.draw_route_maps()

    # ================= 标签页三：运输效率评估 =================
    def init_dashboard_tab(self):
        frame = self.tab_frames["dashboard"]

        title_bar = ttk.Frame(frame)
        title_bar.pack(fill=tk.X, padx=20, pady=(18, 8))
        ttk.Label(title_bar, text="算法性能与车辆满载率分析",
                  style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Label(title_bar, text="基础 GA（对照组） vs 改进 GA（实验组）",
                  style="Subtitle.TLabel").pack(side=tk.LEFT, padx=(14, 0))

        # 统计信息卡片
        stat_card = ttk.Frame(frame, style="Card.TFrame")
        stat_card.pack(fill=tk.X, padx=20, pady=(0, 12))
        self.stat_label = ttk.Label(stat_card,
                                    text="暂无评估数据，请先在"
                                         "【线路规划与调度】中启动算法引擎...",
                                    font=("Microsoft YaHei", 11),
                                    foreground=COLORS["mid_text"])
        self.stat_label.pack(padx=18, pady=14)

        self.canvas_frame = ttk.Frame(frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=12)

        self.btn_sim = ttk.Button(frame,
                                  text="启动 IGA 最优路径动态仿真",
                                  style="Accent.TButton",
                                  state=tk.DISABLED,
                                  command=self.launch_sim)
        self.btn_sim.pack(pady=(10, 14))

    def draw_dashboard(self):
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        m = self.controller.get_evaluation_metrics()
        if not m:
            return

        self._update_dashboard_text(m)
        fig = self._generate_dashboard_figure(m)

        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _update_dashboard_text(self, m):
        imp = ((m['total_cost_pure'] - m['total_cost_improved']) /
               m['total_cost_pure']) * 100
        text = (
            f"  基础 GA 成本: {m['total_cost_pure']:.2f}  │  "
            f"改进 GA 成本: {m['total_cost_improved']:.2f}  │  "
            f"优化提升率: {imp:.2f}%  │  "
            f"调派车辆: {m['vehicle_count']} 辆"
        )
        self.stat_label.config(text=text, foreground=COLORS["primary"])
        self.btn_sim.config(state=tk.NORMAL)

    def _generate_dashboard_figure(self, m):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

        ax1.plot(m['history_pure'], color='gray', linestyle='--',
                 label='对照组 (基础GA)')
        ax1.plot(m['history_improved'], color='#4CAF50', linewidth=2,
                 label='实验组 (改进GA)')
        ax1.set_title("算法收敛性能对比分析",
                      fontdict={'family': 'SimHei'})
        ax1.set_xlabel("迭代代数", fontdict={'family': 'SimHei'})
        ax1.set_ylabel("规划成本 (距离)", fontdict={'family': 'SimHei'})
        ax1.legend(prop={'family': 'SimHei'})
        ax1.grid(True, alpha=0.3)

        vehicles, rates = (zip(*m['load_rates'])
                           if m['load_rates'] else ([], []))
        bars = ax2.bar(vehicles, rates, color='#4CAF50', alpha=0.85)
        ax2.set_title("各清运车辆满载率评估 (%)",
                      fontdict={'family': 'SimHei'})
        ax2.set_ylim(0, max(110, max(rates) + 10) if rates else 110)
        ax2.axhline(100, color='#D32F2F', linestyle=':',
                     label='标准容量线 (100%)')
        ax2.legend(prop={'family': 'SimHei'})

        for bar in bars:
            yval = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2.0, yval + 1,
                     f'{yval:.1f}%', ha='center', va='bottom', fontsize=8)

        plt.tight_layout()
        os.makedirs("data/output", exist_ok=True)
        try:
            fig.savefig("data/output/evolution.svg",
                        format="svg", bbox_inches='tight')
            fig.savefig("data/output/evolution.png",
                        format="png", dpi=300, bbox_inches='tight')
            print("效率评估图表已保存到 data/output/ 目录！")
        except Exception as e:
            print(f"保存图表失败: {e}")
        return fig

    def launch_sim(self):
        nodes_data = self.controller.nodes
        solution_data = self.controller.best_solution

        if hasattr(self.controller, 'grid_map'):
            grid_map_data = self.controller.grid_map
        elif hasattr(self.controller, 'grid'):
            grid_map_data = self.controller.grid
        elif hasattr(self.controller, 'map_data'):
            grid_map_data = self.controller.map_data
        elif hasattr(self.controller, 'obstacle_map'):
            grid_map_data = self.controller.obstacle_map
        elif hasattr(self.controller, 'matrix'):
            grid_map_data = self.controller.matrix
        else:
            print("=" * 50)
            print("找不到地图变量！Controller 实际拥有的变量是：")
            print(list(self.controller.__dict__.keys()))
            print("=" * 50)
            grid_map_data = np.zeros((101, 101)).tolist()

        import multiprocessing
        sim_process = multiprocessing.Process(
            target=start_pygame_renderer,
            args=(nodes_data, grid_map_data, solution_data)
        )
        sim_process.start()

    # ================= 标签页四：线路对比图谱 =================
    def init_map_tab(self):
        frame = self.tab_frames["map"]

        title_bar = ttk.Frame(frame)
        title_bar.pack(fill=tk.X, padx=20, pady=(18, 8))
        ttk.Label(title_bar, text="双算法路线规划可视化对比",
                  style="Title.TLabel").pack(side=tk.LEFT)

        self.map_info_label = ttk.Label(frame,
                                        text="暂无图谱数据，请先在"
                                             "【线路规划与调度】中运行算法...",
                                        font=("Microsoft YaHei", 11),
                                        foreground=COLORS["mid_text"])
        self.map_info_label.pack(pady=8)

        self.map_canvas_frame = ttk.Frame(frame)
        self.map_canvas_frame.pack(fill=tk.BOTH, expand=True,
                                   padx=12, pady=(0, 8))

    def draw_route_maps(self):
        for widget in self.map_canvas_frame.winfo_children():
            widget.destroy()

        if not self.controller.best_solution or \
           not self.controller.pure_solution:
            return

        self.map_info_label.config(
            text="全网垃圾收运车辆轨迹详细图谱对比",
            font=("SimHei", 13, "bold"),
            foreground=COLORS["primary"])

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        self.__plot_single_route(
            ax=ax1,
            nodes=self.controller.nodes,
            solution=self.controller.pure_solution,
            title=f"对照组：基础 GA "
                  f"(成本: {self.controller.pure_solution.total_cost:.2f})"
        )
        self.__plot_single_route(
            ax=ax2,
            nodes=self.controller.nodes,
            solution=self.controller.best_solution,
            title=f"实验组：改进 GA "
                  f"(成本: {self.controller.best_solution.total_cost:.2f})"
        )

        plt.tight_layout()
        os.makedirs("data/output", exist_ok=True)
        try:
            fig.savefig("data/output/route_map.svg",
                        format="svg", bbox_inches='tight')
            fig.savefig("data/output/route_map.png",
                        format="png", dpi=300, bbox_inches='tight')
            print("线路对比图谱已保存到 data/output/ 目录！")
        except Exception as e:
            print(f"保存线路图谱失败: {e}")

        canvas = FigureCanvasTkAgg(fig, master=self.map_canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def __plot_single_route(self, ax, nodes, solution, title):
        coords = {n.node_id: (n.x, n.y) for n in nodes}
        display_id = {n.node_id: n.node_id + 1 for n in nodes}

        depot_node = next(n for n in nodes if n.is_depot)
        depot_xy = (depot_node.x, depot_node.y)

        all_x = [n.x for n in nodes if not n.is_depot]
        all_y = [n.y for n in nodes if not n.is_depot]
        ax.scatter(all_x, all_y, c='lightgray', s=30, alpha=0.3, zorder=1)

        cmap = plt.get_cmap('tab20')
        for r_idx, route in enumerate(solution.routes):
            color = cmap(r_idx % 20)
            route_coords = ([depot_xy] +
                            [coords[nid] for nid in route.nodes] +
                            [depot_xy])
            xs, ys = zip(*route_coords)
            ax.plot(xs, ys, color=color, linewidth=1.5, alpha=0.7, zorder=2)

            for i in range(len(xs) - 1):
                ax.annotate('', xy=(xs[i + 1], ys[i + 1]),
                            xytext=(xs[i], ys[i]),
                            arrowprops=dict(arrowstyle='->', color=color,
                                            lw=1, alpha=0.6))

            for nid in route.nodes:
                nx, ny = coords[nid]
                ax.text(nx, ny + 1.2, str(display_id[nid]),
                        color='black', fontsize=8,
                        ha='center', va='center', fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.1', fc='white',
                                  ec=color, alpha=0.8, lw=1))
                ax.scatter(nx, ny, color=color, s=25, zorder=3)

        ax.scatter(*depot_xy, c='red', marker='s', s=150, zorder=5)
        ax.text(depot_xy[0], depot_xy[1] - 2.5,
                f"车场 ({display_id[depot_node.node_id]})",
                color='red', fontweight='bold', ha='center', fontsize=10)

        ax.set_title(title, fontdict={'family': 'SimHei', 'size': 12})
        ax.set_xlabel("地图 X 坐标", fontdict={'family': 'SimHei'})
        ax.set_ylabel("地图 Y 坐标", fontdict={'family': 'SimHei'})
        ax.grid(True, linestyle=':', alpha=0.5)
