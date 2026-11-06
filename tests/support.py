import pygame


# Thực thi lệnh của một ván thật qua Invoker để lịch sử tuân theo chính sách của ván.
def execute_command(command):
    return command.receiver.command_invoker.execute(command)


# Các khung hình chọn chế độ/cấp/lượt qua menu thật; mỗi trang nhận một click.
def menu_frames(menu, mode="bot", level="easy", human_first=True):
    rects = [menu.start_button_rect if mode == "two_players" else menu.versus_bot_button_rect]
    if mode == "bot":
        rects.append({"easy": menu.bot_button_rect, "medium": menu.medium_bot_button_rect,
                      "hard": menu.hard_bot_button_rect}[level])
        rects.append(menu.first_button_rect if human_first else menu.second_button_rect)
    return [[pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center)] for rect in rects]


# Dùng luồng menu thật: hai người vào ngay, đấu bot đi qua chọn cấp/lượt.
def start_game(app, menu, mode="bot", level="easy", human_first=True):
    running = True
    for events in menu_frames(menu, mode, level, human_first):
        running = app.handle_event(events[0])
    return running


# Test pixel kiểm tra hình hoàn tất; test animation dùng đồng hồ giả riêng.
def settle_effects(view, game):
    view.motion.reset(game.board)


# Vân gỗ làm độ sáng biến thiên nhẹ, nhưng phải giữ đúng màu phe/xem trước.
def assert_wood_color(test, pixel, expected):
    for actual, base in zip(tuple(pixel)[:3], expected):
        test.assertLessEqual(abs(actual - base), 15)
