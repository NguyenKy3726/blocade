from abc import ABC, abstractmethod

import pygame


# State định nghĩa cách xử lý sự kiện, cập nhật và vẽ của từng trạng thái ứng dụng.
class AppState(ABC):
    # Mặc định không chạy đồng hồ, ví dụ tại menu, lượt bot và sau thắng.
    def update(self, app):
        return False

    # Mặc định không cho bot chạy; chỉ BotTurnState ghi đè phương thức này.
    def update_bot(self, app):
        return False

    # Mỗi trạng thái quyết định sự kiện nào được chuyển tới ván chơi.
    @abstractmethod
    def handle_event(self, app, event):
        pass

    # Mỗi trạng thái chọn màn hình cần vẽ.
    @abstractmethod
    def draw(self, app):
        pass


# Menu không cho bàn cờ, đồng hồ hoặc bot nhận thao tác.
class MenuState(AppState):
    # Chọn chế độ/cấp qua chuột; vào ván luôn bắt đầu trạng thái lượt người.
    def handle_event(self, app, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return True
        menu = app.menu_view
        if menu.exit_button_rect.collidepoint(event.pos):
            return False
        choices = [(menu.start_button_rect, "two_players", None),
                   (menu.bot_button_rect, "bot", "easy"),
                   (menu.medium_bot_button_rect, "bot", "medium"),
                   (menu.hard_bot_button_rect, "bot", "hard")]
        for rect, mode, level in choices:
            if rect.collidepoint(event.pos):
                app.game_controller.restart_game(mode=mode, bot_level=level)
                app.change_state(HumanTurnState())
                break
        return True

    # Vẽ menu thay vì bàn cờ.
    def draw(self, app):
        app.menu_view.draw()


# Chia sẻ thao tác điều hướng và cách vẽ giữa các trạng thái trong ván.
class PlayingState(AppState):
    # Về menu xóa lịch sử và hủy suy nghĩ; các nút khác chuyển cho controller.
    def handle_event(self, app, event):
        controller = app.game_controller
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and controller.view.menu_button_rect.collidepoint(event.pos)):
            controller.selected_position = None
            controller.game.command_history.clear()
            controller.game.redo_history.clear()
            app.change_state(MenuState())
            return True
        return controller.handle_event(event)

    # Controller ẩn xem trước trong lượt bot hoặc khi đã có người thắng.
    def draw(self, app):
        controller = app.game_controller
        preview = controller.get_wall_preview(pygame.mouse.get_pos())
        controller.view.draw(controller.game, controller.selected_position, preview)


# Người được đi quân/đặt tường; hai người có đồng hồ, đấu bot thì không.
class HumanTurnState(PlayingState):
    # Khi hết giờ, AppController chuyển sang trạng thái của lượt mới.
    def update(self, app):
        return app.game_controller.update()


# Chỉ trạng thái này tiến hành tìm kiếm và thực thi nước bot.
class BotTurnState(PlayingState):
    # Tính tiếp một đoạn rồi trả UI; Command cuối mới thay đổi ván thật.
    def update_bot(self, app):
        return app.game_controller.play_bot_turn()


# Ván kết thúc: không tính giờ/đánh tiếp, vẫn dùng được Undo/Redo và điều hướng.
class GameOverState(PlayingState):
    pass
