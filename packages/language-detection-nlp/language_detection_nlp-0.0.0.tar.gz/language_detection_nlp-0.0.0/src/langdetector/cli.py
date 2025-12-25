import argparse
import sys
from .detect import detect_language, detect_languages


def main(argv=None):
    parser = argparse.ArgumentParser(description="Language detection CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", "-t", help="Text string to detect language for")
    group.add_argument("--file", "-f", help="Path to file to read text from")
    parser.add_argument("--top", "-n", type=int, default=1, help="Number of top candidates to show")
    args = parser.parse_args(argv)

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                text = fh.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return 2
    else:
        text = args.text

    if args.top == 1:
        result = detect_language(text)
        if result["language"] is None:
            print("Could not detect language")
            return 0
        name = result.get("name") or result["language"]
        print(f"{name} ({result['language']}) — confidence={result['confidence']:.3f}")
        return 0

    candidates = detect_languages(text)
    for i, (lang, prob) in enumerate(candidates[: args.top], start=1):
        name = lang
        print(f"{i}. {name} ({lang}) — {prob:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
