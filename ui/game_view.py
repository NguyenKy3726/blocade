import math

import pygame


# Vẽ giao diện; luật chơi được xử lý trong Game.
class GameView:
    # Khởi tạo Pygame, cửa sổ, font và thông số bàn cờ.
    def __init__(self):
        pygame.init()

        self.width = 1050
        self.height = 800
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Blocade")
        self.clock = pygame.time.Clock()

        # Nạp trực tiếp Arial của Windows để hiển thị dấu tiếng Việt.
        font_path = r"C:\Windows\Fonts\arial.ttf"
        self.title_font = pygame.font.Font(font_path, 34)
        self.title_font.set_bold(True)
        self.font = pygame.font.Font(font_path, 22)
        self.small_font = pygame.font.Font(font_path, 17)

        # Mỗi ô rộng 58 pixel, khe giữa các ô rộng 8 pixel.
        self.board_x = 70
        self.board_y = 110
        self.cell_size = 58
        self.cell_gap = 8
        self.cell_stride = self.cell_size + self.cell_gap

        self.background_color = (247, 241, 228)
        self.board_frame_color = (198, 155, 98)
        self.cell_colors = [(234, 220, 191), (218, 197, 160)]
        # Phe 1 xanh lá, phe 2 xanh nước; xem trước hợp lệ dùng màu nhạt hơn.
        self.player_colors = [(46, 139, 87), (40, 120, 190)]
        self.move_hint_colors = [(85, 145, 90), self.player_colors[1]]
        self.wall_preview_colors = [(132, 204, 158), (133, 192, 235)]
        self.invalid_wall_color = (190, 65, 55)
        self.text_color = (70, 52, 38)
        self.restart_button_rect = pygame.Rect(700, 650, 250, 52)
        self.menu_button_rect = pygame.Rect(700, 720, 250, 52)
        self.undo_button_rect = pygame.Rect(700, 600, 120, 40)
        self.redo_button_rect = pygame.Rect(830, 600, 120, 40)

    # Vẽ chữ lên màn hình tại vị trí được chỉ định.
    def draw_text(self, text, font, color, x, y):
        surface = font.render(text, True, color)
        self.screen.blit(surface, (x, y))

    # Đổi vị trí chuột thành ô bàn cờ; trả về None nếu chuột nằm ngoài ô.
    def cell_at_position(self, mouse_position):
        mouse_x, mouse_y = mouse_position
        relative_x = mouse_x - self.board_x
        relative_y = mouse_y - self.board_y

        if relative_x < 0 or relative_y < 0:
            return None

        col = relative_x // self.cell_stride
        row = relative_y // self.cell_stride

        if row >= 9 or col >= 9:
            return None

        # Phần khe không thuộc về ô nào nên không nhận click.
        if relative_x % self.cell_stride >= self.cell_size:
            return None

        if relative_y % self.cell_stride >= self.cell_size:
            return None

        return row, col

    # Vẽ nền bàn và từng ô riêng lẻ để tạo khe giữa các ô.
    def draw_board(self):
        board_width = 9 * self.cell_size + 8 * self.cell_gap
        board_height = 9 * self.cell_size + 8 * self.cell_gap

        pygame.draw.rect(
            self.screen,
            self.board_frame_color,
            (self.board_x - 6, self.board_y - 6, board_width + 12, board_height + 12),
            border_radius=12,
        )

        for row in range(9):
            for col in range(9):
                x = self.board_x + col * self.cell_stride
                y = self.board_y + row * self.cell_stride
                color = self.cell_colors[(row + col) % 2]

                pygame.draw.rect(
                    self.screen,
                    color,
                    (x, y, self.cell_size, self.cell_size),
                    border_radius=6,
                )

    # Tô viền quân đang tới lượt và đánh dấu các ô có thể đi.
    def draw_move_hints(self, selected_position, legal_moves, player_index=0):
        if selected_position is not None:
            row, col = selected_position
            x = self.board_x + col * self.cell_stride
            y = self.board_y + row * self.cell_stride

            pygame.draw.rect(
                self.screen,
                (245, 190, 70),
                (x, y, self.cell_size, self.cell_size),
                width=4,
                border_radius=6,
            )

        for row, col in legal_moves:
            center = (
                self.board_x + col * self.cell_stride + self.cell_size // 2,
                self.board_y + row * self.cell_stride + self.cell_size // 2,
            )
            pygame.draw.circle(self.screen, self.move_hint_colors[player_index], center, 8)

    # Vẽ quân cờ tại vị trí hiện tại của mỗi người chơi.
    def draw_players(self, game):
        for index, player in enumerate(game.players):
            center = (
                self.board_x + player.col * self.cell_stride + self.cell_size // 2,
                self.board_y + player.row * self.cell_stride + self.cell_size // 2,
            )

            pygame.draw.circle(
                self.screen,
                self.player_colors[index],
                center,
                22,
            )
            pygame.draw.circle(self.screen, (255, 255, 255), center, 22, 3)

            number = self.small_font.render(str(index + 1), True, (255, 255, 255))
            self.screen.blit(number, number.get_rect(center=center))

    # Vẽ lượt chơi, vị trí và số tường còn lại ở bên phải bàn.
    def draw_info(self, game):
        info_x = 700

        self.draw_text("BLOCADE", self.title_font, self.text_color, info_x, 120)

        if game.winner is None:
            status = f"Lượt hiện tại: {game.current_player.name}"
        else:
            status = f"{game.winner.name} chiến thắng!"

        self.draw_text(status, self.font, self.text_color, info_x, 180)

        for index, player in enumerate(game.players):
            y = 250 + index * 145
            self.draw_text(
                player.name,
                self.font,
                self.player_colors[index],
                info_x,
                y,
            )
            self.draw_text(
                f"Vị trí: ({player.row}, {player.col})",
                self.small_font,
                self.text_color,
                info_x,
                y + 35,
            )
            self.draw_text(
                f"Tường còn lại: {player.walls_remaining}",
                self.small_font,
                self.text_color,
                info_x,
                y + 60,
            )

            # Chế độ bot không hiển thị đồng hồ của cả hai bên.
            if game.timer_enabled:
                seconds = math.ceil(game.time_remaining[index])
                state = "đang chạy" if index == game.current_turn and game.winner is None else "dừng"
                self.draw_text(
                    f"Lượt: {seconds}s ({state})",
                    self.small_font, self.player_colors[index], info_x, y + 85,
                )

        mode_label = f"Đấu bot {game.bot_level_name}" if game.mode == "bot" else "Hai người chơi"
        self.draw_text(mode_label, self.small_font, self.text_color, info_x, 215)

        self.draw_text(game.notice, self.small_font, self.text_color, 70, 735)
        self.draw_text("Chuột vào khe: xem trước; click: đặt tường.",
                       self.small_font, self.text_color, 70, 765)

    # Vẽ Chơi lại và Về menu cả khi đang chơi lẫn sau khi ván kết thúc.
    def draw_navigation_buttons(self):
        for rect, text in ((self.restart_button_rect, "Chơi lại"),
                           (self.menu_button_rect, "Về menu")):
            hovered = rect.collidepoint(pygame.mouse.get_pos())
            color = (222, 198, 155) if hovered else (234, 220, 191)
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            pygame.draw.rect(self.screen, self.text_color, rect, width=2, border_radius=8)
            label = self.font.render(text, True, self.text_color)
            self.screen.blit(label, label.get_rect(center=rect.center))

    # Vẽ nút lịch sử, làm mờ khi không có hành động tương ứng.
    def draw_history_button(self, rect, text, enabled):
        hovered = enabled and rect.collidepoint(pygame.mouse.get_pos())
        color = (222, 198, 155) if hovered else (234, 220, 191)
        text_color = self.text_color if enabled else (153, 145, 130)
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, text_color, rect, width=2, border_radius=8)
        label = self.font.render(text, True, text_color)
        self.screen.blit(label, label.get_rect(center=rect.center))

    # Chỉ hiện Undo khi đấu bot; giữ hàm riêng để kiểm tra trạng thái nút.
    def draw_undo_button(self, enabled):
        self.draw_history_button(self.undo_button_rect, "Undo", enabled)

    # Redo nằm cạnh Undo và chỉ bật khi còn nhánh có thể làm lại.
    def draw_redo_button(self, enabled):
        self.draw_history_button(self.redo_button_rect, "Redo", enabled)

    # Vẽ toàn bộ giao diện theo trạng thái ván chơi hiện tại.
    def draw(self, game, selected_position=None, wall_preview=None):
        self.screen.fill(self.background_color)

        self.draw_board()
        self.draw_walls(game)
        self.draw_wall_preview(wall_preview, game.current_turn)

        # Luôn hiện nước đi và viền quân bên đang tới lượt, không cần chọn quân.
        legal_moves = [] if game.is_bot_turn else game.get_legal_moves()
        active_position = (game.current_player.position
                           if game.winner is None and not game.is_bot_turn else None)
        self.draw_move_hints(active_position, legal_moves, game.current_turn)
        self.draw_players(game)
        self.draw_info(game)
        preview_y = 530 if game.mode == "bot" else 580
        instruction_y = 560 if game.mode == "bot" else 610
        if wall_preview is not None:
            orientation, _, _, is_valid = wall_preview
            direction = "ngang" if orientation == "horizontal" else "dọc"
            validity = "hợp lệ" if is_valid else "không hợp lệ"
            self.draw_text(f"Tường {direction}: {validity}", self.small_font,
                           self.text_color, 700, preview_y)
        elif game.is_bot_turn:
            self.draw_text("Bot đang suy nghĩ…", self.small_font, self.text_color, 700, preview_y)
        elif game.winner is None:
            self.draw_text("Đưa chuột vào khe ngang/dọc.", self.small_font,
                           self.text_color, 700, preview_y)
        if game.winner is None and not game.is_bot_turn:
            self.draw_text("Click ô được đánh dấu để đi.", self.small_font,
                           self.text_color, 700, instruction_y)

        if game.mode == "bot":
            self.draw_undo_button(game.can_undo)
            self.draw_redo_button(game.can_redo)
        self.draw_navigation_buttons()
        pygame.display.flip()

    # Chọn khe ngang/dọc gần chuột nhất; giao điểm bằng nhau không tự chọn hướng.
    def wall_at_position(self, mouse_position):
        candidates = []
        for orientation in ("horizontal", "vertical"):
            anchor = self.wall_anchor_at_position(mouse_position, orientation)
            if anchor is not None:
                rect = self._wall_rect(orientation, *anchor)
                distance = (abs(mouse_position[1] - rect.centery) if orientation == "horizontal"
                            else abs(mouse_position[0] - rect.centerx))
                candidates.append((distance, orientation, *anchor))
        if not candidates:
            return None
        candidates.sort()
        if len(candidates) == 2 and candidates[0][0] == candidates[1][0]:
            return None
        return candidates[0][1:]

    # Đổi vị trí chuột thành điểm neo của tường.
    # Người chơi phải đưa chuột vào khe đúng hướng.
    def wall_anchor_at_position(self, mouse_position, orientation):
        mouse_x, mouse_y = mouse_position
        relative_x = mouse_x - self.board_x
        relative_y = mouse_y - self.board_y

        if relative_x < 0 or relative_y < 0:
            return None

        col = relative_x // self.cell_stride
        row = relative_y // self.cell_stride
        x_in_stride = relative_x % self.cell_stride
        y_in_stride = relative_y % self.cell_stride

        board_extent = 9 * self.cell_size + 8 * self.cell_gap
        if relative_x >= board_extent or relative_y >= board_extent:
            return None

        if orientation == "horizontal":
            if y_in_stride < self.cell_size or row >= 8:
                return None
            # Khe dưới ô cuối vẫn thuộc tường neo ở cột 7.
            col = min(col, 7)
        elif orientation == "vertical":
            if x_in_stride < self.cell_size or col >= 8:
                return None
            row = min(row, 7)
        else:
            return None

        return row, col

    # Tính hình chữ nhật của tường để dùng khi vẽ tường thật và hình xem trước.
    def _wall_rect(self, orientation, row, col):
        if orientation == "horizontal":
            x = self.board_x + col * self.cell_stride
            y = self.board_y + row * self.cell_stride + self.cell_size
            width = 2 * self.cell_size + self.cell_gap
            height = self.cell_gap
        else:
            x = self.board_x + col * self.cell_stride + self.cell_size
            y = self.board_y + row * self.cell_stride
            width = self.cell_gap
            height = 2 * self.cell_size + self.cell_gap

        return pygame.Rect(x, y, width, height)

    # Vẽ những bức tường đã được đặt trên bàn cờ.
    def draw_walls(self, game):
        for orientation, row, col in game.board.walls:
            owner = game.wall_owners.get((orientation, row, col))
            wall_color = self.player_colors[owner] if owner is not None else (112, 62, 39)
            wall_rect = self._wall_rect(orientation, row, col)
            pygame.draw.rect(
                self.screen,
                wall_color,
                wall_rect,
                border_radius=3,
            )

    # Tường hợp lệ dùng màu phe nhạt hơn; tường không hợp lệ luôn màu đỏ.
    def draw_wall_preview(self, wall_preview, player_index=0):
        if wall_preview is None:
            return

        orientation, row, col, is_valid = wall_preview
        wall_rect = self._wall_rect(orientation, row, col)

        if is_valid:
            color = self.wall_preview_colors[player_index]
        else:
            color = self.invalid_wall_color

        pygame.draw.rect(
            self.screen,
            color,
            wall_rect,
            border_radius=3,
        )
