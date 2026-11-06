from pattern.command.command import Command


# Lệnh đặt tường; Game vẫn kiểm tra hình học và BFS.
class PlaceWallCommand(Command):
    # Lưu hướng và điểm neo; không tự sửa bàn cờ hay số tường.
    def __init__(self, game, orientation, row, col):
        super().__init__(game)
        self.orientation = orientation
        self.row = row
        self.col = col

    # Nhờ Game kiểm tra tường, BFS và số tường trước khi cập nhật ván.
    def _perform(self):
        return self.game.place_wall_current_player(self.orientation, self.row, self.col)
