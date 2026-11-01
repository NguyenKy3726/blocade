from pathlib import Path

import pygame


# Nạp âm đi kèm; máy không có thiết bị âm thanh vẫn chơi bình thường.
class SoundEffects:
    # Mixer và file âm thanh chỉ được nạp một lần cho cả vòng đời cửa sổ.
    def __init__(self):
        self.sounds = {}
        self.enabled = True
        self.available = False
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            folder = Path(__file__).resolve().parents[1] / "assets" / "sounds"
            for name in ("click", "move", "wall", "undo", "win", "timeout"):
                sound = pygame.mixer.Sound(str(folder / f"{name}.wav"))
                sound.set_volume(0.45)
                self.sounds[name] = sound
            self.available = True
        except (pygame.error, OSError):
            self.enabled = False

    # Phát một âm ngắn; lỗi thiết bị trong lúc chơi không làm mất ván.
    def play(self, name):
        if self.available and self.enabled and name in self.sounds:
            try:
                self.sounds[name].play()
            except pygame.error:
                self.available = False
                self.enabled = False

    # Giữ lựa chọn tắt/bật qua Chơi lại và Về menu trong cùng phiên chạy.
    def toggle(self):
        if not self.available:
            return
        self.enabled = not self.enabled
        if not self.enabled:
            for sound in self.sounds.values():
                sound.stop()
        else:
            self.play("click")
