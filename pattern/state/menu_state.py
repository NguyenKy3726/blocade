import pygame

from pattern.state.app_state import AppState


# Trạng thái menu chính; điều phối các lựa chọn vào game hoặc trang phụ.
class MenuState(AppState):
    page = "main"

    # Hai người vào ván ngay; đấu máy chọn cấp/lượt, dấu hỏi mở hướng dẫn.
    def handle_event(self, app, event):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return True
        from pattern.state.bot_level_state import BotLevelState
        from pattern.state.help_state import HelpState
        from pattern.state.human_turn_state import HumanTurnState

        menu = app.menu_view
        if menu.start_button_rect.collidepoint(event.pos):
            app.game_controller.restart_game(mode="two_players", human_first=True)
            app.change_state(HumanTurnState())
        elif menu.versus_bot_button_rect.collidepoint(event.pos):
            app.change_state(BotLevelState())
        elif menu.help_button_rect.collidepoint(event.pos):
            app.change_state(HelpState())
        return True

    # Vẽ menu chính, không hiện các cấp bot trên trang ngoài cùng.
    def draw(self, app):
        app.menu_view.draw()
