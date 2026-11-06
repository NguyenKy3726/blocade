from pattern.state.playing_state import PlayingState


# Trạng thái cho phép người chơi thao tác và cập nhật đồng hồ lượt người.
class HumanTurnState(PlayingState):
    # Khi hết giờ, AppController chuyển sang trạng thái của lượt mới.
    def update(self, app):
        return app.game_controller.update()
