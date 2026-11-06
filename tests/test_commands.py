import unittest

from pattern.command import Command, CommandInvoker, MoveCommand, PlaceWallCommand
from game.game import Game


# Kiểm tra Command thực thi luật thật, không tự sửa dữ liệu hoặc đổi lượt hai lần.
class CommandTests(unittest.TestCase):
    # Tạo đồng hồ điều khiển được để kiểm tra hạn 30 giây mà không phải chờ.
    def setUp(self):
        self.now = 100.0
        self.game = Game(time_source=lambda: self.now)

    # Kiểm tra các vai trò Command và việc Invoker gọi ConcreteCommand.
    def test_command_roles_match_pattern(self):
        self.assertTrue(hasattr(Command, "execute"))
        invoker = CommandInvoker()
        self.assertFalse(invoker.execute())
        command = MoveCommand(self.game, (1, 4))
        self.assertIs(command.receiver, self.game)
        self.assertTrue(invoker.execute(command))
        self.assertIs(invoker.command, command)
        self.assertEqual(self.game.players[0].position, (1, 4))

    # Chụp trạng thái có thể bị ảnh hưởng khi thực hiện một lệnh.
    def snapshot(self):
        return ([(p.position, p.walls_remaining) for p in self.game.players],
                list(self.game.board.walls), set(self.game.board.blocked_edges),
                dict(self.game.wall_owners), self.game.current_turn, self.game.winner,
                list(self.game.time_remaining))

    # Tạo lệnh chưa đi quân; thực thi nước hợp lệ mới di chuyển và đổi lượt một lần.
    def test_move_creation_execution_and_rejection(self):
        before = self.snapshot()
        command = MoveCommand(self.game, (1, 4))
        self.assertEqual(self.snapshot(), before)
        self.assertTrue(command.execute())
        self.assertEqual(self.game.players[0].position, (1, 4))
        self.assertEqual(self.game.current_turn, 1)
        before = self.snapshot()
        self.assertFalse(MoveCommand(self.game, (4, 4)).execute())
        self.assertEqual(self.snapshot(), before)

    # Đặt tường qua Command vẫn giữ đúng phe, số tường và chống chồng/cắt.
    def test_wall_creation_execution_and_rejection(self):
        before = self.snapshot()
        command = PlaceWallCommand(self.game, "horizontal", 3, 3)
        self.assertEqual(self.snapshot(), before)
        self.assertTrue(command.execute())
        self.assertEqual(self.game.wall_owners, {("horizontal", 3, 3): 0})
        self.assertEqual(self.game.players[0].walls_remaining, 9)
        self.assertEqual(self.game.current_turn, 1)
        before = self.snapshot()
        for wall in [("horizontal", 3, 3), ("horizontal", 3, 4), ("vertical", 3, 3)]:
            self.assertFalse(PlaceWallCommand(self.game, *wall).execute())
            self.assertEqual(self.snapshot(), before)

    # Command không được bỏ qua BFS hoặc cho đặt thêm khi đã hết tường.
    def test_wall_bfs_and_inventory(self):
        self.game.players[0].row, self.game.players[0].col = 0, 0
        self.assertTrue(PlaceWallCommand(self.game, "horizontal", 0, 0).execute())
        before = self.snapshot()
        self.assertFalse(PlaceWallCommand(self.game, "vertical", 0, 1).execute())
        self.assertEqual(self.snapshot(), before)
        self.game.current_player.walls_remaining = 0
        before = self.snapshot()
        self.assertFalse(PlaceWallCommand(self.game, "vertical", 4, 4).execute())
        self.assertEqual(self.snapshot(), before)

    # Hai lệnh đều kiểm tra lại giờ lúc execute, không dùng kết quả cũ khi tạo lệnh.
    def test_commands_respect_timeout(self):
        for command_type, arguments in [(MoveCommand, ((1, 4),)),
                                        (PlaceWallCommand, ("horizontal", 3, 3))]:
            with self.subTest(command=command_type.__name__):
                self.game.reset()
                command = command_type(self.game, *arguments)
                self.now += 30
                self.assertFalse(command.execute())
                self.assertEqual(self.game.current_turn, 1)
                self.assertEqual(self.game.players[0].position, (0, 4))
                self.assertEqual(self.game.board.walls, [])
                self.assertEqual(self.game.players[0].walls_remaining, 10)

    # Đi nhảy thẳng hoặc chéo qua Command vẫn do luật hiện tại của Game quyết định.
    def test_commands_keep_jump_rules(self):
        for blocked, destination in [(False, (6, 4)), (True, (5, 3))]:
            with self.subTest(blocked=blocked):
                self.game.reset()
                self.game.players[0].row, self.game.players[0].col = 4, 4
                self.game.players[1].row, self.game.players[1].col = 5, 4
                if blocked:
                    self.assertTrue(self.game.board.place_wall("horizontal", 5, 4))
                self.assertTrue(MoveCommand(self.game, destination).execute())
                self.assertEqual(self.game.players[0].position, destination)
                self.assertEqual(self.game.current_turn, 1)

    # Command ghi nhận thắng và từ chối cả hai hành động sau khi ván kết thúc.
    def test_commands_respect_game_over(self):
        self.game.players[0].row = 7
        self.game.players[1].col = 0
        self.assertTrue(MoveCommand(self.game, (8, 4)).execute())
        self.assertIs(self.game.winner, self.game.players[0])
        before = self.snapshot()
        self.assertFalse(MoveCommand(self.game, (7, 4)).execute())
        self.assertFalse(PlaceWallCommand(self.game, "horizontal", 3, 3).execute())
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
