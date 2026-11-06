from time import perf_counter

import pygame

from pattern.command import CommandInvoker, MoveCommand, PlaceWallCommand
from pattern.strategy import BotStrategyFactory


# Chuyển click chuột thành Command đi quân hoặc đặt tường.
class GameController:
    # Kết nối game với giao diện và khởi tạo trạng thái thao tác.
    def __init__(self, game, view):
        self.game = game
        self.view = view
        self.command_invoker = CommandInvoker()
        self.selected_position = None
        self.bot_strategy = BotStrategyFactory.create(game.bot_level)
        self.pending_search = None
        self.search_board = None

    # Hủy generator cũ trước khi Undo/Redo, reset hoặc rời ván; chỉ bỏ bản sao tìm kiếm.
    def cancel_search(self):
        if self.pending_search is not None:
            self.pending_search.close()
        self.pending_search = None
        self.search_board = None

    # Nhận diện click trái trong nút Chơi lại, tách khỏi thao tác bàn cờ.
    def is_restart_event(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.view.restart_rect(self.game).collidepoint(event.pos)
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
    def restart_game(self, mode=None, bot_level=None, human_first=None):
        self.cancel_search()
        previous_level = self.game.bot_level
        self.game.reset(mode=mode, bot_level=bot_level, human_first=human_first)
        if self.game.bot_level != previous_level:
            self.bot_strategy = BotStrategyFactory.create(self.game.bot_level)
        self.selected_position = None
        self.view.reset_effects(self.game)

    # Cập nhật đồng hồ và bỏ lựa chọn cũ khi người chơi bị mất lượt.
    def update(self):
        expired = self.game.update_time()
        if expired:
            self.selected_position = None
            self.view.audio.play("timeout")
        return expired

    # Chỉ sau Command thành công mới phát âm và tạo hình chuyển động.
    def execute_command(self, command):
        if command is None:
            return False
        before = self.game.capture_state()
        if not self.command_invoker.execute(command):
            return False
        self.view.present_action(self.game, before)
        return True

    # Bot khó dùng khoảng 8ms mỗi khung hình; các cấp khác giữ cách chạy trực tiếp.
    def play_bot_turn(self):
        if not self.game.is_bot_turn:
            self.cancel_search()
            return False
        if self.pending_search is not None and self.search_board is not self.game.board:
            self.cancel_search()
        if self.pending_search is None:
            self.pending_search = self.bot_strategy.start_search(self.game)
            self.search_board = self.game.board
            if self.pending_search is None:
                command = self.bot_strategy.choose_command(self.game)
                return self.execute_command(command)
        started = perf_counter()
        while True:
            try:
                command = next(self.pending_search)
            except StopIteration:
                self.cancel_search()
                return False
            if command is not None:
                self.cancel_search()
                return self.execute_command(command)
            if perf_counter() - started >= 0.008:
                return False

    # Xử lý đóng cửa sổ, chơi lại và các hành động bằng chuột.
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.cancel_search()
            return False

        # Nút vẫn dùng được sau thắng ván hoặc tại đúng mốc hết giờ.
        if self.is_restart_event(event):
            self.restart_game()
            return True

        if self.is_undo_event(event):
            self.cancel_search()
            before = self.game.capture_state()
            if self.game.undo_round():
                self.view.present_action(self.game, before, "undo")
            self.selected_position = None
            return True

        if self.is_redo_event(event):
            self.cancel_search()
            before = self.game.capture_state()
            if self.game.redo_round():
                self.view.present_action(self.game, before, "redo")
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
            self.execute_command(command)
        self.selected_position = None

    # Xác nhận đặt tường bằng chuột; chỉ thành công mới chuyển lượt.
    def _handle_wall_click(self, mouse_position):
        if self.game.winner is not None:
            return
        wall = self.view.wall_at_position(mouse_position)
        if wall is None:
            return
        command = PlaceWallCommand(self.game, *wall)
        self.execute_command(command)
        self.selected_position = None

    # Xem trước cả hai hướng bằng chuột, không làm thay đổi trạng thái ván.
    def get_wall_preview(self, mouse_position):
        if self.game.winner is not None or self.game.is_bot_turn:
            return None
        wall = self.view.wall_at_position(mouse_position)
        if wall is None:
            return None
        if not self.game.can_place_wall_current_player(*wall):
            return None
        return (*wall, True)
