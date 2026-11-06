Lộ trình làm game Blocade
1. Phạm vi game
Game có hai chế độ:
- Hai người chơi trên cùng máy: hai người thay phiên dùng chuột.
- Một người đấu với bot: chọn cấp độ dễ, trung bình hoặc khó.
Luật và phạm vi bản đầu:
- Bàn cờ 9×9 ô.
- Mỗi bên có một quân và tối đa 10 bức tường.
- Mỗi lượt, người chơi di chuyển quân hoặc đặt một bức tường.
- Quân đi một ô theo chiều ngang hoặc dọc nếu không bị tường chắn.
- Nếu quân đối thủ đứng ở ô ngay phía trước, người chơi được nhảy thẳng qua đối thủ khi ô phía sau đối thủ nằm trong bàn và không bị tường chặn.
- Nếu không thể nhảy thẳng vì có tường hoặc mép bàn, người chơi có thể đi chéo sang một ô bên cạnh đối thủ, miễn đường đi đến ô chéo đó không bị tường chắn.
- Không được đặt tường chồng lên hoặc cắt ngang tường khác.
- Sau khi đặt tường, cả hai người vẫn phải còn ít nhất một đường tới hàng đích.
- Ai đưa quân tới hàng đích của mình trước thì thắng.
Phần nhảy qua quân là luật chính thức trong bản game này, không phải tính năng để sau.
2. Cài công cụ
Cài Python 3, VS Code, Git và extension Python của Microsoft trong VS Code. Extension hỗ trợ chọn Python interpreter, chạy và gỡ lỗi chương trình. 

Dùng "deactivate" để thoát môi trường ảo

Mở Terminal trong VS Code trên Windows và chạy:
mkdir blocade
cd blocade
py -m venv .venv 
<!-- Lệnh này dùng để tạo môi trường ảo -->
<!-- "-m venv" Yêu cầu Python chạy module có sẵn tên là venv (viết tắt của Virtual Environment). -->
<!-- ".venv" Tên của thư mục sẽ được tạo ra để chứa môi trường ảo (dấu chấm phía trước giúp ẩn thư mục này trên một số hệ điều hành). -->
<!-- Mục đích: Cô lập dự án, tránh xung đột phiên bản, dễ quản lý -->

.\.venv\Scripts\Activate.ps1
<!-- Lệnh này dùng để kích hoạt môi trường ảo vừa mới tạo -->
<!-- ".\" đại diện cho thư mục hiện tại -->
<!-- ".venv\Scripts\" thư mục chứa các công cụ cript quản lý môi trường ảo -->
<!-- "Activate.ps1" file kịch bản dành riêng cho powershell-->

python -m pip install --upgrade pip
<!-- pip là công cụ quản lý thư viện -->
<!-- "-m pip" Chạy module pip (giúp đảm bảo bạn đang thao tác đúng với pip gắn liền với môi trường Python hiện tại, tránh bị nhầm lẫn giữa các phiên bản Python trên máy)-->
<!--"install --upgrade pip" ra lệnh cho pip tự tải về, cài đặt phiên bản mới nhất của nó -->

python -m pip install pygame
<!-- "pygame là thưu viện dùng để lập trình game 2D -->

Pygame dùng để vẽ game, nhận thao tác chuột/bàn phím và chạy vòng lặp chính. 

Trong VS Code, nhấn Ctrl+Shift+P → chọn Python: Select Interpreter → chọn Python nằm trong .venv.
3. Cấu trúc chương trình và OOP
Có thể chia code thành các phần sau:
blocade/
├── main.py
├── game/
│   ├── board.py
│   ├── player.py
│   ├── game.py
│   └── pathfinder.py
├── pattern/
│   ├── command/       # Command, MoveCommand, PlaceWallCommand
│   ├── state/         # AppController, AppState và mỗi trạng thái riêng file
│   └── strategy/      # BotStrategy, từng cấp bot và Factory
├── ui/
│   ├── game_view.py
│   ├── menu_view.py
│   └── controller.py
└── assets/

Lớp	Nhiệm vụ
Board	Lưu các ô và tường; kiểm tra đường đi giữa hai ô
Player	Lưu vị trí quân, hàng đích, số tường còn lại
Game	Quản lý chế độ chơi, lượt hiện tại, hành động và thắng thua
PathFinder	Tìm đường bằng BFS, kiểm tra tường có khóa đường không
GameView	Vẽ bàn cờ, quân, tường và thông tin
GameController	Nhận thao tác người dùng và chuyển thành hành động


4. Các design pattern nên dùng
Command: biểu diễn nước đi và đặt tường
Tạo MoveCommand và PlaceWallCommand. Mỗi lệnh chịu trách nhiệm kiểm tra và thực hiện một hành động hợp lệ. GameController không tự thay đổi tọa độ quân hay danh sách tường.

Command hiện đã lưu lịch sử và hỗ trợ Undo theo cặp lượt trong chế độ đấu bot; chế độ hai người không có Undo.
State: quản lý lượt và trạng thái game
Các trạng thái chính:
MenuState
HumanTurnState
BotTurnState
GameOverState

Ở chế độ hai người, game luân phiên lượt người 1 và người 2. Ở chế độ đấu bot, game luân phiên giữa người chơi và bot. Khi có người thắng, chuyển sang GameOverState.
Strategy: thay đổi cấp độ bot
BotStrategy định nghĩa phương thức chọn hành động. Các lớp con:
- EasyStrategy: chọn nước hợp lệ, ưu tiên tiến về hàng đích.
- MediumStrategy: dùng BFS và hàm đánh giá để chọn nước đi hoặc đặt tường.
- HardStrategy: dùng Minimax, có thể kết hợp Alpha–Beta.
Chế độ hai người không cần bot hoặc Strategy.
Factory: tạo bot theo cấp độ
BotStrategyFactory tạo chiến lược tương ứng với cấp được chọn. Pattern này chỉ dùng ở chế độ đấu bot. Nếu cần giữ code đơn giản, có thể khởi tạo trực tiếp chiến lược mà chưa cần Factory.
5. Làm luật di chuyển, bao gồm nhảy qua quân
Trước khi làm UI, hoàn thiện các quy tắc bằng tọa độ (row, col):
1. Từ một ô, tạo danh sách ô kề bốn hướng.
2. Loại bỏ các bước đi bị tường chặn.
3. Nếu ô kế bên trống, thêm bước đi bình thường.
4. Nếu ô kế bên có quân đối thủ, kiểm tra ô phía sau:
   - Nếu nằm trong bàn và không bị tường chặn: thêm bước nhảy thẳng.
   - Nếu bị tường chặn hoặc nằm ngoài bàn: kiểm tra hai ô chéo hai bên đối thủ.
5. Chỉ thêm ô chéo nếu đường đi từ vị trí đối thủ tới ô chéo không bị tường chặn.
Như vậy luật nhảy nằm trong phần tính các nước đi hợp lệ, dùng chung cho cả người chơi và bot. Giao diện chỉ hiển thị những ô hợp lệ đó.
6. Dùng BFS và kiểm tra tường
Dùng BFS trên các ô bàn cờ để tìm số bước ngắn nhất tới hàng đích. Tường quyết định các ô nào kết nối được với nhau.

BFS có hai vai trò:
- Kiểm tra tường: sau khi thử đặt tường, xác nhận mỗi bên vẫn còn đường tới đích.
- Bot: ước lượng khoảng cách của bot và đối thủ để chọn nước có lợi.
Khi kiểm tra một bức tường mới, tạm đưa nó vào bàn cờ, chạy BFS cho cả hai bên, rồi bỏ tường nếu một bên không còn đường.

Luật nhảy được xử lý trong hàm tìm nước đi hợp lệ của quân. Còn BFS dùng để đo đường tới đích và kiểm tra khả năng tiếp cận, không nên gộp toàn bộ luật điều khiển quân vào một hàm duy nhất.
7. Làm chế độ hai người trước
Đây là chế độ đầu tiên cần hoàn thiện, vì giúp xác nhận luật trước khi thêm bot:
1. Tạo menu chọn Hai người chơi hoặc Đấu với bot.
2. Vẽ bàn cờ 9×9, hai quân xuất phát và số tường mỗi bên.
3. Cho chọn quân để di chuyển.
4. Hiển thị các ô hợp lệ, bao gồm nhảy thẳng và đi chéo khi bị chặn.
5. Cho chọn vị trí đặt tường và báo lỗi nếu vị trí không hợp lệ.
6. Chuyển lượt sau mỗi hành động.
7. Hiện người thắng và nút chơi lại.
Hai người dùng chung chuột, thay phiên nhau thao tác. Không cần Internet, tài khoản hay kết nối mạng.
8. Thêm bot theo cấp độ
Sau khi chế độ hai người chạy đúng:
- Dễ: bot chọn một nước hợp lệ và thường đi về phía đích.
- Trung bình: bot dùng BFS để so sánh đường đi, có thể chọn đặt tường nếu làm chậm đối thủ.
- Khó: bot dùng Minimax để xem xét lượt của mình và nước đáp trả của đối thủ. Alpha–Beta giảm số nhánh phải duyệt.
Bot phải dùng chung hàm tạo danh sách nước đi hợp lệ với người chơi để nó cũng biết nhảy qua quân đúng luật.
9. Làm giao diện bằng Pygame
Khi luật và chế độ hai người đã chạy, thiết kế giao diện:
- Menu: chọn chế độ; nếu chọn bot thì chọn cấp độ/thứ tự. Nút ? mở luật và hướng dẫn.
- Bàn cờ: bàn ở giữa, hai quân màu khác nhau, tường dễ phân biệt.
- Thông tin: lượt hiện tại, số tường còn lại, chế độ và cấp bot.
- Di chuyển: làm nổi bật ô hợp lệ, bao gồm ô nhảy và ô chéo.
- Đặt tường: xem trước hướng/vị trí tường trước khi xác nhận.
- Kết thúc: hiện người thắng và nút chơi lại/về menu.
Tách phần vẽ trong GameView, phần nhận click trong GameController, phần luật trong Game và Board.
10. Khi nào nhờ Claude hỗ trợ
Claude có thể giúp viết hoặc rà những phần thuật toán riêng biệt. Nên dùng ở các mốc sau:
- Sau khi chốt tọa độ và cách lưu tường: nhờ viết BFS.
- Khi làm luật nhảy: nhờ rà các trường hợp đi thẳng, nhảy thẳng, nhảy chéo và bị tường chặn.
- Khi kiểm tra tường: nhờ viết hàm xác nhận cả hai người còn đường tới đích.
- Khi làm bot trung bình/khó: nhờ thiết kế hàm đánh giá, Minimax và Alpha–Beta.
Khi nhờ Claude, cung cấp cấu trúc dữ liệu và luật cụ thể, yêu cầu giải thích từng hàm và liệt kê trường hợp biên. Tích hợp từng phần vào dự án rồi tự kiểm tra, không yêu cầu Claude sinh toàn bộ game trong một lần.
11. Thứ tự triển khai
1. Cài công cụ và tạo dự án.
2. Chốt luật, bao gồm nhảy thẳng và nhảy chéo.
3. Tạo Board, Player, Game.
4. Làm Command và các nước đi hợp lệ.
5. Làm BFS và kiểm tra đặt tường.
6. Hoàn thiện chế độ hai người trên cùng máy.
7. Thêm bot dễ, trung bình rồi khó.
8. Làm menu và giao diện Pygame.
9. Hoàn thiện báo cáo, sơ đồ lớp và giải thích pattern.
Thứ tự này giúp bạn kiểm chứng luật nhảy qua quân trong chế độ hai người trước, rồi mới dùng đúng luật đó cho bot.

12. Ghi chú bổ sung và lộ trình triển khai cập nhật

12.1. Điều khiển đặt tường

Trạng thái hiện tại: đặt tường bằng chuột, hướng ngang/dọc được xác định theo khe con trỏ đang trỏ. Không còn chế độ khóa hướng H/V hoặc hủy bằng Esc.

Yêu cầu mới của người chơi:
- Không bắt buộc nhấn H/V để đặt tường.
- Trong cùng một chế độ chơi, người chơi có thể chọn đặt tường ngang hoặc dọc mà không cần chuyển chế độ bằng bàn phím.
- Hướng tường cần được chọn bằng thao tác chuột rõ ràng, có hình xem trước trước khi xác nhận.
- Theo cập nhật đã chốt: bỏ H/V/Esc cho thao tác đặt tường; chỉ dùng chuột.
- Hình xem trước phải phân biệt vị trí hợp lệ và không hợp lệ. Tường chỉ được đặt sau khi người chơi xác nhận bằng chuột.
- Thiết kế cách chọn hướng phải rõ ràng cả tại vị trí có thể đặt tường ngang lẫn dọc; tránh trường hợp người chơi không biết hướng nào đang được chọn.

12.2. Bộ đếm thời gian

Yêu cầu mới: bổ sung bộ đếm thời gian cho chế độ chơi. Trước khi lập trình, cần chốt:
- Dùng đồng hồ đếm ngược cho mỗi lượt, hay đồng hồ ghi tổng thời gian của từng người chơi.
- Thời lượng ban đầu và hành vi khi hết giờ.
- Đồng hồ chỉ chạy cho người đang đến lượt hay chạy liên tục.
- Cách xử lý khi chơi lại, về menu và khi ván đã kết thúc.

Gợi ý: bắt đầu với đồng hồ hiển thị riêng cho mỗi người chơi và chỉ tính thời gian trong lượt của người đó. Chỉ dùng gợi ý này nếu người chơi đồng ý với quy tắc đó trước khi triển khai.

12.3. Lộ trình cập nhật theo ưu tiên

1. Hoàn thiện thao tác đặt tường không phụ thuộc H/V:
   - Chọn được cả tường ngang và dọc bằng chuột trong cùng chế độ.
   - Hiển thị hướng/vị trí xem trước, phân biệt hợp lệ/không hợp lệ.
   - Click xác nhận đặt một tường và chuyển lượt đúng một lần.
   - Không còn khóa hướng H/V/Esc.
2. Chốt quy tắc đồng hồ với người chơi, sau đó thêm timer và hiển thị rõ lượt/thời gian còn lại.
3. Rà chế độ hai người bằng các trường hợp: đi thường; nhảy thẳng; nhảy chéo khi sát mép hoặc bị tường chặn; đặt tường ngang/dọc; tường chồng/cắt; tường bị từ chối vì khóa đường; số tường, chuyển lượt và thắng ván.
4. Hoàn thiện trải nghiệm hai người: nút chơi lại, nút về menu và trạng thái kết thúc rõ ràng. Theo lựa chọn mới của người chơi, không bổ sung thông báo lý do nước đi/tường bị từ chối.
5. Khi hành động đã ổn định, thêm Command cho MoveCommand và PlaceWallCommand để tách việc yêu cầu hành động khỏi việc tự sửa trạng thái trong GameController.
6. Thêm menu chọn hai người hoặc đấu bot; dùng State để quản lý menu, lượt người, lượt bot và kết thúc nếu cấu trúc thực tế cần đến.
7. Thêm bot theo thứ tự dễ, trung bình, khó. Mọi bot phải dùng chung hàm lấy nước đi hợp lệ với người chơi. Dùng Strategy để thay đổi cách chọn hành động; dùng Factory để tạo cấp bot được chọn.
8. Hoàn thiện báo cáo, sơ đồ lớp và giải thích OOP/pattern.

Ghi chú: thứ tự ở mục 12 này cập nhật và ưu tiên hơn thứ tự triển khai cũ ở mục 11 khi hai mục khác nhau. Luật nhảy thẳng/chéo và kiểm tra BFS là yêu cầu cốt lõi, không được bỏ hoặc trì hoãn.

12.4. Quy tắc đã chốt và thao tác sau cập nhật

- Trong chế độ hai người, mỗi người có đồng hồ riêng, đếm ngược 30 giây cho mỗi lượt. Chỉ bên đang tới lượt chạy đồng hồ; bên chờ giữ nguyên số hiển thị tới lượt tiếp theo.
- Đi quân hoặc đặt tường hợp lệ kết thúc lượt. Khi nhận lượt mới, đồng hồ của người đó được đặt lại thành 30 giây.
- Hết giờ thì mất lượt, không bị xử thua và không bị trừ tường. Nước đi hoặc tường không hợp lệ không đặt lại đồng hồ.
- Khi có người thắng, cả hai đồng hồ dừng. Nút Chơi lại ở bên phải khi đang chơi và trong khung kết quả sau khi thắng: đưa quân về vị trí đầu, xóa tường và màu sở hữu, cấp lại 10 tường và 30 giây mỗi phe trong chế độ hai người, giữ lựa chọn đi trước/đi sau, xóa lựa chọn cũ và thông báo hết giờ. Menu phân cấp theo mục 12.12; nút Về menu trên bàn cờ kết thúc luồng ván hiện tại, vào lại bắt đầu ván mới.
- Đưa chuột vào khe ngang/dọc để xem trước; click trái để xác nhận đặt tường. Tại giao điểm, hướng theo đường giữa khe gần chuột hơn; nếu bằng nhau thì chưa chọn hướng, hãy dịch chuột vào khe muốn đặt.
- Đặt tường hoàn toàn bằng chuột; H/V/Esc không thay đổi hướng hoặc chế độ chơi.
- Hai phe dùng màu xanh lá và xanh nước cho quân và tường đã đặt. Không còn vẽ số trên quân ở cả hai chế độ; vòng sáng, thẻ phe và các ô gợi ý xác định lượt chơi (mục 12.13).
- Tường xem trước hợp lệ dùng màu nhạt hơn của phe đang tới lượt; không hợp lệ luôn màu đỏ, kèm chữ ghi hướng và tính hợp lệ.
- Chấm gợi ý nước đi của phe xanh lá giữ màu xanh lá hiện tại; phe xanh nước dùng màu xanh nước cùng màu quân.
- Các ô đi hợp lệ hiện ngay khi tới lượt, kể cả sau khi đặt tường hoặc hết giờ. Click thẳng ô đích để di chuyển, không cần chọn quân. Khi ván kết thúc, không còn gợi ý đi.
- Chạy `python -m unittest discover -s tests -v` từ thư mục repo có Pygame. Font Noto Sans đi kèm repo, hỗ trợ tiếng Việt; không cần Arial hoặc cấu hình font theo máy. Các kiểm tra dùng SDL headless và đồng hồ giả, không thay thế việc kiểm tra GUI bằng tay.
- Trên Codex/Linux hiện tại có thể chạy từ repo bằng `/workspace/blocade-env/bin/python -m unittest discover -s tests -v`; không còn cần thư mục runtime hoặc liên kết giả đường dẫn font Windows. Đường dẫn font dựa trên vị trí file Python nên chạy `main.py` từ thư mục khác cũng được.

12.5. Command cho hành động đi quân và đặt tường

- `pattern/command/` tách `Command`, `CommandInvoker`, `MoveCommand` và `PlaceWallCommand` thành các file riêng.
- Ánh xạ theo sơ đồ bài giảng: `GameController` là Client, `CommandInvoker` là Invoker, `Command` là interface `ICommand`, `MoveCommand`/`PlaceWallCommand` là ConcreteCommand và `Game` là Receiver.
- Controller nhận click, đổi tọa độ chuột thành ô đích hoặc tường, tạo ConcreteCommand rồi giao cho Invoker gọi `execute()`. Lệnh không được lưu hàng đợi hoặc tự chạy lại.
- Tạo Command chỉ lưu yêu cầu và Receiver; `execute()` mới gọi Game và trả về True/False. Game vẫn là nơi kiểm tra nước đi, tường, BFS, số tường, thời gian và cập nhật lượt/kết quả. Không chép luật sang Command hoặc controller.
- Xem trước không thực thi Command. `Command` chỉ thực hiện hành động qua Receiver, không kiểm tra chế độ chơi hay tự ghi lịch sử. `CommandInvoker` chụp snapshot và ghi lệnh thành công khi phiên bật lịch sử; phiên bot thật bật để dùng Undo/Redo, phiên hai người tắt. Chơi lại và hết giờ vẫn do luồng hiện tại xử lý.

12.6. Quy tắc đấu bot/Undo đã chốt và lộ trình tiếp theo

Mục này ưu tiên hơn thứ tự cũ khi có khác nhau:
- Chế độ hai người vẫn có 30 giây mỗi lượt như mục 12.4.
- Chế độ đấu bot không chạy, không hiển thị đồng hồ và không có mất lượt do hết giờ.
- Undo khi đấu bot: nếu bot đã đáp trả, hoàn tác cả hành động của bot và hành động trước đó của người, trả về lượt người để chọn lại. Nếu bot chưa đi, chỉ hoàn tác hành động của người. Không cho hoàn tác khi chưa có hành động; không Undo xuyên qua Chơi lại/ván mới.
- Lịch sử chỉ lưu hành động thành công. Hoàn tác phục hồi vị trí quân, tường/cạnh bị chặn, chủ sở hữu và số tường, lượt và kết quả ván bằng snapshot của Command.

1. Menu (đã hoàn thành): mở ứng dụng ở menu, vào Hai người chơi, Chơi lại/Về menu cả trước và sau thắng; không tính giờ ở menu. Vào lại bắt đầu ván mới, không tiếp tục ván cũ. Lựa chọn Đấu bot dễ đã được thêm khi bot hoạt động.
2. Bot dễ (đã hoàn thành): lựa chọn Đấu bot dễ trên menu, dùng chung luật/Command, không có đồng hồ; người đi rồi bot đáp trả.
3. Undo/Redo đấu bot (đã hoàn thành): bổ sung trạng thái trước hành động, lịch sử và hoàn tác cặp lượt theo quy tắc trên; xóa lịch sử khi Chơi lại hoặc bắt đầu ván mới.
4. Bot dễ/trung bình/khó đã hoàn thành với Strategy/Factory; cấp khó dùng tìm kiếm sâu có giới hạn.
5. State đã quản lý menu/lượt người/lượt bot/kết thúc. Người dùng đã tự kiểm tra trải nghiệm; cập nhật bàn gỗ/âm thanh ở mục 12.13, sau đó hoàn thiện báo cáo/sơ đồ OOP/pattern.

`pattern/state/app_controller.py` chứa Context `AppController` của State pattern; `pattern/state/` có `AppState` và từng lớp trạng thái trong file riêng: `MenuState`, `HelpState`, `BotLevelState`, `TurnOrderState`, `PlayingState`, `HumanTurnState`, `BotTurnState` và `GameOverState`. MenuView dùng cùng cửa sổ/font với GameView. Vẫn không thêm thông báo lý do hành động bị từ chối theo lựa chọn của người chơi.

12.7. Cách chơi với bot dễ hiện tại

- Chọn Đấu với máy → Dễ → Chơi trước hoặc Chơi sau. Bạn xanh lá luôn ở dưới, bot xanh nước ở trên; lựa chọn thứ tự quyết định bên mở đầu.
- Bạn có thể đi quân hoặc đặt tường bằng chuột. Bot đáp trả một nước sau hành động hợp lệ của bạn, qua MoveCommand; click sai không khiến bot được đi.
- Bot dễ chỉ đi quân: lấy danh sách nước hợp lệ từ Game (bao gồm nhảy), dùng BFS đánh giá đường còn lại qua tường rồi chọn nước có khoảng cách nhỏ nhất. Nếu hòa, chọn ngẫu nhiên. Bot chưa đánh giá đặt tường hoặc nhìn trước nước đáp trả.
- `PathFinder.shortest_distance` tính số cạnh tới hàng đích, bỏ qua vị trí quân. Đây là ước lượng để chọn trong các nước đã hợp lệ, không thay thế luật nhảy của Game.
- Bot chạy sau khi xử lý các sự kiện của khung hình, không dùng sleep/thread. Trong lượt bot, bỏ click đi quân/đặt tường của người; Chơi lại/Về menu vẫn được ưu tiên.
- Chơi lại giữ chế độ bot và lựa chọn đi trước/đi sau. Về menu rồi chọn Hai người chơi sẽ vào ván ngay và bật lại đồng hồ 30 giây/lượt, xanh lá số 1 đi trước.
- Kiến trúc hiện có BotStrategy, EasyStrategy, MediumStrategy, HardStrategy và BotStrategyFactory để chọn cấp. Undo đã có theo quy tắc mục 12.6 và cách dùng mục 12.8.
- Kiểm tra riêng bot: `python -m unittest discover -s tests -p test_easy_bot.py -v` trong repo. Chạy toàn bộ test với `python -m unittest discover -s tests -v`. Test giao diện dùng SDL headless; vẫn cần chơi thử trên Windows.

12.8. Undo bằng Command pattern

- Khi đấu bot, nút Undo nằm trên Chơi lại. Nút bị mờ khi chưa có hành động của người để lùi. Chế độ hai người không hiện nút hoặc cho Undo.
- Bot đã đáp trả: Undo gọi undo() của lệnh bot, rồi của lệnh người gần nhất, trả về lúc người chọn nước trước đó. Bot chưa đi (kể cả người vừa thắng): chỉ lùi lệnh người. Sau Undo, bot không được đáp trả cho tới khi người chọn một hành động hợp lệ mới.
- Có thể Undo liên tiếp từng cặp lượt; dùng được sau người hoặc bot thắng. Nước không hợp lệ và hình xem trước không vào lịch sử.
- `Command.execute()` gọi hành động của ConcreteCommand; không chụp snapshot và không biết lịch sử hay mode. `CommandInvoker.execute()` chụp trạng thái trước/sau khi lịch sử được bật, gọi Command và chỉ lưu lệnh thành công. `MoveCommand` và `PlaceWallCommand` giữ riêng dữ liệu hành động; `Game` vẫn giữ toàn bộ luật.
- `Command.undo()`/`redo()` ủy quyền cho Invoker gắn với lệnh. `CommandInvoker` sở hữu ngăn Undo/Redo và khôi phục snapshot qua `Game.restore_state()`. `Game.undo_round()` chỉ điều phối thứ tự hoàn tác tới lệnh của người, không tự suy ngược luật di chuyển/đặt tường.
- Trạng thái gồm vị trí và số tường hai phe, danh sách tường/cạnh bị chặn, chủ sở hữu, lượt, người thắng, dữ liệu đồng hồ và thông báo. Đấu bot vẫn không chạy đồng hồ. Chỉ chụp dữ liệu của ván, không sao chép cửa sổ Pygame hoặc lịch sử vào snapshot.
- Chơi lại, Về menu hoặc bắt đầu ván mới xóa lịch sử; lệnh giữ tham chiếu Board để không execute/undo xuyên sang ván mới. Mỗi Command thành công chỉ execute một lần; làm lại phải gọi redo() theo mục 12.9.
- Test riêng: `python -m unittest discover -s tests -p test_undo.py -v`. Trên Windows cần thử đi quân/đặt tường → bot đáp trả → Undo, Undo nhiều lần, Undo sau thắng và Chơi lại/Về menu xóa lịch sử.

12.9. Redo bằng Command pattern

- Chế độ đấu bot có Redo cạnh Undo; nút bị mờ nếu chưa có lệnh đã Undo. Hai người không có Undo/Redo, vẫn giữ đồng hồ như cũ.
- `CommandInvoker` lưu before_state và after_state. Undo khôi phục before_state và chuyển Command từ ngăn Undo sang ngăn Redo. Redo khôi phục after_state, không thực thi lại hành động hoặc yêu cầu bot chọn nước mới.
- Game.redo_round() gọi redo() theo thứ tự người rồi bot đã có, dừng trước lệnh người của vòng tiếp theo. Nếu trước Undo bot chưa đáp trả, chỉ khôi phục lệnh người; bot sau đó đi lần đầu theo luồng bình thường.
- Có thể Undo/Redo liên tiếp nhiều vòng; khôi phục đúng quân, tường, cạnh bị chặn, màu, số tường, lượt và kết quả thắng. Redo cặp đầy đủ không khiến bot đánh thêm một nước.
- Hành động mới thành công qua Invoker sau Undo xóa toàn bộ ngăn Redo. Nước sai, tường bị BFS từ chối và hình xem trước không xóa nhánh Redo.
- Chơi lại, Về menu và bắt đầu ván mới xóa cả hai lịch sử. Command.redo() chỉ chấp nhận đúng lệnh trên cùng ngăn Redo, cùng Board và trạng thái hiện tại đúng before_state, tránh khôi phục trên ván/nhánh khác.
- Mỗi Command chỉ thực thi thành công một lần; Undo/Redo có thể lặp lại qua Invoker. Các snapshot chỉ lưu dữ liệu ván, không lưu đệ quy các lịch sử.
- Trong main, click Undo/Redo bỏ các sự kiện dư của khung hình để tránh thực hiện ngay một nước khác sau khi lùi/làm lại.
- Test riêng: `python -m unittest discover -s tests -p test_redo.py -v`. Trên Windows thử đi/đặt tường → bot đáp trả → Undo → Redo, nhiều vòng liên tiếp, đổi nước sau Undo, Redo sau thắng và Chơi lại/Về menu xóa cả hai lịch sử.
- Bot trung bình đã sử dụng cùng Command/Undo/Redo và không đồng hồ; xem mục 12.10.

12.10. Bot trung bình và Strategy/Factory

- Chọn Đấu với máy → Trung bình rồi chọn thứ tự chơi. Người xanh lá ở dưới; bot xanh nước ở trên. Cả ba cấp bot đều không có đồng hồ, dùng cùng luật đi/nhảy, đặt tường, BFS và lịch sử Command.
- BotStrategy định nghĩa choose_command(game). EasyStrategy và MediumStrategy thực hiện giao diện này. BotStrategyFactory.create(level) hiện tạo chiến lược theo easy/medium/hard; cấp không hỗ trợ bị từ chối, không tự thay bằng cấp khác. Game giữ bot_level, controller giữ Strategy được Factory tạo.
- MediumStrategy ưu tiên nước tới đích ngay. Nếu chưa thắng được, thử các nước đi hợp lệ và tối đa 128 vị trí/hướng tường khi còn tường.
- PathFinder.distances_to_goal chạy BFS ngược từ cả hàng đích để tính bản đồ đường còn lại. Đánh giá số lượt dùng nước đầu hợp lệ từ Game, vì vậy có tính nhảy thẳng/chéo ở bước đầu; phần đường sau đó là ước lượng qua tường, không mô phỏng toàn bộ quân/lượt tương lai.
- Xếp hạng: ưu tiên phương án không cho người thắng ngay ở lượt tới; sau đó tối đa hóa khoảng cách người trừ khoảng cách bot. Đặt tường bị trừ 0.5 điểm để tránh phí tường khi lợi ích ngang nhau. Các phương án ngang điểm được chọn ngẫu nhiên.
- Tường thử phải hợp lệ về hình học và cả hai phe vẫn nằm trong bản đồ BFS tới đích. Tường khóa đường bị loại, không làm mất tường thật.
- Các lựa chọn được đánh giá tạm bằng cách chụp và khôi phục trạng thái trong `try/finally`; không ghi lịch sử hoặc Redo. Chỉ Command được chọn cuối cùng mới được thực thi qua Invoker của ván thật và được ghi lịch sử.
- Chơi lại giữ cấp đã chọn; về menu có thể chọn lại dễ/trung bình/hai người. Undo/Redo lùi/làm lại cả tường do bot đặt và nước người. Redo không gọi lại Strategy, nên giữ đúng tường/nước bot cũ.
- Cấp này đánh giá một hành động và mối đe dọa thắng ngay, chưa dùng Minimax/Alpha–Beta; không bảo đảm luôn chọn nước tối ưu hoặc chặn được mọi đe dọa.
- Test riêng: `python -m unittest discover -s tests -p test_medium_bot.py -v`. Trên Windows thử chọn Trung bình, tiến gần hàng đích để xem bot chặn, đặt tường cản bot, Undo/Redo tường xanh, Chơi lại giữ cấp và chuyển về Hai người kiểm tra đồng hồ.
- Bot khó đã được thêm ở mục 12.11; trung bình giữ thuật toán đánh giá một hành động như trên.

12.11. Bot khó và đầy đủ các pattern đã thống nhất

- Chọn Đấu với máy → Khó rồi chọn thứ tự chơi. Bạn xanh lá ở dưới, bot xanh nước ở trên; không có đồng hồ. Chơi lại giữ cấp và thứ tự; Về menu chọn lại chế độ/cấp/lượt. Undo/Redo vẫn hoàn tác/làm lại cặp lượt bằng chính Command, không cho bot tính lại khi Redo.
- HardStrategy dùng Minimax: bot tối đa hóa điểm, người tối thiểu hóa điểm. Alpha–Beta bỏ nhánh không thể cải thiện kết quả hiện tại. Tìm sâu dần: hoàn tất đánh giá một hành động trước, rồi hai, tối đa ba (bot → người → bot).
- Mỗi gốc xét mọi vị trí tường; tầng sâu lấy tường trên các cạnh của đường ngắn hai phe (tối đa 6 cạnh đầu mỗi đường). Sau xếp hạng chỉ giữ tối đa 4 tường tốt và mọi nước đi hợp lệ ở mỗi nút. Đây là Minimax/Alpha–Beta trên cây rút gọn, không vét cạn toàn bộ tường hoặc bảo đảm tối ưu tuyệt đối.
- Điểm thắng/thua lớn hơn mọi điểm đường đi; ưu tiên thắng sớm và trì hoãn thua. Điểm thường dùng chênh lệch khoảng cách BFS có tính nhảy ở nước đầu, số tường và đe dọa thắng ngay.
- Mô phỏng dùng Game riêng với lịch sử Invoker tắt. Minimax thực thi Command trên bản sao rồi khôi phục snapshot trong `finally` sau mỗi nhánh; Undo/Redo của người chơi không tham gia tìm kiếm. Ván thật không bị đổi bàn, màu, thời gian hoặc lịch sử. Khi chọn xong, chỉ tạo một Command gắn với ván thật để controller thực thi và ghi lịch sử bot thật.
- Ngân sách mặc định: tối đa 512 nút Minimax, 0.6 giây tính theo thời gian thực và độ sâu 3. Không phải mọi lượt đều đạt độ sâu 3. Hết ngân sách giữ nước của tầng đã hoàn tất; nếu chưa hoàn tất tầng đầu, dùng nước hợp lệ ưu tiên về đích. Nước thắng ngay được nhận trước khi mở cây.
- HardStrategy.start_search trả generator: yield None để nhường UI, cuối cùng yield Command đã chọn. Controller đặt mục tiêu khoảng 8ms công việc mỗi khung hình, không dùng sleep/thread; một đơn vị nhỏ có thể vượt nhẹ mục tiêu tùy máy. Đây là ngân sách tính toán, không phải đồng hồ giới hạn lượt người.
- Undo/Redo, Chơi lại, Về menu, đóng cửa sổ hoặc rời BotTurnState đều đóng generator đang chạy. Vì chỉ dùng bản sao, tác vụ bị hủy không để lại nước đi muộn trên ván thật.
- last_stats ghi nodes, cutoffs, completed_depth, limited để chẩn đoán; không hiển thị thông số kỹ thuật trong luồng chơi.

Vai trò các pattern:
- Command: MoveCommand/PlaceWallCommand đóng gói hành động; CommandInvoker thực thi lệnh và quản lý Undo/Redo theo cấu hình của phiên.
- Strategy: EasyStrategy/MediumStrategy/HardStrategy cùng giao diện BotStrategy; cấp khó thêm tìm kiếm tăng dần cho UI.
- Factory: BotStrategyFactory tạo đúng Strategy từ easy/medium/hard, từ chối cấp không hỗ trợ.
- State: AppState định nghĩa xử lý/cập nhật/vẽ; MenuState chỉ chọn chế độ, HumanTurnState cập nhật lượt người/đồng hồ, BotTurnState mới được tiến tìm kiếm, GameOverState dừng giờ và đánh tiếp nhưng giữ Undo/Redo/điều hướng. PlayingState dùng chung cách vẽ và điều hướng trong ván; AppController đồng bộ State sau hành động, hết giờ hoặc hoàn tác.

Kiểm tra:
- `python -m unittest discover -s tests -p test_hard_bot.py -v` kiểm tra thuật toán, giới hạn, hủy tác vụ và các State. Kiểm tra Alpha–Beta với vét cạn dùng cùng cây chỉ đi quân để có đối chứng đầy đủ, không đánh đồng với mọi cây có tường.
- `python -m unittest discover -s tests -v` chạy toàn bộ kiểm tra. Test dùng SDL headless; GUI Windows cần thử riêng.
- Trên Windows: chọn Khó, đi/đặt tường, thử Undo hoặc Về menu khi hiện Bot đang suy nghĩ, Chơi lại giữ cấp, Redo đúng nước cũ, và chuyển Hai người để xác nhận đồng hồ hoạt động lại. Kiểm tra thắng ván vẫn có thể Undo/Redo và đóng cửa sổ luôn được.
- Bước tiếp theo dự kiến: rà/tinh chỉnh qua chơi thử Windows và hoàn thiện báo cáo, sơ đồ lớp cùng giải thích các pattern; chưa làm trong bước bot khó này.

12.12. Font đi kèm, menu phân cấp, hướng dẫn và chọn thứ tự chơi

- `assets/fonts/NotoSans-Regular.ttf` là font dùng chung cho mọi màn hình, có dấu tiếng Việt. `OFL.txt` lưu giấy phép SIL Open Font License 1.1, `README.md` ghi nguồn và mã SHA-256. GameView lấy đường dẫn tuyệt đối từ `__file__`, không đọc font hệ thống hoặc tải font lúc chạy.
- Menu chính chỉ có Hai người chơi và Đấu với máy, kèm icon ? ở góc trên để mở Hướng dẫn. Không có nút Thoát; dùng dấu X của cửa sổ để đóng game.
- Hai người chơi vào ván ngay, xanh lá số 1 đi trước; không chọn chơi trước/sau. Luồng này luôn đặt lại thứ tự mặc định, kể cả khi ván đấu bot trước đó người chọn chơi sau.
- Đấu với máy mở trang Dễ/Trung bình/Khó, sau đó chọn Chơi trước/Chơi sau. Các trang cấp, thứ tự và hướng dẫn đều có nút mũi tên Quay lại ở góc trên trái, trở về trang trước. Khi còn ở bất kỳ trang menu/hướng dẫn nào, đồng hồ và bot đều chưa hoạt động.
- Người/xanh lá luôn bắt đầu ở dưới màn hình; bot/xanh nước ở trên. Khi đấu bot, Chơi trước thì người mở đầu; Chơi sau thì bot mở đầu. Quân không có số. Người không thể đi thay trong lượt mở đầu của bot.
- Chỉ số nội bộ vẫn giữ nguyên: `players[0]` luôn là người/xanh lá, `players[1]` là bot/xanh nước. Game vẫn giữ hàng xuất phát/đích cũ; GameView phản chiếu trục dọc cho ô, quân, gợi ý, tường và biến đổi ngược click về tọa độ luật. BFS, nhảy và cách chọn nước của bot không đổi.
- Bảng thông tin bỏ dòng Vị trí; giữ tên phe và Tường còn lại. Hai người vẫn có đồng hồ 30 giây; đấu bot vẫn không có đồng hồ. Màu quân, tường và gợi ý tiếp tục theo phe, độc lập với số 1/2.
- Bỏ các dòng chỉ thao tác cố định khỏi bàn cờ và menu chọn chế độ/cấp/lượt. Icon ? mở trang Hướng dẫn gồm luật đi/nhảy thẳng/chéo, hàng đích, đặt tường và điều kiện còn đường, màu xem trước, thao tác chuột, đồng hồ, Undo/Redo và điều hướng. Nội dung chia hai cột, tự xuống dòng theo độ rộng font. Bàn cờ vẫn giữ thông tin trạng thái như lượt hiện tại, hết giờ, bot đang suy nghĩ và tính hợp lệ của tường đang xem trước.
- Chơi lại giữ chế độ, cấp bot và thứ tự đã chọn; xóa cả hai lịch sử như cũ. Nếu chọn chơi sau, bot mở đầu lại ván mới.
- Undo/Redo vẫn gọi Command theo cặp lượt người → bot. Nếu người chơi sau, nước bot mở đầu được giữ lại: chưa có nước người thì Undo bị mờ; Undo hết các cặp cũng chỉ trở về lượt người ngay sau nước mở đầu đó. Redo không cho bot đánh thêm ngoài các Command đã lưu.
- MenuState quản lý trang chính và vào hai người ngay; HelpState đọc hướng dẫn mà không thay đổi ván; BotLevelState chọn Strategy; TurnOrderState chỉ lưu cấp bot tạm, khởi tạo ván khi người chọn thứ tự. Các State lượt người/bot/kết thúc và Factory/Strategy/Command tiếp tục dùng chung.
- Kiểm tra riêng: `python -m unittest tests.test_menu_setup -v`. Bao gồm font khi chạy từ thư mục khác, menu/Quay lại, Hướng dẫn không làm chạy ván và không tràn chữ, hai người vào ngay, cả ba cấp bot/cả hai thứ tự, quân không số, đồng hồ, Undo/Redo/Chơi lại và click tường sau phản chiếu. Chạy toàn bộ với `python -m unittest discover -s tests -v`.
- Người dùng đã tự kiểm tra luồng chơi, không yêu cầu thêm một đợt rà trải nghiệm. Phần giao diện gỗ và âm thanh mới được mô tả ở mục 12.13; Codex chỉ xác minh bằng headless, không khẳng định đã chạy GUI/loa Windows.

12.13. Giao diện bàn gỗ, hiệu ứng và âm thanh

- Chọn phong cách bàn gỗ đồng bộ cho bàn, menu, trang cấp/thứ tự, hướng dẫn và khung chiến thắng. WoodTheme tạo đường vân/mắt gỗ bằng Pygame và random cục bộ có seed, cache các Surface để dùng lại; không tải ảnh, không thêm thư viện và không ảnh hưởng random của bot.
- Quân là đĩa gỗ có viền nổi, nhuộm xanh lá/xanh nước; tường cũng có vân chạy dọc theo chiều dài và giữ màu phe. Tường xem trước hợp lệ vẫn có màu phe nhạt hơn, sai vẫn đỏ. Vân làm độ sáng biến thiên nhẹ trong cùng màu.
- Không hiển thị số trên quân ở cả hai chế độ. Game vẫn giữ chỉ số/Player và tên Hai người chơi để điều phối lượt, luật, bot và Command. Phe tới lượt có vòng sáng quanh quân, viền thẻ thông tin và nhãn ĐANG ĐI; ô gợi ý của người tiếp tục hiện tự động.
- Tất cả nút dùng chung chất liệu gỗ, đổi màu khi hover và lún ngắn khi nhấn. Nút Undo/Redo chưa dùng được vẫn mờ. Quay lại ở đầu trang; không thêm lại nút Thoát hoặc các câu chỉ thao tác lên bàn.
- GamePresentation chỉ nội suy tọa độ vẽ khoảng 0.20 giây và tăng độ đậm tường mới trong 0.18 giây. Game/Command cập nhật luật ngay, không chờ hình vẽ; không sleep, không thay đổi giới hạn 30 giây hoặc cách bot tìm nước.
- GameController.execute_command gọi Command.execute rồi mới gửi trạng thái trước hành động sang view nếu thành công. Hiệu ứng không được ghi vào snapshot/lịch sử. Undo/Redo khôi phục hình ngay và xóa hiệu ứng cũ; Chơi lại/Về menu/ván mới cũng xóa, tránh quân hoặc tường xuất hiện muộn.
- Khi thắng, phần bàn được làm tối và hiện khung gỗ có tên bên thắng, Chơi lại và Về menu. Các nút chuyển vào khung, chỉ vùng đang hiển thị nhận click; Undo/Redo đấu bot vẫn nằm ở cạnh phải và dùng được sau thắng.
- SoundEffects nạp các WAV đi kèm `assets/sounds`: click, đi quân, đặt tường, Undo/Redo, thắng và hết giờ. Bộ âm được tự tổng hợp bằng thư viện chuẩn trong `generate.py`, có thể tạo lại; không dùng âm tải ngoài. Âm hành động chỉ phát khi thành công, không phát khi preview, click sai hoặc vẽ lại màn hình. Mô phỏng của bot không phát tiếng.
- Nút Âm thanh: Bật/Tắt ở phía trên mọi màn hình. Giữ lựa chọn qua Chơi lại/Về menu trong phiên chạy, không lưu sau khi đóng app. Không có thiết bị âm thanh thì game vẫn chạy im lặng. Âm thanh trên loa thật Windows chưa được xác minh trong môi trường headless.
- Kiểm tra hiệu ứng riêng: `python -m unittest tests.test_wood_ui -v`. Bao gồm nội suy với giờ giả, tường có tác dụng ngay, Undo/Redo/reset giữa animation, khung thắng và điều hướng, âm chỉ phát sau hành động thật, tắt/bật và thiếu thiết bị, vân/cache/random riêng, hover/nhấn và không còn số trên quân. Toàn bộ: `python -m unittest discover -s tests -v`.
- Bước tiếp theo dự kiến sau khi chốt giao diện: hoàn thiện tài liệu chạy game, sơ đồ lớp và phần giải thích OOP/pattern; chưa thực hiện trong bước giao diện này.


12.14. Tách lớp pattern theo mẫu của giảng viên

- Thư mục `pattern/` nằm ở thư mục gốc Blocade; bên trong có `command/`, `state/` và `strategy/`. Mỗi lớp tham gia pattern được đặt trong file riêng để dễ tìm và đối chiếu với sơ đồ lớp.
- State: `AppController` là Context, giữ `state` hiện tại và giao xử lý sự kiện/cập nhật/vẽ cho nó. `AppState` là lớp cơ sở trừu tượng. Mỗi trạng thái cụ thể như `MenuState`, `HumanTurnState`, `BotTurnState` và `GameOverState` nằm trong file riêng, tương tự lớp tài khoản giữ một tham chiếu tới trạng thái hiện tại, rồi chuyển yêu cầu cho đối tượng State.
- Command: `Command` là lớp cơ sở; `MoveCommand` và `PlaceWallCommand` nằm riêng. Mỗi lệnh chuyển yêu cầu tới `Game`, nơi vẫn giữ luật và cập nhật ván.
- Strategy: `BotStrategy` là lớp cơ sở; `EasyStrategy`, `MediumStrategy` và `HardStrategy` nằm riêng. `BotStrategyFactory` tạo chiến lược được chọn.
- Tách file không làm đổi luật chơi, BFS, cách chọn nước bot hay luồng UI; mục tiêu là làm cấu trúc lớp rõ và dễ học hơn.
- Khi trình bày báo cáo, phân biệt: BFS là thuật toán tìm/đo đường; OOP là cách đóng gói dữ liệu và hành vi trong lớp; State/Command/Strategy là các design pattern tổ chức cách những lớp phối hợp.
