from abc import ABC, abstractmethod


# Interface lệnh chung, tương ứng với ICommand trong sơ đồ của giảng viên.
class Command(ABC):
    # Gắn ConcreteCommand với Receiver; tạo lệnh chưa làm thay đổi ván.
    def __init__(self, receiver):
        self.receiver = receiver
        # Giữ bí danh game để các phần lịch sử cũ đọc dễ hiểu và tương thích.
        self.game = receiver
        self.board = receiver.board
        self.player_index = None
        self.before_state = None
        self.after_state = None
        self.executed = False

    # Dùng chung phần ghi snapshot/lịch sử; hành động cụ thể do lớp con cung cấp.
    def _execute_action(self, action):
        if self.executed or self.board is not self.receiver.board:
            return False
        before = self.receiver.capture_state() if self.receiver.mode == "bot" else None
        if not action():
            return False
        self.executed = True
        if before is not None:
            self.before_state = before
            self.after_state = self.receiver.capture_state()
            # Chỉ nước mới thành công mới bỏ nhánh đã Undo; xem trước/nước sai giữ nhánh.
            self.receiver.redo_history.clear()
            self.player_index = before["current_turn"]
            self.receiver.command_history.append(self)
        return True

    # Mỗi ConcreteCommand phải cung cấp phương thức execute như ICommand.
    @abstractmethod
    def execute(self):
        pass

    # Lùi lệnh ở đỉnh lịch sử và chuyển nó sang ngăn Redo, giữ cả hai snapshot.
    def undo(self):
        history = self.receiver.command_history
        if (self.before_state is None or self.board is not self.receiver.board
                or self.receiver.mode != "bot" or not history or history[-1] is not self):
            return False
        self.receiver.restore_state(self.before_state)
        history.pop()
        self.receiver.redo_history.append(self)
        return True

    # Làm lại đúng lệnh vừa Undo, không gọi luật hoặc để bot chọn hành động mới.
    def redo(self):
        history = self.receiver.redo_history
        if (self.after_state is None or self.board is not self.receiver.board
                or self.receiver.mode != "bot" or not history or history[-1] is not self
                or self.receiver.capture_state() != self.before_state):
            return False
        self.receiver.restore_state(self.after_state)
        history.pop()
        self.receiver.command_history.append(self)
        return True
