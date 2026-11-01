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
        # Bỏ click cũ sau điều hướng hoặc Undo/Redo, tránh đánh lại ngay nước vừa lùi.
        if not running or navigating:
            break

    if not running:
        break

    # Bot đáp trả sau toàn bộ click: người không thể click thay quân bot trong lượt đó.
    app.update_bot()
    # Vẽ menu hoặc bàn cờ; chỉ tính hình xem trước khi đang trong ván.
    app.draw()
    view.clock.tick(60)

# Giải phóng tài nguyên khi đóng cửa sổ hoặc chọn Thoát trên menu.
pygame.quit()
