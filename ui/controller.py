import pygame


class GameController:
    # GameController kết nối thao tác người chơi với Game và GameView.
    def __init__(self, game, view):
        self.game = game
        self.view = view
        self.selected_position = None
        self.wall_orientation = "horizontal"
        self.placing_wall = False

    # Xử lý sự kiện đóng cửa sổ, chọn hướng tường và click chuột.
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_h:
                self.wall_orientation = "horizontal"
                self.placing_wall = True
                self.selected_position = None

            elif event.key == pygame.K_v:
                self.wall_orientation = "vertical"
                self.placing_wall = True
                self.selected_position = None

            elif event.key == pygame.K_ESCAPE:
                self.placing_wall = False
                self.selected_position = None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.placing_wall:
                self._handle_wall_click(event.pos)
            else:
                self._handle_move_click(event.pos)

        return True

    # Chọn quân hiện tại hoặc di chuyển tới một ô đang được đánh dấu hợp lệ.
    def _handle_move_click(self, mouse_position):
        if self.game.winner is not None:
            return

        clicked_cell = self.view.cell_at_position(mouse_position)

        if self.selected_position is None:
            if clicked_cell == self.game.current_player.position:
                self.selected_position = clicked_cell
            return

        if clicked_cell in self.game.get_legal_moves():
            self.game.move_current_player(clicked_cell)

        self.selected_position = None

    # Xác nhận đặt tường tại vị trí chuột nếu vị trí đó hợp lệ.
    def _handle_wall_click(self, mouse_position):
        if self.game.winner is not None:
            return

        anchor = self.view.wall_anchor_at_position(
            mouse_position,
            self.wall_orientation,
        )

        if anchor is None:
            return

        row, col = anchor
        placed = self.game.place_wall_current_player(
            self.wall_orientation,
            row,
            col,
        )

        if placed:
            self.placing_wall = False

    # Trả thông tin tường xem trước để GameView vẽ màu xanh hoặc đỏ.
    def get_wall_preview(self, mouse_position):
        if not self.placing_wall or self.game.winner is not None:
            return None

        anchor = self.view.wall_anchor_at_position(
            mouse_position,
            self.wall_orientation,
        )

        if anchor is None:
            return None

        row, col = anchor
        is_valid = self.game.can_place_wall_current_player(
            self.wall_orientation,
            row,
            col,
        )

        return self.wall_orientation, row, col, is_valid