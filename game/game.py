from time import monotonic

from game.board import Board
from game.player import Player
from game.pathfinder import PathFinder


# Quản lý bàn cờ, người chơi, lượt chơi và kết quả ván.
class Game:
    # Khởi tạo ván 9×9, mặc định hai người; chế độ bot được chọn từ menu.
    def __init__(self, time_source=monotonic, mode="two_players"):
        # Tách đồng hồ khỏi Pygame để kiểm tra mà không cần chờ thật.
        self.time_source = time_source
        self.turn_duration = 30.0
        self.mode = mode
        self.reset()

    # Bắt đầu lại ván, giữ chế độ cũ nếu không truyền chế độ khác.
    def reset(self, mode=None):
        if mode is not None:
            self.mode = mode
        if self.mode not in ("two_players", "bot"):
            raise ValueError("Chế độ chơi không hợp lệ")
        self.board = Board(size=9)
        self.players = [
            Player("Bạn" if self.mode == "bot" else "Người chơi 1", 0, 4, 8),
            Player("Bot dễ" if self.mode == "bot" else "Người chơi 2", 8, 4, 0),
        ]
        self.current_turn = 0
        self.winner = None
        self.path_finder = PathFinder()
        self.time_remaining = [self.turn_duration, self.turn_duration]
        self.turn_started_at = self.time_source() if self.timer_enabled else None
        self.wall_owners = {}
        self.notice = ""
        self.command_history = []
        self.redo_history = []

    # Chụp dữ liệu có thể đổi trong hành động; tạo bản sao để lịch sử không bị ghi đè.
    def capture_state(self):
        return {
            "players": [(p.row, p.col, p.walls_remaining) for p in self.players],
            "walls": list(self.board.walls),
            "blocked_edges": set(self.board.blocked_edges),
            "wall_owners": dict(self.wall_owners),
            "current_turn": self.current_turn,
            "winner": self.players.index(self.winner) if self.winner is not None else None,
            "time_remaining": list(self.time_remaining),
            "turn_started_at": self.turn_started_at,
            "notice": self.notice,
        }

    # Khôi phục trạng thái của một Command, giữ nguyên các đối tượng Game/Board.
    def restore_state(self, state):
        for player, data in zip(self.players, state["players"]):
            player.row, player.col, player.walls_remaining = data
        self.board.walls = list(state["walls"])
        self.board.blocked_edges = set(state["blocked_edges"])
        self.wall_owners = dict(state["wall_owners"])
        self.current_turn = state["current_turn"]
        self.winner = self.players[state["winner"]] if state["winner"] is not None else None
        self.time_remaining = list(state["time_remaining"])
        self.turn_started_at = state["turn_started_at"]
        self.notice = state["notice"]

    # Chỉ đấu bot mới Undo; phải có hành động của người để trở về lúc người chọn nước.
    @property
    def can_undo(self):
        return self.mode == "bot" and any(c.player_index == 0 for c in self.command_history)

    # Hoàn tác từ lệnh mới nhất về tới hành động gần nhất của người chơi.
    def undo_round(self):
        if not self.can_undo:
            return False
        while self.command_history:
            command = self.command_history[-1]
            if not command.undo():
                return False
            if command.player_index == 0:
                return True
        return False

    # Chỉ đấu bot có Redo, khi có Command đã Undo của ván hiện tại.
    @property
    def can_redo(self):
        return self.mode == "bot" and bool(self.redo_history)

    # Làm lại lệnh người rồi lệnh bot đã có, dừng trước lượt người kế tiếp.
    def redo_round(self):
        if not self.can_redo:
            return False
        while self.redo_history:
            command = self.redo_history[-1]
            if not command.redo():
                return False
            if not self.redo_history or self.redo_history[-1].player_index == 0:
                return True
        return False

    # Chỉ chế độ hai người mới dùng đồng hồ và mất lượt do hết giờ.
    @property
    def timer_enabled(self):
        return self.mode == "two_players"

    # Bot là phe xanh nước và không đi tiếp khi đã có người thắng.
    @property
    def is_bot_turn(self):
        return self.mode == "bot" and self.current_turn == 1 and self.winner is None

    # Cập nhật riêng đồng hồ bên đang đi; hết giờ thì mất lượt, không xử thua.
    def update_time(self):
        if not self.timer_enabled or self.winner is not None:
            return False

        now = self.time_source()
        elapsed = max(0.0, now - self.turn_started_at)
        self.time_remaining[self.current_turn] = max(0.0, self.turn_duration - elapsed)
        if self.time_remaining[self.current_turn] > 0:
            return False

        self.notice = f"{self.current_player.name} hết giờ, mất lượt."
        self._next_turn(now)
        return True

    # Chuyển sang người còn lại và cấp đủ 30 giây cho lượt mới.
    def _next_turn(self, now=None):
        self.current_turn = 1 - self.current_turn
        if not self.timer_enabled:
            return
        self.time_remaining[self.current_turn] = self.turn_duration
        self.turn_started_at = self.time_source() if now is None else now

    # Trả về người chơi đang đến lượt.
    @property
    def current_player(self):
        return self.players[self.current_turn]

    # Tìm người chơi còn lại, không phải người chơi được truyền vào.
    def get_opponent(self, player):
        for other_player in self.players:
            if other_player is not player:
                return other_player
        return None

    # Kiểm tra một ô có quân của người chơi khác đứng hay không.
    def _is_occupied_by_other_player(self, position, player):
        for other_player in self.players:
            if other_player is not player and other_player.position == position:
                return True
        return False

    # Tính các ô đi hợp lệ, gồm đi thường và nhảy qua đối thủ.
    def get_legal_moves(self, player=None):
        if self.winner is not None:
            return []

        if player is None:
            player = self.current_player

        opponent = self.get_opponent(player)
        row, col = player.position
        moves = []

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for row_change, col_change in directions:
            adjacent = (row + row_change, col + col_change)

            if not self.board.is_inside(*adjacent):
                continue

            if self.board.is_edge_blocked(player.position, adjacent):
                continue

            if adjacent == opponent.position:
                behind = (
                    opponent.row + row_change,
                    opponent.col + col_change,
                )

                can_jump_straight = (
                    self.board.is_inside(*behind)
                    and not self.board.is_edge_blocked(opponent.position, behind)
                )

                if can_jump_straight:
                    moves.append(behind)
                else:
                    diagonal_directions = [
                        (-col_change, row_change),
                        (col_change, -row_change),
                    ]

                    for dr, dc in diagonal_directions:
                        diagonal = (opponent.row + dr, opponent.col + dc)

                        if not self.board.is_inside(*diagonal):
                            continue

                        if self.board.is_edge_blocked(opponent.position, diagonal):
                            continue

                        if not self._is_occupied_by_other_player(diagonal, player):
                            moves.append(diagonal)

            elif not self._is_occupied_by_other_player(adjacent, player):
                moves.append(adjacent)

        return moves

    # Thực hiện nước đi hợp lệ; sau đó đổi lượt hoặc ghi nhận người thắng.
    def move_current_player(self, destination):
        # Không cho một click đến muộn trở thành nước đi của người tiếp theo.
        if self.update_time():
            return False
        if destination not in self.get_legal_moves():
            return False

        self.notice = ""
        player = self.current_player
        player.row, player.col = destination

        if self.has_won(player):
            self.winner = player
        else:
            self._next_turn()

        return True

    # Kiểm tra quân đã tới hàng đích của người chơi chưa.
    def has_won(self, player):
        return player.row == player.goal_row

    # Đặt thử tường, chạy BFS cho cả hai người rồi gỡ tường thử.
    # Dùng để tô màu xem trước trên UI mà không làm đổi trạng thái bàn cờ.
    def can_place_wall_current_player(self, orientation, row, col):
        player = self.current_player

        if self.winner is not None or player.walls_remaining <= 0:
            return False

        if not self.board.place_wall(orientation, row, col):
            return False

        both_have_paths = self.path_finder.both_players_have_paths(
            self.board,
            self.players,
        )

        self.board.remove_wall(orientation, row, col)
        return both_have_paths

    # Đặt tường hợp lệ, trừ một tường của người chơi và chuyển lượt.
    def place_wall_current_player(self, orientation, row, col):
        if self.update_time():
            return False
        if not self.can_place_wall_current_player(orientation, row, col):
            return False

        if not self.board.place_wall(orientation, row, col):
            return False

        self.wall_owners[(orientation, row, col)] = self.current_turn
        self.current_player.walls_remaining -= 1
        self.notice = ""
        self._next_turn()
        return True
