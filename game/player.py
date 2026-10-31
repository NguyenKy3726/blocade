class Player:
    # Player lưu tên, vị trí quân, hàng đích và số tường của một người chơi.
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