class LevelCalculator:
    @staticmethod
    def get_level(points: int) -> str:
        if 100 <= points <= 299:
            level = "silver"
        elif 300 <= points <= 999:
            level = "gold"
        elif points >= 1000:
            level = "diamond"
        else:
            level = "bronze"
        return level
