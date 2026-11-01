import pygame

from ui.states import MenuState, HumanTurnState, BotTurnState, GameOverState


# Context của State pattern: giao công việc cho trạng thái hiện tại.
class AppController:
    # Khởi đầu ở menu, dùng chung controller và cửa sổ cho mọi trạng thái.
    def __init__(self, game_controller, menu_view):
        self.game_controller = game_controller
        self.menu_view = menu_view
        self.state = MenuState()

    # Tên màn hình giữ giao diện cũ; các lượt được phân biệt bằng đối tượng State.
    @property
    def screen(self):
        return "menu" if isinstance(self.state, MenuState) else "game"

    # Cho phép chuyển màn hình rõ ràng, không đưa chuỗi trạng thái lạ vào ứng dụng.
    @screen.setter
    def screen(self, value):
        if value == "menu":
            self.change_state(MenuState())
        elif value == "game":
            self.change_state(HumanTurnState())
            self.sync_state()
        else:
            raise ValueError("Màn hình không hợp lệ")

    # Rời lượt bot hủy tác vụ cũ, để không có nước đáp trả sau Undo hoặc về menu.
    def change_state(self, state):
        if isinstance(self.state, BotTurnState) and not isinstance(state, BotTurnState):
            self.game_controller.cancel_search()
        self.state = state

    # Đồng bộ sau Command, hết giờ, Undo/Redo hoặc reset; menu chỉ đổi khi chọn chế độ.
    def sync_state(self):
        if isinstance(self.state, MenuState):
            return
        game = self.game_controller.game
        target = GameOverState if game.winner is not None else (BotTurnState if game.is_bot_turn else HumanTurnState)
        if not isinstance(self.state, target):
            self.change_state(target())

    # State quyết định có cập nhật giờ hay không.
    def update(self):
        self.sync_state()
        expired = self.state.update(self)
        self.sync_state()
        return expired

    # Nhận diện nút điều hướng để main bỏ các sự kiện cũ sau khi đổi trạng thái.
    def is_navigation_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        if self.screen == "menu":
            rects = self.menu_view.navigation_rects(self.state.page)
        else:
            view = self.game_controller.view
            game = self.game_controller.game
            rects = (view.restart_rect(game), view.menu_rect(game))
            if self.game_controller.game.mode == "bot":
                rects += (view.undo_button_rect, view.redo_button_rect)
        return any(rect.collidepoint(event.pos) for rect in
                   (*rects, self.game_controller.view.sound_button_rect))

    # Chỉ nút đang hiển thị và đang bật mới nhận phản hồi nhấn/âm click.
    def feedback_rects(self):
        controller = self.game_controller
        game, view = controller.game, controller.view
        if self.screen == "menu":
            return self.menu_view.navigation_rects(self.state.page)
        rects = [view.restart_rect(game), view.menu_rect(game)]
        if game.can_undo:
            rects.append(view.undo_button_rect)
        if game.can_redo:
            rects.append(view.redo_button_rect)
        return rects

    # Đóng cửa sổ luôn được ưu tiên, kể cả khi bot đang tìm kiếm.
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.game_controller.cancel_search()
            return False
        self.sync_state()
        view = self.game_controller.view
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if view.sound_button_rect.collidepoint(event.pos):
                view.theme.press(view.sound_button_rect)
                view.audio.toggle()
                return True
            for rect in self.feedback_rects():
                if rect.collidepoint(event.pos):
                    view.button_feedback(rect)
                    break
        running = self.state.handle_event(self, event)
        self.sync_state()
        return running

    # State chỉ cho bot chạy trong BotTurnState, không chạy ở menu hoặc sau thắng.
    def update_bot(self):
        self.sync_state()
        played = self.state.update_bot(self)
        self.sync_state()
        return played

    # Giao State hiện tại chọn menu hoặc bàn cờ để vẽ.
    def draw(self):
        self.sync_state()
        self.state.draw(self)
