import math
import random
from time import perf_counter

import pygame


# Cộng độ sáng nhưng giữ từng kênh màu trong khoảng hợp lệ của Pygame.
def shade(color, amount):
    return tuple(max(0, min(255, channel + amount)) for channel in color)


# Dùng chung chất liệu gỗ, bóng, nút và quân giữa mọi màn hình.
class WoodTheme:
    # Random cục bộ không ảnh hưởng việc bot chọn ngẫu nhiên khi các nước hòa điểm.
    def __init__(self, time_source=perf_counter):
        self.time_source = time_source
        self.text_color = (66, 44, 29)
        self.cache = {}
        self.pressed = {}

    # Tạo vân theo các đường cong và mắt gỗ; lưu cache để không tạo lại mỗi frame.
    def wood(self, size, color, seed=0, radius=8, circle=False, vertical=False):
        key = (tuple(size), tuple(color), seed, radius, circle, vertical)
        if key in self.cache:
            return self.cache[key]
        width, height = size
        if vertical:
            surface = pygame.transform.rotate(self.wood((height, width), color, seed, radius), 90)
            self.cache[key] = surface
            return surface
        rng = random.Random(seed)
        surface = pygame.Surface(size, pygame.SRCALPHA)
        surface.fill(color)
        phase = rng.random() * math.tau
        for y in range(-6, height + 6, 3):
            amount = rng.choice((-13, -8, -5, 4, 7))
            points = [(x, round(y + 1.8 * math.sin(x * 0.035 + phase + y * 0.09)
                                + 0.7 * math.sin(x * 0.11 + phase)))
                      for x in range(-4, width + 9, 8)]
            pygame.draw.lines(surface, shade(color, amount), False, points)
        if width > 100 and height > 45:
            cx, cy = rng.randrange(width), rng.randrange(height)
            for ring in range(3):
                pygame.draw.ellipse(surface, shade(color, -9 + ring * 3),
                                    (cx - 18 - ring * 11, cy - 3 - ring * 3,
                                     36 + ring * 22, 6 + ring * 6), 1)
        mask = pygame.Surface(size, pygame.SRCALPHA)
        if circle:
            pygame.draw.ellipse(mask, (255, 255, 255), mask.get_rect())
        else:
            pygame.draw.rect(mask, (255, 255, 255), mask.get_rect(), border_radius=radius)
        surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.cache[key] = surface
        return surface

    # Khung gỗ có bóng và mép sáng, dùng cho bàn, thẻ thông tin và menu.
    def panel(self, screen, rect, color=(231, 205, 164), radius=14, seed=0, shadow=True):
        if shadow:
            pygame.draw.rect(screen, (111, 83, 55), rect.move(0, 5), border_radius=radius)
        screen.blit(self.wood(rect.size, color, seed, radius), rect)
        pygame.draw.rect(screen, shade(color, -60), rect, width=2, border_radius=radius)
        pygame.draw.rect(screen, shade(color, 18), rect.inflate(-6, -6), width=1,
                         border_radius=max(1, radius - 3))

    # Lưu nhấn ngắn theo vùng nút để có phản hồi cả khi click đổi màn hình ngay.
    def press(self, rect):
        now = self.time_source()
        self.pressed = {key: until for key, until in self.pressed.items() if until > now}
        self.pressed[tuple(rect)] = now + 0.14

    # Nút đổi màu khi hover, lún xuống khi nhấn và làm mờ khi chưa dùng được.
    def button(self, screen, rect, text, font, enabled=True):
        hovered = enabled and rect.collidepoint(pygame.mouse.get_pos())
        pressed = enabled and (self.pressed.get(tuple(rect), 0) > self.time_source()
                               or (hovered and pygame.mouse.get_pressed()[0]))
        color = ((193, 150, 96) if pressed else (242, 215, 171) if hovered
                 else (227, 195, 147) if enabled else (219, 208, 188))
        face = rect.move(0, 3 if pressed else 0)
        self.panel(screen, face, color, radius=10, seed=3, shadow=not pressed)
        label = font.render(text, True, self.text_color if enabled else (145, 132, 112))
        screen.blit(label, label.get_rect(center=face.center))
        return face

    # Quân là đĩa gỗ nhuộm màu, có mép nổi và vòng nhấn mạnh khi tới lượt.
    def pawn(self, screen, center, color, active=False):
        center = tuple(round(value) for value in center)
        x, y = center
        if active:
            radius = 26 + round(math.sin(self.time_source() * 4) * 1)
            pygame.draw.circle(screen, (241, 190, 89), center, radius, 2)
        pygame.draw.ellipse(screen, (107, 83, 56), (x - 22, y - 14, 46, 40))
        screen.blit(self.wood((44, 44), color, seed=11, circle=True), (x - 22, y - 22))
        pygame.draw.circle(screen, shade(color, -38), center, 22, 2)
        pygame.draw.circle(screen, shade(color, 42), (x, y - 1), 18, 1)
        pygame.draw.arc(screen, shade(color, 75), (x - 18, y - 19, 36, 35),
                        math.pi * 0.15, math.pi * 0.85, 2)

    # Tường có vân dọc theo chiều dài, giữ nguyên màu phe hoặc màu xem trước.
    def wall(self, screen, rect, color, alpha=255):
        surface = self.wood(rect.size, color, seed=7, radius=3,
                            vertical=rect.height > rect.width)
        if alpha < 255:
            surface = surface.copy()
            surface.set_alpha(alpha)
        screen.blit(surface, rect)
        edge = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(edge, (*shade(color, -35), alpha), edge.get_rect(), 1, border_radius=3)
        screen.blit(edge, rect)
