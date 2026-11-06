# Các design pattern trong Blocade

Mã nguồn pattern được đặt trong thư mục này và tách mỗi lớp chính thành một file riêng để dễ đối chiếu với sơ đồ lớp.

## State

- `state/app_state.py`: lớp cơ sở trừu tượng, tương tự `ITrangThai` trong bài mẫu.
- `state/app_controller.py`: Context; giữ State hiện tại và chuyển xử lý tới State đó, tương tự `TaiKhoan` giữ thuộc tính trạng thái.
- `state/menu_state.py`, `state/human_turn_state.py`, `state/bot_turn_state.py`, `state/game_over_state.py` cùng các trạng thái phụ: các lớp trạng thái cụ thể.
- Mỗi lớp State nằm trong một file cùng tên trong `state/`.

## Command

- `command/command.py`: interface `Command`, tương ứng với `ICommand`; khai báo `execute()` và ủy quyền `undo()`/`redo()` cho Invoker nếu lệnh được ghi vào lịch sử.
- `command/move_command.py` và `command/place_wall_command.py`: ConcreteCommand; mỗi lớp có `execute()` riêng và giữ dữ liệu cần cho hành động.
- `command/invoker.py`: `CommandInvoker` gọi `execute()`, đồng thời sở hữu các ngăn Undo/Redo và chính sách bật/tắt lịch sử.
- `ui/controller.py` (`GameController`): Client; hiểu thao tác chuột, tạo ConcreteCommand rồi giao cho Invoker.
- `game/game.py` (`Game`): Receiver; kiểm tra luật, BFS, giờ và cập nhật lượt/kết quả khi ConcreteCommand gọi hành động tương ứng.
- Các chiến lược bot có thể tạo Command để mô phỏng tìm kiếm; hành động bot được chọn cuối cùng cũng đi qua `GameController` và `CommandInvoker`.

Ánh xạ theo sơ đồ bài giảng: `GameController` → Client; `CommandInvoker` → Invoker; `Command` → ICommand; `MoveCommand`/`PlaceWallCommand` → ConcreteCommand; `Game` → Receiver. Command giữ tham chiếu Receiver và lệnh cụ thể gọi `receiver` khi `execute()` chạy. Command không kiểm tra chế độ chơi và không tự quyết định lưu lịch sử.

- Ván bot thật bật lịch sử để người chơi Undo/Redo; ván hai người tắt lịch sử. Bản Game mô phỏng của bot khó cũng tắt lịch sử. Các nhánh Minimax chụp và khôi phục snapshot trực tiếp quanh từng nước giả định, nên không ghi lịch sử chơi hoặc Redo.

## Strategy

- **Context:** `ui/controller.py` — lớp `GameController` giữ tham chiếu `bot_strategy`, được tạo bằng `BotStrategyFactory`, rồi giao việc chọn hành động cho Strategy hiện tại.
- **Strategy interface:** `strategy/bot_strategy.py` — lớp trừu tượng `BotStrategy` định nghĩa thao tác chung `choose_command(game)`.
- **Concrete Strategies:** `strategy/easy_strategy.py`, `strategy/medium_strategy.py`, `strategy/hard_strategy.py` — mỗi lớp kế thừa `BotStrategy` và triển khai `choose_command(game)` bằng một cách chọn nước khác nhau.
- **Factory bổ sung:** `strategy/bot_strategy_factory.py` tạo đúng chiến lược theo cấp người chơi chọn. Factory không thay vai trò Context hoặc Strategy interface.
- `HardStrategy` có thêm `start_search(game)` để chia tìm kiếm Minimax qua nhiều khung hình. Đây là phần mở rộng kỹ thuật cho bot khó; `choose_command(game)` vẫn là thao tác chung mà mọi Strategy cung cấp.
- `strategy/search_context.py` và `strategy/search_limit.py`: các lớp hỗ trợ tìm kiếm của bot khó, mỗi lớp ở file riêng.

Ánh xạ theo sơ đồ bài giảng: `GameController` → Context; `BotStrategy` → Strategy; `EasyStrategy`/`MediumStrategy`/`HardStrategy` → ConcreteStrategyA/B/C; `choose_command()` → AlgorithmInterface.

## Đừng nhầm thuật toán với pattern

`game/pathfinder.py` dùng BFS để tìm khoảng cách/đường tới hàng đích. BFS là thuật toán; State, Command và Strategy là design pattern.
