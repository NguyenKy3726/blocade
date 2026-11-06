# Lưu dữ liệu tạm của một lần bot suy nghĩ, tách khỏi trạng thái ván thật.
class _SearchContext:
    # Khởi tạo giới hạn, bộ đếm, cache BFS và thông tin độ sâu đã hoàn tất.
    def __init__(self, strategy):
        self.deadline = strategy.clock() + strategy.time_budget
        self.nodes = 0
        self.cutoffs = 0
        self.completed_depth = 0
        self.limited = False
        self.maps = {}
