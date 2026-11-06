import pygame

from game.game import Game
from ui.game_view import GameView
from ui.controller import GameController
from ui.menu_view import MenuView
from pattern.state import AppController


# Dùng một cửa sổ cho cả menu và bàn cờ; ứng dụng bắt đầu tại menu.
game = Game()
view = GameView()
controller = GameController(game, view)
menu_view = MenuView(view)
app = AppController(controller, menu_view)
running = True

# State điều phối menu/lượt/kết thúc; controller tạo Command từ click trong ván.
while running:
    # Menu và hướng dẫn không tính giờ; hai người vào ngay, bot chọn cấp/lượt.
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

    # Sau click, BotTurnState tiến một đoạn tìm kiếm hoặc đáp trả; vẫn nhường UI mỗi khung hình.
    app.update_bot()
    # Vẽ chất liệu gỗ và nội suy animation; Game/Command đã cập nhật trước đó.
    # Âm thanh chỉ phát khi có hành động, không phát lại mỗi lần vẽ.
    app.draw()
    view.clock.tick(60)

# Giải phóng tài nguyên khi đóng cửa sổ bằng nút X.
pygame.quit()
