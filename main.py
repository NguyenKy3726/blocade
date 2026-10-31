import pygame

from game.game import Game
from ui.game_view import GameView
from ui.controller import GameController


# Tạo phần quản lý luật, giao diện và điều khiển thao tác.
game = Game()
view = GameView()
controller = GameController(game, view)

running = True

# Vòng lặp chính chuyển từng sự kiện cho GameController xử lý.
while running:
    for event in pygame.event.get():
        running = controller.handle_event(event)

    # Cập nhật hình xem trước theo vị trí chuột hiện tại.
    wall_preview = controller.get_wall_preview(pygame.mouse.get_pos())

    # Vẽ lại giao diện với quân được chọn và tường xem trước.
    view.draw(
        game,
        controller.selected_position,
        wall_preview,
    )

    # Giới hạn vòng lặp ở 60 khung hình mỗi giây.
    view.clock.tick(60)

# Giải phóng tài nguyên Pygame sau khi thoát vòng lặp.
pygame.quit()