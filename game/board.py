class Board:
    # Board lưu kích thước bàn cờ và các cạnh đang bị tường chặn.
    def __init__(self, size=9):
        self.size = size
        self.blocked_edges = set()

    # Kiểm tra tọa độ có nằm trong bàn cờ không.
    def is_inside(self, row, col):
        return 0 <= row < self.size and 0 <= col < self.size

    # Tạo khóa chung cho cạnh nối giữa hai ô, không phụ thuộc thứ tự hai ô.
    def _edge_key(self, first, second):
        return frozenset((first, second))

    # Kiểm tra đường đi trực tiếp giữa hai ô có bị tường chặn không.
    def is_edge_blocked(self, first, second):
        return self._edge_key(first, second) in self.blocked_edges

    # Đánh dấu cạnh giữa hai ô bị chặn; sẽ được dùng khi triển khai đặt tường.
    def block_edge(self, first, second):
        self.blocked_edges.add(self._edge_key(first, second))