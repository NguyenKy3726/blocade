from game.board import Board
from game.player import Player
from game.pathfinder import PathFinder


class Game:
    # Game quản lý bàn cờ, người chơi, lượt chơi và kết quả ván.
    def __init__(self):
        self.board = Board(size=9)
        self.players = [
            Player("Người chơi 1", 0, 4, 8),
            Player("Người chơi 2", 8, 4, 0),
        ]
        self.current_turn = 0
        self.winner = None
        self.path_finder = PathFinder()

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
        if destination not in self.get_legal_moves():
            return False

        player = self.current_player
        player.row, player.col = destination

        if self.has_won(player):
            self.winner = player
        else:
            self.current_turn = 1 - self.current_turn

        return True

    # Kiểm tra quân đã tới hàng đích của người chơi chưa.
    def has_won(self, player):
        return player.row == player.goal_row

    # Đặt tường nếu hợp lệ và không khóa hết đường của bên nào.
    def place_wall_current_player(self, orientation, row, col):
        if self.winner is not None:
            return False

        player = self.current_player

        if player.walls_remaining <= 0:
            return False

        if not self.board.place_wall(orientation, row, col):
            return False

        if not self.path_finder.both_players_have_paths(
            self.board,
            self.players,
        ):
            self.board.remove_wall(orientation, row, col)
            return False

        player.walls_remaining -= 1
        self.current_turn = 1 - self.current_turn
        return True