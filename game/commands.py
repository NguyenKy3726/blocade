from abc import ABC, abstractmethod


# Giao diện chung cho các yêu cầu hành động trong ván chơi.
class Command(ABC):
    # Thực hiện hành động và trả về True nếu được luật chơi chấp nhận.
    @abstractmethod
    def execute(self):
        pass


# Đóng gói yêu cầu đi quân; Game vẫn chịu trách nhiệm kiểm tra luật.
class MoveCommand(Command):
    # Lưu ván chơi và ô đích; tạo lệnh chưa làm quân di chuyển.
    def __init__(self, game, destination):
        self.game = game
        self.destination = destination

    # Yêu cầu Game đi quân, kiểm tra giờ, đổi lượt hoặc ghi nhận thắng.
    def execute(self):
        return self.game.move_current_player(self.destination)


# Đóng gói yêu cầu đặt tường; không tự sửa bàn, số tường hoặc lượt chơi.
class PlaceWallCommand(Command):
    # Lưu hướng và điểm neo tường; chưa đặt tường khi khởi tạo lệnh.
    def __init__(self, game, orientation, row, col):
        self.game = game
        self.orientation = orientation
        self.row = row
        self.col = col

    # Yêu cầu Game kiểm tra tường/BFS/giờ rồi đặt tường nếu hợp lệ.
    def execute(self):
        return self.game.place_wall_current_player(self.orientation, self.row, self.col)
