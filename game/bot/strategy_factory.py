from random import choice

from game.bot.easy import EasyStrategy
from game.bot.hard import HardStrategy
from game.bot.medium import MediumStrategy


# Factory tập trung việc tạo đúng chiến lược theo cấp được chọn trên menu.
class BotStrategyFactory:
    # Không mặc định sang cấp khác nếu tên cấp không hợp lệ.
    @staticmethod
    def create(level, choose=choice):
        strategies = {"easy": EasyStrategy, "medium": MediumStrategy, "hard": HardStrategy}
        if level not in strategies:
            raise ValueError("Cấp bot không hợp lệ")
        return strategies[level](choose=choose)
