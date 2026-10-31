from game.board import Board
from game.player import Player


class Game:
    # Game quản lý bàn cờ, người chơi, lượt hiện tại và kết quả ván.
    def __init__(self):
        self.board = Board(size=9)
        self.players = [
            Player("Người chơi 1", 0, 4, 8),
            Player("Người chơi 2", 8, 4, 0),
        ]
        self.current_turn = 0
        self.winner = None

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

    # Tính các ô mà người chơi có thể đi theo luật hiện tại.
    def get_legal_moves(self, player=None):
        if self.winner is not None:
            return []

        if player is None:
            player = self.current_player

        opponent = self.get_opponent(player)
        row, col = player.position
        moves = []

        directions = [
            (-1, 0),  # lên
            (1, 0),   # xuống
            (0, -1),  # trái
            (0, 1),   # phải
        ]

        for row_change, col_change in directions:
            adjacent = (row + row_change, col + col_change)

            if not self.board.is_inside(*adjacent):
                continue

            if self.board.is_edge_blocked(player.position, adjacent):
                continue

            # Nếu ô kế bên là đối thủ, thử nhảy thẳng qua đối thủ.
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
                    if behind not in moves:
                        moves.append(behind)
                else:
                    # Không thể nhảy thẳng vì mép bàn hoặc tường:
                    # xét hai ô chéo hai bên đối thủ.
                    diagonal_directions = [
                        (-col_change, row_change),
                        (col_change, -row_change),
                    ]

                    for diagonal_row_change, diagonal_col_change in diagonal_directions:
                        diagonal = (
                            opponent.row + diagonal_row_change,
                            opponent.col + diagonal_col_change,
                        )

                        if not self.board.is_inside(*diagonal):
                            continue

                        if self.board.is_edge_blocked(opponent.position, diagonal):
                            continue

                        if self._is_occupied_by_other_player(diagonal, player):
                            continue

                        if diagonal not in moves:
                            moves.append(diagonal)

            # Nếu ô kế bên trống, đây là nước đi một ô bình thường.
            elif not self._is_occupied_by_other_player(adjacent, player):
                if adjacent not in moves:
                    moves.append(adjacent)

        return moves

    # Thực hiện nước đi nếu ô đích nằm trong danh sách nước hợp lệ.
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

    # Kiểm tra quân đã đến hàng đích của người chơi chưa.
    def has_won(self, player):
        return player.row == player.goal_row