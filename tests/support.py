import pygame


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
