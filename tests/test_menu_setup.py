import os
import tempfile
import unittest
from pathlib import Path
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
from ui.states import BotLevelState, BotTurnState, HumanTurnState, MenuState, TurnOrderState


# Kiểm tra font, các trang menu và chơi trước/sau qua giao diện thật headless.
class MenuSetupTests(unittest.TestCase):
    # Mỗi test dùng ván mới và đồng hồ giả, không phụ thuộc tốc độ máy.
    def setUp(self):
        self.now = 100.0
        self.game = Game(time_source=lambda: self.now)
        self.view = GameView()
        self.controller = GameController(self.game, self.view)
        self.menu = MenuView(self.view)
        self.app = AppController(self.controller, self.menu)

    # Giải phóng cửa sổ SDL sau từng tình huống.
    def tearDown(self):
        pygame.quit()

    # Gửi click trái qua AppController, giống cách main chuyển sự kiện.
    def click(self, rect):
        return self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))

    # Font vẫn nạp được khi chạy từ thư mục rỗng, không có Arial của Windows.
    def test_bundled_vietnamese_font_from_another_directory(self):
        previous = Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as directory:
                os.chdir(directory)
                with patch("pygame.font.Font", wraps=pygame.font.Font) as load_font:
                    view = GameView()
                for call in load_font.call_args_list:
                    font_path = Path(call.args[0])
                    self.assertTrue(font_path.is_absolute())
                    self.assertEqual(font_path.name, "NotoSans-Regular.ttf")
                    self.assertTrue(font_path.is_file())
                self.assertTrue(all(metric is not None for metric in
                                    view.font.metrics("ĐấủờễộệỵƯơ")))
                MenuView(view).draw()
        finally:
            os.chdir(previous)

    # Menu chính chỉ có hai cách chơi; chọn cấp chưa tự chạy bot hoặc tính giờ.
    def test_menu_hierarchy_and_no_game_before_order_choice(self):
        with patch.object(self.menu, "draw_button", wraps=self.menu.draw_button) as draw:
            self.app.draw()
            self.assertEqual([call.args[1] for call in draw.call_args_list],
                             ["Hai người chơi", "Đấu với máy", "Thoát"])
        self.click(self.menu.versus_bot_button_rect)
        self.assertIsInstance(self.app.state, BotLevelState)
        with patch.object(self.menu, "draw_button", wraps=self.menu.draw_button) as draw:
            self.app.draw()
            self.assertEqual([call.args[1] for call in draw.call_args_list],
                             ["Dễ", "Trung bình", "Khó", "Quay lại"])
        self.click(self.menu.medium_bot_button_rect)
        self.assertIsInstance(self.app.state, TurnOrderState)
        self.assertEqual(self.app.state.bot_level, "medium")
        self.now += 300
        before = self.game.capture_state()
        self.assertFalse(self.app.update())
        self.assertFalse(self.app.update_bot())
        self.assertEqual(self.game.capture_state(), before)
        self.app.draw()

    # Quay lại đúng trang trước; nút đang ẩn không có tác dụng trên trang chọn lượt.
    def test_back_navigation_and_hidden_buttons(self):
        self.click(self.menu.versus_bot_button_rect)
        self.click(self.menu.hard_bot_button_rect)
        order_state = self.app.state
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                   pos=self.menu.exit_button_rect.center)
        self.assertFalse(self.app.is_navigation_event(event))
        self.assertTrue(self.app.handle_event(event))
        self.assertIs(self.app.state, order_state)
        self.click(self.menu.back_button_rect)
        self.assertIsInstance(self.app.state, BotLevelState)
        self.click(self.menu.back_button_rect)
        self.assertIs(type(self.app.state), MenuState)
        self.click(self.menu.start_button_rect)
        self.assertIsInstance(self.app.state, TurnOrderState)
        self.click(self.menu.back_button_rect)
        self.assertIs(type(self.app.state), MenuState)

    # Cả ba cấp đều cho người ở dưới và bot mở đầu nếu người chọn chơi sau.
    def test_all_bot_levels_and_both_turn_orders(self):
        for level in ("easy", "medium", "hard"):
            for human_first in (True, False):
                with self.subTest(level=level, human_first=human_first):
                    self.app.screen = "menu"
                    start_game(self.app, self.menu, level=level, human_first=human_first)
                    self.assertEqual(self.game.bot_level, level)
                    self.assertEqual(self.game.current_turn, 0 if human_first else 1)
                    self.assertIsInstance(self.app.state, HumanTurnState if human_first else BotTurnState)
                    self.assertEqual([self.game.player_number(i) for i in range(2)],
                                     [1, 2] if human_first else [2, 1])
                    human, bot = self.game.players
                    self.assertGreater(self.view.cell_center(*human.position)[1],
                                       self.view.cell_center(*bot.position)[1])
                    self.assertEqual([human.goal_row, bot.goal_row], [8, 0])
                    self.assertIsNone(self.game.turn_started_at)
                    self.app.draw()
                    if not human_first:
                        # Giới hạn số khung để phát hiện bot không thực hiện được lượt đầu.
                        for _ in range(1000):
                            if self.app.update_bot():
                                break
                        else:
                            self.fail("Bot không hoàn tất lượt mở đầu")
                        self.assertEqual(self.game.current_turn, 0)
                        self.assertEqual(len(self.game.command_history), 1)
                        self.assertFalse(self.game.can_undo)

    # Đổi số trên quân theo lựa chọn, vẫn giữ màu xanh lá/xanh nước theo phe.
    def test_rendered_numbers_and_sidebar(self):
        for human_first in (True, False):
            self.game.reset(mode="bot", human_first=human_first)
            with patch.object(self.view, "small_font", wraps=self.view.small_font) as font:
                self.view.draw_players(self.game)
                self.assertEqual([call.args[0] for call in font.render.call_args_list],
                                 ["1", "2"] if human_first else ["2", "1"])
            with patch.object(self.view, "draw_text", wraps=self.view.draw_text) as text:
                self.view.draw_info(self.game)
                labels = [call.args[0] for call in text.call_args_list]
                self.assertEqual(sum(label == "Tường còn lại: 10" for label in labels), 2)
                self.assertFalse(any(label.startswith(("Vị trí:", "Lượt:")) for label in labels))

    # Hai người vẫn đếm đúng đồng hồ của bên số 1 khi bên dưới chọn chơi sau.
    def test_two_player_second_starts_correct_clock(self):
        start_game(self.app, self.menu, mode="two_players", human_first=False)
        self.assertEqual([p.name for p in self.game.players], ["Người chơi 2", "Người chơi 1"])
        self.assertEqual(self.game.current_turn, 1)
        self.now += 5
        self.app.update()
        self.assertEqual(self.game.time_remaining, [30, 25])
        self.now += 25
        self.assertTrue(self.app.update())
        self.assertEqual(self.game.current_turn, 0)
        self.assertIsNone(self.game.winner)

    # Chơi lại giữ thứ tự/cấp; Undo/Redo chỉ lùi cặp lượt, giữ nước bot mở đầu.
    def test_second_player_undo_redo_and_restart(self):
        start_game(self.app, self.menu, human_first=False)
        self.assertTrue(self.app.update_bot())
        opening_state = self.game.capture_state()
        opening_command = self.game.command_history[0]
        self.click(self.view.cell_rect(1, 4))
        self.assertTrue(self.app.update_bot())
        after_round = self.game.capture_state()
        self.click(self.view.undo_button_rect)
        self.assertEqual(self.game.capture_state(), opening_state)
        self.assertEqual(self.game.command_history, [opening_command])
        self.assertFalse(self.game.can_undo)
        self.click(self.view.redo_button_rect)
        self.assertEqual(self.game.capture_state(), after_round)
        self.assertFalse(self.app.update_bot())
        self.click(self.view.restart_button_rect)
        self.assertFalse(self.game.human_first)
        self.assertEqual(self.game.current_turn, 1)
        self.assertIsInstance(self.app.state, BotTurnState)
        self.assertEqual(self.game.command_history, [])
        self.assertEqual(self.game.redo_history, [])

    # Kiểm tra các mép ô, không chỉ tâm, để phép phản chiếu không lệch click.
    def test_all_cell_hitboxes_after_flipping_board(self):
        for row in range(9):
            for col in range(9):
                rect = self.view.cell_rect(row, col)
                for point in (rect.topleft, (rect.right - 1, rect.bottom - 1),
                              self.view.cell_center(row, col)):
                    self.assertEqual(self.view.cell_at_position(point), (row, col))
        self.assertIsNone(self.view.cell_at_position((self.view.board_x - 1, self.view.board_y)))
        self.assertIsNone(self.view.cell_at_position((self.view.board_x, self.view.board_y - 1)))

    # Click mỗi hướng tường sau phản chiếu phải đặt đúng tường, chặn đúng cạnh.
    def test_wall_clicks_and_rendering_after_flipping_board(self):
        for orientation in ("horizontal", "vertical"):
            for row in range(8):
                for col in range(8):
                    with self.subTest(orientation=orientation, row=row, col=col):
                        self.game.reset()
                        if orientation == "horizontal":
                            model_point = (self.view.board_x + col * 66 + 20,
                                           self.view.board_y + row * 66 + 62)
                            edge = ((row, col), (row + 1, col))
                        else:
                            model_point = (self.view.board_x + col * 66 + 62,
                                           self.view.board_y + row * 66 + 20)
                            edge = ((row, col), (row, col + 1))
                        point = self.view.model_to_screen_point(model_point)
                        self.assertEqual(self.view.wall_at_position(point), (orientation, row, col))
                        self.controller.handle_event(pygame.event.Event(
                            pygame.MOUSEBUTTONDOWN, button=1, pos=point))
                        self.assertEqual(self.game.board.walls, [(orientation, row, col)])
                        self.assertTrue(self.game.board.is_edge_blocked(*edge))
                        self.view.draw_walls(self.game)
                        self.assertEqual(tuple(self.view.screen.get_at(point))[:3],
                                         self.view.player_colors[0])


if __name__ == "__main__":
    unittest.main()
