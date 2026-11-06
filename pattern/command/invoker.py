# Invoker giữ Command hiện tại và gọi execute theo mẫu Command.
class CommandInvoker:
    # Tạo Invoker chưa gắn lệnh nào.
    def __init__(self):
        self.command = None

    # Gán lệnh sẽ được Invoker thực thi.
    def set_command(self, command):
        self.command = command

    # Yêu cầu lệnh đã gán thực thi và trả về kết quả thành công/thất bại.
    def execute(self, command=None):
        if command is not None:
            self.set_command(command)
        if self.command is None:
            return False
        return self.command.execute()
