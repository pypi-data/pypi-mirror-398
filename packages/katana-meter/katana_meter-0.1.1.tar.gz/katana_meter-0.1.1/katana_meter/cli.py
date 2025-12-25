import argparse
from .core import analyze_file, DEFAULT_TARGET_LUFS


def main():
    parser = argparse.ArgumentParser(
        prog="katana-meter",
        description="Katana Meter CLI (Analyzer Only)"
    )
    parser.add_argument("file", nargs="?", help="Audio file path")
    parser.add_argument("--target", type=float, default=DEFAULT_TARGET_LUFS)
    parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if not args.file:
        parser.print_help()
        return

    result = analyze_file(args.file, target_lufs=args.target)

    if args.json:
        print(result)
        return

    print(f"Integrated LUFS : {result['lufs']}")
    print(f"Gain to {result['target_lufs']} : {result['gain_to_target_db']} dB")
    print(f"Peak (approx)   : {result['peak_dbtp_approx']} dBTP")
    print(f"ΔE              : {result['delta_e']}")


if __name__ == "__main__":
    main()
