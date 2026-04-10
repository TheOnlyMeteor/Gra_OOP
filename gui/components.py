import pygame


class Checkbox:
    """右侧面板中的路线开关组件"""

    def __init__(self, x, y, width, height, route_id, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.route_id = route_id
        self.color = color
        self.is_visible = True

    def draw(self, screen, font, scroll_y):
        # 考虑滚动条偏移量的绘制
        draw_rect = self.rect.move(0, -scroll_y)

        # 绘制复选框外框
        pygame.draw.rect(screen, (255, 255, 255), draw_rect, 2)
        if self.is_visible:
            # 绘制内部填充颜色
            pygame.draw.rect(screen, self.color, draw_rect.inflate(-8, -8))

        # 绘制文字
        text = font.render(f"Route {self.route_id + 1}", True, self.color)
        screen.blit(text, (draw_rect.right + 16, draw_rect.top + 2))

    def check_click(self, mouse_pos, scroll_y):
        # 考虑滚动条偏移量的点击检测
        check_rect = self.rect.move(0, -scroll_y)
        if check_rect.collidepoint(mouse_pos):
            self.is_visible = not self.is_visible
            return True
        return False