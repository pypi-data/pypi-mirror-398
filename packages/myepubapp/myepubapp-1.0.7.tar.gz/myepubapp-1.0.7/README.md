# MyEPUBApp

[![PyPI version](https://badge.fury.io/py/myepubapp.svg)](https://pypi.org/project/myepubapp/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful and flexible text-to-EPUB conversion tool that transforms plain text files into standard EPUB e-book format with advanced features for content processing and validation.

## ✨ Features

- 📖 **Text to EPUB Conversion**: Convert plain text files to fully EPUB-compliant e-books
- 📑 **Intelligent Chapter Detection**: Automatically identify and split chapters using special marker symbols
- 🎯 **Smart Volume Detection**: Automatic hierarchical TOC generation based on chapter level combinations
  - Detects h1+h2 pattern and makes h1 chapters into volumes
  - Detects h2+h3 pattern and makes h2 chapters into volumes
  - Detects h1+h3 pattern and makes h1 chapters into volumes
- 🔄 **Flexible Operation Modes**: Support for creating new EPUB files or appending chapters to existing ones
- ✅ **EPUB Validation**: Built-in EPUB format validation with detailed compliance checking
- 🏗️ **Modular Architecture**: Clean, maintainable code structure for easy extension
- 📝 **Comprehensive Logging**: Detailed operation logging with configurable log levels
- 🎨 **Cover Image Support**: Add custom cover images to your EPUB files
- 📋 **Table of Contents**: Automatic generation of navigation and table of contents with hierarchical structure

## 🚀 Installation

### Requirements
- Python 3.8 or higher
- pip package manager

### Option 1: Install from PyPI (Recommended)

```bash
pip install myepubapp
```

### Option 2: Install from Source

1. Clone the repository:
```bash
git clone https://github.com/eyes1971/myepubapp.git
cd myepubapp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install in development mode:
```bash
pip install -e .
```

## 📖 Usage

### Basic Usage

#### 1. Create New EPUB File
```bash
myepubapp -i input.txt --output-epub output.epub
```

**Automatic Title Generation**: Book titles are automatically generated from input filenames (e.g., `my_book.txt` becomes "My Book")

#### 2. Append Chapters to Existing EPUB
```bash
myepubapp -a input.txt --input-epub existing.epub --output-epub updated.epub
```

#### 3. Validate EPUB File
```bash
myepubapp -v --input-epub file.epub
```

### Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--init` | `-i` | Initialize mode: create new EPUB file |
| `--append` | `-a` | Append mode: add chapters to existing EPUB |
| `--validate` | `-v` | Validate EPUB file format and structure |
| `input_file` | | Input text file path (not required for validate mode) |
| `--input-epub` | `-ie` | Existing EPUB file (required for append/validate modes) |
| `--output-epub` | `-o` | Output EPUB file path |
| `--convert-tags` | `-ct` | Convert `<>` tags to Chinese book title marks `《》` |
| `--cover` | `-c` | Path to cover image file |

### Input File Format

Text files should use special marker symbols for chapter organization:

```
※☆ Introduction Title
This is the introduction content.
It can span multiple paragraphs and will be displayed as a separate introduction page.

※ⅰ Chapter 1 Title
Chapter content goes here...
Multiple paragraphs are supported.

※ⅱ Chapter 1 Section 1
Subsection content...

※ⅲ Chapter 1 Section 1 Subsection 1
Deeper level content with full formatting support.
```

#### Marker Symbols:
- `※☆`: Introduction page (creates separate intro page)
- `※ⅰ`: Level 1 chapter (h1 heading)
- `※ⅱ`: Level 2 chapter (h2 heading)
- `※ⅲ`: Level 3 chapter (h3 heading)

## 📋 Examples

### Create Simple EPUB
```bash
myepubapp -i sample.txt --output-epub mybook.epub
```

### Create EPUB with Chinese Tag Conversion
```bash
myepubapp -i sample.txt --output-epub mybook.epub --convert-tags
```

### Add Cover Image
```bash
myepubapp -i sample.txt --output-epub mybook.epub --cover cover.jpg
```

### Append Chapters to Existing EPUB
```bash
myepubapp -a chapter2.txt --input-epub mybook.epub --output-epub mybook_updated.epub
```

### Validate EPUB File
```bash
myepubapp -v --input-epub mybook.epub
```

## 🏗️ Project Structure

```
myepubapp/
├── core/                    # Core business logic
│   ├── __init__.py
│   ├── book.py             # EPUB book management
│   ├── chapter.py          # Chapter data structures
│   └── metadata.py         # EPUB metadata handling
├── generators/             # Content generation modules
│   ├── __init__.py
│   ├── content.py          # Content processing and chapter generation
│   └── toc.py             # Table of contents generation
├── utils/                  # Utility modules
│   ├── __init__.py
│   ├── epub_validator.py   # EPUB format validation
│   ├── file_handler.py     # File I/O operations
│   ├── logger.py          # Logging configuration
│   └── text_processor.py   # Text processing utilities
├── exceptions/             # Custom exception classes
│   ├── __init__.py
│   └── epub_exceptions.py  # EPUB-specific exceptions
├── cli.py                 # Command-line interface
├── __init__.py            # Package initialization
└── py.typed               # Type hints marker
```

## 📋 Dependencies

- `ebooklib>=0.18.0`: Core EPUB file processing and manipulation
- `beautifulsoup4>=4.12.0`: HTML/XML parsing and manipulation

## 🔍 Validation Features

The built-in EPUB validator checks:
- ✅ File structure compliance
- ✅ Required metadata presence
- ✅ MIME type validation
- ✅ Container XML format
- ✅ Content OPF validation
- ✅ Spine and manifest integrity
- ✅ XHTML content validation

## 📝 Logging

All operations are logged with configurable verbosity. Logs are written to:
- Console output (with appropriate log levels)
- `logs/myepubapp.log` file (detailed operation logs)

## 🤝 Contributing

We welcome contributions! Please feel free to:

1. Report bugs via [GitHub Issues](https://github.com/eyes1971/myepubapp/issues)
2. Submit feature requests
3. Create pull requests with improvements

### Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/myepubapp.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate the environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
5. Install development dependencies: `pip install -r requirements.txt`
6. Install in development mode: `pip install -e .`
7. Run tests: `python -m pytest`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [ebooklib](https://github.com/aerkalov/ebooklib) for EPUB processing
- Uses [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing
- Inspired by the need for simple, reliable text-to-EPUB conversion tools

## 📞 Support

If you encounter any issues or have questions:

- Check the [Issues](https://github.com/eyes1971/myepubapp/issues) page
- Create a new issue with detailed information
- Include sample input files and error messages when reporting bugs

## 📋 Changelog

### Version 1.0.4 (2025-09-08)
- ✨ **Added Smart Volume Detection**: Automatic hierarchical TOC generation based on chapter level combinations
  - Detects h1+h2 pattern and makes h1 chapters into volumes
  - Detects h2+h3 pattern and makes h2 chapters into volumes
  - Detects h1+h3 pattern and makes h1 chapters into volumes
- 🎯 **Added Intelligent TOC Structure**: Creates nested table of contents for multi-volume books
- 📖 **Enhanced Chapter Processing**: Improved chapter ordering and Introduction page positioning
- 🐛 **Fixed Critical EPUB Generation Errors**: Resolved multiple epubcheck validation failures
  - Fixed duplicate cover image entries in manifest
  - Fixed undefined cover property errors
  - Fixed duplicate "cover" IDs causing OPF validation errors
- 🔧 **Fixed TOC Reading Order Issues**: Fixed NAV-011 warnings about TOC link order mismatch
  - TOC links now match spine reading order
  - Proper EPUB 3.0 compliance for navigation structure
- 📋 **Fixed Cover Image Handling**: Resolved cover image declaration and property issues
  - Fixed RSC-008 error: Referenced resource not declared in OPF manifest
  - Fixed OPF-027 error: Undefined property "cover"
  - Fixed RSC-005 error: Duplicate entries in ZIP file
- 📖 **Fixed Introduction Page Ordering**: Fixed Introduction page appearing at the end instead of beginning
  - Proper spine ordering: nav → intro → chapters
  - Correct TOC positioning for introduction content
- ✅ **Enhanced EPUB 3.0 Compliance**: All generated EPUB files now pass epubcheck validation

### Version 1.0.3 (2025-09-08)
- This update primarily focuses on optimizing the core `src/myepubapp/core/book.py` module:
- Updated function documentation: `_extract_chapters_from_epub()` and `merge_existing_epub_with_new_chapters()`
- Updated log outputs: EPUB merge success and error messages
- Maintained functionality integrity: All changes are non-breaking, preserving all functional logic

### Version 1.0.2 (2025-09-05)
- 🐛 **Fixed**: Critical TOC generation bug causing missing chapters in table of contents
- 🐛 **Fixed**: TOC only showing first few chapters, skipping subsequent ones in multi-chapter documents
- 🔧 **Improved**: TOC generator recursive logic now properly handles chapter indexing after processing child elements
- 🔧 **Improved**: Fixed index management in `build_toc_level()` function to prevent chapter skipping
- ✅ **Enhanced**: TOC generation now works correctly for any number of chapters and all hierarchy levels

### Version 1.0.1 (2025-09-05)
- 🐛 **Fixed**: EPUB TOC generation error when using h2/h3 chapter levels
- � **Fixed**: Empty `<ol>` elements in nav.xhtml causing epubcheck validation failures
- 🔧 **Improved**: TOC generator now properly handles all chapter level combinations (h1, h2, h3)
- 🔧 **Improved**: Automatic level detection for chapters with skipped levels (e.g., intro → h2)
- ✅ **Enhanced**: EPUB validation compliance for all supported chapter structures

### Version 1.0.0 (2025-09-01)
- ✨ Initial release with full text-to-EPUB conversion functionality
- �📖 Support for Chinese content with automatic title mark conversion
- 📑 Intelligent chapter detection using marker symbols
- 🔄 Flexible operation modes (create new EPUB or append chapters)
- ✅ Built-in EPUB validation with detailed compliance checking
- 🎨 Cover image support
- 📋 Automatic table of contents generation

---

**Version**: 1.0.4
**Author**: Sam Weng
**Repository**: [https://github.com/eyes1971/myepubapp](https://github.com/eyes1971/myepubapp)
