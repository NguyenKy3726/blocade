import os
import random
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from pattern.command import MoveCommand, PlaceWallCommand
from game.game import Game
from tests.support import start_game
from pattern.state import AppController
from ui.controller import GameController
from ui.game_view import GameView
from ui.menu_view import MenuView
from ui.sound_effects import SoundEffects
from pattern.state import GameOverState, HumanTurnState, MenuState


# Kiểm tra hiệu ứng mới qua controller thật, dùng giờ giả thay vì chờ animation.
class WoodUITests(unittest.TestCase):
    # Âm WAV vẫn nạp bằng mixer SDL dummy; đồng hồ hình vẽ độc lập với luật.
    def setUp(self):
        self.now = 100.0
        self.game = Game(time_source=lambda: self.now)
        self.view = GameView()
        self.view.motion.time_source = lambda: self.now
        self.view.theme.time_source = lambda: self.now
        self.controller = GameController(self.game, self.view)
        self.menu = MenuView(self.view)
        self.app = AppController(self.controller, self.menu)

    # Hủy tác vụ bot và giải phóng cả video lẫn mixer sau mỗi test.
    def tearDown(self):
        self.controller.cancel_search()
        pygame.quit()

    # Mô phỏng click trái ở tâm vùng điều khiển đang hiển thị.
    def click(self, rect):
        return self.app.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))

    # Quân dịch chuyển ở hình vẽ nhưng Game/Command đã ở đích ngay, không ghi thêm lịch sử.
    def test_move_animation_does_not_change_rules_or_history(self):
        start_game(self.app, self.menu)
        command = MoveCommand(self.game, (1, 4))
        self.assertTrue(self.controller.execute_command(command))
        self.assertEqual(self.game.players[0].position, (1, 4))
        self.assertEqual(self.view.motion.position(0, (1, 4)), (0, 4))
        self.now += 0.1
        halfway = self.view.motion.position(0, (1, 4))
        self.assertGreater(halfway[0], 0)
        self.assertLess(halfway[0], 1)
        before = self.game.capture_state()
        self.view.draw(self.game)
        self.assertEqual(self.game.capture_state(), before)
        self.assertEqual(self.game.command_history, [command])
        self.now += 0.2
        self.assertEqual(self.view.motion.position(0, (1, 4)), (1, 4))
        self.assertEqual(self.view.motion.moves, {})

    # Tường mới mờ rồi rõ, nhưng cạnh chắn và kiểm tra BFS có tác dụng ngay.
    def test_wall_appearance_and_reset_cancel_effects(self):
        wall = ("horizontal", 2, 2)
        self.assertTrue(self.controller.execute_command(PlaceWallCommand(self.game, *wall)))
        self.assertTrue(self.game.board.is_edge_blocked((2, 2), (3, 2)))
        self.assertEqual(self.view.motion.wall_alpha(wall), 80)
        self.now += 0.09
        self.assertGreater(self.view.motion.wall_alpha(wall), 80)
        self.assertLess(self.view.motion.wall_alpha(wall), 255)
        self.now += 0.1
        self.assertEqual(self.view.motion.wall_alpha(wall), 255)
        self.controller.restart_game()
        self.assertEqual(self.view.motion.moves, {})
        self.assertEqual(self.view.motion.wall_births, {})
        self.assertIs(self.view.motion.board, self.game.board)

    # Undo/Redo khi quân hoặc tường còn đang chuyển động phải khôi phục hình ngay.
    def test_undo_redo_during_animation_has_no_ghosts(self):
        start_game(self.app, self.menu)
        before = self.game.capture_state()
        self.controller.execute_command(MoveCommand(self.game, (1, 4)))
        self.controller.execute_command(PlaceWallCommand(self.game, "vertical", 3, 3))
        after = self.game.capture_state()
        self.assertTrue(self.view.motion.moves)
        self.assertTrue(self.view.motion.wall_births)
        self.click(self.view.undo_button_rect)
        self.assertEqual(self.game.capture_state(), before)
        self.assertEqual(self.view.motion.moves, {})
        self.assertEqual(self.view.motion.wall_births, {})
        with patch.object(self.controller.bot_strategy, "choose_command") as choose:
            self.click(self.view.redo_button_rect)
            self.assertFalse(self.app.update_bot())
            choose.assert_not_called()
        self.assertEqual(self.game.capture_state(), after)
        self.assertEqual(self.view.motion.moves, {})
        self.assertEqual(self.view.motion.wall_births, {})
        self.click(self.view.menu_rect(self.game))
        self.assertIs(type(self.app.state), MenuState)
        self.assertEqual(self.view.motion.moves, {})

    # Người và bot chỉ phát tiếng khi đi thật; preview, nước sai và redraw không phát.
    def test_action_sounds_only_after_success(self):
        start_game(self.app, self.menu)
        self.assertTrue(self.view.audio.available)
        with patch.object(self.view.audio, "play", wraps=self.view.audio.play) as play:
            self.assertFalse(self.controller.execute_command(MoveCommand(self.game, (4, 4))))
            self.controller.get_wall_preview(self.view._wall_rect("horizontal", 2, 2).midleft)
            play.assert_not_called()
            self.assertTrue(self.controller.execute_command(MoveCommand(self.game, (1, 4))))
            self.assertTrue(self.app.update_bot())
            self.view.draw(self.game)
            self.view.draw(self.game)
            self.assertEqual([call.args[0] for call in play.call_args_list], ["move", "move"])

    # Kết quả nằm trong khung trên bàn; nút bên phải giữ chỗ và lịch sử bị khóa.
    def test_victory_overlay_and_sidebar_controls(self):
        start_game(self.app, self.menu)
        self.game.players[0].row = 7
        self.game.players[1].col = 0
        restart_rect = self.view.restart_rect(self.game).copy()
        menu_rect = self.view.menu_rect(self.game).copy()
        with patch.object(self.view.audio, "play", wraps=self.view.audio.play) as play:
            self.controller.execute_command(MoveCommand(self.game, (8, 4)))
            self.app.draw()
            self.app.draw()
            self.assertEqual([call.args[0] for call in play.call_args_list], ["move", "win"])
        self.assertIsInstance(self.app.state, GameOverState)
        board_frame = pygame.Rect(self.view.board_x - 18, self.view.board_y - 18,
                                  self.view.board_extent + 36, self.view.board_extent + 36)
        self.assertEqual(self.view.info_panel_rect.top, board_frame.top)
        self.assertEqual(self.view.info_panel_rect.bottom, board_frame.bottom)
        first_bottom = self.view.player_card_top + self.view.player_card_height
        second_top = self.view.player_card_top + self.view.player_card_height + self.view.player_card_gap
        second_bottom = second_top + self.view.player_card_height
        self.assertEqual(second_top - first_bottom, self.view.player_card_gap)
        self.assertEqual(self.view.undo_button_rect.top - second_bottom,
                         self.view.player_card_gap)
        self.assertEqual(self.view.restart_rect(self.game), restart_rect)
        self.assertEqual(self.view.menu_rect(self.game), menu_rect)
        with patch.object(self.view.theme, "panel", wraps=self.view.theme.panel) as draw_panel, \
                patch.object(self.view.theme, "button") as draw_button, \
                patch.object(self.view.theme, "pawn", wraps=self.view.theme.pawn) as draw_pawn:
            self.view.draw_victory(self.game)
            draw_panel.assert_called_once()
            draw_button.assert_not_called()
            self.assertEqual(draw_pawn.call_count, 2)
        with patch.object(self.view, "draw_undo_button") as draw_undo, \
                patch.object(self.view, "draw_redo_button") as draw_redo:
            self.view.draw(self.game)
            draw_undo.assert_called_once_with(False)
            draw_redo.assert_called_once_with(False)
        self.assertNotIn(self.view.undo_button_rect, self.app.feedback_rects())
        self.assertNotIn(self.view.redo_button_rect, self.app.feedback_rects())
        finished = self.game.capture_state()
        self.click(self.view.undo_button_rect)
        self.click(self.view.redo_button_rect)
        self.assertEqual(self.game.capture_state(), finished)
        self.click(self.view.restart_rect(self.game))
        self.assertIsNone(self.game.winner)
        self.assertEqual(self.game.command_history, [])
        self.game.winner = self.game.players[1]
        self.click(self.view.menu_rect(self.game))
        self.assertIs(type(self.app.state), MenuState)

    # Kết quả đấu bot được nói theo góc nhìn người chơi, không gọi bot là người thắng.
    def test_bot_victory_message_uses_player_perspective(self):
        self.game.reset(mode="bot")
        self.game.winner = self.game.players[1]
        self.assertEqual(self.view.victory_message(self.game), "Bạn thua!")
        with patch.object(self.view, "draw_text", wraps=self.view.draw_text) as draw_text:
            self.view.draw_info(self.game)
        self.assertIn("Bạn thua!", [call.args[0] for call in draw_text.call_args_list])

        self.game.winner = self.game.players[0]
        self.assertEqual(self.view.victory_message(self.game), "Bạn thắng!")

    # Bật/tắt ở mọi màn hình giữ lựa chọn qua ván mới và không đổi dữ liệu game.
    def test_sound_toggle_persists_and_does_not_play_a_move(self):
        self.assertTrue(self.view.audio.enabled)
        before = self.game.capture_state()
        self.click(self.view.sound_button_rect)
        self.assertFalse(self.view.audio.enabled)
        self.assertEqual(self.game.capture_state(), before)
        start_game(self.app, self.menu)
        self.controller.restart_game()
        self.assertFalse(self.view.audio.enabled)
        before = self.game.capture_state()
        self.click(self.view.sound_button_rect)
        self.assertTrue(self.view.audio.enabled)
        self.assertEqual(self.game.capture_state(), before)
        self.click(self.view.menu_rect(self.game))
        self.click(self.menu.help_button_rect)
        self.click(self.view.sound_button_rect)
        self.assertFalse(self.view.audio.enabled)

    # Thiếu thiết bị âm thanh không ngăn game khởi động và chơi im lặng.
    def test_missing_audio_device_is_safe(self):
        with patch("pygame.mixer.get_init", return_value=None), \
                patch("pygame.mixer.init", side_effect=pygame.error("no audio device")):
            audio = SoundEffects()
        self.assertFalse(audio.available)
        self.assertFalse(audio.enabled)
        audio.play("move")
        audio.toggle()
        self.assertFalse(audio.enabled)

    # Gỗ có biến thiên màu/cache nhưng không tiêu thụ random chung của bot.
    def test_wood_texture_cache_and_no_numbers_on_either_mode(self):
        rng_before = random.getstate()
        texture = self.view.theme.wood((124, 8), self.view.player_colors[0], seed=7)
        colors = {tuple(texture.get_at((x, 4))) for x in range(8, 116)}
        self.assertGreater(len(colors), 1)
        self.assertIs(texture, self.view.theme.wood((124, 8), self.view.player_colors[0], seed=7))
        self.assertEqual(random.getstate(), rng_before)
        for mode in ("two_players", "bot"):
            self.game.reset(mode=mode)
            with patch.object(self.view, "small_font", wraps=self.view.small_font) as font:
                self.view.draw_players(self.game)
                font.render.assert_not_called()

    # Hover và nhấn làm đổi hình nút; nút bị mờ không tạo trạng thái nhấn.
    def test_button_hover_and_press_feedback(self):
        rect = self.menu.start_button_rect
        with patch("pygame.mouse.get_pos", return_value=(0, 0)):
            self.menu.draw_button(rect, "Hai người chơi")
        normal = pygame.image.tobytes(self.view.screen.subsurface(rect), "RGB")
        with patch("pygame.mouse.get_pos", return_value=rect.center):
            self.menu.draw_button(rect, "Hai người chơi")
        hovered = pygame.image.tobytes(self.view.screen.subsurface(rect), "RGB")
        self.assertNotEqual(normal, hovered)
        self.view.theme.press(rect)
        face = self.view.theme.button(self.view.screen, rect, "Hai người chơi", self.view.font)
        self.assertGreater(face.y, rect.y)
        disabled = self.view.theme.button(self.view.screen, rect, "Hai người chơi", self.view.font,
                                          enabled=False)
        self.assertEqual(disabled.y, rect.y)
        self.now += 0.2
        face = self.view.theme.button(self.view.screen, rect, "Hai người chơi", self.view.font)
        self.assertEqual(face.y, rect.y)

    # Hết giờ phát một âm, không lặp ở frame sau và vẫn chỉ mất lượt.
    def test_timeout_sound_once(self):
        start_game(self.app, self.menu, mode="two_players")
        with patch.object(self.view.audio, "play", wraps=self.view.audio.play) as play:
            self.now += 30
            self.assertTrue(self.app.update())
            self.assertFalse(self.app.update())
            play.assert_called_once_with("timeout")
        self.assertIsNone(self.game.winner)
        self.assertEqual(self.game.current_turn, 1)


if __name__ == "__main__":
    unittest.main()
