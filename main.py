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
    # Cập nhật giờ trước thao tác; bỏ click cũ trong khung hình vừa hết giờ.
    expired = controller.update()
    for event in pygame.event.get():
        restarting = controller.is_restart_event(event)
        if expired and event.type != pygame.QUIT and not restarting:
            continue
        running = controller.handle_event(event)
        # Bỏ phần sự kiện còn lại của ván cũ sau khi bấm Chơi lại.
        if not running or restarting:
            break

    if not running:
        break

    # Cập nhật hình xem trước theo vị trí chuột hiện tại.
    wall_preview = controller.get_wall_preview(pygame.mouse.get_pos())

    # Vẽ trạng thái ván hiện tại, gợi ý nước đi và tường xem trước.
    view.draw(
        game,
        controller.selected_position,
        wall_preview,
    )

    # Giới hạn vòng lặp ở 60 khung hình mỗi giây.
    view.clock.tick(60)

# Giải phóng tài nguyên Pygame sau khi thoát vòng lặp.
pygame.quit()
