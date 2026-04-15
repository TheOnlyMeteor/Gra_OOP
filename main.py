"""
垃圾运输优化系统 - 程序入口
启动基于 Tkinter 的 MVC 图形界面
"""
from controllers import SystemController
from system_ui import SystemMainWindow
import matplotlib

# 解决 Matplotlib 中文字体显示问题
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
matplotlib.rcParams['axes.unicode_minus'] = False

if __name__ == "__main__":
    # 1. 实例化核心控制器
    controller = SystemController()

    # 2. 实例化并启动图形系统界面
    app = SystemMainWindow(controller)
    app.mainloop()