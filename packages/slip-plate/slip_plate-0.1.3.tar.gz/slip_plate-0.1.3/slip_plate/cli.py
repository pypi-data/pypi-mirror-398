import argparse

from .slip_plate import main as run_demo


def build_parser():
    parser = argparse.ArgumentParser(description="Slip-plate demo CLI")
    parser.add_argument("--dek-size", type=int, choices=[128, 192, 256], default=256)
    parser.add_argument("--parts", type=int, default=3)
    parser.add_argument("--threshold", type=int, default=2)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    run_demo(args.dek_size, args.parts, args.threshold)


if __name__ == "__main__":
    main()