from time import perf_counter


# Nội suy hình vẽ, tách biệt với tọa độ thật và lịch sử Command của ván.
class GamePresentation:
    # Có thể truyền đồng hồ giả để kiểm tra animation mà không phải chờ thật.
    def __init__(self, time_source=perf_counter):
        self.time_source = time_source
        self.board = None
        self.moves = {}
        self.wall_births = {}
        self.move_duration = 0.20
        self.wall_duration = 0.18

    # Chơi lại/ván mới xóa mọi chuyển động cũ, không để quân hay tường xuất hiện muộn.
    def reset(self, board=None):
        self.board = board
        self.moves.clear()
        self.wall_births.clear()

    # Điểm vẽ mượt từ đầu tới đích; trả vị trí thật khi hiệu ứng hoàn tất.
    def position(self, index, actual_position):
        if index not in self.moves:
            return actual_position
        start, target, started = self.moves[index]
        progress = min(1.0, max(0.0, (self.time_source() - started) / self.move_duration))
        if progress >= 1:
            del self.moves[index]
            return actual_position
        eased = progress * progress * (3 - 2 * progress)
        return tuple(a + (b - a) * eased for a, b in zip(start, target))

    # Tường mới tăng độ đậm ngắn; tường cũ hoặc đã hoàn tất luôn vẽ đầy đủ.
    def wall_alpha(self, wall):
        if wall not in self.wall_births:
            return 255
        progress = min(1.0, max(0.0, (self.time_source() - self.wall_births[wall]) / self.wall_duration))
        if progress >= 1:
            del self.wall_births[wall]
        return round(80 + 175 * progress)

    # Chỉ ghi hiệu ứng sau hành động thành công; Undo/Redo khôi phục hình ngay.
    def record(self, game, before, kind="action"):
        if self.board is not game.board or kind in ("undo", "redo"):
            self.reset(game.board)
        if kind in ("undo", "redo"):
            return
        now = self.time_source()
        for index, player in enumerate(game.players):
            old = before["players"][index][:2]
            if old != player.position:
                start = self.position(index, old)
                self.moves[index] = (start, player.position, now)
        for wall in game.board.walls:
            if wall not in before["walls"]:
                self.wall_births[wall] = now
