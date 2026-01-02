import sys

from nepali_unicoder.convert import Converter


def main():
    args = sys.argv[1:]
    mode = "roman"

    if "--preeti" in args:
        mode = "preeti"
        args.remove("--preeti")

    if len(args) < 1:
        # Check if there is stdin
        if not sys.stdin.isatty():
            input_text = sys.stdin.read()
        else:
            print('Usage: python -m nepali_unicoder "your roman text here"')
            print('       python -m nepali_unicoder --preeti "your preeti text here"')
            print('       or: echo "namaste" | python -m nepali_unicoder')
            return
    else:
        input_text = " ".join(args)

    converter = Converter(mode=mode)
    result = converter.convert(input_text)
    print(result)


if __name__ == "__main__":
    main()
