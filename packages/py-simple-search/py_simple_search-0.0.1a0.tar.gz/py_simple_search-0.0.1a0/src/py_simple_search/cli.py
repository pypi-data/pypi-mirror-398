import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="My CLI")
    parser.add_argument("--name", type=str, help="Name")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(args)


if __name__ == "__main__":
    main()
