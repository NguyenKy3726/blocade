from pattern.strategy.bot_strategy import BotStrategy
from pattern.command import MoveCommand, PlaceWallCommand


# Chiến lược trung bình đánh giá đường đi và hiệu quả đặt tường.
class MediumStrategy(BotStrategy):
    # Ước lượng số lượt tới đích, dùng nước đầu hợp lệ để tính cả nhảy qua đối thủ.
    def _turns_to_goal(self, game, player, distances):
        if player.row == player.goal_row:
            return 0
        remaining = [distances[cell] for cell in game.get_legal_moves(player)
                     if cell in distances]
        return 1 + min(remaining) if remaining else None

    # Ưu tiên không cho đối thủ thắng ngay, rồi so chênh lệch đường; trừ nhẹ khi tốn tường.
    def _evaluate(self, game, wall_cost=0.0):
        bot = game.current_player
        human = game.get_opponent(bot)
        bot_paths = game.path_finder.distances_to_goal(game.board, bot.goal_row)
        human_paths = game.path_finder.distances_to_goal(game.board, human.goal_row)
        # Đồng thời kiểm tra BFS: không được chặn hết đường của bất cứ phe nào.
        if bot.position not in bot_paths or human.position not in human_paths:
            return None
        bot_turns = self._turns_to_goal(game, bot, bot_paths)
        human_turns = self._turns_to_goal(game, human, human_paths)
        if bot_turns is None or human_turns is None:
            return None
        return human_turns > 1, human_turns - bot_turns - wall_cost

    # Thử đi quân và tường, luôn hoàn nguyên; chỉ tạo Command cho các phương án hợp lệ.
    def choose_command(self, game):
        if not game.is_bot_turn:
            return None
        bot = game.current_player
        moves = game.get_legal_moves()
        winning_moves = [cell for cell in moves if cell[0] == bot.goal_row]
        if winning_moves:
            return MoveCommand(game, self.choose(winning_moves))

        candidates = []
        original_position = bot.position
        for destination in moves:
            try:
                bot.row, bot.col = destination
                rank = self._evaluate(game)
                if rank is not None:
                    candidates.append((rank, MoveCommand(game, destination)))
            finally:
                bot.row, bot.col = original_position

        if bot.walls_remaining > 0:
            for orientation in ("horizontal", "vertical"):
                for row in range(game.board.size - 1):
                    for col in range(game.board.size - 1):
                        if not game.board.place_wall(orientation, row, col):
                            continue
                        try:
                            rank = self._evaluate(game, wall_cost=0.5)
                            if rank is not None:
                                candidates.append((rank, PlaceWallCommand(game, orientation, row, col)))
                        finally:
                            game.board.remove_wall(orientation, row, col)

        if not candidates:
            return None
        best_rank = max(rank for rank, _ in candidates)
        return self.choose([command for rank, command in candidates if rank == best_rank])
