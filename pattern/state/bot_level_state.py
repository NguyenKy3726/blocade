import pygame

from pattern.state.menu_state import MenuState


# Trạng thái chọn cấp độ bot trước khi chọn thứ tự lượt.
class BotLevelState(MenuState):
    page = "levels"

    # Chọn cấp chuyển sang chọn lượt; Quay lại về menu chính.
    def handle_event(self, app, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return True
        from pattern.state.turn_order_state import TurnOrderState

        menu = app.menu_view
        if menu.back_button_rect.collidepoint(event.pos):
            app.change_state(MenuState())
            return True
        for rect, level in ((menu.bot_button_rect, "easy"), (menu.medium_bot_button_rect, "medium"),
                            (menu.hard_bot_button_rect, "hard")):
            if rect.collidepoint(event.pos):
                app.change_state(TurnOrderState(level))
                break
        return True

    # Chỉ vẽ ba cấp Dễ/Trung bình/Khó và nút Quay lại.
    def draw(self, app):
        app.menu_view.draw(self.page)
