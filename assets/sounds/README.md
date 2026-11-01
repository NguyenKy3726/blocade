# Hiệu ứng âm thanh Blocade

Các file WAV được tự tổng hợp bằng `generate.py`, không dùng mẫu âm từ bên ngoài.
Chạy `python assets/sounds/generate.py` nếu muốn tạo lại cùng bộ âm.

- `click`: bấm nút.
- `move`: đi quân thành công, cả người và bot.
- `wall`: đặt tường thành công.
- `undo`: Undo/Redo thành công.
- `win`: thắng ván.
- `timeout`: hết 30 giây trong chế độ hai người.

Âm PCM mono 16-bit / 22050 Hz, được nạp theo đường dẫn mã nguồn. Nút Âm thanh
cho phép tắt/bật trong mọi màn hình; lựa chọn được giữ trong phiên đang chạy.
