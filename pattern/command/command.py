from abc import ABC, abstractmethod


# Lớp trừu tượng chung cho các hành động có thể thực thi/hoàn tác.
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
