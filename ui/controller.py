import pygame


# Chuyển thao tác chuột và bàn phím thành yêu cầu cho game.
class GameController:
    # Kết nối game với giao diện và khởi tạo trạng thái thao tác.
    def __init__(self, game, view):
        self.game = game
        self.view = view
        self.selected_position = None
        self.wall_orientation = "horizontal"
        self.placing_wall = False

    # Nhận diện click trái trong nút Chơi lại, tách khỏi thao tác bàn cờ.
    def is_restart_event(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.view.restart_button_rect.collidepoint(event.pos)
        )

    # Chơi lại trên cùng cửa sổ và bỏ trạng thái thao tác của ván cũ.
    def restart_game(self):
        self.game.reset()
        self.selected_position = None
        self.wall_orientation = "horizontal"
        self.placing_wall = False

    # Cập nhật đồng hồ và bỏ lựa chọn cũ khi người chơi bị mất lượt.
    def update(self):
        expired = self.game.update_time()
        if expired:
            self.selected_position = None
            self.placing_wall = False
        return expired

    # Xử lý sự kiện đóng cửa sổ, chọn hướng tường và click chuột.
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False

        # Nút vẫn dùng được sau thắng ván hoặc tại đúng mốc hết giờ.
        if self.is_restart_event(event):
            self.restart_game()
            return True

        if self.update():
            return True

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
            if self._wall_at_position(event.pos) is not None:
                self._handle_wall_click(event.pos)
            else:
                self._handle_move_click(event.pos)

        return True

    # Click thẳng vào ô hợp lệ để đi, không cần click chọn quân trước.
    def _handle_move_click(self, mouse_position):
        if self.game.winner is not None:
            return

        clicked_cell = self.view.cell_at_position(mouse_position)
        if clicked_cell in self.game.get_legal_moves():
            if self.game.move_current_player(clicked_cell):
                self.placing_wall = False

        self.selected_position = None

    # Chọn hướng theo khe chuột đang trỏ; H/V chỉ là cách khóa hướng tùy chọn.
    def _wall_at_position(self, mouse_position):
        if self.placing_wall:
            anchor = self.view.wall_anchor_at_position(mouse_position, self.wall_orientation)
            if anchor is None:
                return None
            return self.wall_orientation, *anchor
        return self.view.wall_at_position(mouse_position)

    # Xác nhận đặt tường bằng chuột; chỉ thành công mới chuyển lượt.
    def _handle_wall_click(self, mouse_position):
        if self.game.winner is not None:
            return
        wall = self._wall_at_position(mouse_position)
        if wall is None:
            return
        if self.game.place_wall_current_player(*wall):
            self.placing_wall = False
            self.selected_position = None

    # Xem trước cả hai hướng bằng chuột, không làm thay đổi trạng thái ván.
    def get_wall_preview(self, mouse_position):
        if self.game.winner is not None:
            return None
        wall = self._wall_at_position(mouse_position)
        if wall is None:
            return None
        return (*wall, self.game.can_place_wall_current_player(*wall))
