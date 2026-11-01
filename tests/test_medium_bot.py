import os
from time import perf_counter
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from game.board import Board
from game.bot.easy import EasyStrategy
from game.bot.medium import MediumStrategy
from game.bot.strategy import BotStrategy
from game.bot.strategy_factory import BotStrategyFactory
from game.commands import MoveCommand, PlaceWallCommand
from game.game import Game
from game.pathfinder import PathFinder
from tests.support import start_game
from ui.app_controller import AppController
from ui.controller import GameController
from ui.game_view import GameView
from ui.menu_view import MenuView


# Rà quyết định bot trung bình và việc thử hành động không ảnh hưởng ván thật.
class MediumBotTests(unittest.TestCase):
    # Cố định cách chọn khi hòa để kết quả test lặp lại được.
    def setUp(self):
        self.game = Game(mode="bot", bot_level="medium")
        self.strategy = MediumStrategy(choose=lambda choices: choices[0])

    # Factory tạo hai Strategy khác nhau và từ chối cấp chưa được hỗ trợ.
    def test_factory_selects_strategy(self):
        self.assertIsInstance(BotStrategyFactory.create("easy"), EasyStrategy)
        self.assertIsInstance(BotStrategyFactory.create("medium"), MediumStrategy)
        self.assertIsInstance(self.strategy, BotStrategy)
        self.assertIsInstance(EasyStrategy(), BotStrategy)
        with self.assertRaises(ValueError):
            BotStrategyFactory.create("unknown")

    # Bản đồ BFS khớp BFS một nguồn tại mọi ô, cả khi có vùng không tới được đích.
    def test_distance_map_matches_single_source_bfs(self):
        board = Board()
        for wall in [("horizontal", 0, 0), ("vertical", 0, 1),
                     ("horizontal", 3, 3), ("vertical", 5, 5)]:
            self.assertTrue(board.place_wall(*wall))
        finder = PathFinder()
        for goal in (0, 8):
            distances = finder.distances_to_goal(board, goal)
            for row in range(9):
                for col in range(9):
                    with self.subTest(goal=goal, cell=(row, col)):
                        self.assertEqual(distances.get((row, col)),
                                         finder.shortest_distance(board, (row, col), goal))

    # Đầu ván không phí tường nếu đi quân có lợi hơn; lựa chọn không đổi trạng thái/lịch sử.
    def test_opening_moves_without_wasting_wall_or_mutation(self):
        self.assertIsNone(self.strategy.choose_command(self.game))
        self.assertTrue(MoveCommand(self.game, (1, 4)).execute())
        before = self.game.capture_state()
        history = self.game.command_history.copy()
        with patch.object(PlaceWallCommand, "execute", side_effect=AssertionError("Không được thử execute")):
            command = self.strategy.choose_command(self.game)
        self.assertIsInstance(command, MoveCommand)
        self.assertEqual(command.destination, (7, 4))
        self.assertEqual(self.game.capture_state(), before)
        self.assertEqual(self.game.command_history, history)
        self.assertEqual(self.game.redo_history, [])
        self.assertTrue(command.execute())
        self.assertEqual(self.game.current_turn, 0)
        self.assertEqual(self.game.players[1].walls_remaining, 10)

    # Bot thắng ngay thay vì đặt tường, ngay cả khi người cũng sắp tới đích.
    def test_take_immediate_win(self):
        self.game.players[0].row, self.game.players[0].col = 7, 0
        self.game.players[1].row = 1
        self.game.current_turn = 1
        command = self.strategy.choose_command(self.game)
        self.assertIsInstance(command, MoveCommand)
        self.assertEqual(command.destination, (0, 4))
        self.assertTrue(command.execute())
        self.assertIs(self.game.winner, self.game.players[1])
        self.assertIsNone(self.strategy.choose_command(self.game))

    # Nếu không thể thắng ngay, chặn nước tới đích của người bằng tường đúng luật.
    def test_block_human_immediate_win(self):
        self.game.players[0].row = 7
        self.game.players[1].col = 0
        self.game.current_turn = 1
        before = self.game.capture_state()
        command = self.strategy.choose_command(self.game)
        self.assertIsInstance(command, PlaceWallCommand)
        self.assertEqual(self.game.capture_state(), before)
        self.assertTrue(command.execute())
        self.assertEqual(self.game.players[1].walls_remaining, 9)
        self.assertEqual(self.game.wall_owners,
                         {(command.orientation, command.row, command.col): 1})
        self.assertFalse(any(cell[0] == 8 for cell in self.game.get_legal_moves()))
        self.assertTrue(self.game.path_finder.both_players_have_paths(self.game.board, self.game.players))

    # Hết tường vẫn chọn nước đi hợp lệ, không đi âm tường để chặn đối thủ.
    def test_no_walls_left(self):
        self.game.players[0].row = 7
        self.game.players[1].col = 0
        self.game.players[1].walls_remaining = 0
        self.game.current_turn = 1
        command = self.strategy.choose_command(self.game)
        self.assertIsInstance(command, MoveCommand)
        self.assertIn(command.destination, self.game.get_legal_moves())
        self.assertTrue(command.execute())
        self.assertEqual(self.game.players[1].walls_remaining, 0)

    # Đánh giá một tường khóa đường phải loại bỏ, dù chặn được đối thủ.
    def test_evaluation_rejects_locked_paths(self):
        cases = [(0, (0, 0), [("horizontal", 0, 0), ("vertical", 0, 1)]),
                 (1, (8, 8), [("horizontal", 7, 7), ("vertical", 7, 6)])]
        for trapped, position, walls in cases:
            with self.subTest(trapped=trapped):
                self.game.reset()
                self.game.current_turn = 1
                self.game.players[trapped].row, self.game.players[trapped].col = position
                for wall in walls:
                    self.assertTrue(self.game.board.place_wall(*wall))
                self.assertIsNone(self.strategy._evaluate(self.game, wall_cost=0.5))

    # Nhảy thẳng/chéo tới đích vẫn theo luật chung, không bị đánh giá tường làm bỏ lỡ.
    def test_winning_jumps(self):
        for blocked in (False, True):
            with self.subTest(blocked=blocked):
                self.game.reset()
                self.game.current_turn = 1
                self.game.players[0].row, self.game.players[0].col = 1, 4
                self.game.players[1].row, self.game.players[1].col = 2, 4
                if blocked:
                    self.assertTrue(self.game.board.place_wall("horizontal", 0, 4))
                command = self.strategy.choose_command(self.game)
                self.assertIsInstance(command, MoveCommand)
                self.assertIn(command.destination, self.game.get_legal_moves())
                if blocked:
                    self.assertIn(command.destination, {(1, 3), (1, 5)})
                else:
                    self.assertEqual(command.destination, (0, 4))
                    self.assertTrue(command.execute())
                    self.assertIs(self.game.winner, self.game.players[1])

    # Luôn trả lại tường/vị trí thử nếu việc đánh giá gặp ngoại lệ.
    def test_trials_restore_state_after_exception(self):
        self.game.current_turn = 1
        before = self.game.capture_state()
        with patch.object(self.strategy, "_evaluate", side_effect=RuntimeError("test")):
            with self.assertRaises(RuntimeError):
                self.strategy.choose_command(self.game)
        self.assertEqual(self.game.capture_state(), before)
        # Bỏ phần thử đi để kiểm tra riêng khối finally của phần thử tường.
        with patch.object(self.game, "get_legal_moves", return_value=[]), \
                patch.object(self.strategy, "_evaluate", side_effect=RuntimeError("test")):
            with self.assertRaises(RuntimeError):
                self.strategy.choose_command(self.game)
        self.assertEqual(self.game.capture_state(), before)

    # Đánh giá cả bàn sau Undo không được làm mất nhánh Redo cũ.
    def test_thinking_does_not_clear_redo(self):
        self.assertTrue(MoveCommand(self.game, (1, 4)).execute())
        self.assertTrue(MoveCommand(self.game, (7, 4)).execute())
        self.assertTrue(MoveCommand(self.game, (2, 4)).execute())
        self.assertTrue(MoveCommand(self.game, (6, 4)).execute())
        self.assertTrue(self.game.command_history[-1].undo())
        before = self.game.capture_state()
        redo = self.game.redo_history.copy()
        self.strategy.choose_command(self.game)
        self.assertEqual(self.game.capture_state(), before)
        self.assertEqual(self.game.redo_history, redo)


# Rà menu chọn cấp và tích hợp bot đặt tường với Undo/Redo qua Command.
class MediumFlowTests(unittest.TestCase):
    # Dùng ứng dụng và giao diện thật trên SDL headless.
    def setUp(self):
        self.game = Game()
        self.view = GameView()
        self.controller = GameController(self.game, self.view)
        self.menu = MenuView(self.view)
        self.app = AppController(self.controller, self.menu)

    # Giải phóng tài nguyên sau mỗi test.
    def tearDown(self):
        pygame.quit()

    # Gửi click trái qua lớp điều hướng.
    def click(self, position):
        return self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=position))

    # Chọn trung bình, chơi lại giữ cấp; chuyển dễ/hai người vẫn đúng chiến lược và giờ.
    def test_select_restart_and_switch_levels(self):
        start_game(self.app, self.menu, mode="bot", level="medium")
        self.assertEqual(self.game.bot_level, "medium")
        self.assertEqual(self.game.players[1].name, "Bot trung bình")
        self.assertIsInstance(self.controller.bot_strategy, MediumStrategy)
        self.assertFalse(self.game.timer_enabled)
        self.click(self.view.restart_button_rect.center)
        self.assertEqual(self.game.bot_level, "medium")
        self.assertIsInstance(self.controller.bot_strategy, MediumStrategy)
        with patch.object(self.view, "draw_text", wraps=self.view.draw_text) as text:
            self.app.draw()
            labels = [call.args[0] for call in text.call_args_list]
            self.assertIn("Đấu bot trung bình", labels)
            self.assertFalse(any(label.startswith("Lượt:") for label in labels))
        self.click(self.view.menu_button_rect.center)
        start_game(self.app, self.menu, mode="bot", level="easy")
        self.assertEqual(self.game.bot_level, "easy")
        self.assertIsInstance(self.controller.bot_strategy, EasyStrategy)
        self.click(self.view.menu_button_rect.center)
        start_game(self.app, self.menu, mode="two_players", level="easy")
        self.assertTrue(self.game.timer_enabled)
        self.assertFalse(self.app.update_bot())

    # Bot đặt tường qua Command; Undo/Redo khôi phục cả tường xanh và nước người.
    def test_wall_command_undo_redo(self):
        start_game(self.app, self.menu, mode="bot", level="medium")
        self.game.players[0].row = 6
        self.game.players[1].col = 0
        before = self.game.capture_state()
        self.click(self.view.model_to_screen_point((self.view.board_x + 4 * 66 + 29, self.view.board_y + 7 * 66 + 29)))
        self.assertTrue(self.app.update_bot())
        self.assertIsInstance(self.game.command_history[-1], PlaceWallCommand)
        self.assertEqual(self.game.players[1].walls_remaining, 9)
        after = self.game.capture_state()
        self.app.draw()
        for wall, owner in self.game.wall_owners.items():
            self.assertEqual(owner, 1)
            self.assertEqual(tuple(self.view.screen.get_at(self.view._wall_rect(*wall).center))[:3],
                             self.view.player_colors[1])
        self.click(self.view.undo_button_rect.center)
        self.assertEqual(self.game.capture_state(), before)
        with patch.object(self.controller.bot_strategy, "choose_command") as choose:
            self.click(self.view.redo_button_rect.center)
            self.assertFalse(self.app.update_bot())
            choose.assert_not_called()
        self.assertEqual(self.game.capture_state(), after)

    # Chạy nhiều lượt thật: mọi nước bot hợp lệ, không khóa đường và lịch sử tăng đúng.
    def test_representative_game_and_decision_cost(self):
        start_game(self.app, self.menu, mode="bot", level="medium")
        longest = 0.0
        for _ in range(12):
            if self.game.winner is not None:
                break
            self.assertTrue(MoveCommand(self.game, self.game.get_legal_moves()[0]).execute())
            if self.game.winner is not None:
                break
            start = perf_counter()
            self.assertTrue(self.app.update_bot())
            longest = max(longest, perf_counter() - start)
            self.assertTrue(self.game.path_finder.both_players_have_paths(self.game.board, self.game.players))
            self.assertTrue(all(p.walls_remaining >= 0 for p in self.game.players))
        self.assertGreaterEqual(len(self.game.command_history), 2)
        # Chỉ ghi số đo để chẩn đoán, tránh test phụ thuộc tốc độ máy.
        print(f"Medium bot: quyết định chậm nhất trong ván mẫu {longest:.3f}s")


if __name__ == "__main__":
    unittest.main()
