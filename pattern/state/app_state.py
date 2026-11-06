from abc import ABC, abstractmethod


# Lớp trừu tượng quy định giao diện chung cho các trạng thái ứng dụng.
class AppState(ABC):
    # Mặc định không chạy đồng hồ, ví dụ tại menu, lượt bot và sau thắng.
    def update(self, app):
        return False

    # Mặc định không cho bot chạy; chỉ BotTurnState ghi đè phương thức này.
    def update_bot(self, app):
        return False

    # Mỗi trạng thái quyết định sự kiện nào được chuyển tới ván chơi.
    @abstractmethod
    def handle_event(self, app, event):
        pass

    # Mỗi trạng thái chọn màn hình cần vẽ.
    @abstractmethod
    def draw(self, app):
        pass
