from game.board import Board
from game.player import Player


class Game:
    def __init__(self):
        self.board = Board(size=9)

        self.players = [
            Player("Người chơi 1", row=0, col=4, goal_row=8),
            Player("Người chơi 2", row=8, col=4, goal_row=0),
        ]

        self.current_turn = 0

    @property
    def current_player(self):
        return self.players[self.current_turn]

    def get_opponent(self):
        opponent_index = 1 - self.current_turn
        return self.players[opponent_index]

    def switch_turn(self):
        self.current_turn = 1 - self.current_turn

    def has_won(self, player):
        return player.row == player.goal_row