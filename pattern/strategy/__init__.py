# Xuất giao diện, ba chiến lược cụ thể và Factory tạo bot.
from pattern.strategy.bot_strategy import BotStrategy
from pattern.strategy.bot_strategy_factory import BotStrategyFactory
from pattern.strategy.easy_strategy import EasyStrategy
from pattern.strategy.hard_strategy import HardStrategy
from pattern.strategy.medium_strategy import MediumStrategy

__all__ = [
    "BotStrategy", "BotStrategyFactory", "EasyStrategy", "HardStrategy", "MediumStrategy",
]
