# EPUB to Text Converter

A professional, high-performance EPUB conversion library for extracting and converting EPUB files to multiple formats (Text, Markdown, JSON). Supports both single-file and batch processing with parallel execution.

**Features:**

- 📚 Extract chapters, images, and metadata from EPUB files
- 📝 Export to multiple formats: Text, Markdown, JSON, HTML
- 🔄 Batch process multiple EPUB files in parallel
- 🖼️ Extract and link images with proper paths
- 📊 Get detailed book information and statistics
- 🎯 Simple CLI and comprehensive Python API

## Installation

```bash
pip install epub-to-text
```

Or from source:

```bash
pip install https://github.com/thinh-vu/epub_to_text.git
```

## Quick Start

### Command Line

```bash
# Convert to markdown chapters with images
epub-to-text your_book.epub --chapters-markdown --extract-images

# Convert to all formats
epub-to-text book.epub --all -o output/

# Show book information
epub-to-text your_book.epub --info

# Batch process EPUBs with parallel execution
epub-to-text /your_epub_folder_path --batch --all --parallel
```

### Python API

```python
from epub_to_text import EpubProcessor

# Basic usage
processor = EpubProcessor('book.epub', 'output/')
summary = processor.get_summary()
processor.export_chapters_markdown()
processor.extract_images()
```

```python
from epub_to_text import BatchProcessor

# Batch processing
batch = BatchProcessor(max_workers=4)
result = batch.process_batch(
    '/epub/folder',
    './output',
    {'chapters_markdown': True, 'extract_images': True},
    recursive=True,
    parallel=True
)
```

## Documentation

Complete documentation available in the [`docs/`](./docs/) folder:

- **[Quick Start](docs/QUICK_START.md)** - Get started in minutes
- **[API Reference](docs/API_REFERENCE.md)** - Complete class/method documentation
- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design and patterns
- **[Integration Guide](docs/INTEGRATION_GUIDE.md)** - AI agent integration patterns
- **[Advanced Usage](docs/ADVANCED_USAGE.md)** - Custom processors and optimization

## CLI Options

```bash
Usage: epub-to-text [OPTIONS] <file_or_directory>

Options:
  --single-text          Export entire book as text
  --single-markdown      Export entire book as markdown
  --chapters-text        Export each chapter as text files
  --chapters-markdown    Export each chapter as markdown files
  --json                 Export as JSON with metadata
  --all                  Export in all formats
  --extract-images       Extract and save images
  --batch                Process multiple EPUBs
  --recursive            Search subdirectories
  --parallel             Process files in parallel
  --max-workers N        Number of parallel workers (default: 4)
  --info                 Show book information only
  --verbose              Detailed output
  -o, --output DIR       Output directory (default: ./exported_books)
```

## Output Structure

**Single file mode:**

```
output/
├── book.md          # Complete book as markdown
├── book.txt         # Complete book as text
└── book.json        # Structured data
```

**Chapter-wise mode:**

```
output/
└── Book_Title/
    ├── 01_Introduction.md
    ├── 02_Chapter_Two.md
    ├── 03_Conclusion.md
    └── images/
        ├── cover.jpg
        └── diagram1.png
```

## Project Structure

```
epub_to_text/
├── __init__.py        # Package initialization
├── cli.py             # Command-line interface
├── reader.py          # EPUB file reading
├── extractor.py       # Content extraction
├── converter.py       # Format conversion
├── processor.py       # Single-file processing
└── batch_processor.py # Batch processing
```

## Key Classes

| Class              | Purpose                                |
| ------------------ | -------------------------------------- |
| `EpubProcessor`    | High-level single-file processing      |
| `BatchProcessor`   | Batch processing with parallel support |
| `EpubExtractor`    | Extract chapters, images, metadata     |
| `ContentConverter` | Format conversion utilities            |
| `EpubReader`       | Low-level EPUB file reading            |

## Requirements

- Python 3.10+
- ebooklib >= 0.17.1
- beautifulsoup4 >= 4.9.0

## Use Cases

- **Knowledge Base**: Extract EPUB content for building AI training datasets
- **Content Analysis**: Process multiple books for NLP tasks
- **Digital Library**: Convert EPUB collections to searchable text/markdown
- **Accessibility**: Generate alternative formats from EPUB books
- **Content Preservation**: Archive book content in multiple formats

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

1. Check the [documentation](docs/)
2. Review [API Reference](docs/API_REFERENCE.md) and [Architecture Guide](docs/ARCHITECTURE.md)
3. Search existing [issues](https://github.com/your-repo/epub_to_text/issues)

## Acknowledgments

- [ebooklib](https://github.com/aerkalov/ebooklib) - EPUB parsing
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML/XML parsing