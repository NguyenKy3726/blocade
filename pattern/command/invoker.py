# Một mục lưu lệnh cùng snapshot để thực hiện Undo/Redo.
class _HistoryEntry:
    # Ghi nhận trạng thái trước/sau và người đã thực hiện lệnh.
    def __init__(self, command, before_state, after_state):
        self.command = command
        self.before_state = before_state
        self.after_state = after_state
        self.player_index = before_state["current_turn"]


# Invoker gọi Command và quản lý lịch sử riêng của ván đang chạy.
class CommandInvoker:
    # Gắn Invoker với Game; lịch sử bật/tắt theo loại phiên chơi.
    def __init__(self, receiver, history_enabled=False):
        self.receiver = receiver
        self.history_enabled = history_enabled
        self.command = None
        self.undo_stack = []
        self.redo_stack = []

    # Gán Command sẽ được Invoker thực thi.
    def set_command(self, command):
        self.command = command

    # Bật hoặc tắt lịch sử mà không cần Command biết chế độ chơi.
    def set_history_enabled(self, enabled):
        self.history_enabled = bool(enabled)

    # Xóa lịch sử cũ khi bắt đầu ván mới hoặc rời ván.
    def clear(self):
        self.undo_stack.clear()
        self.redo_stack.clear()

    # Thực thi lệnh; chỉ phiên được cấu hình lưu lịch sử mới chụp snapshot.
    def execute(self, command=None):
        if command is not None:
            self.set_command(command)
        if self.command is None or self.command.receiver is not self.receiver:
            return False

        before_state = self.receiver.capture_state() if self.history_enabled else None
        if not self.command.execute():
            return False

        if before_state is not None:
            entry = _HistoryEntry(self.command, before_state, self.receiver.capture_state())
            self.command.player_index = entry.player_index
            self.command._invoker = self
            self.undo_stack.append(entry)
            self.redo_stack.clear()
        return True

    # Trả các lệnh đã thực hiện theo thứ tự lịch sử để Game/UI đọc.
    @property
    def commands(self):
        return [entry.command for entry in self.undo_stack]

    # Trả các lệnh đã hoàn tác theo thứ tự ngăn Redo.
    @property
    def redo_commands(self):
        return [entry.command for entry in self.redo_stack]

    # Cho phép Undo khi còn ít nhất một nước của người chơi thật.
    @property
    def can_undo(self):
        return self.history_enabled and any(entry.player_index == 0 for entry in self.undo_stack)

    # Cho phép Redo khi có lệnh đã được hoàn tác.
    @property
    def can_redo(self):
        return self.history_enabled and bool(self.redo_stack)

    # Hoàn tác đúng lệnh ở đỉnh ngăn Undo.
    def undo_command(self, command):
        if not self.undo_stack or self.undo_stack[-1].command is not command:
            return False
        entry = self.undo_stack.pop()
        self.receiver.restore_state(entry.before_state)
        self.redo_stack.append(entry)
        return True

    # Làm lại snapshot của lệnh vừa Undo nếu trạng thái hiện tại chưa đổi.
    def redo_command(self, command):
        if not self.redo_stack or self.redo_stack[-1].command is not command:
            return False
        entry = self.redo_stack[-1]
        if self.receiver.capture_state() != entry.before_state:
            return False
        self.receiver.restore_state(entry.after_state)
        self.redo_stack.pop()
        self.undo_stack.append(entry)
        return True

    # Hoàn tác các nước gần nhất tới nước của người chơi để họ chọn lại.
    def undo_round(self):
        if not self.can_undo:
            return False
        while self.undo_stack:
            entry = self.undo_stack[-1]
            if not entry.command.undo():
                return False
            if entry.player_index == 0:
                return True
        return False

    # Làm lại nước người rồi nước bot đã lưu, không chọn hành động mới.
    def redo_round(self):
        if not self.can_redo:
            return False
        while self.redo_stack:
            entry = self.redo_stack[-1]
            if not entry.command.redo():
                return False
            if not self.redo_stack or self.redo_stack[-1].player_index == 0:
                return True
        return False
