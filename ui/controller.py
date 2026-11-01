import pygame

from game.commands import MoveCommand, PlaceWallCommand
from game.bot.easy import EasyStrategy


# Chuyển click chuột thành Command đi quân hoặc đặt tường.
class GameController:
    # Kết nối game với giao diện và khởi tạo trạng thái thao tác.
    def __init__(self, game, view):
        self.game = game
        self.view = view
        self.selected_position = None
        self.bot_strategy = EasyStrategy()

    # Nhận diện click trái trong nút Chơi lại, tách khỏi thao tác bàn cờ.
    def is_restart_event(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.view.restart_button_rect.collidepoint(event.pos)
        )

    # Undo nhận trước khi chặn click lượt bot hoặc ván kết thúc.
    def is_undo_event(self, event):
        return (
            self.game.mode == "bot"
            and event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.view.undo_button_rect.collidepoint(event.pos)
        )

    # Redo được nhận cả sau thắng và trước khi kiểm tra lượt bot.
    def is_redo_event(self, event):
        return (
            self.game.mode == "bot"
            and event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.view.redo_button_rect.collidepoint(event.pos)
        )

    # Chơi lại trên cùng cửa sổ và bỏ trạng thái thao tác của ván cũ.
    def restart_game(self, mode=None):
        self.game.reset(mode=mode)
        self.selected_position = None

    # Cập nhật đồng hồ và bỏ lựa chọn cũ khi người chơi bị mất lượt.
    def update(self):
        expired = self.game.update_time()
        if expired:
            self.selected_position = None
        return expired

    # Thực hiện tối đa một nước bot sau khi xử lý các sự kiện của khung hình.
    def play_bot_turn(self):
        if not self.game.is_bot_turn:
            return False
        command = self.bot_strategy.choose_command(self.game)
        return command.execute() if command is not None else False

    # Xử lý đóng cửa sổ, chơi lại và các hành động bằng chuột.
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False

        # Nút vẫn dùng được sau thắng ván hoặc tại đúng mốc hết giờ.
        if self.is_restart_event(event):
            self.restart_game()
            return True

        if self.is_undo_event(event):
            self.game.undo_round()
            self.selected_position = None
            return True

        if self.is_redo_event(event):
            self.game.redo_round()
            self.selected_position = None
            return True

        if self.update() or self.game.is_bot_turn:
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.view.wall_at_position(event.pos) is not None:
                self._handle_wall_click(event.pos)
            else:
                self._handle_move_click(event.pos)

        return True

    # Click thẳng vào ô hợp lệ để đi, không cần click chọn quân trước.
    def _handle_move_click(self, mouse_position):
        if self.game.winner is not None:
            return

        clicked_cell = self.view.cell_at_position(mouse_position)
        if clicked_cell is not None:
            command = MoveCommand(self.game, clicked_cell)
            command.execute()
        self.selected_position = None

    # Xác nhận đặt tường bằng chuột; chỉ thành công mới chuyển lượt.
    def _handle_wall_click(self, mouse_position):
        if self.game.winner is not None:
            return
        wall = self.view.wall_at_position(mouse_position)
        if wall is None:
            return
        command = PlaceWallCommand(self.game, *wall)
        command.execute()
        self.selected_position = None

    # Xem trước cả hai hướng bằng chuột, không làm thay đổi trạng thái ván.
    def get_wall_preview(self, mouse_position):
        if self.game.winner is not None or self.game.is_bot_turn:
            return None
        wall = self.view.wall_at_position(mouse_position)
        if wall is None:
            return None
        return (*wall, self.game.can_place_wall_current_player(*wall))
