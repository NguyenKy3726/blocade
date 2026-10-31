class Board:
    def __init__(self, size=9):
        self.size = size
        self.walls = []

    def is_inside(self, row, col):
        """Kiểm tra ô (row, col) có nằm trong bàn cờ không."""
        return 0 <= row < self.size and 0 <= col < self.size