import argparse
from pathlib import Path
from typing import Optional

from .core.book import Book
from .core.metadata import Metadata
from .exceptions.epub_exceptions import EPUBError
from .generators.content import ContentGenerator
from .utils.epub_validator import EPUBValidator
from .utils.file_handler import FileHandler
from .utils.logger import setup_logger

logger = None  # Will be initialized after argument parsing


def generate_title_from_filename(input_file: str) -> str:
    """Generate book title from input filename"""
    try:
        # Get filename without path
        file_path = Path(input_file)
        file_name = file_path.stem  # Remove extension

        # Convert underscores and hyphens to spaces, capitalize each word
        title = file_name.replace("_", " ").replace("-", " ")
        words = title.split()
        capitalized_words = []
        for word in words:
            capitalized_words.append(word.capitalize())
        title = " ".join(capitalized_words)

        # Use default name if filename is empty
        if not title.strip():
            title = "Generated from Text"

        return title

    except Exception as e:
        logger.warning(f"Error generating title: {e}")
        return "Generated from Text"


def initialize_epub(
    input_file: str,
    output_epub: str,
    convert_tags: bool = False,
    cover_path: Optional[str] = None,
) -> None:
    """Initialize and generate new EPUB file"""
    try:
        file_handler = FileHandler()
        content = file_handler.read_file(input_file)

        # Auto-generate book title from input filename
        book_title = generate_title_from_filename(input_file)
        logger.info(f"Generated title: {book_title}")

        metadata = Metadata(
            title=book_title, language="zh", author="Text to EPUB Converter"
        )

        book = Book(metadata)
        content_generator = ContentGenerator()
        chapters = content_generator.generate_chapters(content, convert_tags)

        for chapter in chapters:
            book.add_chapter(chapter)

        # Add cover if provided
        if cover_path:
            book.add_cover(cover_path)

        # Generate EPUB structure (TOC, nav, spine)
        book.generate_epub(output_epub)
        logger.info(f"EPUB file '{output_epub}' generated successfully.")

    except EPUBError as e:
        logger.error(f"Error generating EPUB: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="EPUB creation script",
        epilog="""
Symbol Guide for Input Files:
  ※☆ Introduction page (creates separate intro page)
  ※VOL Volume title (creates hierarchical TOC structure)
  ※ⅰ Level 1 chapter (h1)
  ※ⅱ Level 2 chapter (h2)
  ※ⅲ Level 3 chapter (h3)

Example Input Format:
  ※☆ Book Introduction
  This is the introduction content...

  ※VOL 第一卷：开端
  ※ⅰ Chapter 1 Title
  Chapter content here...

  ※ⅱ Chapter 1 Section 1
  Subsection content...

  ※VOL 第二卷：发展
  ※ⅰ Chapter 21 Title
  More chapter content...
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-i", dest="init", help="Initialize EPUB file", action="store_true"
    )
    parser.add_argument(
        "-a",
        dest="append",
        help="Append new chapters to existing EPUB file",
        action="store_true",
    )
    parser.add_argument(
        "-v", dest="validate", help="Validate EPUB file", action="store_true"
    )
    parser.add_argument(
        "input_file", nargs="?", help="Input text file (not required for validate mode)"
    )
    parser.add_argument(
        "--input-epub", "-oe", help="Existing EPUB file (append mode only)"
    )
    parser.add_argument("--output-epub", "-o", help="Output EPUB file path")
    parser.add_argument(
        "--convert-tags",
        "-ct",
        action="store_true",
        help="Convert <> tags to Chinese book title marks 《》",
    )
    parser.add_argument("--cover", "-c", help="Path to cover image file")
    parser.add_argument(
        "--debug", "-d", action="store_true", help="Enable debug logging"
    )

    args = parser.parse_args()

    # Initialize logger after parsing arguments
    global logger
    logger = setup_logger(debug=args.debug)

    try:
        if args.validate:
            if not args.input_epub:
                raise EPUBError("EPUB file must be specified for validation.")
            validator = EPUBValidator()
            results = validator.validate_epub(args.input_epub)
            validator.print_validation_report(results)
            if not results["is_valid"]:
                exit(1)

        elif args.init:
            if not args.output_epub:
                raise EPUBError("Output EPUB file path must be specified in init mode.")
            initialize_epub(
                args.input_file, args.output_epub, args.convert_tags, args.cover
            )

        elif args.append:
            if not args.input_epub:
                raise EPUBError("Existing EPUB file must be specified in append mode.")

            output_epub = args.output_epub or f"new_{Path(args.input_epub).name}"
            if not args.output_epub:
                logger.info(f"Output file not specified. Writing to '{output_epub}'")
            Book.merge_existing_epub_with_new_chapters(
                args.input_epub,
                args.input_file,
                output_epub,
                convert_tags=args.convert_tags,
            )
        else:
            raise EPUBError("Please specify -i, -a, or -v mode.")

    except EPUBError as e:
        logger.error(f"EPUB processing error: {str(e)}")
        exit(1)
    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        exit(1)
    except PermissionError as e:
        logger.error(f"Permission denied: {str(e)}")
        exit(1)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        exit(130)
    except Exception as e:
        logger.error(f"Unexpected error during execution: {str(e)}")
        logger.debug("Full traceback:", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()
