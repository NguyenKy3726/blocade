from pattern.command.command import Command


# Lệnh di chuyển quân; luật hợp lệ vẫn do Game quyết định.
class MoveCommand(Command):
    # Lưu ô đích; chưa làm quân di chuyển khi tạo lệnh.
    def __init__(self, game, destination):
        super().__init__(game)
        self.destination = destination

    # Nhờ Game kiểm tra nước đi, giờ, chuyển lượt hoặc ghi nhận thắng.
    def _perform(self):
        return self.game.move_current_player(self.destination)
