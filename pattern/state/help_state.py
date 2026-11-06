import pygame

from pattern.state.menu_state import MenuState


# Trạng thái hiển thị hướng dẫn; kế thừa cách trình bày menu.
class HelpState(MenuState):
    page = "help"

    # Chỉ nút quay lại nhận click; đọc hướng dẫn không thay đổi dữ liệu ván.
    def handle_event(self, app, event):
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and app.menu_view.back_button_rect.collidepoint(event.pos)):
            app.change_state(MenuState())
        return True

    # MenuView dùng font đi kèm để vẽ luật và hướng dẫn tiếng Việt.
    def draw(self, app):
        app.menu_view.draw(self.page)
