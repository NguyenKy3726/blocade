import pygame

from pattern.state.app_state import AppState
from pattern.state.menu_state import MenuState


# Lớp cha chia sẻ điều hướng và cách vẽ giữa các trạng thái đang chơi.
class PlayingState(AppState):
    # Về menu xóa lịch sử và hủy suy nghĩ; các nút khác chuyển cho controller.
    def handle_event(self, app, event):
        controller = app.game_controller
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and controller.view.menu_rect(controller.game).collidepoint(event.pos)):
            controller.selected_position = None
            controller.game.command_history.clear()
            controller.game.redo_history.clear()
            controller.view.reset_effects(controller.game)
            app.change_state(MenuState())
            return True
        return controller.handle_event(event)

    # Controller ẩn xem trước trong lượt bot hoặc khi đã có người thắng.
    def draw(self, app):
        controller = app.game_controller
        preview = controller.get_wall_preview(pygame.mouse.get_pos())
        controller.view.draw(controller.game, controller.selected_position, preview)
