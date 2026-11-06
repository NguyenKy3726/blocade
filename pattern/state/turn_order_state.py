import pygame

from pattern.state.menu_state import MenuState


# Trạng thái chọn người đi trước trong ván đấu bot.
class TurnOrderState(MenuState):
    page = "order"

    # Giữ cấp đã chọn trong lúc người dùng chọn chơi trước hoặc chơi sau.
    def __init__(self, bot_level):
        self.bot_level = bot_level

    # Người/xanh lá luôn ở dưới; chọn chơi sau thì bot mở đầu.
    def handle_event(self, app, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return True
        from pattern.state.bot_level_state import BotLevelState
        from pattern.state.bot_turn_state import BotTurnState
        from pattern.state.human_turn_state import HumanTurnState

        menu = app.menu_view
        if menu.back_button_rect.collidepoint(event.pos):
            app.change_state(BotLevelState())
            return True
        for rect, human_first in ((menu.first_button_rect, True), (menu.second_button_rect, False)):
            if rect.collidepoint(event.pos):
                app.game_controller.restart_game(mode="bot", bot_level=self.bot_level,
                                                  human_first=human_first)
                game = app.game_controller.game
                app.change_state(BotTurnState() if game.is_bot_turn else HumanTurnState())
                break
        return True

    # Vẽ trang chọn thứ tự của ván đấu máy.
    def draw(self, app):
        app.menu_view.draw(self.page)
