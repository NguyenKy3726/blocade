from collections import deque


# Dùng BFS để kiểm tra đường tới hàng đích.
class PathFinder:
    # Kiểm tra từ ô xuất phát có đường tới hàng đích hay không.
    def has_path(self, board, start, goal_row):
        return self.shortest_distance(board, start, goal_row) is not None

    # Đếm số cạnh ít nhất tới hàng đích, bỏ qua quân để đánh giá đường qua tường.
    def shortest_distance(self, board, start, goal_row):
        queue = deque([(start, 0)])
        visited = {start}

        directions = [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
        ]

        while queue:
            (row, col), distance = queue.popleft()

            # Chạm tới hàng đích nghĩa là đã tìm thấy đường.
            if row == goal_row:
                return distance

            for row_change, col_change in directions:
                next_cell = (row + row_change, col + col_change)

                if not board.is_inside(*next_cell):
                    continue

                if board.is_edge_blocked((row, col), next_cell):
                    continue

                if next_cell not in visited:
                    visited.add(next_cell)
                    queue.append((next_cell, distance + 1))

        return None

    # BFS ngược từ cả hàng đích: tạo bản đồ khoảng cách cho mọi ô chỉ trong một lần.
    def distances_to_goal(self, board, goal_row):
        distances = {(goal_row, col): 0 for col in range(board.size)}
        queue = deque(distances)
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                adjacent = row + dr, col + dc
                if (board.is_inside(*adjacent) and adjacent not in distances
                        and not board.is_edge_blocked((row, col), adjacent)):
                    distances[adjacent] = distances[(row, col)] + 1
                    queue.append(adjacent)
        return distances

    # Kiểm tra lần lượt cả hai người chơi đều còn đường tới hàng đích.
    def both_players_have_paths(self, board, players):
        for player in players:
            if not self.has_path(board, player.position, player.goal_row):
                return False

        return True