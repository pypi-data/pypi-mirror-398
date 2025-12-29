# cli.py
import argparse
import os
import sys
from epub_to_text.processor import EpubProcessor
from epub_to_text.batch_processor import BatchProcessor

def main():
    parser = argparse.ArgumentParser(
        description="Advanced EPUB to Text/Markdown converter with batch processing support.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert single EPUB to markdown chapters
  epub-to-text book.epub --chapters-markdown
  
  # Convert single EPUB to single markdown file with images
  epub-to-text book.epub --single-markdown --extract-images
  
  # Batch process all EPUBs in a directory
  epub-to-text /path/to/epub/folder --batch --chapters-markdown --recursive
  
  # Export everything from a single EPUB
  epub-to-text book.epub --all --extract-images -o output_folder
        """
    )
    
    # Input arguments
    parser.add_argument("input", help="Path to EPUB file or directory containing EPUB files")
    parser.add_argument("-o", "--output", help="Output directory (default: './exported_books')", default="./exported_books")
    
    # Export format options
    parser.add_argument("--single-text", help="Export entire book as single text file", action="store_true")
    parser.add_argument("--single-markdown", help="Export entire book as single markdown file", action="store_true")
    parser.add_argument("--chapters-text", help="Export each chapter as separate text files", action="store_true")
    parser.add_argument("--chapters-markdown", help="Export each chapter as separate markdown files", action="store_true")
    parser.add_argument("--json", help="Export book data as JSON file", action="store_true")
    parser.add_argument("--all", help="Export in all available formats", action="store_true")
    
    # Additional options
    parser.add_argument("--extract-images", help="Extract and save images from EPUB files", action="store_true")
    parser.add_argument("--batch", help="Process multiple EPUB files (input should be directory)", action="store_true")
    parser.add_argument("--recursive", help="Search subdirectories recursively (with --batch)", action="store_true")
    parser.add_argument("--parallel", help="Process files in parallel (with --batch)", action="store_true", default=True)
    parser.add_argument("--max-workers", help="Maximum number of parallel workers", type=int, default=4)
    
    # Other options
    parser.add_argument("--info", help="Show book information only (no conversion)", action="store_true")
    parser.add_argument("--quiet", "-q", help="Suppress output messages", action="store_true")
    parser.add_argument("--verbose", "-v", help="Show detailed output", action="store_true")

    args = parser.parse_args()
    
    # Validate input
    if not os.path.exists(args.input):
        print(f"Error: Input path '{args.input}' does not exist.")
        return 1
    
    # Check if any export option is selected (unless --info or --batch)
    export_options = [
        args.single_text, args.single_markdown, args.chapters_text, 
        args.chapters_markdown, args.json, args.all
    ]
    
    if not any(export_options) and not args.info:
        print("Error: Please specify at least one export format or use --info flag.")
        print("Use --help for more information.")
        return 1
    
    # Set all formats if --all is specified
    if args.all:
        args.single_text = True
        args.single_markdown = True
        args.chapters_text = True
        args.chapters_markdown = True
        args.json = True
        args.extract_images = True
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    try:
        if args.batch or os.path.isdir(args.input):
            # Batch processing mode
            return process_batch(args)
        else:
            # Single file processing mode
            return process_single_file(args)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

def process_single_file(args):
    """Process a single EPUB file."""
    if not args.input.lower().endswith('.epub'):
        print(f"Error: File '{args.input}' is not an EPUB file.")
        return 1
    
    if not args.quiet:
        print(f"Processing: {os.path.basename(args.input)}")
    
    try:
        processor = EpubProcessor(args.input, args.output)
        
        # Show info if requested
        if args.info:
            summary = processor.get_summary()
            print("\n" + "="*50)
            print("EPUB INFORMATION")
            print("="*50)
            print(f"File: {summary['file_path']}")
            print(f"Title: {summary['title']}")
            print(f"Author: {summary['author']}")
            print(f"Language: {summary['language']}")
            print(f"Chapters: {summary['total_chapters']}")
            print(f"Images: {summary['total_images']}")
            
            if args.verbose and summary['chapter_titles']:
                print("\nChapter Titles:")
                for i, title in enumerate(summary['chapter_titles'], 1):
                    print(f"  {i:2d}. {title}")
            print("="*50)
            return 0
        
        # Process based on arguments
        files_created = []
        
        if args.single_text:
            file_path = processor.export_single_text()
            files_created.append(file_path)
            if not args.quiet:
                print(f"✓ Single text file: {os.path.basename(file_path)}")
        
        if args.single_markdown:
            file_path = processor.export_single_markdown()
            files_created.append(file_path)
            if not args.quiet:
                print(f"✓ Single markdown file: {os.path.basename(file_path)}")
        
        if args.chapters_text:
            file_paths = processor.export_chapters_text()
            files_created.extend(file_paths)
            if not args.quiet:
                print(f"✓ Chapter text files: {len(file_paths)} files created")
        
        if args.chapters_markdown:
            file_paths = processor.export_chapters_markdown()
            files_created.extend(file_paths)
            if not args.quiet:
                print(f"✓ Chapter markdown files: {len(file_paths)} files created")
        
        if args.json:
            file_path = processor.export_json()
            files_created.append(file_path)
            if not args.quiet:
                print(f"✓ JSON file: {os.path.basename(file_path)}")
        
        if args.extract_images:
            images_mapping = processor.extract_images()
            if images_mapping:
                if not args.quiet:
                    print(f"✓ Images extracted: {len(images_mapping)} images saved")
            else:
                if not args.quiet:
                    print("ℹ No images found in EPUB file")
        
        if not args.quiet:
            print(f"\nProcessing complete! Files saved to: {args.output}")
            if args.verbose:
                print(f"Total files created: {len(files_created)}")
        
        return 0
        
    except Exception as e:
        print(f"Error processing EPUB file: {e}")
        return 1

def process_batch(args):
    """Process multiple EPUB files in batch mode."""
    if not args.quiet:
        print(f"Batch processing EPUBs in: {args.input}")
    
    try:
        batch_processor = BatchProcessor(max_workers=args.max_workers)
        
        # Prepare processing options
        options = {
            'single_text': args.single_text,
            'single_markdown': args.single_markdown,
            'chapters_text': args.chapters_text,
            'chapters_markdown': args.chapters_markdown,
            'json': args.json,
            'extract_images': args.extract_images
        }
        
        # Process batch
        result = batch_processor.process_batch(
            args.input,
            args.output,
            options,
            recursive=args.recursive,
            parallel=args.parallel
        )
        
        if not args.quiet:
            print(f"\n{result['message']}")
            
            if args.verbose and result['results']:
                print(f"\nDetailed Results:")
                for res in result['results']:
                    status = "✓" if res['success'] else "✗"
                    filename = os.path.basename(res['epub_path'])
                    print(f"  {status} {filename}")
                    if not res['success'] and res['error']:
                        print(f"    Error: {res['error']}")
                    elif res['success'] and args.verbose:
                        print(f"    Files created: {len(res['files_created'])}")
        
        # Return 0 if any files were processed successfully, 1 if all failed
        return 0 if result['processed'] > 0 else 1
        
    except Exception as e:
        print(f"Error in batch processing: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
