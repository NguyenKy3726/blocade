import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from pattern.command import MoveCommand, PlaceWallCommand
from game.game import Game
from tests.support import start_game, menu_frames
from pattern.state import AppController
from ui.controller import GameController
from ui.game_view import GameView
from ui.menu_view import MenuView


# Kiểm tra từng Command hoàn tác và lịch sử ghép lượt đúng quy tắc đấu bot.
class UndoTests(unittest.TestCase):
    # Tạo ván bot không có đồng hồ cho mỗi tình huống.
    def setUp(self):
        self.game = Game(mode="bot")

    # Một Command chỉ execute một lần và undo một lần; tạo lệnh chưa đổi ván.
    def test_move_command_undo_lifecycle(self):
        before = self.game.capture_state()
        command = MoveCommand(self.game, (1, 4))
        self.assertFalse(command.undo())
        self.assertTrue(command.execute())
        after = self.game.capture_state()
        self.assertFalse(command.execute())
        self.assertEqual(self.game.capture_state(), after)
        self.assertEqual(self.game.command_history, [command])
        self.assertTrue(command.undo())
        self.assertEqual(self.game.capture_state(), before)
        self.assertEqual(self.game.command_history, [])
        self.assertFalse(command.undo())
        self.assertFalse(command.execute())

    # Undo tường khôi phục cả cạnh bị chặn, màu sở hữu và số tường cho cả hai phe.
    def test_wall_commands_undo_both_owners(self):
        before = self.game.capture_state()
        human = PlaceWallCommand(self.game, "horizontal", 2, 2)
        bot = PlaceWallCommand(self.game, "vertical", 5, 5)
        self.assertTrue(human.execute())
        self.assertTrue(bot.execute())
        self.assertEqual(len(self.game.board.blocked_edges), 4)
        self.assertEqual([p.walls_remaining for p in self.game.players], [9, 9])
        self.assertTrue(self.game.undo_round())
        self.assertEqual(self.game.capture_state(), before)
        self.assertEqual(self.game.board.blocked_edges, set())
        self.assertEqual(self.game.wall_owners, {})
        self.assertEqual([p.walls_remaining for p in self.game.players], [10, 10])

    # Không cho undo một lệnh cũ khi vẫn còn lệnh mới phía trên lịch sử.
    def test_commands_require_reverse_order(self):
        first = MoveCommand(self.game, (1, 4))
        second = MoveCommand(self.game, (7, 4))
        self.assertTrue(first.execute())
        middle = self.game.capture_state()
        self.assertTrue(second.execute())
        after = self.game.capture_state()
        self.assertFalse(first.undo())
        self.assertEqual(self.game.capture_state(), after)
        self.assertTrue(second.undo())
        self.assertEqual(self.game.capture_state(), middle)
        self.assertTrue(first.undo())

    # Khi bot chưa đi chỉ lùi nước người; bot không còn lượt để đáp trả sau Undo.
    def test_undo_before_bot_response(self):
        before = self.game.capture_state()
        self.assertTrue(MoveCommand(self.game, (1, 4)).execute())
        self.assertTrue(self.game.is_bot_turn)
        self.assertTrue(self.game.undo_round())
        self.assertEqual(self.game.capture_state(), before)
        self.assertFalse(self.game.is_bot_turn)

    # Lùi cả nước nhảy thẳng/chéo và đáp trả, giữ nguyên tường đã có trước đó.
    def test_undo_jump_round(self):
        for diagonal in (False, True):
            with self.subTest(diagonal=diagonal):
                self.game.reset()
                self.game.players[0].row, self.game.players[0].col = 4, 4
                self.game.players[1].row, self.game.players[1].col = 5, 4
                if diagonal:
                    self.assertTrue(self.game.board.place_wall("horizontal", 5, 4))
                before = self.game.capture_state()
                destination = (5, 3) if diagonal else (6, 4)
                self.assertTrue(MoveCommand(self.game, destination).execute())
                self.assertTrue(MoveCommand(self.game, (4, 4)).execute())
                self.assertTrue(self.game.undo_round())
                self.assertEqual(self.game.capture_state(), before)

    # Mỗi lần Undo lùi đúng một cặp lượt, không lùi mất các vòng trước.
    def test_repeated_round_undo(self):
        initial = self.game.capture_state()
        self.assertTrue(MoveCommand(self.game, (1, 4)).execute())
        self.assertTrue(MoveCommand(self.game, (7, 4)).execute())
        first_round = self.game.capture_state()
        self.assertTrue(PlaceWallCommand(self.game, "vertical", 3, 3).execute())
        self.assertTrue(MoveCommand(self.game, (6, 4)).execute())
        self.assertTrue(self.game.undo_round())
        self.assertEqual(self.game.capture_state(), first_round)
        self.assertEqual(len(self.game.command_history), 2)
        self.assertTrue(self.game.undo_round())
        self.assertEqual(self.game.capture_state(), initial)
        self.assertFalse(self.game.can_undo)
        self.assertFalse(self.game.undo_round())

    # Nước sai, tường chồng/cắt và xem trước không chiếm chỗ trong lịch sử.
    def test_failures_and_preview_do_not_enter_history(self):
        self.assertFalse(MoveCommand(self.game, (5, 5)).execute())
        self.assertFalse(self.game.can_undo)
        self.assertTrue(PlaceWallCommand(self.game, "horizontal", 2, 2).execute())
        history = self.game.command_history.copy()
        for wall in [("horizontal", 2, 2), ("horizontal", 2, 3), ("vertical", 2, 2)]:
            command = PlaceWallCommand(self.game, *wall)
            self.assertFalse(command.execute())
            self.assertFalse(command.undo())
        self.game.can_place_wall_current_player("horizontal", 5, 5)
        self.assertEqual(self.game.command_history, history)
        self.assertTrue(self.game.undo_round())
        self.assertEqual(self.game.board.walls, [])

    # Tường bị BFS từ chối không tạo snapshot có thể hoàn tác.
    def test_bfs_rejection_does_not_enter_history(self):
        self.game.players[0].row, self.game.players[0].col = 0, 0
        self.assertTrue(self.game.board.place_wall("horizontal", 0, 0))
        before = self.game.capture_state()
        command = PlaceWallCommand(self.game, "vertical", 0, 1)
        self.assertFalse(command.execute())
        self.assertFalse(command.undo())
        self.assertEqual(self.game.capture_state(), before)
        self.assertEqual(self.game.command_history, [])

    # Undo được sau thắng của người hoặc bot, khôi phục kết quả và lượt người.
    def test_undo_after_either_player_wins(self):
        for winner in (0, 1):
            with self.subTest(winner=winner):
                self.game.reset()
                if winner == 0:
                    self.game.players[0].row = 7
                    self.game.players[1].col = 0
                    before = self.game.capture_state()
                    self.assertTrue(MoveCommand(self.game, (8, 4)).execute())
                else:
                    self.game.players[0].col = 0
                    self.game.players[1].row = 1
                    before = self.game.capture_state()
                    self.assertTrue(PlaceWallCommand(self.game, "horizontal", 5, 5).execute())
                    self.assertTrue(MoveCommand(self.game, (0, 4)).execute())
                self.assertIs(self.game.winner, self.game.players[winner])
                self.assertTrue(self.game.undo_round())
                self.assertEqual(self.game.capture_state(), before)
                self.assertIsNone(self.game.winner)
                self.assertEqual(self.game.current_turn, 0)
                self.assertTrue(self.game.get_legal_moves())

    # Lệnh của ván cũ không được execute/undo trên ván mới sau reset.
    def test_reset_invalidates_old_commands(self):
        pending = MoveCommand(self.game, (0, 3))
        executed = MoveCommand(self.game, (1, 4))
        self.assertTrue(executed.execute())
        self.game.reset()
        before = self.game.capture_state()
        self.assertFalse(self.game.can_undo)
        self.assertFalse(pending.execute())
        self.assertFalse(executed.undo())
        self.assertEqual(self.game.capture_state(), before)

    # Hai người không có Undo và không lưu lịch sử, đồng hồ vẫn chạy bình thường.
    def test_two_player_mode_keeps_timer_without_undo(self):
        now = [100.0]
        game = Game(time_source=lambda: now[0])
        command = MoveCommand(game, (1, 4))
        self.assertTrue(command.execute())
        self.assertEqual(game.command_history, [])
        self.assertFalse(command.undo())
        self.assertFalse(game.undo_round())
        now[0] += 5
        game.update_time()
        self.assertEqual(game.time_remaining, [30, 25])


# Kiểm tra nút Undo và điều phối bot/chuột qua giao diện thật.
class UndoFlowTests(unittest.TestCase):
    # Mở chế độ bot qua menu như người dùng thật.
    def setUp(self):
        self.game = Game()
        self.view = GameView()
        self.controller = GameController(self.game, self.view)
        self.menu = MenuView(self.view)
        self.app = AppController(self.controller, self.menu)
        start_game(self.app, self.menu, mode="bot", level="easy")

    # Giải phóng cửa sổ sau mỗi test.
    def tearDown(self):
        pygame.quit()

    # Gửi click qua lớp điều hướng.
    def click(self, position):
        return self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=position))

    # Ô đích đầu tiên của người chơi xanh lá.
    def first_move(self):
        self.click(self.view.model_to_screen_point((self.view.board_x + 4 * 66 + 29, self.view.board_y + 66 + 29)))

    # Nút ban đầu bị mờ; sau một vòng, bấm nút phải gọi undo của cả hai Command.
    def test_button_uses_command_undo_and_updates_hints(self):
        with patch.object(self.view, "draw_undo_button", wraps=self.view.draw_undo_button) as draw:
            self.app.draw()
            draw.assert_called_once_with(False)
        self.first_move()
        self.assertTrue(self.app.update_bot())
        human, bot = self.game.command_history
        with patch.object(human, "undo", wraps=human.undo) as undo_human, \
                patch.object(bot, "undo", wraps=bot.undo) as undo_bot:
            self.click(self.view.undo_button_rect.center)
            undo_bot.assert_called_once()
            undo_human.assert_called_once()
        self.assertEqual([p.position for p in self.game.players], [(0, 4), (8, 4)])
        self.assertEqual(self.game.current_turn, 0)
        self.assertFalse(self.app.update_bot())
        self.app.draw()
        center = self.view.model_to_screen_point((self.view.board_x + 4 * 66 + 29, self.view.board_y + 66 + 29))
        self.assertEqual(tuple(self.view.screen.get_at(center))[:3], (85, 145, 90))
        self.first_move()
        self.assertTrue(self.app.update_bot())
        self.assertEqual(len(self.game.command_history), 2)

    # Bấm Undo trước bot đáp trả thì bot không đánh ngay lại sau đó.
    def test_undo_cancels_pending_response(self):
        self.first_move()
        self.click(self.view.undo_button_rect.center)
        with patch.object(self.controller.bot_strategy, "choose_command") as choose:
            self.assertFalse(self.app.update_bot())
            choose.assert_not_called()
        self.assertEqual(self.game.command_history, [])

    # Nút Undo vẫn nhận click sau người thắng hoặc sau bot thắng qua luồng chơi thật.
    def test_button_after_either_winner(self):
        for winner in (0, 1):
            with self.subTest(winner=winner):
                self.click(self.view.restart_rect(self.game).center)
                if winner == 0:
                    self.game.players[0].row = 7
                    self.game.players[1].col = 0
                    before = self.game.capture_state()
                    self.click(self.view.model_to_screen_point((self.view.board_x + 4 * 66 + 29, self.view.board_y + 8 * 66 + 29)))
                    self.assertFalse(self.app.update_bot())
                else:
                    self.game.players[0].col = 0
                    self.game.players[1].row = 1
                    before = self.game.capture_state()
                    self.click(self.view.model_to_screen_point((self.view.board_x + 66 + 29, self.view.board_y + 29)))
                    self.assertTrue(self.app.update_bot())
                self.assertIs(self.game.winner, self.game.players[winner])
                self.app.draw()
                self.click(self.view.undo_button_rect.center)
                self.assertEqual(self.game.capture_state(), before)
                self.assertFalse(self.app.update_bot())

    # Reset/về menu xóa lịch sử; chế độ hai người không vẽ hoặc nhận Undo.
    def test_history_cleared_on_restart_and_menu(self):
        self.first_move()
        self.app.update_bot()
        self.click(self.view.restart_rect(self.game).center)
        self.assertEqual(self.game.command_history, [])
        self.first_move()
        self.app.update_bot()
        self.click(self.view.menu_rect(self.game).center)
        self.assertEqual(self.game.command_history, [])
        start_game(self.app, self.menu, mode="two_players", level="easy")
        self.assertFalse(self.game.can_undo)
        with patch.object(self.view, "draw_undo_button") as draw:
            self.app.draw()
            draw.assert_not_called()

    # Vòng lặp main bỏ click còn lại sau Undo, không tự đánh lại nước vừa lùi.
    def test_main_discards_click_after_undo(self):
        human = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                   pos=self.view.model_to_screen_point((self.view.board_x + 4 * 66 + 29, self.view.board_y + 66 + 29)))
        undo = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                  pos=self.view.undo_button_rect.center)
        main_path = Path(__file__).resolve().parents[1] / "main.py"
        with patch("game.game.Game", return_value=self.game), \
                patch("ui.game_view.GameView", return_value=self.view), \
                patch("ui.controller.GameController", return_value=self.controller), \
                patch("pygame.event.get", side_effect=[*menu_frames(self.menu), [human], [undo, human],
                                                       [pygame.event.Event(pygame.QUIT)]]):
            runpy.run_path(str(main_path), run_name="__main__")
        self.assertEqual([p.position for p in self.game.players], [(0, 4), (8, 4)])
        self.assertEqual(self.game.command_history, [])
        self.assertEqual(self.game.current_turn, 0)


if __name__ == "__main__":
    unittest.main()
