from abc import ABC, abstractmethod


# Đóng gói thực thi và hoàn tác; lịch sử chỉ lưu lệnh thành công khi đấu bot.
class Command(ABC):
    # Gắn lệnh với ván hiện tại; chưa lưu trạng thái hoặc thay đổi bàn cờ.
    def __init__(self, game):
        self.game = game
        self.board = game.board
        self.player_index = None
        self.before_state = None
        self.after_state = None
        self.executed = False

    # Kiểm tra luật qua Game rồi mới ghi lịch sử; mỗi lệnh chỉ thực thi một lần.
    def execute(self):
        if self.executed or self.board is not self.game.board:
            return False
        before = self.game.capture_state() if self.game.mode == "bot" else None
        if not self._perform():
            return False
        self.executed = True
        if before is not None:
            self.before_state = before
            self.after_state = self.game.capture_state()
            # Chỉ nước mới thành công mới bỏ nhánh đã Undo; xem trước/nước sai giữ nhánh.
            self.game.redo_history.clear()
            self.player_index = before["current_turn"]
            self.game.command_history.append(self)
        return True

    # Lùi lệnh ở đỉnh lịch sử và chuyển nó sang ngăn Redo, giữ cả hai snapshot.
    def undo(self):
        history = self.game.command_history
        if (self.before_state is None or self.board is not self.game.board
                or self.game.mode != "bot" or not history or history[-1] is not self):
            return False
        self.game.restore_state(self.before_state)
        history.pop()
        self.game.redo_history.append(self)
        return True

    # Làm lại đúng lệnh vừa Undo, không gọi luật hoặc để bot chọn hành động mới.
    def redo(self):
        history = self.game.redo_history
        if (self.after_state is None or self.board is not self.game.board
                or self.game.mode != "bot" or not history or history[-1] is not self
                or self.game.capture_state() != self.before_state):
            return False
        self.game.restore_state(self.after_state)
        history.pop()
        self.game.command_history.append(self)
        return True

    # Mỗi loại lệnh chỉ cần chỉ ra hành động cụ thể; Game giữ toàn bộ luật.
    @abstractmethod
    def _perform(self):
        pass


# Yêu cầu đi quân, dùng chung cơ chế execute/undo của Command.
class MoveCommand(Command):
    # Lưu ô đích; chưa làm quân di chuyển khi tạo lệnh.
    def __init__(self, game, destination):
        super().__init__(game)
        self.destination = destination

    # Nhờ Game kiểm tra nước đi, giờ, chuyển lượt hoặc ghi nhận thắng.
    def _perform(self):
        return self.game.move_current_player(self.destination)


# Yêu cầu đặt tường, dùng chung cơ chế execute/undo của Command.
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
