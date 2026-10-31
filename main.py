import pygame

from game.game import Game
from ui.game_view import GameView


# Tạo đối tượng quản lý luật chơi và đối tượng hiển thị.
game = Game()
view = GameView()

# Lưu ô đang được chọn; ban đầu chưa chọn quân nào.
selected_position = None
running = True

# Vòng lặp chính nhận sự kiện chuột và cập nhật màn hình.
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Khi click chuột trái, chọn quân hoặc đi tới ô hợp lệ.
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game.winner is None:
                clicked_cell = view.cell_at_position(event.pos)

                if selected_position is None:
                    if clicked_cell == game.current_player.position:
                        selected_position = clicked_cell
                else:
                    if clicked_cell in game.get_legal_moves():
                        game.move_current_player(clicked_cell)
                        selected_position = None
                    else:
                        selected_position = None

    # Vẽ lại giao diện; quân được chọn sẽ hiện các ô có thể đi.
    view.draw(game, selected_position)
    view.clock.tick(60)

# Đóng Pygame khi người chơi thoát cửa sổ.
pygame.quit()