from pathlib import Path
import unittest


def main() -> None:
    """Discover and run all test modules under the tests package."""
    root = Path(__file__).resolve().parent
    suite = unittest.defaultTestLoader.discover(str(root))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
