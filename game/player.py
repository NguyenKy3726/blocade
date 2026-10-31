# Lưu thông tin và vị trí của một người chơi.
class Player:
    # Khởi tạo vị trí xuất phát, hàng đích và 10 tường.
    def __init__(self, name, row, col, goal_row):
        self.name = name
        self.row = row
        self.col = col
        self.goal_row = goal_row
        self.walls_remaining = 10

    # Trả vị trí quân dưới dạng (hàng, cột).
    @property
    def position(self):
        return self.row, self.col