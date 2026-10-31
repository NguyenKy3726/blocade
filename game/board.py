class Board:
    # Board lưu kích thước bàn cờ, các cạnh bị chặn và vị trí các bức tường.
    def __init__(self, size=9):
        self.size = size
        self.blocked_edges = set()
        self.walls = []

    # Kiểm tra tọa độ có nằm trong bàn cờ không.
    def is_inside(self, row, col):
        return 0 <= row < self.size and 0 <= col < self.size

    # Tạo khóa chung cho cạnh nối hai ô, dù truyền ô nào trước.
    def _edge_key(self, first, second):
        return frozenset((first, second))

    # Kiểm tra đường đi trực tiếp giữa hai ô có bị tường chặn không.
    def is_edge_blocked(self, first, second):
        return self._edge_key(first, second) in self.blocked_edges

    # Trả về hai cạnh mà một bức tường sẽ chặn.
    # Tường ngang chặn đường đi lên/xuống qua hai cặp ô.
    # Tường dọc chặn đường đi trái/phải qua hai cặp ô.
    def _get_wall_edges(self, orientation, row, col):
        if orientation == "horizontal":
            return [
                ((row, col), (row + 1, col)),
                ((row, col + 1), (row + 1, col + 1)),
            ]

        if orientation == "vertical":
            return [
                ((row, col), (row, col + 1)),
                ((row + 1, col), (row + 1, col + 1)),
            ]

        return None

    # Kiểm tra tường có thể đặt tại hướng và tọa độ đã chọn không.
    def can_place_wall(self, orientation, row, col):
        if orientation not in ("horizontal", "vertical"):
            return False

        # Tường dài hai cạnh nên điểm neo phải nằm trong vùng 8×8.
        if not (0 <= row < self.size - 1 and 0 <= col < self.size - 1):
            return False

        # Hai tường vuông góc cùng điểm neo sẽ cắt nhau.
        other_orientation = (
            "vertical" if orientation == "horizontal" else "horizontal"
        )
        if (other_orientation, row, col) in self.walls:
            return False

        # Nếu một cạnh đã bị chặn, tường mới sẽ chồng lên tường cũ.
        edges = self._get_wall_edges(orientation, row, col)
        for first, second in edges:
            if self.is_edge_blocked(first, second):
                return False

        return True

    # Đặt tường và ghi nhận hai cạnh mà tường đó chặn.
    def place_wall(self, orientation, row, col):
        if not self.can_place_wall(orientation, row, col):
            return False

        wall = (orientation, row, col)
        self.walls.append(wall)

        for first, second in self._get_wall_edges(orientation, row, col):
            self.blocked_edges.add(self._edge_key(first, second))

        return True

    # Gỡ một tường đã đặt; dùng khi BFS phát hiện tường làm khóa đường.
    def remove_wall(self, orientation, row, col):
        wall = (orientation, row, col)

        if wall not in self.walls:
            return False

        self.walls.remove(wall)

        for first, second in self._get_wall_edges(orientation, row, col):
            self.blocked_edges.remove(self._edge_key(first, second))

        return True