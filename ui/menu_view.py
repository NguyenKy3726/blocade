import pygame


# Vẽ menu chính trên cùng cửa sổ và dùng chung font/màu với bàn cờ.
class MenuView:
    # Nhận giao diện đã khởi tạo để không tạo thêm cửa sổ Pygame.
    def __init__(self, game_view):
        self.view = game_view
        self.start_button_rect = pygame.Rect(350, 350, 350, 60)
        self.exit_button_rect = pygame.Rect(350, 440, 350, 60)

    # Vẽ nhãn ở giữa nút và đổi nền khi chuột trỏ vào.
    def draw_button(self, rect, text):
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        color = (222, 198, 155) if hovered else (234, 220, 191)
        pygame.draw.rect(self.view.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.view.screen, self.view.text_color, rect,
                         width=2, border_radius=8)
        label = self.view.font.render(text, True, self.view.text_color)
        self.view.screen.blit(label, label.get_rect(center=rect.center))

    # Chỉ hiển thị các chế độ đã chơi được; không vẽ hoặc cập nhật đồng hồ ván.
    def draw(self):
        self.view.screen.fill(self.view.background_color)
        title = self.view.title_font.render("BLOCADE", True, self.view.text_color)
        self.view.screen.blit(title, title.get_rect(center=(525, 225)))
        for x, color in zip((495, 555), self.view.player_colors):
            pygame.draw.circle(self.view.screen, color, (x, 285), 16)
        self.draw_button(self.start_button_rect, "Hai người chơi")
        self.draw_button(self.exit_button_rect, "Thoát")
        label = self.view.small_font.render("30 giây mỗi lượt · Điều khiển bằng chuột",
                                           True, self.view.text_color)
        self.view.screen.blit(label, label.get_rect(center=(525, 550)))
        pygame.display.flip()
