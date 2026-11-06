import unittest

from game.board import Board
from game.game import Game


# Rà luật bằng các tình huống cố định, không cần Pygame hay chờ đồng hồ thật.
class GameRulesTests(unittest.TestCase):
    # Tạo ván có thời gian đứng yên để chỉ kiểm tra luật bàn cờ.
    def new_game(self):
        return Game(time_source=lambda: 100.0)

    # Xoay ô 90 độ để cùng một tình huống được kiểm tra ở cả bốn hướng.
    def rotate_cell(self, cell, turns):
        row, col = cell
        for _ in range(turns):
            row, col = col, 8 - row
        return row, col

    # Xoay hướng và điểm neo tường tương ứng với phép xoay các ô.
    def rotate_wall(self, wall, turns):
        orientation, row, col = wall
        for _ in range(turns):
            orientation = "vertical" if orientation == "horizontal" else "horizontal"
            row, col = col, 7 - row
        return orientation, row, col

    # Chụp trạng thái luật để phát hiện việc thử hoặc từ chối tường làm đổi ván.
    def snapshot(self, game):
        return (
            list(game.board.walls), set(game.board.blocked_edges),
            dict(game.wall_owners), game.current_turn, game.winner,
            [(p.position, p.walls_remaining) for p in game.players],
            list(game.time_remaining), game.turn_started_at,
        )

    # Đi bốn hướng ở giữa bàn, chỉ đi vào trong tại các góc, không tự đi chéo.
    def test_ordinary_moves_and_corners(self):
        cases = [
            ((4, 4), {(3, 4), (5, 4), (4, 3), (4, 5)}),
            ((0, 0), {(0, 1), (1, 0)}),
            ((0, 8), {(0, 7), (1, 8)}),
            ((8, 0), {(7, 0), (8, 1)}),
            ((8, 8), {(7, 8), (8, 7)}),
        ]
        for position, expected in cases:
            with self.subTest(position=position):
                game = self.new_game()
                game.players[0].row, game.players[0].col = position
                game.players[1].row, game.players[1].col = 2, 2
                self.assertEqual(set(game.get_legal_moves()), expected)

    # Nhảy thẳng khi được phép; chỉ đi chéo nếu sau đối thủ bị chặn hoặc hết bàn.
    def test_jumps_in_all_four_directions(self):
        cases = [
            ("straight", (4, 4), (5, 4), [],
             {(3, 4), (4, 3), (4, 5), (6, 4)}),
            ("wall_behind", (4, 4), (5, 4), [("horizontal", 5, 4)],
             {(3, 4), (4, 3), (4, 5), (5, 3), (5, 5)}),
            ("one_diagonal_blocked", (4, 4), (5, 4),
             [("horizontal", 5, 4), ("vertical", 4, 3)],
             {(3, 4), (4, 5), (5, 5)}),
            ("wall_between_players", (4, 4), (5, 4), [("horizontal", 4, 4)],
             {(3, 4), (4, 3), (4, 5)}),
            ("edge", (7, 4), (8, 4), [],
             {(6, 4), (7, 3), (7, 5), (8, 3), (8, 5)}),
            ("corner", (7, 0), (8, 0), [], {(6, 0), (7, 1), (8, 1)}),
        ]
        for name, first, second, walls, expected in cases:
            for turns in range(4):
                with self.subTest(case=name, rotation=turns):
                    game = self.new_game()
                    for player, cell in zip(game.players, (first, second)):
                        player.row, player.col = self.rotate_cell(cell, turns)
                    for wall in walls:
                        self.assertTrue(game.board.place_wall(*self.rotate_wall(wall, turns)))
                    moves = game.get_legal_moves()
                    self.assertEqual(set(moves), {self.rotate_cell(c, turns) for c in expected})
                    self.assertEqual(len(moves), len(set(moves)))
                    self.assertNotIn(game.players[1].position, moves)

    # Tường chặn bước đi từ cả hai phía; không được đi xuyên hay nhảy qua tường.
    def test_wall_blocks_both_directions(self):
        for turns in range(4):
            with self.subTest(rotation=turns):
                game = self.new_game()
                wall = self.rotate_wall(("horizontal", 3, 3), turns)
                self.assertTrue(game.board.place_wall(*wall))
                first = self.rotate_cell((3, 3), turns)
                second = self.rotate_cell((4, 3), turns)
                for origin, target in [(first, second), (second, first)]:
                    game.players[0].row, game.players[0].col = origin
                    game.players[1].row, game.players[1].col = 0, 0
                    self.assertNotIn(target, game.get_legal_moves())
                    before = self.snapshot(game)
                    self.assertFalse(game.move_current_player(target))
                    self.assertEqual(self.snapshot(game), before)

    # Hai hướng đều đặt được ở bốn góc vùng neo; ngoài vùng 0..7 bị từ chối.
    def test_wall_anchor_bounds(self):
        for orientation in ("horizontal", "vertical"):
            for row in (0, 7):
                for col in (0, 7):
                    with self.subTest(orientation=orientation, anchor=(row, col)):
                        board = Board()
                        self.assertTrue(board.place_wall(orientation, row, col))
                        self.assertEqual(len(board.blocked_edges), 2)
                        self.assertTrue(board.remove_wall(orientation, row, col))
                        self.assertEqual(board.blocked_edges, set())
            for row, col in [(-1, 0), (0, -1), (8, 0), (0, 8), (9, 9)]:
                with self.subTest(orientation=orientation, anchor=(row, col)):
                    game = self.new_game()
                    before = self.snapshot(game)
                    self.assertFalse(game.place_wall_current_player(orientation, row, col))
                    self.assertEqual(self.snapshot(game), before)
        self.assertFalse(Board().place_wall("diagonal", 3, 3))

    # Cấm chồng cả tường, chồng một cạnh và cắt giữa; cho phép nối tiếp hoặc chạm đầu.
    def test_overlapping_crossing_and_touching_walls(self):
        forbidden = [("horizontal", 3, 3), ("horizontal", 3, 2),
                     ("horizontal", 3, 4), ("vertical", 3, 3)]
        allowed = [("horizontal", 3, 1), ("horizontal", 3, 5),
                   ("horizontal", 2, 3), ("vertical", 2, 3), ("vertical", 4, 3)]
        for turns in (0, 1):
            for wall in forbidden + allowed:
                with self.subTest(rotation=turns, wall=wall):
                    board = Board()
                    self.assertTrue(board.place_wall(*self.rotate_wall(("horizontal", 3, 3), turns)))
                    self.assertEqual(board.place_wall(*self.rotate_wall(wall, turns)), wall in allowed)

    # Cấm khóa đường của bất cứ phe nào, dù đó là người đang đi hay đối thủ.
    def test_bfs_protects_each_player_on_either_turn(self):
        cases = [
            (0, (0, 0), ("horizontal", 0, 0), ("vertical", 0, 1)),
            (1, (8, 8), ("horizontal", 7, 7), ("vertical", 7, 6)),
        ]
        for trapped, position, first_wall, closing_wall in cases:
            for turn in (0, 1):
                with self.subTest(trapped=trapped, turn=turn):
                    game = self.new_game()
                    game.players[trapped].row, game.players[trapped].col = position
                    self.assertTrue(game.place_wall_current_player(*first_wall))
                    game.current_turn = turn
                    before = self.snapshot(game)
                    self.assertFalse(game.can_place_wall_current_player(*closing_wall))
                    self.assertEqual(self.snapshot(game), before)
                    self.assertFalse(game.place_wall_current_player(*closing_wall))
                    self.assertEqual(self.snapshot(game), before)
                    # Chứng minh đúng là BFS từ chối, không phải tường chồng/cắt.
                    self.assertTrue(game.board.place_wall(*closing_wall))
                    self.assertFalse(game.path_finder.has_path(game.board, position,
                                                               game.players[trapped].goal_row))

    # Thử toàn bộ 128 tường sau một tường thật không làm đổi bàn, lượt, màu hay số tường.
    def test_all_previews_leave_game_unchanged(self):
        game = self.new_game()
        self.assertTrue(game.place_wall_current_player("horizontal", 3, 3))
        before = self.snapshot(game)
        for orientation in ("horizontal", "vertical"):
            for row in range(8):
                for col in range(8):
                    with self.subTest(wall=(orientation, row, col)):
                        game.can_place_wall_current_player(orientation, row, col)
                        self.assertEqual(self.snapshot(game), before)

    # Đặt đủ 10 tường mỗi bên; tường thứ 11 bị từ chối nhưng vẫn được đi quân.
    def test_wall_inventory_cannot_go_negative(self):
        game = self.new_game()
        candidates = [(orientation, row, col)
                      for orientation in ("horizontal", "vertical")
                      for row in range(8) for col in range(8)]
        for _ in range(20):
            wall = next((candidate for candidate in candidates
                         if game.can_place_wall_current_player(*candidate)), None)
            self.assertIsNotNone(wall)
            self.assertTrue(game.place_wall_current_player(*wall))
        self.assertEqual([p.walls_remaining for p in game.players], [0, 0])
        before = self.snapshot(game)
        self.assertFalse(game.can_place_wall_current_player("vertical", 7, 7))
        self.assertFalse(game.place_wall_current_player("vertical", 7, 7))
        self.assertEqual(self.snapshot(game), before)
        self.assertTrue(game.move_current_player(game.get_legal_moves()[0]))
        self.assertEqual(game.current_turn, 1)

    # Chơi từ đầu tới hàng đích cho từng phe rồi kiểm tra ván đã khóa mọi hành động.
    def test_complete_games_for_both_winners(self):
        for winner in (0, 1):
            with self.subTest(winner=winner):
                game = self.new_game()
                for step in range(8):
                    if winner == 1:
                        self.assertTrue(game.move_current_player((0, 5 if step % 2 == 0 else 6)))
                    destination = (step + 1, 4) if winner == 0 else (7 - step, 4)
                    self.assertTrue(game.move_current_player(destination))
                    if winner == 0 and step < 7:
                        self.assertTrue(game.move_current_player((8, 5 if step % 2 == 0 else 6)))
                self.assertIs(game.winner, game.players[winner])
                before = self.snapshot(game)
                self.assertEqual(game.get_legal_moves(), [])
                self.assertFalse(game.move_current_player((4, 4)))
                self.assertFalse(game.place_wall_current_player("horizontal", 3, 3))
                self.assertFalse(game.update_time())
                self.assertEqual(self.snapshot(game), before)


if __name__ == "__main__":
    unittest.main()
