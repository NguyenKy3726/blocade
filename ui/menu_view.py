import pygame


# Vẽ menu, chọn bot và hướng dẫn trên cùng cửa sổ/font của ván.
class MenuView:
    # Các trang có thể dùng chung vị trí nút, chỉ trang hiện tại nhận click.
    def __init__(self, game_view):
        self.view = game_view
        self.start_button_rect = pygame.Rect(350, 350, 350, 60)
        self.versus_bot_button_rect = pygame.Rect(350, 440, 350, 60)
        self.bot_button_rect = pygame.Rect(350, 350, 350, 60)
        self.medium_bot_button_rect = pygame.Rect(350, 440, 350, 60)
        self.hard_bot_button_rect = pygame.Rect(350, 530, 350, 60)
        self.first_button_rect = pygame.Rect(350, 350, 350, 60)
        self.second_button_rect = pygame.Rect(350, 440, 350, 60)
        self.back_button_rect = pygame.Rect(40, 32, 144, 48)
        self.help_button_rect = pygame.Rect(self.view.width - 92, 32, 52, 52)

    # Nút nào được coi là điều hướng phụ thuộc trang đang hiển thị.
    def navigation_rects(self, page):
        if page == "main":
            return self.start_button_rect, self.versus_bot_button_rect, self.help_button_rect
        if page == "levels":
            return self.bot_button_rect, self.medium_bot_button_rect, self.hard_bot_button_rect, self.back_button_rect
        if page == "help":
            return (self.back_button_rect,)
        return self.first_button_rect, self.second_button_rect, self.back_button_rect

    # Vẽ nhãn giữa nút và đổi nền khi chuột trỏ vào.
    def draw_button(self, rect, text):
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        color = (222, 198, 155) if hovered else (234, 220, 191)
        pygame.draw.rect(self.view.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.view.screen, self.view.text_color, rect, width=2, border_radius=8)
        label = self.view.font.render(text, True, self.view.text_color)
        self.view.screen.blit(label, label.get_rect(center=rect.center))

    # Vẽ mũi tên bằng nét Pygame để icon không cần thêm ảnh hoặc font ký hiệu.
    def draw_back_button(self):
        rect = self.back_button_rect
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        color = (222, 198, 155) if hovered else (234, 220, 191)
        pygame.draw.rect(self.view.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.view.screen, self.view.text_color, rect, width=2, border_radius=8)
        x, y = rect.x + 20, rect.centery
        pygame.draw.line(self.view.screen, self.view.text_color, (x, y), (x + 20, y), 3)
        pygame.draw.lines(self.view.screen, self.view.text_color, False,
                          [(x + 8, y - 8), (x, y), (x + 8, y + 8)], 3)
        label = self.view.small_font.render("Quay lại", True, self.view.text_color)
        self.view.screen.blit(label, label.get_rect(midleft=(x + 34, y)))

    # Nút dấu hỏi ở góc trên menu chính mở trang luật và cách thao tác.
    def draw_help_button(self):
        rect = self.help_button_rect
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        color = (222, 198, 155) if hovered else (234, 220, 191)
        pygame.draw.circle(self.view.screen, color, rect.center, rect.width // 2)
        pygame.draw.circle(self.view.screen, self.view.text_color, rect.center,
                           rect.width // 2, width=2)
        label = self.view.title_font.render("?", True, self.view.text_color)
        self.view.screen.blit(label, label.get_rect(center=rect.center))

    # Chia nội dung theo độ rộng thực của font để tiếng Việt không tràn cột.
    def draw_help_section(self, title, paragraphs, x, y, width):
        self.view.draw_text(title, self.view.font, self.view.player_colors[0], x, y)
        y += 46
        for paragraph in paragraphs:
            words = ("• " + paragraph).split()
            line = ""
            for word in words:
                candidate = f"{line} {word}" if line else word
                if line and self.view.small_font.size(candidate)[0] > width:
                    self.view.draw_text(line, self.view.small_font, self.view.text_color, x, y)
                    y += 26
                    line = word
                else:
                    line = candidate
            self.view.draw_text(line, self.view.small_font, self.view.text_color, x, y)
            y += 36

    # Luật và thao tác chỉ xuất hiện ở trang này, không phủ chữ lên bàn cờ.
    def draw_help(self):
        self.view.screen.fill(self.view.background_color)
        self.draw_back_button()
        title = self.view.title_font.render("HƯỚNG DẪN", True, self.view.text_color)
        self.view.screen.blit(title, title.get_rect(center=(525, 112)))
        self.draw_help_section("Luật chơi", [
            "Bàn 9×9, mỗi bên có 1 quân và 10 tường. Tới hàng đối diện trước là thắng.",
            "Mỗi lượt chọn đi quân hoặc đặt một tường.",
            "Đi 1 ô ngang hoặc dọc qua cạnh không có tường chắn.",
            "Gặp quân đối thủ ở ô liền kề: nhảy thẳng qua nếu phía sau còn ô và không bị tường chắn.",
            "Nếu không thể nhảy thẳng vì tường hoặc mép bàn, được đi chéo sang cạnh đối thủ còn đường trống.",
            "Tường dài 2 ô, đặt ngang hoặc dọc. Không được chồng, cắt nhau hoặc khóa hết đường tới đích của bất kỳ bên nào.",
        ], 60, 190, 440)
        self.draw_help_section("Cách chơi", [
            "Các ô có thể đi được đánh dấu sẵn. Click trái vào ô đích, không cần chọn quân.",
            "Đưa chuột vào khe ngang/dọc để xem trước tường, click trái để đặt. Ở giao điểm, dịch vào khe muốn chọn.",
            "Gợi ý tường hợp lệ có màu phe nhạt hơn; không hợp lệ màu đỏ. Tường đã đặt mang màu phe sở hữu.",
            "Hai người: số 1 đi trước, mỗi lượt 30 giây. Hết giờ chỉ mất lượt, không thua ngay.",
            "Đấu máy: chọn cấp và chơi trước/sau. Bạn ở dưới, số 1 đi trước; không có đồng hồ.",
            "Undo/Redo chỉ khi đấu máy, lùi/làm lại cặp lượt của bạn và bot. Nếu bạn chơi sau, giữ nước bot mở đầu.",
            "Chơi lại bắt đầu ván mới. Về menu chọn lại chế độ; nút X đóng game.",
        ], 550, 190, 440)
        pygame.display.flip()

    # Hai người vào ván ngay; chỉ đấu bot cần các trang chọn cấp và lượt.
    def draw(self, page="main"):
        if page == "help":
            self.draw_help()
            return
        self.view.screen.fill(self.view.background_color)
        titles = {"main": "BLOCADE", "levels": "ĐẤU VỚI MÁY", "order": "CHỌN LƯỢT CHƠI"}
        title = self.view.title_font.render(titles[page], True, self.view.text_color)
        self.view.screen.blit(title, title.get_rect(center=(525, 225)))
        if page == "main":
            buttons = [(self.start_button_rect, "Hai người chơi"),
                       (self.versus_bot_button_rect, "Đấu với máy")]
            self.draw_help_button()
        elif page == "levels":
            buttons = [(self.bot_button_rect, "Dễ"), (self.medium_bot_button_rect, "Trung bình"),
                       (self.hard_bot_button_rect, "Khó")]
        else:
            buttons = [(self.first_button_rect, "Chơi trước"), (self.second_button_rect, "Chơi sau")]
        if page != "main":
            self.draw_back_button()
        for rect, text in buttons:
            self.draw_button(rect, text)
        pygame.display.flip()
