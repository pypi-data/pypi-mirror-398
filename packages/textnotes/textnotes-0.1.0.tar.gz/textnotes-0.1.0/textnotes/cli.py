import sys
from .processor import process_all

def main():
    if len(sys.argv) < 2:
        print("Usage: textnotes \"your text here\"")
        return

    text = " ".join(sys.argv[1:])
    output, filepath = process_all(text)

    print(output)
    print(f"\n💾 Output saved to file: {filepath}")
