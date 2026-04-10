import pygame
import sys
import os

# --- 1. 配置参数 ---
VRP_FILE = "X-n125-k30.vrp"  # 请确保该文件在目录下
OUTPUT_FILE = "obstacles_dev.txt"
ROWS = 101
COLS = 101
CELL_SIZE = 8  # 每个格子占 8 像素
WIDTH = COLS * CELL_SIZE
HEIGHT = ROWS * CELL_SIZE

# 颜色定义
WHITE = (255, 255, 255)  # 墙壁 (1)
BLACK = (30, 30, 30)  # 通路 (0) - 道路
RED = (255, 0, 0)  # VRP 节点
GRAY = (200, 200, 200)  # 网格线


# --- 2. VRP 解析函数 ---
def parse_vrp_coords(filepath):
    coords = []
    if not os.path.exists(filepath):
        print(f"找不到文件: {filepath}")
        return []

    reading = False
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("NODE_COORD_SECTION"):
                reading = True
                continue
            if line.startswith("DEMAND_SECTION") or line.startswith("DEPOT_SECTION"):
                reading = False
                break
            if reading:
                parts = line.split()
                if len(parts) >= 3:
                    # 提取 x, y 并转为整数
                    x, y = int(float(parts[1])), int(float(parts[2]))
                    coords.append((x, y))
    return coords


# --- 3. 保存地图函数 ---
def save_map(grid):
    with open(OUTPUT_FILE, "w") as f:
        for row in grid:
            f.write(" ".join(map(str, row)) + "\n")
    print(f"地图已成功保存至: {OUTPUT_FILE}")


# --- 4. 主程序 ---
def main():
    # 禁用 pygame 的音频和 joystick 模块，减少系统文件访问
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("地图编辑器: 左键画道路, 右键画墙壁, 空格保存")

    # 初始化网格 (0 为通路)
    grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    
    # 尝试加载现有obstacles.txt文件
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r') as f:
                for r, line in enumerate(f):
                    if r < ROWS:
                        parts = line.strip().split()
                        for c, val in enumerate(parts):
                            if c < COLS:
                                grid[r][c] = int(val)
            print(f"成功加载现有地图: {OUTPUT_FILE}")
        except Exception as e:
            print(f"加载地图失败: {e}")
    else:
        print("未找到现有地图，使用空白地图")

    # 加载 VRP 坐标
    node_coords = parse_vrp_coords(VRP_FILE)

    clock = pygame.time.Clock()

    drawing = False
    erasing = False

    while True:
        screen.fill(WHITE)

        # 绘制网格状态
        for r in range(ROWS):
            for c in range(COLS):
                if grid[r][c] == 0:  # 通路 - 道路
                    pygame.draw.rect(screen, BLACK, (r * CELL_SIZE, c * CELL_SIZE, CELL_SIZE, CELL_SIZE))
                else:  # 墙壁
                    pygame.draw.rect(screen, WHITE, (r * CELL_SIZE, c * CELL_SIZE, CELL_SIZE, CELL_SIZE))

        # 绘制网格线 (可选，方便对齐)
        for i in range(0, WIDTH, CELL_SIZE):
            pygame.draw.line(screen, GRAY, (i, 0), (i, HEIGHT))
            pygame.draw.line(screen, GRAY, (0, i), (WIDTH, i))

        # 绘制 VRP 红色点 (显示在最上层)
        for x, y in node_coords:
            if 0 <= x < ROWS and 0 <= y < COLS:
                # 画一个小圆形代表节点
                pygame.draw.circle(screen, RED,
                                   (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2),
                                   CELL_SIZE // 2)

        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # 鼠标按下
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: drawing = True  # 左键
                if event.button == 3: erasing = True  # 右键

            # 鼠标松开
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1: drawing = False
                if event.button == 3: erasing = False

            # 按键处理
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    save_map(grid)
                    # 闪烁效果提示已保存
                    screen.fill((0, 255, 0))
                    pygame.display.update()
                    pygame.time.delay(200)

        # 涂抹逻辑
        if drawing or erasing:
            mx, my = pygame.mouse.get_pos()
            # 注意：坐标映射 x -> row, y -> col
            grid_x = mx // CELL_SIZE
            grid_y = my // CELL_SIZE

            if 0 <= grid_x < ROWS and 0 <= grid_y < COLS:
                grid[grid_x][grid_y] = 0 if drawing else 1  # 左键画道路(0)，右键画墙壁(1)

        pygame.display.update()
        clock.tick(60)


if __name__ == "__main__":
    print("启动地图编辑器...")
    print(f"VRP文件: {VRP_FILE}")
    print(f"输出文件: {OUTPUT_FILE}")
    print("操作说明:")
    print("- 左键: 画道路 (黑色)")
    print("- 右键: 画墙壁 (白色)")
    print("- 空格: 保存地图")
    print("- ESC: 退出")
    
    try:
        main()
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()