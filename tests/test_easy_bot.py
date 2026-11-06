import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from game.board import Board
from pattern.strategy import EasyStrategy
from pattern.command import MoveCommand, PlaceWallCommand
from game.game import Game
from game.pathfinder import PathFinder
from tests.support import start_game, menu_frames, execute_command
from pattern.state import AppController
from ui.controller import GameController
from ui.game_view import GameView
from ui.menu_view import MenuView


# Rà lựa chọn nước đi và luật của chế độ bot không phụ thuộc màn hình.
class EasyBotTests(unittest.TestCase):
    # Dùng cách chọn đầu tiên khi hòa để test có thể lặp lại chính xác.
    def setUp(self):
        self.game = Game(mode="bot")
        self.strategy = EasyStrategy(choose=lambda moves: moves[0])

    # BFS trả về khoảng cách, 0 khi đã tới đích và None nếu bị khóa đường.
    def test_bfs_distances(self):
        finder = PathFinder()
        board = Board()
        self.assertEqual(finder.shortest_distance(board, (0, 4), 8), 8)
        self.assertEqual(finder.shortest_distance(board, (8, 4), 8), 0)
        self.assertTrue(board.place_wall("horizontal", 0, 3))
        self.assertEqual(finder.shortest_distance(board, (0, 4), 8), 9)
        blocked = Board(size=2)
        self.assertTrue(blocked.place_wall("horizontal", 0, 0))
        self.assertIsNone(finder.shortest_distance(blocked, (0, 0), 1))
        self.assertFalse(finder.has_path(blocked, (0, 0), 1))

    # Không gọi nguồn thời gian ở bất kỳ lượt nào khi chơi bot, kể cả chờ rất lâu.
    def test_bot_mode_never_uses_timer(self):
        clock = Mock(side_effect=AssertionError("Không được chạy đồng hồ trong chế độ bot"))
        game = Game(mode="bot", time_source=clock)
        self.assertFalse(game.timer_enabled)
        self.assertIsNone(game.turn_started_at)
        self.assertFalse(game.update_time())
        self.assertTrue(execute_command(MoveCommand(game, (1, 4))))
        self.assertTrue(execute_command(self.strategy.choose_command(game)))
        self.assertTrue(execute_command(PlaceWallCommand(game, "horizontal", 3, 3)))
        game.reset()
        self.assertEqual(game.mode, "bot")
        clock.assert_not_called()

    # Tạo quyết định không đổi ván; bot chỉ đi một lần rồi trả lượt cho người.
    def test_strategy_returns_legal_command_without_mutating(self):
        self.assertIsNone(self.strategy.choose_command(self.game))
        self.assertTrue(execute_command(MoveCommand(self.game, (1, 4))))
        positions = [p.position for p in self.game.players]
        command = self.strategy.choose_command(self.game)
        self.assertIsInstance(command, MoveCommand)
        self.assertEqual(command.destination, (7, 4))
        self.assertIn(command.destination, self.game.get_legal_moves())
        self.assertEqual([p.position for p in self.game.players], positions)
        self.assertTrue(execute_command(command))
        self.assertEqual(self.game.current_turn, 0)
        self.assertIsNone(self.strategy.choose_command(self.game))

    # Bot chọn đường vòng qua tường thay vì cố đi xuyên hoặc lặp bước tiến bị chặn.
    def test_bot_routes_around_wall(self):
        self.game.current_turn = 1
        self.game.players[1].row = 4
        self.assertTrue(self.game.board.place_wall("horizontal", 3, 3))
        command = self.strategy.choose_command(self.game)
        self.assertEqual(command.destination, (4, 5))
        self.assertTrue(execute_command(command))

    # Bot dùng chung nhảy thẳng/chéo; không tự chép luật vào chiến lược.
    def test_bot_straight_and_diagonal_jump(self):
        for blocked in (False, True):
            with self.subTest(blocked=blocked):
                self.game.reset()
                self.game.current_turn = 1
                self.game.players[0].row, self.game.players[0].col = 3, 4
                self.game.players[1].row, self.game.players[1].col = 4, 4
                if blocked:
                    self.assertTrue(self.game.board.place_wall("horizontal", 2, 4))
                command = self.strategy.choose_command(self.game)
                expected = {(3, 3), (3, 5)} if blocked else {(2, 4)}
                self.assertIn(command.destination, expected)
                self.assertTrue(execute_command(command))

    # Chơi cả ván tới bot thắng, sau đó không cho bot đáp trả thêm.
    def test_bot_completes_game_and_stops_on_win(self):
        for step in range(8):
            self.assertTrue(execute_command(MoveCommand(self.game, (0, 5 if step % 2 == 0 else 6))))
            command = self.strategy.choose_command(self.game)
            self.assertTrue(execute_command(command))
        self.assertIs(self.game.winner, self.game.players[1])
        self.assertEqual(self.game.players[1].position, (0, 4))
        self.assertIsNone(self.strategy.choose_command(self.game))

    # Người tới đích thì không phát sinh nước bot sau đó.
    def test_human_win_stops_bot(self):
        self.game.players[0].row = 7
        self.game.players[1].col = 0
        self.assertTrue(execute_command(MoveCommand(self.game, (8, 4))))
        self.assertIs(self.game.winner, self.game.players[0])
        self.assertIsNone(self.strategy.choose_command(self.game))


# Rà menu, chuột và giao diện bot qua controller thật trên SDL headless.
class BotFlowTests(unittest.TestCase):
    # Tạo một ứng dụng có đồng hồ giả để kiểm tra đổi chế độ.
    def setUp(self):
        self.now = 100.0
        self.game = Game(time_source=lambda: self.now)
        self.view = GameView()
        self.controller = GameController(self.game, self.view)
        self.menu = MenuView(self.view)
        self.app = AppController(self.controller, self.menu)

    # Giải phóng tài nguyên sau mỗi test.
    def tearDown(self):
        pygame.quit()

    # Tạo click trái và gửi qua điều hướng như vòng lặp main.
    def click(self, position):
        return self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=position))

    # Đổi tọa độ ô thành vị trí click ở giữa ô.
    def cell(self, row, col):
        return self.view.model_to_screen_point((self.view.board_x + col * 66 + 29, self.view.board_y + row * 66 + 29))

    # Menu vào đúng bot; không mất lượt khi chờ lâu, không vẽ bất kỳ đồng hồ nào.
    def test_bot_menu_disables_and_hides_clocks(self):
        start_game(self.app, self.menu, mode="bot", level="easy")
        self.assertEqual(self.app.screen, "game")
        self.assertEqual(self.game.mode, "bot")
        self.now += 1000
        self.assertFalse(self.app.update())
        self.assertEqual(self.game.current_turn, 0)
        self.assertEqual(self.game.notice, "")
        with patch.object(self.view, "draw_text", wraps=self.view.draw_text) as text:
            self.app.draw()
            labels = [call.args[0] for call in text.call_args_list]
            self.assertIn("Đấu bot dễ", labels)
            self.assertFalse(any(label.startswith("Lượt:") for label in labels))

    # Người chỉ được đi một nước; click đi/đặt tường khi tới lượt bot đều bị bỏ.
    def test_one_reply_and_no_human_input_on_bot_turn(self):
        start_game(self.app, self.menu, mode="bot", level="easy")
        self.click(self.cell(1, 4))
        self.assertTrue(self.game.is_bot_turn)
        self.click(self.cell(7, 4))
        wall_position = self.view.model_to_screen_point((self.view.board_x + 20, self.view.board_y + 62))
        self.click(wall_position)
        self.assertEqual(self.game.players[1].position, (8, 4))
        self.assertEqual(self.game.board.walls, [])
        self.assertIsNone(self.controller.get_wall_preview(wall_position))
        self.assertTrue(self.app.update_bot())
        self.assertEqual(self.game.current_turn, 0)
        self.assertEqual(self.game.players[1].position, (7, 4))
        self.assertFalse(self.app.update_bot())

    # Nước sai không gọi bot; đặt tường hợp lệ vẫn được bot đáp trả qua Command.
    def test_invalid_click_and_wall_response(self):
        start_game(self.app, self.menu, mode="bot", level="easy")
        self.click(self.cell(5, 5))
        self.assertFalse(self.app.update_bot())
        self.click(self.view.model_to_screen_point((self.view.board_x + 20, self.view.board_y + 62)))
        self.assertTrue(self.app.update_bot())
        self.assertEqual(self.game.wall_owners, {("horizontal", 0, 0): 0})
        self.assertEqual(self.game.players[0].walls_remaining, 9)
        self.assertEqual(self.game.current_turn, 0)

    # Chơi lại giữ chế độ bot; về menu không chạy bot và chuyển hai người bật lại giờ.
    def test_restart_back_and_switch_to_two_players(self):
        start_game(self.app, self.menu, mode="bot", level="easy")
        self.click(self.cell(1, 4))
        self.click(self.view.restart_rect(self.game).center)
        self.assertEqual(self.game.mode, "bot")
        self.assertFalse(self.game.timer_enabled)
        self.assertEqual(self.game.players[0].position, (0, 4))
        self.assertFalse(self.app.update_bot())
        self.click(self.cell(1, 4))
        self.click(self.view.menu_rect(self.game).center)
        self.assertFalse(self.app.update_bot())
        start_game(self.app, self.menu, mode="two_players", level="easy")
        self.assertTrue(self.game.timer_enabled)
        self.assertEqual(self.game.players[1].name, "Người chơi 2")
        self.now += 30
        self.assertTrue(self.app.update())
        self.assertEqual(self.game.current_turn, 1)
        self.assertFalse(self.app.update_bot())

    # Chạy main thật với hai click cùng khung hình; chỉ một nước bot được thực thi.
    def test_main_runs_bot_after_events(self):
        human = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=self.cell(1, 4))
        extra = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=self.cell(7, 4))
        main_path = Path(__file__).resolve().parents[1] / "main.py"
        with patch("game.game.Game", return_value=self.game), \
                patch("ui.game_view.GameView", return_value=self.view), \
                patch("ui.controller.GameController", return_value=self.controller), \
                patch("pygame.event.get", side_effect=[*menu_frames(self.menu), [human, extra],
                                                       [pygame.event.Event(pygame.QUIT)]]), \
                patch.object(self.controller.bot_strategy, "choose_command",
                             wraps=self.controller.bot_strategy.choose_command) as choose:
            runpy.run_path(str(main_path), run_name="__main__")
        choose.assert_called_once_with(self.game)
        self.assertEqual([p.position for p in self.game.players], [(1, 4), (7, 4)])
        self.assertEqual(self.game.current_turn, 0)


if __name__ == "__main__":
    unittest.main()
