import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from game.game import Game
from game.commands import MoveCommand, PlaceWallCommand
from ui.controller import GameController
from ui.game_view import GameView
from ui.menu_view import MenuView


# Cung cấp thời gian giả để kiểm tra mốc 30 giây ngay lập tức.
class FakeClock:
    # Bắt đầu ở mốc thời gian cố định.
    def __init__(self):
        self.now = 100.0

    # Cho phép truyền đối tượng này vào Game như một hàm lấy giờ.
    def __call__(self):
        return self.now


# Kiểm tra thời gian, chủ sở hữu tường và các luật chịu ảnh hưởng.
class TurnTests(unittest.TestCase):
    # Tạo ván mới và đồng hồ riêng cho mỗi phép kiểm tra.
    def setUp(self):
        self.clock = FakeClock()
        self.game = Game(time_source=self.clock)

    # Chỉ bên đang đi mất thời gian; nước đi hợp lệ cấp 30 giây cho bên kia.
    def test_active_clock_and_move(self):
        self.clock.now += 12
        self.assertFalse(self.game.update_time())
        self.assertEqual(self.game.time_remaining, [18, 30])
        self.assertTrue(self.game.move_current_player((1, 4)))
        self.clock.now += 5
        self.game.update_time()
        self.assertEqual(self.game.time_remaining, [18, 25])
        self.assertTrue(self.game.move_current_player((7, 4)))
        self.assertEqual(self.game.time_remaining, [30, 25])

    # Hết giờ chỉ chuyển lượt một lần, không đổi quân hay số tường.
    def test_timeout_passes_without_losing(self):
        self.clock.now += 30
        self.assertTrue(self.game.update_time())
        self.assertEqual(self.game.current_turn, 1)
        self.assertIsNone(self.game.winner)
        self.assertEqual(self.game.players[0].position, (0, 4))
        self.assertEqual(self.game.players[0].walls_remaining, 10)
        self.assertEqual(self.game.time_remaining, [0, 30])
        self.assertFalse(self.game.update_time())

    # Click tại đúng hạn bị bỏ, không được thực hiện cho người mới tới lượt.
    def test_late_actions_are_rejected(self):
        for action in (lambda g: g.move_current_player((1, 4)),
                       lambda g: g.place_wall_current_player("horizontal", 2, 2)):
            game = Game(time_source=self.clock)
            self.clock.now += 30
            self.assertFalse(action(game))
            self.assertEqual(game.current_turn, 1)
            self.assertEqual(game.board.walls, [])

    # Nước sai không cấp lại thời gian và không chuyển lượt.
    def test_invalid_action_keeps_clock(self):
        self.clock.now += 10
        self.assertFalse(self.game.move_current_player((5, 5)))
        self.assertFalse(self.game.place_wall_current_player("horizontal", 8, 8))
        self.assertEqual(self.game.current_turn, 0)
        self.assertEqual(self.game.time_remaining[0], 20)

    # Xem trước không ghi chủ sở hữu; tường thành công giữ đúng phe sau đổi lượt.
    def test_wall_ownership_and_rejection(self):
        self.assertTrue(self.game.can_place_wall_current_player("horizontal", 2, 2))
        self.assertEqual(self.game.wall_owners, {})
        self.assertEqual(self.game.board.walls, [])
        self.assertTrue(self.game.place_wall_current_player("horizontal", 2, 2))
        self.assertTrue(self.game.place_wall_current_player("vertical", 5, 5))
        self.assertEqual(self.game.wall_owners,
                         {("horizontal", 2, 2): 0, ("vertical", 5, 5): 1})
        self.assertFalse(self.game.place_wall_current_player("vertical", 2, 2))
        self.assertFalse(self.game.place_wall_current_player("horizontal", 2, 3))
        self.assertEqual([p.walls_remaining for p in self.game.players], [9, 9])

    # Tường khóa quân ở góc bị BFS từ chối và không để lại dữ liệu thử.
    def test_bfs_rejection_restores_state(self):
        self.game.players[0].row, self.game.players[0].col = 0, 0
        self.assertTrue(self.game.place_wall_current_player("horizontal", 0, 0))
        before = (list(self.game.board.walls), set(self.game.board.blocked_edges),
                  dict(self.game.wall_owners))
        self.assertFalse(self.game.place_wall_current_player("vertical", 0, 1))
        self.assertEqual(before, (self.game.board.walls, self.game.board.blocked_edges,
                                  self.game.wall_owners))
        self.assertEqual(self.game.current_turn, 1)
        self.assertEqual(self.game.players[1].walls_remaining, 10)

    # Các nhánh nhảy thẳng và nhảy chéo vẫn tuân theo tường và mép bàn.
    def test_jumps(self):
        red, blue = self.game.players
        red.row, red.col = 4, 4
        blue.row, blue.col = 5, 4
        self.assertIn((6, 4), self.game.get_legal_moves())
        self.assertNotIn((5, 3), self.game.get_legal_moves())
        self.game.board.place_wall("horizontal", 5, 4)
        self.assertNotIn((6, 4), self.game.get_legal_moves())
        self.assertTrue({(5, 3), (5, 5)} <= set(self.game.get_legal_moves()))
        red.row, blue.row = 7, 8
        self.assertTrue({(8, 3), (8, 5)} <= set(self.game.get_legal_moves()))

    # Thắng ván dừng cả đồng hồ và mọi hành động tiếp theo.
    def test_winner_stops_time(self):
        self.game.players[0].row = 7
        self.game.players[1].col = 0
        self.clock.now += 4
        self.assertTrue(self.game.move_current_player((8, 4)))
        remaining = self.game.time_remaining.copy()
        self.clock.now += 100
        self.assertFalse(self.game.update_time())
        self.assertEqual(self.game.time_remaining, remaining)
        self.assertFalse(self.game.place_wall_current_player("horizontal", 2, 2))


# Kiểm tra tương tác chuột và màu pixel bằng SDL không cần màn hình.
class MouseTests(unittest.TestCase):
    # Khởi tạo giao diện thật để kiểm tra cả tọa độ và quá trình vẽ.
    def setUp(self):
        self.clock = FakeClock()
        self.game = Game(time_source=self.clock)
        self.view = GameView()
        self.controller = GameController(self.game, self.view)

    # Giải phóng tài nguyên sau từng phép kiểm tra.
    def tearDown(self):
        pygame.quit()

    # Đổi tọa độ tương đối trên bàn thành tọa độ cửa sổ.
    def position(self, x, y):
        return self.view.board_x + x, self.view.board_y + y

    # Gửi click trái giống thao tác người chơi.
    def click(self, position):
        self.controller.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=position))

    # Đặt hai hướng liên tiếp bằng chuột, không nhấn H/V; kiểm tra màu đã vẽ.
    def test_mouse_walls_and_colors(self):
        horizontal = self.position(20, 62)
        vertical = self.position(2 * 66 + 62, 2 * 66 + 20)
        self.assertEqual(self.controller.get_wall_preview(horizontal),
                         ("horizontal", 0, 0, True))
        self.click(horizontal)
        self.assertEqual(self.game.current_turn, 1)
        self.assertFalse(self.controller.get_wall_preview(horizontal)[3])
        self.click(horizontal)
        self.assertEqual(self.game.current_turn, 1)
        self.click(vertical)
        self.assertEqual(self.game.current_turn, 0)
        self.view.draw(self.game)
        for wall, owner in self.game.wall_owners.items():
            pixel = self.view.screen.get_at(self.view._wall_rect(*wall).center)
            self.assertEqual(tuple(pixel)[:3], self.view.player_colors[owner])

    # Giao điểm chọn theo khoảng cách; ngoài bàn không được nhận làm tường.
    def test_intersections_and_edges(self):
        self.assertIsNone(self.view.wall_at_position(self.position(62, 62)))
        self.assertEqual(self.view.wall_at_position(self.position(60, 62))[0], "horizontal")
        self.assertEqual(self.view.wall_at_position(self.position(62, 60))[0], "vertical")
        self.assertEqual(self.view.wall_at_position(self.position(8 * 66 + 20, 62)),
                         ("horizontal", 0, 7))
        self.assertEqual(self.view.wall_at_position(self.position(62, 8 * 66 + 20)),
                         ("vertical", 7, 0))
        for position in [(-1, 0), (586, 0), (0, 586), (20, 20)]:
            self.assertIsNone(self.view.wall_at_position(self.position(*position)))

    # Hết giờ xóa lựa chọn cũ; click tại hạn không đặt tường cho bên kia.
    def test_timeout_clears_selection(self):
        self.controller.selected_position = (0, 4)
        self.clock.now += 30
        self.click(self.position(20, 62))
        self.assertIsNone(self.controller.selected_position)
        self.assertEqual(self.game.board.walls, [])
        self.assertEqual(self.game.current_turn, 1)

    # Màu xem trước hợp lệ theo phe đang đi, nhạt hơn tường thật; sai luôn đỏ.
    def test_team_preview_colors(self):
        wall = ("horizontal", 2, 2)
        center = self.view._wall_rect(*wall).center
        for turn in (0, 1):
            self.game.current_turn = turn
            self.view.draw(self.game, wall_preview=(*wall, True))
            pixel = tuple(self.view.screen.get_at(center))[:3]
            self.assertEqual(pixel, self.view.wall_preview_colors[turn])
            self.assertTrue(all(light > base for light, base in
                                zip(pixel, self.view.player_colors[turn])))
            self.view.draw(self.game, wall_preview=(*wall, False))
            self.assertEqual(tuple(self.view.screen.get_at(center))[:3], (190, 65, 55))

    # Kiểm tra các chấm gợi ý thật sự được vẽ mà không có quân được chọn.
    def assert_visible_moves(self):
        self.assertIsNone(self.controller.selected_position)
        self.view.draw(self.game)
        for row, col in self.game.get_legal_moves():
            center = self.position(col * 66 + 29, row * 66 + 29)
            expected_color = [(85, 145, 90), (40, 120, 190)][self.game.current_turn]
            self.assertEqual(tuple(self.view.screen.get_at(center))[:3], expected_color)

    # Click một lần để đi; gợi ý cập nhật sau nước đi, tường và mất lượt.
    def test_direct_move_and_automatic_hints(self):
        self.assert_visible_moves()
        self.click(self.position(4 * 66 + 20, 66 + 20))
        self.assertEqual(self.game.players[0].position, (1, 4))
        self.assertEqual(self.game.current_turn, 1)
        self.assert_visible_moves()
        self.click(self.position(20, 62))
        self.assertEqual(self.game.current_turn, 0)
        self.assert_visible_moves()
        self.clock.now += 30
        self.controller.update()
        self.assertEqual(self.game.current_turn, 1)
        self.assert_visible_moves()

    # Click ngoài bàn hoặc vào ô sai không di chuyển; kết thúc ván bỏ gợi ý.
    def test_invalid_click_and_finished_game(self):
        for position in [(-20, -20), (20, 4 * 66 + 20)]:
            self.click(self.position(*position))
        self.assertEqual(self.game.current_turn, 0)
        self.assertEqual(self.game.players[0].position, (0, 4))
        old_moves = self.game.get_legal_moves()
        self.game.winner = self.game.players[0]
        self.view.draw(self.game)
        for row, col in old_moves:
            center = self.position(col * 66 + 29, row * 66 + 29)
            self.assertNotEqual(tuple(self.view.screen.get_at(center))[:3], (85, 145, 90))
        self.click(self.position(4 * 66 + 20, 66 + 20))
        self.assertEqual(self.game.players[0].position, (0, 4))

    # Kiểm tra toàn bộ trạng thái ban đầu và cửa sổ được giữ sau khi chơi lại.
    def assert_restarted(self):
        self.assertIs(self.controller.game, self.game)
        self.assertEqual([p.position for p in self.game.players], [(0, 4), (8, 4)])
        self.assertEqual([p.walls_remaining for p in self.game.players], [10, 10])
        self.assertEqual(self.game.board.walls, [])
        self.assertEqual(self.game.board.blocked_edges, set())
        self.assertEqual(self.game.wall_owners, {})
        self.assertEqual(self.game.current_turn, 0)
        self.assertIsNone(self.game.winner)
        self.assertEqual(self.game.time_remaining, [30, 30])
        self.assertEqual(self.game.turn_started_at, self.clock.now)
        self.assertEqual(self.game.notice, "")
        self.assertIsNone(self.controller.selected_position)
        self.assertIs(pygame.display.get_surface(), self.view.screen)
        self.assert_visible_moves()

    # Chơi lại giữa ván xóa tường, lựa chọn cũ và mốc giờ; ván mới vẫn chơi được.
    def test_restart_during_game(self):
        self.assertTrue(self.game.place_wall_current_player("horizontal", 2, 2))
        self.assertTrue(self.game.move_current_player((7, 4)))
        self.controller.selected_position = (0, 4)
        self.clock.now += 12
        self.controller.update()
        self.click(self.view.restart_button_rect.center)
        self.assert_restarted()
        self.clock.now += 3
        self.controller.update()
        self.assertEqual(self.game.time_remaining, [27, 30])
        self.click(self.position(4 * 66 + 20, 66 + 20))
        self.assertEqual(self.game.players[0].position, (1, 4))
        self.assertEqual(self.game.current_turn, 1)

    # Nút luôn được vẽ và nhận click sau thắng ván hoặc hết giờ; bấm nhiều lần an toàn.
    def test_restart_after_win_or_timeout(self):
        for finished in (False, True):
            with self.subTest(finished=finished):
                if finished:
                    self.game.players[0].row = 7
                    self.game.players[1].col = 0
                    self.assertTrue(self.game.move_current_player((8, 4)))
                self.clock.now += 30
                self.view.draw(self.game)
                rect = self.view.restart_button_rect
                self.assertNotEqual(tuple(self.view.screen.get_at((rect.left + 10, rect.top + 10)))[:3],
                                    self.view.background_color)
                self.click(rect.center)
                self.assert_restarted()
                self.click(rect.center)
                self.assert_restarted()

    # Chỉ click trái bên trong nút mới chơi lại; ngoài nút hoặc chuột phải không reset.
    def test_restart_button_hit_area(self):
        self.assertTrue(self.game.move_current_player((1, 4)))
        rect = self.view.restart_button_rect
        self.controller.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=3, pos=rect.center))
        self.click((rect.right, rect.bottom))
        self.assertEqual(self.game.players[0].position, (1, 4))
        self.assertEqual(self.game.current_turn, 1)

    # Chạy main thật: vào từ menu, chơi lại và bỏ click còn từ ván cũ.
    def test_main_menu_start_restart_discards_old_clicks(self):
        self.assertTrue(self.game.place_wall_current_player("horizontal", 2, 2))
        self.clock.now += 30
        start = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                   pos=MenuView(self.view).start_button_rect.center)
        restart = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                     pos=self.view.restart_button_rect.center)
        old_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                       pos=self.position(20, 62))
        quit_event = pygame.event.Event(pygame.QUIT)
        main_path = Path(__file__).resolve().parents[1] / "main.py"
        with patch("game.game.Game", return_value=self.game), \
                patch("ui.game_view.GameView", return_value=self.view), \
                patch("pygame.event.get", side_effect=[[start], [restart, old_click], [quit_event]]), \
                patch.object(self.view, "draw", wraps=self.view.draw) as draw:
            result = runpy.run_path(str(main_path), run_name="__main__")
        self.assertEqual(self.game.board.walls, [])
        self.assertEqual(self.game.time_remaining, [30, 30])
        self.assertEqual(self.game.current_turn, 0)
        self.assertEqual(self.game.notice, "")
        self.assertEqual(draw.call_count, 2)
        self.assertIs(draw.call_args.args[0], self.game)
        self.assertIs(result["controller"].game, self.game)

    # Click phải qua đúng Command; di chuyển và đặt tường vẫn đổi lượt một lần.
    def test_controller_executes_commands(self):
        with patch("ui.controller.MoveCommand", wraps=MoveCommand) as move, \
                patch("ui.controller.PlaceWallCommand", wraps=PlaceWallCommand) as wall:
            self.click(self.position(4 * 66 + 20, 66 + 20))
            move.assert_called_once_with(self.game, (1, 4))
            wall.assert_not_called()
            self.assertEqual(self.game.players[0].position, (1, 4))
            self.assertEqual(self.game.current_turn, 1)
            self.click(self.position(20, 62))
            wall.assert_called_once_with(self.game, "horizontal", 0, 0)
            self.assertEqual(self.game.current_turn, 0)
            self.assertEqual(self.game.wall_owners, {("horizontal", 0, 0): 1})

    # H/V/Esc không khóa hướng, đổi lượt hoặc cản xem trước bằng chuột nữa.
    def test_keyboard_does_not_lock_wall_direction(self):
        horizontal = self.position(20, 62)
        vertical = self.position(2 * 66 + 62, 2 * 66 + 20)
        for key in (pygame.K_h, pygame.K_v, pygame.K_ESCAPE):
            self.controller.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))
            self.assertEqual(self.controller.get_wall_preview(horizontal),
                             ("horizontal", 0, 0, True))
            self.assertEqual(self.controller.get_wall_preview(vertical),
                             ("vertical", 2, 2, True))
            self.assertEqual(self.game.current_turn, 0)
            self.assertEqual(self.game.board.walls, [])
        self.click(vertical)
        self.click(horizontal)
        self.assertEqual(self.game.board.walls,
                         [("vertical", 2, 2), ("horizontal", 0, 0)])

    # Xem trước chỉ kiểm tra luật, không được tạo hay thực thi Command.
    def test_preview_does_not_execute_commands(self):
        with patch("ui.controller.MoveCommand") as move, \
                patch("ui.controller.PlaceWallCommand") as wall:
            self.assertTrue(self.controller.get_wall_preview(self.position(20, 62))[3])
            move.assert_not_called()
            wall.assert_not_called()
        self.assertEqual(self.game.board.walls, [])
        self.assertEqual(self.game.current_turn, 0)


if __name__ == "__main__":
    unittest.main()
