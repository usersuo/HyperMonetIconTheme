from processors.cleaner import Cleaner
from configs.config import CleanConfig


def main():
    print("Cleaner: 手动清理")
    Cleaner.cleanup(CleanConfig.clean_up)


if __name__ == "__main__":
    main()
