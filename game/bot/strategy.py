from abc import ABC, abstractmethod
from random import choice


# Giao diện Strategy chung để thay đổi cấp bot mà không đổi controller.
class BotStrategy(ABC):
    # Tách hàm chọn ngẫu nhiên để các kiểm tra có thể chọn kết quả cố định.
    def __init__(self, choose=choice):
        self.choose = choose

    # Trả về Command đã chọn, không tự execute hoặc ghi lịch sử.
    @abstractmethod
    def choose_command(self, game):
        pass
