class Player:
    def __init__(self, name, row, col, goal_row):
        self.name = name
        self.row = row
        self.col = col
        self.goal_row = goal_row
        self.walls_remaining = 10

    @property
    def position(self):
        """Trả về vị trí hiện tại dưới dạng (hàng, cột)."""
        return self.row, self.col