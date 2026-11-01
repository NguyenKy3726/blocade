import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from game.game import Game
from tests.support import start_game
from ui.app_controller import AppController
from ui.controller import GameController
from ui.game_view import GameView
from ui.menu_view import MenuView


# Kiểm tra điều hướng thật giữa menu và bàn cờ trong cùng cửa sổ headless.
class MenuTests(unittest.TestCase):
    # Dùng giờ giả để kiểm tra menu không tiêu hao lượt dù chờ lâu.
    def setUp(self):
        self.now = 100.0
        self.game = Game(time_source=lambda: self.now)
        self.view = GameView()
        self.controller = GameController(self.game, self.view)
        self.menu = MenuView(self.view)
        self.app = AppController(self.controller, self.menu)

    # Giải phóng cửa sổ sau mỗi test.
    def tearDown(self):
        pygame.quit()

    # Tạo click trái hoặc phải và gửi qua lớp điều hướng.
    def click(self, position, button=1):
        return self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=button, pos=position))

    # Menu không gọi tính giờ hoặc tính hình xem trước tường.
    def test_initial_menu_does_not_run_game(self):
        self.assertEqual(self.app.screen, "menu")
        self.now += 120
        with patch.object(self.game, "update_time", wraps=self.game.update_time) as update, \
                patch.object(self.controller, "get_wall_preview") as preview, \
                patch.object(self.menu, "draw", wraps=self.menu.draw) as draw:
            self.assertFalse(self.app.update())
            self.app.draw()
            update.assert_not_called()
            preview.assert_not_called()
            draw.assert_called_once()
        self.assertEqual(self.game.current_turn, 0)
        self.assertEqual(self.game.time_remaining, [30, 30])

    # Chỉ click trái vào Hai người chơi mới bắt đầu và khởi động đồng hồ lượt đầu.
    def test_start_after_waiting_on_menu(self):
        self.now += 90
        self.click(self.menu.start_button_rect.center, button=3)
        self.click(self.view.model_to_screen_point((self.view.board_x + 20, self.view.board_y + 20)))
        self.assertEqual(self.app.screen, "menu")
        self.assertTrue(start_game(self.app, self.menu, mode="two_players", level="easy"))
        self.assertEqual(self.app.screen, "game")
        self.assertEqual(self.game.turn_started_at, self.now)
        self.now += 5
        self.assertFalse(self.app.update())
        self.assertEqual(self.game.time_remaining, [25, 30])
        self.app.draw()

    # Về menu trước/sau thắng hoặc tại hạn; vào lại luôn là ván mới đủ quân/tường/giờ.
    def test_back_to_menu_and_start_fresh(self):
        for state in ("playing", "winner", "timeout"):
            with self.subTest(state=state):
                start_game(self.app, self.menu, mode="two_players", level="easy")
                self.assertTrue(self.game.place_wall_current_player("horizontal", 2, 2))
                if state == "winner":
                    self.game.winner = self.game.players[0]
                if state == "timeout":
                    self.now += 30
                    self.assertTrue(self.app.update())
                self.assertTrue(self.click(self.view.menu_button_rect.center))
                self.assertEqual(self.app.screen, "menu")
                remaining = self.game.time_remaining.copy()
                self.now += 120
                self.assertFalse(self.app.update())
                self.app.draw()
                self.assertEqual(self.game.time_remaining, remaining)
                start_game(self.app, self.menu, mode="two_players", level="easy")
                self.assertEqual(self.app.screen, "game")
                self.assertEqual([p.position for p in self.game.players], [(0, 4), (8, 4)])
                self.assertEqual([p.walls_remaining for p in self.game.players], [10, 10])
                self.assertEqual(self.game.board.walls, [])
                self.assertEqual(self.game.board.blocked_edges, set())
                self.assertEqual(self.game.wall_owners, {})
                self.assertEqual(self.game.time_remaining, [30, 30])
                self.assertEqual(self.game.current_turn, 0)
                self.assertIsNone(self.game.winner)
                # Chuẩn bị màn hình menu cho tình huống kế tiếp.
                self.click(self.view.menu_button_rect.center)

    # Trong ván, AppController vẫn chuyển click cho Command và nút Chơi lại.
    def test_game_actions_and_restart_through_app(self):
        start_game(self.app, self.menu, mode="two_players", level="easy")
        self.click(self.view.model_to_screen_point((self.view.board_x + 4 * 66 + 20, self.view.board_y + 66 + 20)))
        self.assertEqual(self.game.players[0].position, (1, 4))
        self.assertEqual(self.game.current_turn, 1)
        self.now += 30
        self.assertTrue(self.app.update())
        self.click(self.view.restart_button_rect.center)
        self.assertEqual(self.app.screen, "game")
        self.assertEqual(self.game.players[0].position, (0, 4))
        self.assertEqual(self.game.time_remaining, [30, 30])

    # Nhận diện nút theo màn hình hiện tại và không coi click phải là điều hướng.
    def test_navigation_buttons_follow_screen(self):
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                   pos=self.menu.start_button_rect.center)
        self.assertTrue(self.app.is_navigation_event(event))
        event.button = 3
        self.assertFalse(self.app.is_navigation_event(event))
        start_game(self.app, self.menu, mode="two_players", level="easy")
        for rect in (self.view.restart_button_rect, self.view.menu_button_rect):
            event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)
            self.assertTrue(self.app.is_navigation_event(event))
        self.assertFalse(self.app.is_navigation_event(pygame.event.Event(pygame.QUIT)))

    # Thoát trên menu và nút đóng cửa sổ đều kết thúc vòng lặp ứng dụng.
    def test_exit_and_close(self):
        self.assertTrue(self.click(self.menu.exit_button_rect.center, button=3))
        self.assertFalse(self.click(self.menu.exit_button_rect.center))
        for screen in ("menu", "game"):
            self.app.screen = screen
            self.assertFalse(self.app.handle_event(pygame.event.Event(pygame.QUIT)))


if __name__ == "__main__":
    unittest.main()
