from random import choice

from pattern.strategy.easy_strategy import EasyStrategy
from pattern.strategy.hard_strategy import HardStrategy
from pattern.strategy.medium_strategy import MediumStrategy


# Factory tạo đúng chiến lược bot theo cấp độ người chơi chọn.
class BotStrategyFactory:
    # Không mặc định sang cấp khác nếu tên cấp không hợp lệ.
    @staticmethod
    def create(level, choose=choice):
        strategies = {"easy": EasyStrategy, "medium": MediumStrategy, "hard": HardStrategy}
        if level not in strategies:
            raise ValueError("Cấp bot không hợp lệ")
        return strategies[level](choose=choose)
