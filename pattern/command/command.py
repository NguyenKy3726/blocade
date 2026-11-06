from abc import ABC, abstractmethod


# Interface lệnh chung, tương ứng với ICommand trong sơ đồ của giảng viên.
class Command(ABC):
    # Gắn ConcreteCommand với Receiver; tạo lệnh chưa làm thay đổi ván.
    def __init__(self, receiver):
        self.receiver = receiver
        self.board = receiver.board
        self.player_index = None
        self.executed = False
        self._invoker = None

    # Kiểm tra lệnh còn dùng được rồi thực hiện hành động do lớp con cung cấp.
    def _execute_action(self, action):
        if self.executed or self.board is not self.receiver.board:
            return False
        if not action():
            return False
        self.executed = True
        return True

    # Mỗi ConcreteCommand triển khai thao tác Execute của interface chung.
    @abstractmethod
    def execute(self):
        pass

    # Ủy quyền hoàn tác cho Invoker đang quản lý lịch sử của ván thật.
    def undo(self):
        return self._invoker.undo_command(self) if self._invoker is not None else False

    # Ủy quyền làm lại cho Invoker; Command không tự quản lý ngăn Redo.
    def redo(self):
        return self._invoker.redo_command(self) if self._invoker is not None else False
