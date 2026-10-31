import pygame


class GameView:
    # GameView chỉ vẽ giao diện; luật chơi được xử lý trong Game.
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
        self.player_colors = [(178, 68, 58), (55, 100, 154)]
        self.text_color = (70, 52, 38)

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

    # Tô viền quân đang được chọn và đánh dấu các ô có thể đi.
    def draw_move_hints(self, selected_position, legal_moves):
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
            pygame.draw.circle(self.screen, (85, 145, 90), center, 8)

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
            y = 250 + index * 105
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

    # Vẽ toàn bộ giao diện theo trạng thái ván chơi hiện tại.
    def draw(self, game, selected_position=None, wall_preview=None):
        self.screen.fill(self.background_color)

        self.draw_board()
        self.draw_walls(game)
        self.draw_wall_preview(wall_preview)

        legal_moves = []
        if selected_position == game.current_player.position:
            legal_moves = game.get_legal_moves()

        self.draw_move_hints(selected_position, legal_moves)
        self.draw_players(game)
        self.draw_info(game)

        pygame.display.flip()

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

        if orientation == "horizontal":
            if y_in_stride < self.cell_size:
                return None
        elif orientation == "vertical":
            if x_in_stride < self.cell_size:
                return None
        else:
            return None

        if row >= 8 or col >= 8:
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
        wall_color = (112, 62, 39)

        for orientation, row, col in game.board.walls:
            wall_rect = self._wall_rect(orientation, row, col)
            pygame.draw.rect(
                self.screen,
                wall_color,
                wall_rect,
                border_radius=3,
            )

    # Vẽ tường xem trước; xanh nghĩa là hợp lệ, đỏ nghĩa là bị từ chối.
    def draw_wall_preview(self, wall_preview):
        if wall_preview is None:
            return

        orientation, row, col, is_valid = wall_preview
        wall_rect = self._wall_rect(orientation, row, col)

        if is_valid:
            color = (75, 150, 85)
        else:
            color = (190, 65, 55)

        pygame.draw.rect(
            self.screen,
            color,
            wall_rect,
            border_radius=3,
        )