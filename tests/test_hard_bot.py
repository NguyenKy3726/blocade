import inspect
import os
from pathlib import Path
import runpy
from time import perf_counter
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from pattern.strategy import HardStrategy
from pattern.strategy.search_context import _SearchContext
from pattern.strategy import BotStrategy
from pattern.strategy import BotStrategyFactory
from pattern.command import MoveCommand, PlaceWallCommand
from game.game import Game
from tests.support import start_game, menu_frames
from pattern.state import AppController
from ui.controller import GameController
from ui.game_view import GameView
from ui.menu_view import MenuView
from pattern.state import MenuState, HumanTurnState, BotTurnState, GameOverState


# Kiểm tra Minimax/Alpha–Beta, giới hạn và tính độc lập của ván mô phỏng.
class HardBotTests(unittest.TestCase):
    # Cố định lựa chọn khi hòa và bỏ phụ thuộc tốc độ máy cho kiểm tra thuật toán.
    def setUp(self):
        self.game = Game(mode="bot", bot_level="hard")
        self.strategy = HardStrategy(choose=lambda items: items[0], clock=lambda: 0.0,
                                     time_budget=100, node_budget=5000)

    # Lấy giá trị return của generator Minimax, bỏ qua các lần nhường UI.
    def result(self, generator):
        while True:
            try:
                next(generator)
            except StopIteration as end:
                return end.value

    # Vét cạn nước đi không tường làm đối chứng độc lập cho việc cắt Alpha–Beta.
    def brute_value(self, game, depth, context, ply):
        if depth == 0 or game.winner is not None:
            return self.strategy._evaluate(game, context, ply)
        maximizing = game.current_turn == 1
        values = []
        for destination in game.get_legal_moves():
            command = MoveCommand(game, destination)
            self.assertTrue(command.execute())
            try:
                values.append(self.brute_value(game, depth - 1, context, ply + 1))
            finally:
                self.assertTrue(command.undo())
        return max(values) if maximizing else min(values)

    # Factory đưa cấp khó vào cùng giao diện Strategy và giữ hai cấp cũ hoạt động.
    def test_factory_and_interface(self):
        self.assertIsInstance(BotStrategyFactory.create("hard"), HardStrategy)
        self.assertIsInstance(self.strategy, BotStrategy)
        with self.assertRaises(ValueError):
            BotStrategyFactory.create("unknown")

    # Chỉ tìm khi tới lượt bot; nước thắng tức thì không bị bỏ qua để đặt tường.
    def test_turn_guard_and_immediate_win(self):
        self.assertIsNone(self.strategy.choose_command(self.game))
        self.game.current_turn = 1
        self.game.players[1].row = 1
        self.game.players[0].col = 0
        before = self.game.capture_state()
        command = self.strategy.choose_command(self.game)
        self.assertEqual(self.game.capture_state(), before)
        self.assertIsInstance(command, MoveCommand)
        self.assertEqual(command.destination, (0, 4))
        self.assertTrue(command.execute())
        self.assertIs(self.game.winner, self.game.players[1])
        self.assertIsNone(self.strategy.choose_command(self.game))

    # Bot chặn nước thắng ngay bằng tường hợp lệ và không khóa đường hai bên.
    def test_block_immediate_human_win(self):
        self.game.current_turn = 1
        self.game.players[0].row = 7
        self.game.players[1].col = 0
        before = self.game.capture_state()
        command = self.strategy.choose_command(self.game)
        self.assertEqual(self.game.capture_state(), before)
        self.assertEqual(self.game.command_history, [])
        self.assertEqual(self.game.redo_history, [])
        self.assertIsInstance(command, PlaceWallCommand)
        self.assertTrue(command.execute())
        self.assertFalse(any(cell[0] == 8 for cell in self.game.get_legal_moves()))
        self.assertEqual(self.game.players[1].walls_remaining, 9)
        self.assertTrue(self.game.path_finder.both_players_have_paths(self.game.board, self.game.players))

    # Alpha–Beta phải cho đúng giá trị như vét cạn trên cùng cây không có tường.
    def test_alpha_beta_matches_brute_force(self):
        self.game.current_turn = 1
        for player in self.game.players:
            player.walls_remaining = 0
        for depth in (2, 3):
            with self.subTest(depth=depth):
                context = _SearchContext(self.strategy)
                expected = self.brute_value(self.game, depth, context, 0)
                before = self.game.capture_state()
                actual = self.result(self.strategy._minimax(
                    self.game, depth, float("-inf"), float("inf"), context, 0))
                self.assertEqual(actual, expected)
                self.assertEqual(self.game.capture_state(), before)
        self.assertGreater(context.cutoffs, 0)

    # Lệnh gốc được chọn phải thuộc tập tốt nhất tính bằng vét cạn 3 hành động.
    def test_root_choice_matches_three_ply_oracle(self):
        self.game.current_turn = 1
        self.game.players[0].row, self.game.players[0].col = 4, 4
        self.game.players[1].row, self.game.players[1].col = 5, 4
        for player in self.game.players:
            player.walls_remaining = 0
        context = _SearchContext(self.strategy)
        values = {}
        for destination in self.game.get_legal_moves():
            command = MoveCommand(self.game, destination)
            self.assertTrue(command.execute())
            try:
                values[destination] = self.brute_value(self.game, 2, context, 1)
            finally:
                self.assertTrue(command.undo())
        command = self.strategy.choose_command(self.game)
        self.assertEqual(values[command.destination], max(values.values()))
        self.assertEqual(self.strategy.last_stats["completed_depth"], 3)

    # Hết ngân sách vẫn có nước hợp lệ, không vượt số nút hoặc ghi thử vào lịch sử thật.
    def test_time_and_node_limits_keep_legal_fallback(self):
        self.game.current_turn = 1
        before = self.game.capture_state()
        for strategy in (HardStrategy(time_budget=0),
                         HardStrategy(node_budget=1, time_budget=100, clock=lambda: 0.0)):
            with self.subTest(nodes=strategy.node_budget):
                command = strategy.choose_command(self.game)
                self.assertIsInstance(command, MoveCommand)
                self.assertIn(command.destination, self.game.get_legal_moves())
                self.assertTrue(strategy.last_stats["limited"])
                self.assertLessEqual(strategy.last_stats["nodes"], strategy.node_budget)
                self.assertEqual(self.game.capture_state(), before)
                self.assertEqual(self.game.command_history, [])

    # Nhảy thẳng/chéo vẫn theo Game, gồm nhảy tới hàng đích khi có quân sát mép.
    def test_jumps_use_shared_rules(self):
        for blocked in (False, True):
            with self.subTest(blocked=blocked):
                self.game.reset()
                self.game.current_turn = 1
                self.game.players[0].row, self.game.players[0].col = 1, 4
                self.game.players[1].row, self.game.players[1].col = 2, 4
                self.game.players[1].walls_remaining = 0
                self.game.players[0].walls_remaining = 0
                if blocked:
                    self.assertTrue(self.game.board.place_wall("horizontal", 0, 4))
                command = self.strategy.choose_command(self.game)
                self.assertIn(command.destination, self.game.get_legal_moves())
                if not blocked:
                    self.assertEqual(command.destination, (0, 4))
                self.assertTrue(command.execute())

    # Đóng generator giữa chừng hoặc gặp lỗi đánh giá không làm đổi ván/hai lịch sử thật.
    def test_cancel_and_error_leave_real_game_unchanged(self):
        self.assertTrue(MoveCommand(self.game, (1, 4)).execute())
        self.assertTrue(MoveCommand(self.game, (7, 4)).execute())
        self.assertTrue(self.game.command_history[-1].undo())
        before = self.game.capture_state()
        history = self.game.command_history.copy()
        redo = self.game.redo_history.copy()
        search = self.strategy.start_search(self.game)
        for _ in range(4):
            self.assertIsNone(next(search))
        search.close()
        self.assertEqual(inspect.getgeneratorstate(search), inspect.GEN_CLOSED)
        with patch.object(self.strategy, "_evaluate", side_effect=RuntimeError("test")):
            with self.assertRaises(RuntimeError):
                self.strategy.choose_command(self.game)
        self.assertEqual(self.game.capture_state(), before)
        self.assertEqual(self.game.command_history, history)
        self.assertEqual(self.game.redo_history, redo)

    # Chơi ván mẫu tới kết thúc: bot tự tiến về đích qua Command, không đi sau thắng.
    def test_complete_representative_game(self):
        self.strategy.max_depth = 2
        self.strategy.wall_limit = 2
        for step in range(12):
            self.assertTrue(MoveCommand(self.game, (0, 5 if step % 2 == 0 else 6)).execute())
            command = self.strategy.choose_command(self.game)
            self.assertIsNotNone(command)
            self.assertTrue(command.execute())
            self.assertTrue(self.game.path_finder.both_players_have_paths(self.game.board, self.game.players))
            if self.game.winner is not None:
                break
        self.assertIs(self.game.winner, self.game.players[1])
        self.assertIsNone(self.strategy.choose_command(self.game))


# Rà các State, tìm kiếm nhiều khung hình và Command/Undo/Redo qua UI thật headless.
class HardFlowTests(unittest.TestCase):
    # Vào cấp khó qua menu, giới hạn sâu 2 cho kiểm tra luồng nhanh và ổn định.
    def setUp(self):
        self.now = 100.0
        self.game = Game(time_source=lambda: self.now)
        self.view = GameView()
        self.controller = GameController(self.game, self.view)
        self.menu = MenuView(self.view)
        self.app = AppController(self.controller, self.menu)
        start_game(self.app, self.menu, mode="bot", level="hard")
        self.controller.bot_strategy = HardStrategy(max_depth=2, time_budget=2)

    # Luôn đóng tác vụ còn sống trước khi giải phóng Pygame.
    def tearDown(self):
        self.controller.cancel_search()
        pygame.quit()

    # Gửi click theo luồng ứng dụng.
    def click(self, position):
        return self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=position))

    # Nước đi đầu tiên của người xanh lá.
    def first_move(self):
        self.click(self.view.model_to_screen_point((self.view.board_x + 4 * 66 + 29, self.view.board_y + 66 + 29)))

    # Cố định một đoạn ngắn để kiểm tra thao tác hủy giữa lúc bot còn suy nghĩ.
    def begin_partial_search(self):
        with patch("ui.controller.perf_counter", side_effect=[0.0, 1.0]):
            self.assertFalse(self.app.update_bot())
        self.assertIsNotNone(self.controller.pending_search)
        return self.controller.pending_search

    # Mô phỏng các khung hình tới khi bot trả lượt, không sleep hoặc chạy thread.
    def finish_bot(self):
        for _ in range(2000):
            if self.app.update_bot():
                return
        self.fail("Bot không kết thúc trong số khung hình kiểm tra")

    # State chuyển người -> bot -> người và chỉ bot State mới được tiến tìm kiếm.
    def test_state_transitions_and_responsive_search(self):
        self.assertIsInstance(self.app.state, HumanTurnState)
        self.assertEqual(self.game.bot_level, "hard")
        self.assertFalse(self.game.timer_enabled)
        self.now += 300
        self.assertFalse(self.app.update())
        self.first_move()
        self.assertIsInstance(self.app.state, BotTurnState)
        before = self.game.capture_state()
        self.begin_partial_search()
        self.assertEqual(self.game.capture_state(), before)
        self.app.draw()
        self.finish_bot()
        self.assertIsInstance(self.app.state, HumanTurnState)
        self.assertEqual(len(self.game.command_history), 2)
        self.assertIsNone(self.controller.pending_search)
        self.assertFalse(self.app.update_bot())

    # Undo trong lúc suy nghĩ đóng generator, trả lượt người và không có đáp trả muộn.
    def test_undo_cancels_search(self):
        self.first_move()
        search = self.begin_partial_search()
        self.click(self.view.undo_button_rect.center)
        self.assertEqual(inspect.getgeneratorstate(search), inspect.GEN_CLOSED)
        self.assertIsNone(self.controller.pending_search)
        self.assertIsInstance(self.app.state, HumanTurnState)
        self.assertEqual(self.game.players[0].position, (0, 4))
        self.assertFalse(self.app.update_bot())

    # Chơi lại giữ cấp; Về menu hủy tác vụ và chọn cấp khác dùng đúng Factory.
    def test_restart_menu_and_level_switch_cancel_search(self):
        for target in ("restart", "menu"):
            self.first_move()
            search = self.begin_partial_search()
            self.click(self.view.restart_rect(self.game).center if target == "restart"
                       else self.view.menu_rect(self.game).center)
            self.assertEqual(inspect.getgeneratorstate(search), inspect.GEN_CLOSED)
            self.assertIsNone(self.controller.pending_search)
            self.assertFalse(self.app.update_bot())
            if target == "restart":
                self.assertEqual(self.game.bot_level, "hard")
                self.assertIsInstance(self.app.state, HumanTurnState)
            else:
                self.assertIsInstance(self.app.state, MenuState)
                self.assertEqual(self.game.command_history, [])
                self.assertEqual(self.game.redo_history, [])
        start_game(self.app, self.menu, mode="bot", level="medium")
        self.assertEqual(self.game.bot_level, "medium")
        self.assertIsInstance(self.app.state, HumanTurnState)
        self.click(self.view.menu_rect(self.game).center)
        start_game(self.app, self.menu, mode="two_players", level="easy")
        self.now += 30
        self.assertTrue(self.app.update())
        self.assertIsInstance(self.app.state, HumanTurnState)
        self.assertEqual(self.game.current_turn, 1)
        self.assertFalse(self.app.update_bot())

    # GameOver State dừng hành động; Undo/Redo đưa về đúng State mà không tìm lại bot.
    def test_game_over_state_undo_redo(self):
        self.game.players[0].row = 7
        self.game.players[1].col = 0
        self.click(self.view.model_to_screen_point((self.view.board_x + 4 * 66 + 29, self.view.board_y + 8 * 66 + 29)))
        self.assertIsInstance(self.app.state, GameOverState)
        self.assertFalse(self.app.update())
        self.assertFalse(self.app.update_bot())
        self.app.draw()
        self.click(self.view.undo_button_rect.center)
        self.assertIsInstance(self.app.state, HumanTurnState)
        self.click(self.view.redo_button_rect.center)
        self.assertIsInstance(self.app.state, GameOverState)

    # Bot đặt tường qua Command, Undo/Redo giữ đúng màu/tường và không gọi lại tìm kiếm.
    def test_wall_round_undo_redo(self):
        self.game.players[0].row = 6
        self.game.players[1].col = 0
        before = self.game.capture_state()
        self.click(self.view.model_to_screen_point((self.view.board_x + 4 * 66 + 29, self.view.board_y + 7 * 66 + 29)))
        self.finish_bot()
        self.assertIsInstance(self.game.command_history[-1], PlaceWallCommand)
        after = self.game.capture_state()
        self.click(self.view.undo_button_rect.center)
        self.assertEqual(self.game.capture_state(), before)
        with patch.object(self.controller.bot_strategy, "start_search") as search:
            self.click(self.view.redo_button_rect.center)
            self.assertFalse(self.app.update_bot())
            search.assert_not_called()
        self.assertEqual(self.game.capture_state(), after)

    # Đóng cửa sổ trong lúc tìm kiếm không để generator tiếp tục chạy.
    def test_close_cancels_search(self):
        self.first_move()
        search = self.begin_partial_search()
        self.assertFalse(self.app.handle_event(pygame.event.Event(pygame.QUIT)))
        self.assertEqual(inspect.getgeneratorstate(search), inspect.GEN_CLOSED)

    # Chạy main thật nhiều khung hình, hủy nước bot qua Undo rồi đóng bình thường.
    def test_main_search_and_undo(self):
        events = [
            *menu_frames(self.menu, level="hard"),
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                pos=self.view.model_to_screen_point((self.view.board_x + 4 * 66 + 29, self.view.board_y + 66 + 29)))],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=self.view.undo_button_rect.center)],
            [pygame.event.Event(pygame.QUIT)],
        ]
        main_path = Path(__file__).resolve().parents[1] / "main.py"
        with patch("game.game.Game", return_value=self.game), \
                patch("ui.game_view.GameView", return_value=self.view), \
                patch("ui.controller.GameController", return_value=self.controller), \
                patch("pygame.event.get", side_effect=events):
            runpy.run_path(str(main_path), run_name="__main__")
        self.assertIsNone(self.controller.pending_search)
        self.assertEqual(self.game.players[0].position, (0, 4))
        self.assertIsNone(self.game.winner)


if __name__ == "__main__":
    unittest.main()
