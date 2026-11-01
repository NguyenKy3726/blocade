import pygame


# Vẽ menu chính, chọn cấp và chọn thứ tự trên cùng cửa sổ/font của ván.
class MenuView:
    # Các trang có thể dùng chung vị trí nút, chỉ trang hiện tại nhận click.
    def __init__(self, game_view):
        self.view = game_view
        self.start_button_rect = pygame.Rect(350, 350, 350, 60)
        self.versus_bot_button_rect = pygame.Rect(350, 440, 350, 60)
        self.exit_button_rect = pygame.Rect(350, 530, 350, 60)
        self.bot_button_rect = pygame.Rect(350, 350, 350, 60)
        self.medium_bot_button_rect = pygame.Rect(350, 440, 350, 60)
        self.hard_bot_button_rect = pygame.Rect(350, 530, 350, 60)
        self.first_button_rect = pygame.Rect(350, 350, 350, 60)
        self.second_button_rect = pygame.Rect(350, 440, 350, 60)
        self.back_button_rect = pygame.Rect(350, 620, 350, 60)

    # Nút nào được coi là điều hướng phụ thuộc trang đang hiển thị.
    def navigation_rects(self, page):
        if page == "main":
            return self.start_button_rect, self.versus_bot_button_rect, self.exit_button_rect
        if page == "levels":
            return self.bot_button_rect, self.medium_bot_button_rect, self.hard_bot_button_rect, self.back_button_rect
        return self.first_button_rect, self.second_button_rect, self.back_button_rect

    # Vẽ nhãn giữa nút và đổi nền khi chuột trỏ vào.
    def draw_button(self, rect, text):
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        color = (222, 198, 155) if hovered else (234, 220, 191)
        pygame.draw.rect(self.view.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.view.screen, self.view.text_color, rect, width=2, border_radius=8)
        label = self.view.font.render(text, True, self.view.text_color)
        self.view.screen.blit(label, label.get_rect(center=rect.center))

    # Tách lựa chọn chế độ, cấp và lượt để menu chính chỉ có hai cách chơi.
    def draw(self, page="main", mode=None):
        self.view.screen.fill(self.view.background_color)
        titles = {"main": "BLOCADE", "levels": "ĐẤU VỚI MÁY", "order": "CHỌN LƯỢT CHƠI"}
        title = self.view.title_font.render(titles[page], True, self.view.text_color)
        self.view.screen.blit(title, title.get_rect(center=(525, 225)))
        if page == "main":
            buttons = [(self.start_button_rect, "Hai người chơi"),
                       (self.versus_bot_button_rect, "Đấu với máy"), (self.exit_button_rect, "Thoát")]
            subtitle = "Hai người: 30 giây/lượt · Đấu máy: không đồng hồ"
        elif page == "levels":
            buttons = [(self.bot_button_rect, "Dễ"), (self.medium_bot_button_rect, "Trung bình"),
                       (self.hard_bot_button_rect, "Khó"), (self.back_button_rect, "Quay lại")]
            subtitle = "Chọn cấp độ của máy"
        else:
            buttons = [(self.first_button_rect, "Chơi trước"), (self.second_button_rect, "Chơi sau"),
                       (self.back_button_rect, "Quay lại")]
            subtitle = ("Bạn luôn ở dưới · Số 1 đi trước, số 2 đi sau" if mode == "bot"
                        else "Bên xanh lá ở dưới · Số 1 đi trước, số 2 đi sau")
        for rect, text in buttons:
            self.draw_button(rect, text)
        label = self.view.small_font.render(subtitle, True, self.view.text_color)
        self.view.screen.blit(label, label.get_rect(center=(525, 735)))
        pygame.display.flip()
