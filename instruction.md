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
│   ├── commands.py
│   ├── states.py
│   ├── pathfinder.py
│   └── bot/
│       ├── strategy.py
│       ├── easy.py
│       ├── medium.py
│       ├── hard.py
│       └── strategy_factory.py
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
- Menu: chọn chế độ; nếu chọn bot thì chọn cấp độ.
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
- Khi có người thắng, cả hai đồng hồ dừng. Nút Chơi lại ở bên phải bàn dùng được cả trong ván và sau khi thắng: đưa quân về vị trí đầu, xóa tường và màu sở hữu, cấp lại 10 tường và 30 giây mỗi phe, xanh lá đi trước, xóa lựa chọn cũ và thông báo hết giờ. Menu đã có Hai người chơi, Đấu bot dễ và Thoát; nút Về menu trên bàn cờ kết thúc luồng ván hiện tại, vào lại bắt đầu ván mới.
- Đưa chuột vào khe ngang/dọc để xem trước; click trái để xác nhận đặt tường. Tại giao điểm, hướng theo đường giữa khe gần chuột hơn; nếu bằng nhau thì chưa chọn hướng, hãy dịch chuột vào khe muốn đặt.
- Đặt tường hoàn toàn bằng chuột; H/V/Esc không thay đổi hướng hoặc chế độ chơi.
- Hai phe dùng màu xanh lá (người chơi 1) và xanh nước (người chơi 2), áp dụng cho quân và tường đã đặt.
- Tường xem trước hợp lệ dùng màu nhạt hơn của phe đang tới lượt; không hợp lệ luôn màu đỏ, kèm chữ ghi hướng và tính hợp lệ.
- Chấm gợi ý nước đi của phe xanh lá giữ màu xanh lá hiện tại; phe xanh nước dùng màu xanh nước cùng màu quân.
- Các ô đi hợp lệ hiện ngay khi tới lượt, kể cả sau khi đặt tường hoặc hết giờ. Click thẳng ô đích để di chuyển, không cần chọn quân. Khi ván kết thúc, không còn gợi ý đi.
- Bộ kiểm tra mới: chạy `python -m unittest discover -s tests -v` từ thư mục repo trên Windows có Pygame và font Arial. Các kiểm tra dùng SDL headless và đồng hồ giả, không thay thế việc kiểm tra GUI bằng tay.
- Trên Codex/Linux, đường dẫn font Windows vẫn được hỗ trợ bởi cấu hình cục bộ đã thiết lập: chạy từ `/workspace/blocade-runtime`, dùng Python `/workspace/blocade-env/bin/python`, đặt `PYTHONPATH=/workspace/blocade` và truyền `-m unittest discover -s /workspace/blocade/tests -v`. Font đa nền tảng trong mã nguồn vẫn là việc riêng cần xử lý sau.

12.5. Command cho hành động đi quân và đặt tường

- `game/commands.py` định nghĩa giao diện `Command.execute()` và hai lệnh `MoveCommand`, `PlaceWallCommand`.
- Controller nhận click, đổi tọa độ chuột thành ô đích hoặc tường rồi tạo lệnh và gọi `execute()` ngay. Lệnh không được lưu hàng đợi hoặc tự chạy lại.
- Tạo Command chỉ lưu yêu cầu; `execute()` mới gọi Game và trả về True/False. Game vẫn là nơi kiểm tra nước đi, tường, BFS, số tường, thời gian và cập nhật lượt/kết quả. Không chép luật sang Command hoặc controller.
- Xem trước không thực thi Command. Lịch sử chỉ lưu Command thành công khi đấu bot; Command.undo() khôi phục trạng thái đã lưu. Chơi lại và hết giờ vẫn do luồng hiện tại xử lý.

12.6. Quy tắc đấu bot/Undo đã chốt và lộ trình tiếp theo

Mục này ưu tiên hơn thứ tự cũ khi có khác nhau:
- Chế độ hai người vẫn có 30 giây mỗi lượt như mục 12.4.
- Chế độ đấu bot không chạy, không hiển thị đồng hồ và không có mất lượt do hết giờ.
- Undo khi đấu bot: nếu bot đã đáp trả, hoàn tác cả hành động của bot và hành động trước đó của người, trả về lượt người để chọn lại. Nếu bot chưa đi, chỉ hoàn tác hành động của người. Không cho hoàn tác khi chưa có hành động; không Undo xuyên qua Chơi lại/ván mới.
- Lịch sử chỉ lưu hành động thành công. Hoàn tác phục hồi vị trí quân, tường/cạnh bị chặn, chủ sở hữu và số tường, lượt và kết quả ván bằng snapshot của Command.

1. Menu (đã hoàn thành): mở ứng dụng ở menu, vào Hai người chơi, Chơi lại/Về menu cả trước và sau thắng; không tính giờ ở menu. Vào lại bắt đầu ván mới, không tiếp tục ván cũ. Lựa chọn Đấu bot dễ đã được thêm khi bot hoạt động.
2. Bot dễ (đã hoàn thành): lựa chọn Đấu bot dễ trên menu, dùng chung luật/Command, không có đồng hồ; người đi rồi bot đáp trả.
3. Undo đấu bot (đã hoàn thành): bổ sung trạng thái trước hành động, lịch sử và hoàn tác cặp lượt theo quy tắc trên; xóa lịch sử khi Chơi lại hoặc bắt đầu ván mới.
4. Bot trung bình rồi khó (bước tiếp theo): dùng Strategy/Factory theo cấp; bổ sung BFS khoảng cách và thuật toán phù hợp khi cần.
5. Hoàn thiện báo cáo/sơ đồ OOP/pattern; cân nhắc State khi luồng thực tế phức tạp hơn.

Luồng menu hiện dùng `AppController` với hai trạng thái menu/game và `MenuView` dùng cùng cửa sổ/font với `GameView`; chưa triển khai đầy đủ State pattern. Vẫn không thêm thông báo lý do hành động bị từ chối theo lựa chọn của người chơi.

12.7. Cách chơi với bot dễ hiện tại

- Chọn Đấu bot dễ ở menu. Bạn là xanh lá, đi trước; bot là xanh nước.
- Bạn có thể đi quân hoặc đặt tường bằng chuột. Bot đáp trả một nước sau hành động hợp lệ của bạn, qua MoveCommand; click sai không khiến bot được đi.
- Bot dễ chỉ đi quân: lấy danh sách nước hợp lệ từ Game (bao gồm nhảy), dùng BFS đánh giá đường còn lại qua tường rồi chọn nước có khoảng cách nhỏ nhất. Nếu hòa, chọn ngẫu nhiên. Bot chưa đánh giá đặt tường hoặc nhìn trước nước đáp trả.
- `PathFinder.shortest_distance` tính số cạnh tới hàng đích, bỏ qua vị trí quân. Đây là ước lượng để chọn trong các nước đã hợp lệ, không thay thế luật nhảy của Game.
- Bot chạy sau khi xử lý các sự kiện của khung hình, không dùng sleep/thread. Trong lượt bot, bỏ click đi quân/đặt tường của người; Chơi lại/Về menu vẫn được ưu tiên.
- Chơi lại giữ chế độ bot, xanh lá bắt đầu ván mới. Về menu rồi chọn Hai người chơi sẽ bật lại đồng hồ 30 giây/lượt.
- Kiến trúc có EasyStrategy với choose_command; chưa cần Factory chọn cấp khi chỉ có một cấp bot. Undo đã có theo quy tắc mục 12.6 và cách dùng mục 12.8.
- Kiểm tra riêng bot: `python -m unittest discover -s tests -p test_easy_bot.py -v` trong repo. Chạy toàn bộ test với `python -m unittest discover -s tests -v`. Test giao diện dùng SDL headless; vẫn cần chơi thử trên Windows.

12.8. Undo bằng Command pattern

- Khi đấu bot, nút Undo nằm trên Chơi lại. Nút bị mờ khi chưa có hành động của người để lùi. Chế độ hai người không hiện nút hoặc cho Undo.
- Bot đã đáp trả: Undo gọi undo() của lệnh bot, rồi của lệnh người gần nhất, trả về lúc người chọn nước trước đó. Bot chưa đi (kể cả người vừa thắng): chỉ lùi lệnh người. Sau Undo, bot không được đáp trả cho tới khi người chọn một hành động hợp lệ mới.
- Có thể Undo liên tiếp từng cặp lượt; dùng được sau người hoặc bot thắng. Nước không hợp lệ và hình xem trước không vào lịch sử.
- Command.execute() dùng chung trong lớp cha: chụp trạng thái trước hành động, gọi _perform() của lệnh cụ thể, chỉ ghi lịch sử nếu thành công. MoveCommand và PlaceWallCommand kế thừa cả execute() và undo(), Game vẫn giữ toàn bộ luật.
- Command.undo() chỉ chấp nhận lệnh trên cùng lịch sử và đúng ván. Nó khôi phục bản sao trạng thái qua Game.restore_state(), rồi bỏ lệnh khỏi lịch sử. Game.undo_round() chỉ điều phối thứ tự gọi undo() về tới lệnh của người, không tự suy ngược luật di chuyển/đặt tường.
- Trạng thái gồm vị trí và số tường hai phe, danh sách tường/cạnh bị chặn, chủ sở hữu, lượt, người thắng, dữ liệu đồng hồ và thông báo. Đấu bot vẫn không chạy đồng hồ. Chỉ chụp dữ liệu của ván, không sao chép cửa sổ Pygame hoặc lịch sử vào snapshot.
- Chơi lại, Về menu hoặc bắt đầu ván mới xóa lịch sử; lệnh giữ tham chiếu Board để không execute/undo xuyên sang ván mới. Không có Redo; mỗi Command thành công chỉ execute một lần, kể cả sau Undo.
- Test riêng: `python -m unittest discover -s tests -p test_undo.py -v`. Trên Windows cần thử đi quân/đặt tường → bot đáp trả → Undo, Undo nhiều lần, Undo sau thắng và Chơi lại/Về menu xóa lịch sử.
