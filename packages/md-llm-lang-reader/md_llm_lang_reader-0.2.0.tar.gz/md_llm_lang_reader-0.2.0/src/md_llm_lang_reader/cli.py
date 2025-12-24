import argparse
import sys

from .generator import Options, generate_file


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="md-llm-lang-reader",
        description="Generate language-learning HTML readers (with sentence-level LLM translations and TTS) from Markdown."
    )
    parser.add_argument("-i", "--input", required=True,
                        help="Input Markdown file path")
    parser.add_argument("-o", "--output", required=True,
                        help="Output HTML file path")
    parser.add_argument("--src", default="fr",
                        help="Source language code (default: fr)")
    parser.add_argument("--tgt", default="en",
                        help="Target language code (default: en)")
    parser.add_argument("--provider", required=True,
                        help="Model provider identifier")
    parser.add_argument("--model", required=True, help="Model name/identifier")
    parser.add_argument(
        "-v",
        "--verbose",
        type=int,
        default=1,
        choices=[0, 1, 2, 3],
        help="Verbosity: 0=silent, 1=headings, 2=paragraph preview, 3=full original paragraphs",
    )
    parser.add_argument(
        "--js-url",
        default="https://cdn.jsdelivr.net/gh/sekika/langreader@main/js/langreader.js",
        help="External JavaScript URL for the reader logic"
    )
    parser.add_argument(
        "--css-url",
        default="https://cdn.jsdelivr.net/gh/sekika/langreader@main/css/langreader.css",
        help="External CSS URL for the reader styles"
    )
    # Added: Option to resume generation
    parser.add_argument(
        "--continue",
        dest="resume",
        action="store_true",
        help="Resume generation from the existing output file if interrupted."
    )

    args = parser.parse_args(argv)

    opts = Options(
        input_path=args.input,
        output_path=args.output,
        src=args.src,
        tgt=args.tgt,
        provider=args.provider,
        model=args.model,
        verbose=args.verbose,
        js_url=args.js_url,
        css_url=args.css_url,
        resume=args.resume,
    )

    try:
        generate_file(opts)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if args.verbose > 0:
        print(f"Generated {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
