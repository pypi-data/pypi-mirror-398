import argparse
import sys
from textnotes.processor import process_all   

def main():
    parser = argparse.ArgumentParser(
        prog="textnotes",
        description="Generate notes, summaries, flashcards, and topic groups from text."
    )

    parser.add_argument(
        "text",
        nargs="*",
        help="Text to process"
    )

    args = parser.parse_args()

    # If no text is provided, show help
    if not args.text:
        parser.print_help()
        sys.exit(0)

    # Combine all words into text
    input_text = " ".join(args.text)

    output, filepath = process_all(input_text)

    print(output)
    print(f"\n💾 Output saved to file: {filepath}")

if __name__ == "__main__":
    main()
