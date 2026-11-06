from pattern.command.command import Command


# Lệnh di chuyển quân; luật hợp lệ vẫn do Game quyết định.
class MoveCommand(Command):
    # Lưu ô đích; chưa làm quân di chuyển khi tạo lệnh.
    def __init__(self, receiver, destination):
        super().__init__(receiver)
        self.destination = destination

    # Triển khai ICommand.execute và giao luật di chuyển cho Receiver là Game.
    def execute(self):
        return self._execute_action(self._perform)

    # Nhờ Game kiểm tra nước đi, giờ, chuyển lượt hoặc ghi nhận thắng.
    def _perform(self):
        return self.receiver.move_current_player(self.destination)
