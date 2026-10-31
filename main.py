import pygame

from game.game import Game
from ui.game_view import GameView
from ui.controller import GameController
from ui.menu_view import MenuView
from ui.app_controller import AppController


# Dùng một cửa sổ cho cả menu và bàn cờ; ứng dụng bắt đầu tại menu.
game = Game()
view = GameView()
controller = GameController(game, view)
menu_view = MenuView(view)
app = AppController(controller, menu_view)
running = True

# Điều hướng trước; khi vào ván, controller tạo và thực thi Command từ click.
while running:
    # Menu không tính giờ. Trong ván, cập nhật giờ trước các thao tác.
    expired = app.update()
    for event in pygame.event.get():
        navigating = app.is_navigation_event(event)
        if expired and event.type != pygame.QUIT and not navigating:
            continue
        running = app.handle_event(event)
        # Không để click từ màn hình/ván cũ lọt sang sau khi điều hướng.
        if not running or navigating:
            break

    if not running:
        break

    # Vẽ menu hoặc bàn cờ; chỉ tính hình xem trước khi đang trong ván.
    app.draw()
    view.clock.tick(60)

# Giải phóng tài nguyên khi đóng cửa sổ hoặc chọn Thoát trên menu.
pygame.quit()
