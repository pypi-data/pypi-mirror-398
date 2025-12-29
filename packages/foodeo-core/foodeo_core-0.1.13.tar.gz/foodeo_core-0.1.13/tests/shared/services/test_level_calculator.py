import unittest

from foodeo_core.shared.services.level_calculator import LevelCalculator


class TestLevelCalculator(unittest.TestCase):
    def test_get_level_thresholds(self) -> None:
        cases = [
            (0, "bronze"),
            (99, "bronze"),
            (100, "silver"),
            (150, "silver"),
            (299, "silver"),
            (300, "gold"),
            (750, "gold"),
            (999, "gold"),
            (1000, "diamond"),
            (5000, "diamond"),
        ]

        for points, expected in cases:
            with self.subTest(points=points):
                self.assertEqual(LevelCalculator.get_level(points), expected)
