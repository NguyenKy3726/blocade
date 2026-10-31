from game.game import Game


game = Game()

print("Kích thước bàn:", game.board.size)
print("Lượt hiện tại:", game.current_player.name)

for player in game.players:
    print(
        player.name,
        "| vị trí:", player.position,
        "| hàng đích:", player.goal_row,
        "| số tường:", player.walls_remaining,
    )