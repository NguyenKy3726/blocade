import math
from pathlib import Path

import pygame

from ui.presentation import GamePresentation
from ui.sound_effects import SoundEffects
from ui.wood_theme import WoodTheme, shade


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

        # Font đi kèm repo, không phụ thuộc hệ điều hành hoặc thư mục đang chạy.
        font_path = str(Path(__file__).resolve().parents[1] / "assets" / "fonts" / "NotoSans-Regular.ttf")
        self.title_font = pygame.font.Font(font_path, 34)
        self.title_font.set_bold(True)
        self.font = pygame.font.Font(font_path, 22)
        self.small_font = pygame.font.Font(font_path, 17)
        self.badge_font = pygame.font.Font(font_path, 13)
        self.theme = WoodTheme()
        self.motion = GamePresentation()
        self.audio = SoundEffects()
        self.board_surface = None

        # Mỗi ô rộng 58 pixel, khe giữa các ô rộng 8 pixel.
        self.board_x = 70
        self.board_y = 110
        self.cell_size = 58
        self.cell_gap = 8
        self.cell_stride = self.cell_size + self.cell_gap
        self.board_extent = 9 * self.cell_size + 8 * self.cell_gap
        self.info_panel_rect = pygame.Rect(
            680, self.board_y - 18, 325, self.board_extent + 36
        )
        self.player_card_top = 238
        self.player_card_height = 118
        self.player_card_gap = 27

        second_card_bottom = (
            self.player_card_top + 2 * self.player_card_height + self.player_card_gap
        )
        history_y = second_card_bottom + self.player_card_gap
        self.undo_button_rect = pygame.Rect(700, history_y, 120, 40)
        self.redo_button_rect = pygame.Rect(830, history_y, 120, 40)
        self.restart_button_rect = pygame.Rect(700, history_y + 50, 250, 52)
        self.menu_button_rect = pygame.Rect(700, history_y + 110, 250, 52)
        self.sound_button_rect = pygame.Rect(770, 32, 160, 48)

        self.background_color = (237, 223, 200)
        self.board_frame_color = (146, 101, 59)
        self.cell_colors = [(235, 205, 163), (216, 180, 131)]
        # Tô nhẹ hàng đích theo màu của hai phe để dễ nhận ra hướng đi.
        self.goal_row_colors = {
            0: [(229, 239, 220), (219, 232, 207)],
            8: [(224, 235, 244), (212, 226, 238)],
        }
        # Quân và tường nhuộm màu theo phe; không còn vẽ số trên quân.
        self.player_colors = [(46, 139, 87), (40, 120, 190)]
        self.move_hint_colors = [(85, 145, 90), self.player_colors[1]]
        self.wall_preview_colors = [(132, 204, 158), (133, 192, 235)]
        self.text_color = self.theme.text_color

    # Nền gỗ được cache; các màn hình chỉ blit lại, không tạo vân mỗi frame.
    def draw_background(self):
        self.screen.blit(self.theme.wood((self.width, self.height), self.background_color,
                                        seed=41, radius=0), (0, 0))

    # Dùng vùng nút thật đang hiển thị, kể cả khi có khung chiến thắng.
    def restart_rect(self, game):
        return self.restart_button_rect

    # Trả về vùng Về menu cố định trên bảng thông tin.
    def menu_rect(self, game):
        return self.menu_button_rect

    # Phản hồi nhấn nút dùng chung; không tạo hoặc thực thi Command của ván.
    def button_feedback(self, rect):
        self.theme.press(rect)
        self.audio.play("click")

    # Cài đặt âm thanh có trên cả menu, hướng dẫn, trong ván và sau thắng.
    def draw_sound_button(self):
        label = "Âm thanh: Bật" if self.audio.enabled else "Âm thanh: Tắt"
        self.theme.button(self.screen, self.sound_button_rect, label, self.small_font,
                          enabled=self.audio.available)

    # Reset chỉ xóa hình chuyển động, giữ cài đặt âm thanh trong phiên đang chạy.
    def reset_effects(self, game):
        self.motion.reset(game.board)

    # Quan sát thay đổi sau Command thành công, không viết ngược vào luật hoặc lịch sử.
    def present_action(self, game, before, kind="action"):
        self.motion.record(game, before, kind)
        if kind in ("undo", "redo"):
            self.audio.play("undo")
        elif len(game.board.walls) > len(before["walls"]):
            self.audio.play("wall")
        else:
            self.audio.play("move")
        if before["winner"] is None and game.winner is not None:
            self.audio.play("win")

    # Vẽ chữ lên màn hình tại vị trí được chỉ định.
    def draw_text(self, text, font, color, x, y):
        surface = font.render(text, True, color)
        self.screen.blit(surface, (x, y))

    # Đảo trục hàng khi vẽ để người/xanh lá (hàng luật 0) nằm dưới màn hình.
    def model_to_screen_point(self, position):
        x, y = position
        return x, self.board_y + self.board_extent - 1 - (y - self.board_y)

    # Phép đối xứng là nghịch đảo của chính nó; dùng khi nhận click vào bàn.
    def screen_to_model_point(self, position):
        return self.model_to_screen_point(position)

    # Tâm ô trên màn hình, dùng chung cho quân, chấm gợi ý và kiểm tra chuột.
    def cell_center(self, row, col):
        return self.model_to_screen_point((
            self.board_x + col * self.cell_stride + self.cell_size // 2,
            self.board_y + row * self.cell_stride + self.cell_size // 2,
        ))

    # Hình chữ nhật ô sau khi phản chiếu bàn; không đổi tọa độ luật trong Game.
    def cell_rect(self, row, col):
        return pygame.Rect(self.board_x + col * self.cell_stride,
                           self.board_y + self.board_extent - row * self.cell_stride - self.cell_size,
                           self.cell_size, self.cell_size)

    # Đổi vị trí chuột thành ô bàn cờ; trả về None nếu chuột nằm ngoài ô.
    def cell_at_position(self, mouse_position):
        mouse_x, mouse_y = self.screen_to_model_point(mouse_position)
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

    # Tạo mặt bàn một lần: khung gỗ tối và các ô có vân khác nhau, giữ nguyên khe.
    def draw_board(self):
        origin = (self.board_x - 18, self.board_y - 18)
        if self.board_surface is None:
            size = self.board_extent + 36
            self.board_surface = pygame.Surface((size, size + 6), pygame.SRCALPHA)
            self.theme.panel(self.board_surface, pygame.Rect(0, 0, size, size),
                             self.board_frame_color, radius=18, seed=21)
            for row in range(9):
                for col in range(9):
                    rect = self.cell_rect(row, col).move(-origin[0], -origin[1])
                    color = self.goal_row_colors.get(
                        row, self.cell_colors
                    )[(row + col) % 2]
                    self.board_surface.blit(self.theme.wood(rect.size, color,
                                                            seed=(row * 9 + col) % 7, radius=5), rect)
                    pygame.draw.rect(self.board_surface, shade(color, 18), rect, 1, border_radius=5)
        self.screen.blit(self.board_surface, origin)

    # Tô viền quân đang tới lượt và đánh dấu các ô có thể đi.
    def draw_move_hints(self, selected_position, legal_moves, player_index=0):
        if selected_position is not None:
            row, col = selected_position

            pygame.draw.rect(
                self.screen,
                (245, 190, 70),
                self.cell_rect(row, col),
                width=4,
                border_radius=6,
            )

        for row, col in legal_moves:
            center = self.cell_center(row, col)
            pygame.draw.circle(self.screen, self.move_hint_colors[player_index], center, 8)

    # Vẽ đĩa gỗ không số tại điểm nội suy; màu và vòng sáng xác định phe/lượt.
    def draw_players(self, game):
        if self.motion.board is not game.board:
            self.motion.reset(game.board)
        for index, player in enumerate(game.players):
            row, col = self.motion.position(index, player.position)
            center = self.cell_center(row, col)
            self.theme.pawn(self.screen, center, self.player_colors[index],
                            active=game.winner is None and game.current_turn == index)

    # Vẽ lượt chơi, tên và số tường; không hiển thị tọa độ nội bộ.
    def draw_info(self, game):
        info_x = 700

        self.draw_text("BLOCADE", self.title_font, self.text_color, info_x, 120)

        if game.winner is None:
            status = f"Lượt hiện tại: {game.current_player.name}"
        else:
            status = self.victory_message(game)

        self.draw_text(status, self.font, self.text_color, info_x, 180)

        for index, player in enumerate(game.players):
            card_top = self.player_card_top + index * (
                self.player_card_height + self.player_card_gap
            )
            y = card_top + 12
            card = pygame.Rect(690, card_top, 295, self.player_card_height)
            self.theme.panel(self.screen, card, (244, 231, 207), radius=12, seed=5, shadow=False)
            if index == game.current_turn and game.winner is None:
                pygame.draw.rect(self.screen, self.player_colors[index], card, 3, border_radius=12)
                self.draw_text("ĐANG ĐI", self.badge_font, self.player_colors[index], 903, y + 6)
            self.draw_text(
                player.name,
                self.font,
                self.player_colors[index],
                info_x,
                y,
            )
            self.draw_text(
                f"Tường còn lại: {player.walls_remaining}",
                self.small_font,
                self.text_color,
                info_x,
                y + 35,
            )

            # Chế độ bot không hiển thị đồng hồ của cả hai bên.
            if game.timer_enabled:
                seconds = math.ceil(game.time_remaining[index])
                state = "đang chạy" if index == game.current_turn and game.winner is None else "dừng"
                self.draw_text(
                    f"Lượt: {seconds}s ({state})",
                    self.small_font, self.player_colors[index], info_x, y + 65,
                )

        mode_label = f"Đấu bot {game.bot_level_name}" if game.mode == "bot" else "Hai người chơi"
        self.draw_text(mode_label, self.small_font, self.text_color, info_x, 215)

        self.draw_text(game.notice, self.small_font, self.text_color, 70, 735)

    # Hiển thị kết quả theo góc nhìn người chơi khi đấu bot.
    def victory_message(self, game):
        if game.mode == "bot":
            return "Bạn thắng!" if game.winner is game.players[0] else "Bạn thua!"
        return f"{game.winner.name} chiến thắng!"

    # Vẽ hai nút điều hướng ở đúng vị trí trên bảng thông tin trong mọi trạng thái.
    def draw_navigation_buttons(self):
        for rect, text in ((self.restart_button_rect, "Chơi lại"),
                           (self.menu_button_rect, "Về menu")):
            self.theme.button(self.screen, rect, text, self.font)

    # Vẽ nút lịch sử, làm mờ khi không có hành động tương ứng.
    def draw_history_button(self, rect, text, enabled):
        self.theme.button(self.screen, rect, text, self.font, enabled)

    # Chỉ hiện Undo khi đấu bot; giữ hàm riêng để kiểm tra trạng thái nút.
    def draw_undo_button(self, enabled):
        self.draw_history_button(self.undo_button_rect, "Undo", enabled)

    # Redo nằm cạnh Undo và chỉ bật khi còn nhánh có thể làm lại.
    def draw_redo_button(self, enabled):
        self.draw_history_button(self.redo_button_rect, "Redo", enabled)

    # Phủ bàn cờ, đặt thông báo trong khung kết quả và giữ nút điều hướng ở bảng bên.
    def draw_victory(self, game):
        veil = pygame.Surface((self.board_extent + 36, self.board_extent + 36), pygame.SRCALPHA)
        veil.fill((49, 34, 23, 120))
        self.screen.blit(veil, (self.board_x - 18, self.board_y - 18))

        panel = pygame.Rect(105, 270, 516, 258)
        self.theme.panel(self.screen, panel, (244, 225, 190), radius=20, seed=31)
        color = self.player_colors[game.players.index(game.winner)]
        title = self.title_font.render(self.victory_message(game), True, self.text_color)
        self.screen.blit(title, title.get_rect(center=(363, 320)))
        if game.mode != "bot":
            name = self.font.render(game.winner.name, True, color)
            self.screen.blit(name, name.get_rect(center=(363, 375)))
        self.theme.pawn(self.screen, (153, 365), color)
        self.theme.pawn(self.screen, (573, 365), color)

    # Vẽ toàn bộ giao diện theo trạng thái ván chơi hiện tại.
    def draw(self, game, selected_position=None, wall_preview=None):
        if self.motion.board is not game.board:
            self.motion.reset(game.board)
        self.draw_background()
        self.theme.panel(self.screen, self.info_panel_rect,
                         (238, 219, 185), radius=18, seed=19)

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
        if game.is_bot_turn:
            self.draw_text("Bot đang suy nghĩ…", self.small_font, self.text_color, 700, 530)

        if game.mode == "bot":
            history_enabled = game.winner is None
            self.draw_undo_button(history_enabled and game.can_undo)
            self.draw_redo_button(history_enabled and game.can_redo)
        self.draw_navigation_buttons()
        if game.winner is not None:
            self.draw_victory(game)
        self.draw_sound_button()
        pygame.display.flip()

    # Chọn khe ngang/dọc gần chuột nhất; giao điểm bằng nhau không tự chọn hướng.
    def wall_at_position(self, mouse_position):
        candidates = []
        for orientation in ("horizontal", "vertical"):
            anchor = self.wall_anchor_at_position(mouse_position, orientation)
            if anchor is not None:
                rect = self._model_wall_rect(orientation, *anchor)
                model_mouse = self.screen_to_model_point(mouse_position)
                distance = (abs(model_mouse[1] - rect.centery) if orientation == "horizontal"
                            else abs(model_mouse[0] - rect.centerx))
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
        mouse_x, mouse_y = self.screen_to_model_point(mouse_position)
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

    # Vị trí tường theo tọa độ luật, trước khi đổi sang màn hình.
    def _model_wall_rect(self, orientation, row, col):
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

    # Phản chiếu tường thật/xem trước giống hệt quân và ô để hình vẽ khớp luật.
    def _wall_rect(self, orientation, row, col):
        rect = self._model_wall_rect(orientation, row, col)
        rect.y = self.board_y + self.board_extent - (rect.y - self.board_y) - rect.height
        return rect

    # Tường nhuộm màu có vân; chỉ tường mới đặt được tăng độ đậm ngắn.
    def draw_walls(self, game):
        for orientation, row, col in game.board.walls:
            owner = game.wall_owners.get((orientation, row, col))
            wall_color = self.player_colors[owner] if owner is not None else (112, 62, 39)
            wall_rect = self._wall_rect(orientation, row, col)
            self.theme.wall(self.screen, wall_rect, wall_color, self.motion.wall_alpha((orientation, row, col)))

    # Chỉ vẽ tường xem trước khi vị trí hợp lệ; vị trí sai được ẩn hoàn toàn.
    def draw_wall_preview(self, wall_preview, player_index=0):
        if wall_preview is None:
            return

        orientation, row, col, is_valid = wall_preview
        if not is_valid:
            return

        wall_rect = self._wall_rect(orientation, row, col)
        color = self.wall_preview_colors[player_index]
        self.theme.wall(self.screen, wall_rect, color)
