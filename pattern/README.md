# Các design pattern trong Blocade

Mã nguồn pattern được đặt trong thư mục này và tách mỗi lớp chính thành một file riêng để dễ đối chiếu với sơ đồ lớp.

## State

- `state/app_state.py`: lớp cơ sở trừu tượng, tương tự `ITrangThai` trong bài mẫu.
- `state/app_controller.py`: Context; giữ State hiện tại và chuyển xử lý tới State đó, tương tự `TaiKhoan` giữ thuộc tính trạng thái.
- `state/menu_state.py`, `state/human_turn_state.py`, `state/bot_turn_state.py`, `state/game_over_state.py` cùng các trạng thái phụ: các lớp trạng thái cụ thể.
- Mỗi lớp State nằm trong một file cùng tên trong `state/`.

## Command

- `command/command.py`: lớp cơ sở chung cho lệnh.
- `command/move_command.py` và `command/place_wall_command.py`: từng hành động là một lớp riêng.
- Luật vẫn do `game/game.py` kiểm tra; Command chỉ đóng gói yêu cầu, thực thi và lịch sử Undo/Redo.

## Strategy

- `strategy/bot_strategy.py`: giao diện chung cho các chiến lược bot.
- `strategy/easy_strategy.py`, `strategy/medium_strategy.py`, `strategy/hard_strategy.py`: cách chọn nước theo từng cấp.
- `strategy/bot_strategy_factory.py`: tạo Strategy theo cấp người chơi chọn.
- `strategy/search_context.py` và `strategy/search_limit.py`: mỗi lớp hỗ trợ tìm kiếm của bot khó nằm trong file riêng.

## Đừng nhầm thuật toán với pattern

`game/pathfinder.py` dùng BFS để tìm khoảng cách/đường tới hàng đích. BFS là thuật toán; State, Command và Strategy là design pattern.
