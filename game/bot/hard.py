from random import choice
from time import perf_counter

from game.bot.easy import EasyStrategy
from game.bot.strategy import BotStrategy
from game.commands import MoveCommand, PlaceWallCommand
from game.game import Game


# Dừng một tầng tìm kiếm khi hết ngân sách, giữ kết quả của tầng đã hoàn tất.
class _SearchLimit(Exception):
    pass


# Dữ liệu chỉ tồn tại trong một lần suy nghĩ, không trộn với lịch sử ván thật.
class _SearchContext:
    # Lưu giới hạn, bộ đếm và cache bản đồ BFS theo cấu hình tường.
    def __init__(self, strategy):
        self.deadline = strategy.clock() + strategy.time_budget
        self.nodes = 0
        self.cutoffs = 0
        self.completed_depth = 0
        self.limited = False
        self.maps = {}


# Bot khó dùng Minimax/Alpha–Beta trên cây rút gọn và tìm sâu dần tới 3 hành động.
class HardStrategy(BotStrategy):
    WIN_SCORE = 1_000_000

    # Giới hạn mặc định để chia việc qua nhiều khung hình và không tìm vô hạn.
    def __init__(self, choose=choice, max_depth=3, wall_limit=4,
                 node_budget=512, time_budget=0.6, clock=perf_counter):
        super().__init__(choose)
        if max_depth < 1 or wall_limit < 0 or node_budget < 1 or time_budget < 0:
            raise ValueError("Giới hạn tìm kiếm không hợp lệ")
        self.max_depth = max_depth
        self.wall_limit = wall_limit
        self.node_budget = node_budget
        self.time_budget = time_budget
        self.clock = clock
        self.last_stats = {}

    # Cùng giao diện Strategy đồng bộ, dùng khi chạy test hoặc công cụ ngoài UI.
    def choose_command(self, game):
        search = self.start_search(game)
        try:
            for command in search:
                if command is not None:
                    return command
            return None
        finally:
            search.close()

    # Kiểm tra trước mỗi đơn vị công việc; UI có thể đóng generator để hủy tác vụ.
    def _check_budget(self, context):
        if context.nodes >= self.node_budget or self.clock() >= context.deadline:
            raise _SearchLimit()

    # Tái sử dụng BFS khi chỉ vị trí quân thay đổi mà tường vẫn giống nhau.
    def _distances(self, game, goal_row, context):
        key = frozenset(game.board.blocked_edges), goal_row
        if key not in context.maps:
            context.maps[key] = game.path_finder.distances_to_goal(game.board, goal_row)
        return context.maps[key]

    # Ước lượng lượt tới đích, tính đúng nhảy ở nước đầu bằng luật của Game.
    def _turns(self, game, player, context):
        if player.row == player.goal_row:
            return 0
        distances = self._distances(game, player.goal_row, context)
        remaining = [distances[cell] for cell in game.get_legal_moves(player)
                     if cell in distances]
        return 1 + min(remaining) if remaining else 999

    # Điểm cố định nhìn từ phe bot; kết quả thắng luôn lớn hơn mọi điểm khoảng cách.
    def _evaluate(self, game, context, ply):
        if game.winner is not None:
            return self.WIN_SCORE - ply if game.winner is game.players[1] else -self.WIN_SCORE + ply
        human, bot = game.players
        human_turns = self._turns(game, human, context)
        bot_turns = self._turns(game, bot, context)
        score = 100 * (human_turns - bot_turns) + 3 * (bot.walls_remaining - human.walls_remaining)
        if game.current_turn == 0 and human_turns == 1:
            score -= 10_000
        if game.current_turn == 1 and bot_turns == 1:
            score += 10_000
        return score

    # Tạo Command mới trên đúng ván; mô phỏng dùng bản sao, nước cuối dùng ván thật.
    def _command(self, game, action):
        if action[0] == "move":
            return MoveCommand(game, action[1:])
        return PlaceWallCommand(game, *action[1:])

    # Tầng đầu xét mọi tường; tầng sâu tập trung vào cạnh của đường ngắn hai phe.
    def _wall_candidates(self, game, context, root):
        if root:
            return [(orientation, row, col) for orientation in ("horizontal", "vertical")
                    for row in range(game.board.size - 1) for col in range(game.board.size - 1)]
        candidates = set()
        for player in game.players:
            distances = self._distances(game, player.goal_row, context)
            cell = player.position
            for _ in range(6):
                if distances.get(cell, 0) == 0:
                    break
                row, col = cell
                adjacent = None
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    other = row + dr, col + dc
                    if (distances.get(other) == distances[cell] - 1
                            and not game.board.is_edge_blocked(cell, other)):
                        adjacent = other
                        break
                if adjacent is None:
                    break
                if adjacent[0] != row:
                    anchor = min(row, adjacent[0])
                    candidates.update((("horizontal", anchor, col), ("horizontal", anchor, col - 1)))
                else:
                    anchor = min(col, adjacent[1])
                    candidates.update((("vertical", row, anchor), ("vertical", row - 1, anchor)))
                cell = adjacent
        return sorted(candidates)

    # Xếp hành động để cắt tỉa hiệu quả; giữ mọi nước đi và tối đa wall_limit tường.
    def _ordered_actions(self, game, context, ply, root=False):
        maximizing = game.current_turn == 1
        actions = [("move", *cell) for cell in game.get_legal_moves()]
        if game.current_player.walls_remaining > 0 and self.wall_limit:
            actions += [("wall", *wall) for wall in self._wall_candidates(game, context, root)]
        ranked = []
        for action in actions:
            self._check_budget(context)
            command = self._command(game, action)
            if command.execute():
                try:
                    ranked.append((self._evaluate(game, context, ply + 1), action))
                finally:
                    command.undo()
            # Nhường lại UI sau khi bản sao đã được hoàn nguyên.
            yield None
        ranked.sort(key=lambda item: item[0], reverse=maximizing)
        moves = [item for item in ranked if item[1][0] == "move"]
        walls = [item for item in ranked if item[1][0] == "wall"][:self.wall_limit]
        return sorted(moves + walls, key=lambda item: item[0], reverse=maximizing)

    # Minimax: bot tối đa hóa, người tối thiểu hóa; Alpha–Beta bỏ nhánh đã đủ kết luận.
    def _minimax(self, game, depth, alpha, beta, context, ply):
        self._check_budget(context)
        context.nodes += 1
        yield None
        if depth == 0 or game.winner is not None:
            return self._evaluate(game, context, ply)
        maximizing = game.current_turn == 1
        actions = yield from self._ordered_actions(game, context, ply)
        if not actions:
            return self._evaluate(game, context, ply)
        best = float("-inf") if maximizing else float("inf")
        for _, action in actions:
            command = self._command(game, action)
            if not command.execute():
                continue
            try:
                value = yield from self._minimax(game, depth - 1, alpha, beta, context, ply + 1)
            finally:
                command.undo()
            if maximizing:
                best = max(best, value)
                alpha = max(alpha, best)
            else:
                best = min(best, value)
                beta = min(beta, best)
            if alpha >= beta:
                context.cutoffs += 1
                break
        return best

    # Tìm sâu dần trên Game riêng; chỉ trả Command gắn với ván thật khi đã chọn xong.
    def start_search(self, game):
        if not game.is_bot_turn:
            return
        context = _SearchContext(self)
        fallback = EasyStrategy(choose=self.choose).choose_command(game)
        if fallback is None:
            return
        best_action = ("move", *fallback.destination)
        simulation = Game(mode="bot", bot_level="hard", human_first=game.human_first)
        simulation.restore_state(game.capture_state())
        try:
            winning = [cell for cell in game.get_legal_moves() if cell[0] == game.current_player.goal_row]
            if winning:
                best_action = ("move", *self.choose(winning))
            else:
                try:
                    actions = yield from self._ordered_actions(simulation, context, 0, root=True)
                    if actions:
                        best_score = actions[0][0]
                        best_action = self.choose([action for score, action in actions if score == best_score])
                        context.completed_depth = 1
                    for depth in range(2, self.max_depth + 1):
                        values = []
                        for _, action in actions:
                            command = self._command(simulation, action)
                            if not command.execute():
                                continue
                            try:
                                value = yield from self._minimax(simulation, depth - 1,
                                                                 float("-inf"), float("inf"), context, 1)
                            finally:
                                command.undo()
                            values.append((value, action))
                        if values:
                            best_score = max(score for score, _ in values)
                            best_action = self.choose([action for score, action in values if score == best_score])
                            context.completed_depth = depth
                except _SearchLimit:
                    context.limited = True
            yield self._command(game, best_action)
        finally:
            self.last_stats = {"nodes": context.nodes, "cutoffs": context.cutoffs,
                               "completed_depth": context.completed_depth, "limited": context.limited}
