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


# Menu chính chỉ chọn Hai người chơi hoặc Đấu với máy.
class MenuState(AppState):
    page = "main"

    # Chọn cách chơi trước, chưa khởi động đồng hồ hoặc bot khi còn ở menu.
    def handle_event(self, app, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return True
        menu = app.menu_view
        if menu.exit_button_rect.collidepoint(event.pos):
            return False
        if menu.start_button_rect.collidepoint(event.pos):
            app.change_state(TurnOrderState("two_players"))
        elif menu.versus_bot_button_rect.collidepoint(event.pos):
            app.change_state(BotLevelState())
        return True

    # Vẽ menu chính, không hiện các cấp bot trên trang ngoài cùng.
    def draw(self, app):
        app.menu_view.draw()


# State chọn một trong ba Strategy, chưa vào ván cho tới khi chọn thứ tự.
class BotLevelState(MenuState):
    page = "levels"

    # Chọn cấp chuyển sang chọn lượt; Quay lại về menu chính.
    def handle_event(self, app, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return True
        menu = app.menu_view
        if menu.back_button_rect.collidepoint(event.pos):
            app.change_state(MenuState())
            return True
        for rect, level in ((menu.bot_button_rect, "easy"), (menu.medium_bot_button_rect, "medium"),
                            (menu.hard_bot_button_rect, "hard")):
            if rect.collidepoint(event.pos):
                app.change_state(TurnOrderState("bot", level))
                break
        return True

    # Chỉ vẽ ba cấp Dễ/Trung bình/Khó và nút Quay lại.
    def draw(self, app):
        app.menu_view.draw(self.page)


# State lưu lựa chọn tạm trong menu; vào ván mới khởi tạo Game và lượt đầu.
class TurnOrderState(MenuState):
    page = "order"

    # Giữ cách chơi/cấp đã chọn khi người dùng chọn lượt hoặc quay lại.
    def __init__(self, mode, bot_level=None):
        self.mode = mode
        self.bot_level = bot_level

    # Bên dưới chơi trước mang số 1, chơi sau mang số 2; bot có thể mở đầu.
    def handle_event(self, app, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return True
        menu = app.menu_view
        if menu.back_button_rect.collidepoint(event.pos):
            app.change_state(BotLevelState() if self.mode == "bot" else MenuState())
            return True
        for rect, human_first in ((menu.first_button_rect, True), (menu.second_button_rect, False)):
            if rect.collidepoint(event.pos):
                app.game_controller.restart_game(mode=self.mode, bot_level=self.bot_level,
                                                  human_first=human_first)
                game = app.game_controller.game
                app.change_state(BotTurnState() if game.is_bot_turn else HumanTurnState())
                break
        return True

    # Nhắc rõ bên người chơi ở phía dưới trước khi vào ván.
    def draw(self, app):
        app.menu_view.draw(self.page, mode=self.mode)


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
