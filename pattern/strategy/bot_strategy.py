from abc import ABC, abstractmethod
from random import choice


# Giao diện trừu tượng thống nhất cách các cấp bot chọn hành động.
class BotStrategy(ABC):
    # Tách hàm chọn ngẫu nhiên để các kiểm tra có thể chọn kết quả cố định.
    def __init__(self, choose=choice):
        self.choose = choose

    # Bot dễ/trung bình chạy trực tiếp; bot khó có thể cung cấp generator chia khung hình.
    def start_search(self, game):
        return None

    # Trả về Command đã chọn, không tự execute hoặc ghi lịch sử.
    @abstractmethod
    def choose_command(self, game):
        pass
