import base64
import requests
import argparse
import os
import sys

from process_pdf import alt_text


def main():
    parser = argparse.ArgumentParser(
        description="Process a PDF or image file with Tesseract OCR"
    )
    parser.add_argument("-i", "--input", type=str, help="The input PDF file")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="The output PDF file",
    )

    parser.add_argument("--name", type=str, default="", help="Pdfix license name")
    parser.add_argument("--key", type=str, default="", help="Pdfix license key")
    parser.add_argument(
        "--overwrite",
        type=bool,
        required=False,
        default=False,
        help="Overwrite alternate text if already present in the tag",
    )
    args = parser.parse_args()

    if not args.input or not args.output:
        parser.error("The following arguments are required: -i/--input, -o/--output ")

    input_file = args.input
    output_file = args.output

    if not os.path.isfile(input_file):
        sys.exit(f"Error: The input file '{input_file}' does not exist.")
        return

    if input_file.lower().endswith(".pdf") and output_file.lower().endswith(".pdf"):
        try:
            alt_text(input_file, output_file, args.name, args.key, args.overwrite)
            # print(desc)
        except Exception as e:
            sys.exit("Failed to run alternate description: {}".format(e))

    else:
        print("Input and output file must be PDF")


if __name__ == "__main__":
    main()
