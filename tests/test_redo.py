import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from game.commands import MoveCommand, PlaceWallCommand
from game.game import Game
from ui.app_controller import AppController
from ui.controller import GameController
from ui.game_view import GameView
from ui.menu_view import MenuView


# Kiểm tra Redo dùng lại đúng Command và snapshot, không thực thi hành động mới.
class RedoTests(unittest.TestCase):
    # Mỗi test bắt đầu ở ván bot mới không đồng hồ.
    def setUp(self):
        self.game = Game(mode="bot")

    # Redo không tồn tại trước Undo; giữ nguyên ván khi bấm lúc chưa có lịch sử.
    def test_redo_requires_undo(self):
        command = MoveCommand(self.game, (1, 4))
        self.assertFalse(command.redo())
        self.assertFalse(self.game.redo_round())
        self.assertTrue(command.execute())
        before = self.game.capture_state()
        self.assertFalse(command.redo())
        self.assertEqual(self.game.capture_state(), before)

    # Một Command có thể undo/redo nhiều lần, nhưng execute không được dùng như redo.
    def test_command_redo_repeats_without_performing(self):
        initial = self.game.capture_state()
        command = MoveCommand(self.game, (1, 4))
        self.assertTrue(command.execute())
        after = self.game.capture_state()
        for _ in range(3):
            self.assertTrue(command.undo())
            self.assertEqual(self.game.capture_state(), initial)
            self.assertFalse(command.execute())
            with patch.object(command, "_perform", side_effect=AssertionError("Không đánh lại")):
                self.assertTrue(command.redo())
            self.assertEqual(self.game.capture_state(), after)
            self.assertEqual(self.game.command_history, [command])
            self.assertEqual(self.game.redo_history, [])
            self.assertFalse(command.redo())

    # Redo theo thứ tự người rồi bot; không được làm lại bot trước nước người.
    def test_command_redo_order(self):
        human = MoveCommand(self.game, (1, 4))
        bot = MoveCommand(self.game, (7, 4))
        self.assertTrue(human.execute())
        self.assertTrue(bot.execute())
        after = self.game.capture_state()
        self.assertTrue(self.game.undo_round())
        self.assertFalse(bot.redo())
        self.assertTrue(human.redo())
        self.assertTrue(bot.redo())
        self.assertEqual(self.game.capture_state(), after)
        self.assertEqual(self.game.command_history, [human, bot])

    # Khôi phục cặp lệnh đặt tường cả hai phe: cạnh chặn, màu và số tường giống hệt.
    def test_redo_restores_walls_and_owners(self):
        human = PlaceWallCommand(self.game, "horizontal", 2, 2)
        bot = PlaceWallCommand(self.game, "vertical", 5, 5)
        self.assertTrue(human.execute())
        self.assertTrue(bot.execute())
        after = self.game.capture_state()
        self.assertTrue(self.game.undo_round())
        with patch.object(human, "redo", wraps=human.redo) as redo_human, \
                patch.object(bot, "redo", wraps=bot.redo) as redo_bot:
            self.assertTrue(self.game.redo_round())
            redo_human.assert_called_once()
            redo_bot.assert_called_once()
        self.assertEqual(self.game.capture_state(), after)
        self.assertEqual(len(self.game.board.blocked_edges), 4)
        self.assertEqual([p.walls_remaining for p in self.game.players], [9, 9])

    # Undo nhiều vòng rồi Redo từng vòng theo thứ tự thời gian, không nhảy mất lượt.
    def test_multiple_rounds_and_mixed_undo_redo(self):
        self.assertTrue(MoveCommand(self.game, (1, 4)).execute())
        self.assertTrue(MoveCommand(self.game, (7, 4)).execute())
        first = self.game.capture_state()
        self.assertTrue(PlaceWallCommand(self.game, "vertical", 3, 3).execute())
        self.assertTrue(MoveCommand(self.game, (6, 4)).execute())
        second = self.game.capture_state()
        self.assertTrue(self.game.undo_round())
        self.assertTrue(self.game.undo_round())
        self.assertEqual(len(self.game.redo_history), 4)
        self.assertTrue(self.game.redo_round())
        self.assertEqual(self.game.capture_state(), first)
        self.assertEqual(len(self.game.redo_history), 2)
        self.assertTrue(self.game.undo_round())
        self.assertTrue(self.game.redo_round())
        self.assertEqual(self.game.capture_state(), first)
        self.assertTrue(self.game.redo_round())
        self.assertEqual(self.game.capture_state(), second)
        self.assertFalse(self.game.redo_round())

    # Chỉ hành động mới thành công mới xóa Redo; lỗi nước đi/tường và preview giữ nhánh.
    def test_branching_and_failed_actions(self):
        self.assertTrue(MoveCommand(self.game, (1, 4)).execute())
        self.assertTrue(MoveCommand(self.game, (7, 4)).execute())
        old_commands = self.game.command_history.copy()
        self.assertTrue(self.game.undo_round())
        redo = self.game.redo_history.copy()
        self.assertFalse(MoveCommand(self.game, (5, 5)).execute())
        self.assertFalse(PlaceWallCommand(self.game, "vertical", 8, 8).execute())
        self.assertTrue(self.game.can_place_wall_current_player("horizontal", 3, 3))
        self.assertEqual(self.game.redo_history, redo)
        self.assertTrue(PlaceWallCommand(self.game, "horizontal", 3, 3).execute())
        self.assertEqual(self.game.redo_history, [])
        self.assertFalse(self.game.can_redo)
        for command in old_commands:
            self.assertFalse(command.redo())

    # Tường bị BFS từ chối không mất nhánh Redo.
    def test_bfs_rejection_preserves_redo(self):
        self.game.players[0].row, self.game.players[0].col = 0, 0
        self.assertTrue(self.game.board.place_wall("horizontal", 0, 0))
        self.assertTrue(PlaceWallCommand(self.game, "vertical", 4, 4).execute())
        self.assertTrue(MoveCommand(self.game, (7, 4)).execute())
        after = self.game.capture_state()
        self.assertTrue(self.game.undo_round())
        self.assertFalse(PlaceWallCommand(self.game, "vertical", 0, 1).execute())
        self.assertTrue(self.game.redo_round())
        self.assertEqual(self.game.capture_state(), after)

    # Redo chính xác nước nhảy thẳng hoặc chéo và nước bot đã đáp trả.
    def test_redo_jump_round(self):
        for diagonal in (False, True):
            with self.subTest(diagonal=diagonal):
                self.game.reset()
                self.game.players[0].row, self.game.players[0].col = 4, 4
                self.game.players[1].row, self.game.players[1].col = 5, 4
                if diagonal:
                    self.assertTrue(self.game.board.place_wall("horizontal", 5, 4))
                self.assertTrue(MoveCommand(self.game, (5, 3) if diagonal else (6, 4)).execute())
                self.assertTrue(MoveCommand(self.game, (4, 4)).execute())
                after = self.game.capture_state()
                self.assertTrue(self.game.undo_round())
                self.assertTrue(self.game.redo_round())
                self.assertEqual(self.game.capture_state(), after)

    # Redo tái lập kết quả thắng của người hoặc bot rồi vẫn có thể Undo lại.
    def test_redo_after_wins(self):
        for winner in (0, 1):
            with self.subTest(winner=winner):
                self.game.reset()
                if winner == 0:
                    self.game.players[0].row = 7
                    self.game.players[1].col = 0
                    self.assertTrue(MoveCommand(self.game, (8, 4)).execute())
                else:
                    self.game.players[0].col = 0
                    self.game.players[1].row = 1
                    self.assertTrue(PlaceWallCommand(self.game, "horizontal", 5, 5).execute())
                    self.assertTrue(MoveCommand(self.game, (0, 4)).execute())
                after = self.game.capture_state()
                self.assertTrue(self.game.undo_round())
                self.assertTrue(self.game.redo_round())
                self.assertEqual(self.game.capture_state(), after)
                self.assertIs(self.game.winner, self.game.players[winner])
                self.assertTrue(self.game.undo_round())

    # Reset xóa cả hai ngăn; lệnh cũ không được Redo xuyên qua ván mới hoặc đổi chế độ.
    def test_reset_and_two_player_mode(self):
        command = MoveCommand(self.game, (1, 4))
        self.assertTrue(command.execute())
        self.assertTrue(self.game.undo_round())
        self.game.reset()
        self.assertEqual(self.game.redo_history, [])
        self.assertFalse(command.redo())
        self.game.reset(mode="two_players")
        self.assertFalse(self.game.can_redo)
        self.assertFalse(self.game.redo_round())

    # Tránh đè snapshot lên bàn nếu có thay đổi trực tiếp ngoài luồng Command.
    def test_redo_rejects_different_current_state(self):
        command = MoveCommand(self.game, (1, 4))
        self.assertTrue(command.execute())
        self.assertTrue(command.undo())
        self.game.players[0].col = 3
        before = self.game.capture_state()
        self.assertFalse(command.redo())
        self.assertEqual(self.game.capture_state(), before)


# Kiểm tra Redo theo luồng menu, chuột, bot và vòng lặp chính.
class RedoFlowTests(unittest.TestCase):
    # Tạo cửa sổ thật headless và vào chế độ bot qua menu.
    def setUp(self):
        self.game = Game()
        self.view = GameView()
        self.controller = GameController(self.game, self.view)
        self.menu = MenuView(self.view)
        self.app = AppController(self.controller, self.menu)
        self.click(self.menu.bot_button_rect.center)

    # Đóng các tài nguyên Pygame sau mỗi phép kiểm tra.
    def tearDown(self):
        pygame.quit()

    # Gửi click qua lớp điều hướng.
    def click(self, position):
        return self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=position))

    # Cho người đi nước đầu để tạo lịch sử cho bot đáp trả.
    def first_move(self):
        self.click((self.view.board_x + 4 * 66 + 29, self.view.board_y + 66 + 29))

    # Nút Redo bật sau Undo; làm lại đúng bot cũ, không gọi chọn nước ngẫu nhiên lần nữa.
    def test_redo_button_does_not_reselect_bot(self):
        with patch.object(self.view, "draw_redo_button", wraps=self.view.draw_redo_button) as draw:
            self.app.draw()
            draw.assert_called_once_with(False)
        self.first_move()
        self.app.update_bot()
        after = self.game.capture_state()
        human, bot = self.game.command_history
        self.click(self.view.undo_button_rect.center)
        with patch.object(self.view, "draw_redo_button", wraps=self.view.draw_redo_button) as draw:
            self.app.draw()
            draw.assert_called_once_with(True)
        with patch.object(human, "redo", wraps=human.redo) as redo_human, \
                patch.object(bot, "redo", wraps=bot.redo) as redo_bot, \
                patch.object(self.controller.bot_strategy, "choose_command") as choose:
            self.click(self.view.redo_button_rect.center)
            self.assertFalse(self.app.update_bot())
            redo_human.assert_called_once()
            redo_bot.assert_called_once()
            choose.assert_not_called()
        self.assertEqual(self.game.capture_state(), after)

    # Nếu lệnh Undo chưa có bot đáp trả, Redo trả tới lượt bot để bot đi lần đầu.
    def test_redo_pending_human_move(self):
        self.first_move()
        after_human = self.game.capture_state()
        self.click(self.view.undo_button_rect.center)
        self.click(self.view.redo_button_rect.center)
        self.assertEqual(self.game.capture_state(), after_human)
        self.assertTrue(self.app.update_bot())
        self.assertFalse(self.app.update_bot())
        self.assertEqual(self.game.current_turn, 0)
        self.assertEqual(len(self.game.command_history), 2)

    # Menu/reset xóa Redo; hai người không vẽ nút và không cho làm lại.
    def test_redo_cleared_by_restart_menu_and_mode(self):
        for target in ("restart", "menu"):
            self.first_move()
            self.app.update_bot()
            self.click(self.view.undo_button_rect.center)
            self.assertTrue(self.game.can_redo)
            if target == "restart":
                self.click(self.view.restart_button_rect.center)
            else:
                self.click(self.view.menu_button_rect.center)
                self.assertEqual(self.game.redo_history, [])
                self.click(self.menu.start_button_rect.center)
            self.assertEqual(self.game.redo_history, [])
            self.assertFalse(self.game.can_redo)
        with patch.object(self.view, "draw_redo_button") as draw:
            self.app.draw()
            draw.assert_not_called()
        self.assertFalse(self.game.redo_round())

    # Main bỏ click dư sau Redo; không gọi bot lần hai cho cặp đã khôi phục.
    def test_main_discards_click_after_redo(self):
        start = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                   pos=self.menu.bot_button_rect.center)
        human = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                   pos=(self.view.board_x + 4 * 66 + 29, self.view.board_y + 66 + 29))
        undo = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                  pos=self.view.undo_button_rect.center)
        redo = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                  pos=self.view.redo_button_rect.center)
        extra = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                   pos=(self.view.board_x + 4 * 66 + 29, self.view.board_y + 2 * 66 + 29))
        main_path = Path(__file__).resolve().parents[1] / "main.py"
        with patch("game.game.Game", return_value=self.game), \
                patch("ui.game_view.GameView", return_value=self.view), \
                patch("ui.controller.GameController", return_value=self.controller), \
                patch("pygame.event.get", side_effect=[[start], [human], [undo], [redo, extra],
                                                       [pygame.event.Event(pygame.QUIT)]]), \
                patch.object(self.controller.bot_strategy, "choose_command",
                             wraps=self.controller.bot_strategy.choose_command) as choose:
            runpy.run_path(str(main_path), run_name="__main__")
        choose.assert_called_once_with(self.game)
        self.assertEqual([p.position for p in self.game.players], [(1, 4), (7, 4)])
        self.assertEqual(len(self.game.command_history), 2)
        self.assertEqual(self.game.redo_history, [])


if __name__ == "__main__":
    unittest.main()
