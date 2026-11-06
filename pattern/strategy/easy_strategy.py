from pattern.strategy.bot_strategy import BotStrategy
from pattern.command import MoveCommand


# Chiến lược dễ chọn nước hợp lệ gần hàng đích nhất theo BFS.
class EasyStrategy(BotStrategy):
    # Chỉ tạo Command, chưa đổi bàn cờ; BFS đánh giá đường đi qua các cạnh chưa bị chặn.
    def choose_command(self, game):
        if not game.is_bot_turn:
            return None
        player = game.current_player
        candidates = []
        for destination in game.get_legal_moves():
            distance = game.path_finder.shortest_distance(game.board, destination, player.goal_row)
            if distance is not None:
                candidates.append((distance, destination))
        if not candidates:
            return None
        best_distance = min(distance for distance, _ in candidates)
        best_moves = [destination for distance, destination in candidates
                      if distance == best_distance]
        return MoveCommand(game, self.choose(best_moves))
