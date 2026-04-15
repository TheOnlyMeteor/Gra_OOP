"""
GUI渲染器文件

该文件实现了SimulationApp类，用于可视化CVRP问题的解决方案。
主要功能包括：
1. 初始化GUI窗口和相关资源
2. 预计算所有车辆的平滑路径
3. 绘制地图、障碍物、节点和车辆
4. 实现动画效果，展示车辆行驶过程
5. 提供交互式控制面板，包括路线开关和动画控制
@Author: Met
@Date: 2026-03-12
"""
import pygame
import sys
import colorsys
from config import *
from utils.path_finding import PathFinder


class SimulationApp:
    """CVRP问题解决方案可视化应用"""
    def __init__(self, nodes, grid_map, solution):
        """
        初始化应用
        :param nodes: 节点列表
        :param grid_map: 网格地图
        :param solution: 解决方案
        """
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(f"多车辆垃圾清运仿真系统 | 共 {len(solution.routes)} 辆车")

        self.nodes = nodes
        self.grid_map = grid_map
        self.solution = solution
        self.finder = PathFinder(grid_map)

        # 字体
        self.font = pygame.font.SysFont("arial, simhei, microsoftyahei", 20)
        self.btn_font = pygame.font.SysFont("arial, simhei, microsoftyahei", 16)

        # 动画状态
        self.clock = pygame.time.Clock()
        self.anim_frame = 0
        self.is_playing = False

        # --- [核心恢复] 1. 预计算所有车辆的平滑路径和节点到达帧率 ---
        print("正在后台计算多车避障平滑路径（A*），请稍候...")
        self.full_paths = []
        self.node_arrival_frames = []
        self.__precompute_all()

        # --- [核心恢复] 2. 滚动条 UI 参数 ---
        self.panel_x = COLS * CELL_SIZE
        self.top_area_height = 70
        self.bottom_area_height = 160
        self.scroll_y = 0
        self.scroll_rect = pygame.Rect(self.panel_x, self.top_area_height, 250,
                                       WINDOW_HEIGHT - self.top_area_height - self.bottom_area_height)

        num_routes = len(solution.routes)
        self.content_height = num_routes * 40
        self.max_scroll = max(0, self.content_height - self.scroll_rect.height)

        # 按钮与复选框
        self.toggle_all_rect = pygame.Rect(self.panel_x + 20, 20, 120, 35)
        self.route_visible = [True] * num_routes
        self.colors = self.__generate_distinct_colors(num_routes)

    def __generate_distinct_colors(self, n):
        """
        生成不同的颜色
        :param n: 颜色数量
        :return: List[Tuple[int, int, int]]: 颜色列表
        """
        colors = []
        for i in range(n):
            hue = (i * 0.618033988749895) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, 0.85, 0.95)
            colors.append((int(r * 255), int(g * 255), int(b * 255)))
        return colors

    def __precompute_all(self):
        """
        预计算所有车辆的平滑路径和节点到达帧率
        """
        depot_node = next(n for n in self.nodes if n.is_depot)

        for route in self.solution.routes:
            # 补齐 Depot
            full_route = [depot_node.node_id] + route.nodes + [depot_node.node_id]
            flat_path = []

            for i in range(len(full_route) - 1):
                n1 = self.nodes[full_route[i]]
                n2 = self.nodes[full_route[i + 1]]
                segment = self.finder.get_a_star_path((n1.x, n1.y), (n2.x, n2.y))

                if not flat_path:
                    flat_path.extend(segment)
                else:
                    flat_path.extend(segment[1:])  # 避免衔接重叠

            self.full_paths.append(flat_path)

            # 计算客户节点在当前车次中被访问的时刻 (帧)
            arrival_dict = {}
            for node_id in route.nodes:
                target_node = self.nodes[node_id]
                try:
                    # 找到该节点在平滑路径中出现的索引
                    arrival_dict[node_id] = flat_path.index((target_node.x, target_node.y))
                except ValueError:
                    arrival_dict[node_id] = 0
            self.node_arrival_frames.append(arrival_dict)

    def __get_visible_max_len(self):
        """
        获取可见路径的最大长度
        :return: int: 最大路径长度
        """
        # 对应你原版的多车同步时间线逻辑
        lengths = [len(self.full_paths[i]) for i in range(len(self.full_paths)) if self.route_visible[i]]
        return max(lengths, default=0)

    def draw(self):
        """
        绘制界面
        """
        self.screen.fill(COLOR_BG)

        # 1. 地图背景和障碍物
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid_map[r][c] == 1:
                    pygame.draw.rect(self.screen, COLOR_OBSTACLE, (r * CELL_SIZE, c * CELL_SIZE, CELL_SIZE, CELL_SIZE))

        # 2. 动态连线
        for i, path in enumerate(self.full_paths):
            if not self.route_visible[i] or len(path) == 0: continue

            curr_idx = min(self.anim_frame, len(path) - 1)
            path_to_draw = path[:curr_idx + 1]

            if len(path_to_draw) > 1:
                points = [(p[0] * CELL_SIZE + CELL_SIZE // 2, p[1] * CELL_SIZE + CELL_SIZE // 2) for p in path_to_draw]
                pygame.draw.lines(self.screen, self.colors[i], False, points, 3)

        # 3. 动态改变节点颜色 (核心同步恢复)
        node_colors = {node.node_id: COLOR_CUST_WAIT for node in self.nodes if not node.is_depot}
        for i in range(len(self.full_paths)):
            if self.route_visible[i]:
                for node_id, arrival_frame in self.node_arrival_frames[i].items():
                    if self.anim_frame >= arrival_frame:
                        node_colors[node_id] = COLOR_CUST_DONE  # 变红

        # 渲染节点
        for node in self.nodes:
            cx, cy = node.x * CELL_SIZE + CELL_SIZE // 2, node.y * CELL_SIZE + CELL_SIZE // 2
            if node.is_depot:
                pygame.draw.rect(self.screen, COLOR_DEPOT,
                                 (node.x * CELL_SIZE, node.y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            else:
                color = node_colors.get(node.node_id, COLOR_CUST_WAIT)
                pygame.draw.circle(self.screen, color, (cx, cy), CELL_SIZE // 2)

        # 4. 车辆动画
        for i, path in enumerate(self.full_paths):
            if self.route_visible[i] and path:
                curr_idx = min(self.anim_frame, len(path) - 1)
                if self.anim_frame > 0 or self.is_playing:
                    px, py = path[curr_idx][0] * CELL_SIZE + CELL_SIZE // 2, path[curr_idx][
                        1] * CELL_SIZE + CELL_SIZE // 2
                    pygame.draw.circle(self.screen, (255, 255, 255), (px, py), CELL_SIZE // 2 + 5)
                    pygame.draw.circle(self.screen, self.colors[i], (px, py), CELL_SIZE // 2 + 2)

        # 5. 右侧 UI 控制面板（包含滚动条）
        self.__draw_ui()

        pygame.display.flip()

    def __draw_ui(self):
        """
        绘制用户界面
        """
        # 面板底色
        pygame.draw.rect(self.screen, (50, 50, 50), (self.panel_x, 0, 250, WINDOW_HEIGHT))
        pygame.draw.line(self.screen, (255, 255, 255), (self.panel_x, 0), (self.panel_x, WINDOW_HEIGHT), 2)

        # 一键开启按钮
        pygame.draw.rect(self.screen, (100, 100, 100), self.toggle_all_rect, border_radius=5)
        pygame.draw.rect(self.screen, (255, 255, 255), self.toggle_all_rect, 2, border_radius=5)
        self.screen.blit(self.font.render("Toggle All", True, (255, 255, 255)),
                         (self.toggle_all_rect.x + 20, self.toggle_all_rect.y + 8))

        # 滚动区域
        self.screen.set_clip(self.scroll_rect)
        for i in range(len(self.solution.routes)):
            item_y = self.top_area_height + i * 40 - self.scroll_y
            if item_y > self.scroll_rect.bottom or item_y + 40 < self.scroll_rect.top: continue

            box_rect = pygame.Rect(self.panel_x + 20, item_y + 8, 24, 24)
            pygame.draw.rect(self.screen, (255, 255, 255), box_rect, 2)
            if self.route_visible[i]:
                pygame.draw.rect(self.screen, self.colors[i], box_rect.inflate(-8, -8))
            self.screen.blit(self.font.render(f"Route {i + 1}", True, self.colors[i]),
                             (box_rect.right + 16, box_rect.top))
        self.screen.set_clip(None)

        # 绘制滚动条
        if self.max_scroll > 0:
            bar_height = max(20, self.scroll_rect.height * (self.scroll_rect.height / self.content_height))
            bar_y = self.scroll_rect.top + (self.scroll_y / self.max_scroll) * (self.scroll_rect.height - bar_height)
            pygame.draw.rect(self.screen, (200, 200, 200), (self.panel_x + 240, bar_y, 6, bar_height), border_radius=3)

        # 底部面板提示
        status_y = WINDOW_HEIGHT - self.bottom_area_height + 20
        status_text = "Status: PLAYING" if self.is_playing else (
            "Status: STOPPED" if self.anim_frame > 0 else "Status: READY")
        self.screen.blit(self.font.render(status_text, True, (0, 255, 0) if self.is_playing else (200, 200, 200)),
                         (self.panel_x + 20, status_y))
        self.screen.blit(self.btn_font.render("[ SPACE ] Play/Pause", True, (200, 200, 200)),
                         (self.panel_x + 20, status_y + 40))
        self.screen.blit(self.btn_font.render("[ R ] Reset Animation", True, (200, 200, 200)),
                         (self.panel_x + 20, status_y + 65))

    def run(self):
        """
        运行应用
        """
        while True:
            visible_max_len = self.__get_visible_max_len()
            if self.is_playing:
                self.anim_frame += 1
                if self.anim_frame >= visible_max_len:
                    self.is_playing = False  # 全部跑完自动归零

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                elif event.type == pygame.MOUSEWHEEL:
                    if self.scroll_rect.collidepoint(pygame.mouse.get_pos()) and self.max_scroll > 0:
                        self.scroll_y -= event.y * 30
                        self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.toggle_all_rect.collidepoint(event.pos):
                            self.route_visible = [False] * len(self.route_visible) if all(self.route_visible) else [
                                                                                                                       True] * len(
                                self.route_visible)
                            self.anim_frame = 0;
                            self.is_playing = False

                        elif self.scroll_rect.collidepoint(event.pos):
                            clicked_idx = int((event.pos[1] - self.top_area_height + self.scroll_y) // 40)
                            if 0 <= clicked_idx < len(self.solution.routes):
                                self.route_visible[clicked_idx] = not self.route_visible[clicked_idx]
                                self.anim_frame = 0;
                                self.is_playing = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.is_playing = not self.is_playing
                        if self.is_playing and self.anim_frame >= visible_max_len: self.anim_frame = 0
                    elif event.key == pygame.K_r:
                        self.anim_frame = 0;
                        self.is_playing = False

            self.draw()
            self.clock.tick(30)