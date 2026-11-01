import math
from pathlib import Path
import random
import struct
import wave


# Tự tổng hợp âm gõ gỗ và hợp âm thắng bằng thư viện chuẩn, không dùng âm tải ngoài.
def generate_sounds():
    folder = Path(__file__).resolve().parent
    rate = 22050
    presets = {"click": (0.065, 980), "move": (0.13, 420), "wall": (0.17, 230),
               "undo": (0.16, 640), "timeout": (0.25, 330), "win": (0.72, 523.25)}
    for name, (duration, frequency) in presets.items():
        rng = random.Random(name)
        samples = []
        for index in range(round(rate * duration)):
            t = index / rate
            if name == "win":
                value = 0.0
                for start, ratio in ((0.0, 1), (0.12, 1.25), (0.24, 1.5)):
                    local = t - start
                    if local >= 0:
                        value += 0.22 * math.sin(math.tau * frequency * ratio * local) * math.exp(-6 * local)
            else:
                pitch = frequency * (1 - 0.15 * t / duration)
                value = (0.48 * math.sin(math.tau * pitch * t)
                         + 0.18 * math.sin(math.tau * pitch * 2.7 * t)
                         + 0.12 * rng.uniform(-1, 1)) * math.exp(-32 * t)
            fade = min(1.0, t / 0.003, (duration - t) / 0.015)
            samples.append(struct.pack("<h", round(max(-1, min(1, value * fade)) * 22000)))
        with wave.open(str(folder / f"{name}.wav"), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(rate)
            output.writeframes(b"".join(samples))


if __name__ == "__main__":
    generate_sounds()
