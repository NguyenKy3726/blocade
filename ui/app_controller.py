import pygame


# Điều hướng giữa menu và ván; chưa cần các lớp State riêng cho hai màn hình.
class AppController:
    # Khởi đầu ở menu, giữ lại controller ván để tái sử dụng cùng cửa sổ.
    def __init__(self, game_controller, menu_view):
        self.game_controller = game_controller
        self.menu_view = menu_view
        self.screen = "menu"

    # Chỉ tính giờ khi đang ở bàn cờ; ở menu không để người chơi mất lượt.
    def update(self):
        if self.screen == "game":
            return self.game_controller.update()
        return False

    # Nhận diện nút đổi màn hình/chơi lại để bỏ các click cũ sau điều hướng.
    def is_navigation_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        if self.screen == "menu":
            rects = (self.menu_view.start_button_rect, self.menu_view.bot_button_rect,
                     self.menu_view.medium_bot_button_rect,
                     self.menu_view.exit_button_rect)
        else:
            view = self.game_controller.view
            rects = (view.restart_button_rect, view.menu_button_rect)
            if self.game_controller.game.mode == "bot":
                rects += (view.undo_button_rect, view.redo_button_rect)
        return any(rect.collidepoint(event.pos) for rect in rects)

    # Ưu tiên đóng cửa sổ và nút điều hướng trước khi giao sự kiện cho ván.
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False
        left_click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
        if self.screen == "menu":
            if left_click and self.menu_view.exit_button_rect.collidepoint(event.pos):
                return False
            if left_click and self.menu_view.start_button_rect.collidepoint(event.pos):
                self.game_controller.restart_game(mode="two_players")
                self.screen = "game"
            elif left_click and self.menu_view.bot_button_rect.collidepoint(event.pos):
                self.game_controller.restart_game(mode="bot", bot_level="easy")
                self.screen = "game"
            elif left_click and self.menu_view.medium_bot_button_rect.collidepoint(event.pos):
                self.game_controller.restart_game(mode="bot", bot_level="medium")
                self.screen = "game"
            return True
        if left_click and self.game_controller.view.menu_button_rect.collidepoint(event.pos):
            self.game_controller.selected_position = None
            self.game_controller.game.command_history.clear()
            self.game_controller.game.redo_history.clear()
            self.screen = "menu"
            return True
        return self.game_controller.handle_event(event)

    # Bot không chạy ở menu; nút Về menu/Chơi lại được xử lý trước nước đáp trả.
    def update_bot(self):
        if self.screen == "game":
            return self.game_controller.play_bot_turn()
        return False

    # Vẽ đúng màn hình; xem trước tường chỉ được tính khi đang trong ván.
    def draw(self):
        if self.screen == "menu":
            self.menu_view.draw()
            return
        controller = self.game_controller
        preview = controller.get_wall_preview(pygame.mouse.get_pos())
        controller.view.draw(controller.game, controller.selected_position, preview)
