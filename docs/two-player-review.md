# Rà soát chế độ hai người

Rà trên code nhánh `work`, nền `f65375c`, ngày 31/10/2026.
Lượt rà này chỉ bổ sung kiểm tra và tài liệu; không đổi luật hoặc thêm tính năng.

## Kết quả tự động

23 test đạt (14 test sẵn có và 9 test luật mới), không test bị bỏ qua.
Smoke check ngoài repo tại `/workspace/blocade-tools/smoke.py` cũng đạt cả hai phần,
bao gồm khởi động và thoát `main.py` bình thường.

| Phần rà | Tình huống đã kiểm tra | Kết quả |
| --- | --- | --- |
| Đi thường | Giữa bàn, bốn góc, không tự đi chéo, không đi xuyên tường từ cả hai phía | Đạt |
| Nhảy | Sáu tình huống xoay đủ bốn hướng: nhảy thẳng, tường sau đối thủ, một nhánh chéo bị chặn, tường giữa hai quân, mép bàn, góc bàn | Đạt |
| Tường | Hai hướng tại bốn góc vùng neo; từ chối neo ngoài bàn, chồng cả tường, chồng một cạnh và cắt giữa; cho phép nối tiếp/chạm đầu | Đạt |
| BFS | Từ chối khóa đường của từng phe, trên lượt của chính phe đó hoặc đối thủ; giữ nguyên bàn, số tường, màu, lượt và đồng hồ khi từ chối | Đạt |
| Xem trước | Thử đủ 128 hướng/điểm neo trên một bàn đã có tường mà không làm đổi trạng thái ván | Đạt |
| Số tường | Đặt đủ 10 tường mỗi bên; từ chối đặt thêm; hết tường vẫn được đi quân | Đạt |
| Thắng ván | Chơi từ vị trí đầu tới thắng cho từng phe; sau thắng không đi/đặt tường được và đồng hồ dừng | Đạt |
| Đồng hồ | Chỉ bên đang đi chạy; mỗi lượt mới đủ 30 giây; hết giờ mất lượt; nước sai không cấp lại giờ; từ chối hành động tại hạn | Đạt |
| Chuột và màu | Đi một click, hai hướng tường không cần H/V, giao điểm/mép bàn, gợi ý tự cập nhật, màu quân/tường/xem trước/chấm đi theo phe | Đạt |

Chưa tái hiện lỗi luật cốt lõi trong các trường hợp trên. Kết quả này không chứng minh
mọi trạng thái bàn cờ hoặc mọi tình huống sự kiện/thời gian đều đã được kiểm tra.

## Phần còn thiếu qua đọc code

- `ui/game_view.py` vẫn nạp trực tiếp font `C:\Windows\Fonts\arial.ttf`.
  Windows cần có file đó; Linux phải dùng cấu hình font cục bộ đã chuẩn bị.
- `Game` và `Board` trả về `False` khi từ chối hành động, nhưng chưa cung cấp lý do
  để controller/view hiển thị. Chữ xem trước hiện chỉ ghi hợp lệ/không hợp lệ.
- Chưa có nút chơi lại hoặc menu. Tạo `Game` mới đặt lại đồng hồ, nhưng chưa có luồng
  người dùng gọi thao tác này.
- BFS hiện kiểm tra có đường hay không, chưa tính khoảng cách phục vụ bot.
  Điều này đủ cho kiểm tra tường của chế độ hai người hiện tại.

## Cách chạy lại

Kiểm tra luật thuần Python, chạy từ thư mục repo:

```powershell
python -m unittest discover -s tests -p test_game_rules.py -v
```

Chạy toàn bộ test trên Windows trong `.venv` có Pygame và font Arial:

```powershell
python -m unittest discover -s tests -v
```

Các test giao diện dùng SDL headless. Trên Codex/Linux, chạy từ
`/workspace/blocade-runtime`, đặt `PYTHONPATH=/workspace/blocade` và dùng
`/workspace/blocade-env/bin/python -m unittest discover -s /workspace/blocade/tests -v`.

## Kiểm tra bằng tay trên Windows

Chưa chạy GUI Windows trong lượt rà này. Sau khi pull nhánh `work`, chạy `python main.py`:

1. Kiểm tra chữ Việt không lỗi hoặc bị cắt; hai đồng hồ hiển thị rõ.
2. Mỗi lượt hiện ngay ô đích; click thẳng để đi. Thử tình huống hai quân sát nhau,
   nhảy thẳng, rồi đặt tường sau quân đối thủ để thử nhảy chéo.
3. Trỏ chuột vào khe ngang/dọc, giao điểm và sát mép bàn. Kiểm tra màu nhạt đúng phe,
   không hợp lệ màu đỏ, tường đã đặt và chấm đi dùng đúng màu đã chốt.
4. Chờ đủ 30 giây: chỉ mất lượt, không mất tường hoặc thua ván. Thử một thao tác sai
   trong lượt và kiểm tra đồng hồ không được cấp lại.
5. Chơi tới đích: có thông báo thắng, hết gợi ý và đồng hồ ngừng chạy.

## Bước tiếp theo đề xuất

Thêm phản hồi lý do nước đi/tường bị từ chối: ngoài bàn, cạnh bị chặn, tường chồng/cắt,
hết tường hoặc khóa đường. Dự kiến làm trong `game/board.py`, `game/game.py`,
`ui/controller.py`, `ui/game_view.py` và test liên quan, giữ nguyên luật hiện có.
Chưa triển khai bước này; nút chơi lại/menu và bot nằm ở các bước sau.
