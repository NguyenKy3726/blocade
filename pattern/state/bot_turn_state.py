from pattern.state.playing_state import PlayingState


# Trạng thái cho phép controller tiếp tục tính nước đi của bot.
class BotTurnState(PlayingState):
    # Tính tiếp một đoạn rồi trả UI; Command cuối mới thay đổi ván thật.
    def update_bot(self, app):
        return app.game_controller.play_bot_turn()
