from collections import deque


# Dùng BFS để kiểm tra đường tới hàng đích.
class PathFinder:
    # Kiểm tra từ ô xuất phát có đường tới hàng đích hay không.
    def has_path(self, board, start, goal_row):
        queue = deque([start])
        visited = {start}

        directions = [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
        ]

        while queue:
            row, col = queue.popleft()

            # Chạm tới hàng đích nghĩa là đã tìm thấy đường.
            if row == goal_row:
                return True

            for row_change, col_change in directions:
                next_cell = (row + row_change, col + col_change)

                if not board.is_inside(*next_cell):
                    continue

                if board.is_edge_blocked((row, col), next_cell):
                    continue

                if next_cell not in visited:
                    visited.add(next_cell)
                    queue.append(next_cell)

        return False

    # Kiểm tra lần lượt cả hai người chơi đều còn đường tới hàng đích.
    def both_players_have_paths(self, board, players):
        for player in players:
            if not self.has_path(board, player.position, player.goal_row):
                return False

        return True