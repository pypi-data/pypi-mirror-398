# batch_processor.py
import os
import glob
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from epub_to_text.processor import EpubProcessor

class BatchProcessor:
    """
    Process multiple EPUB files in batch mode.
    """
    
    def __init__(self, max_workers=4):
        """
        Initialize BatchProcessor.
        
        Args:
            max_workers (int): Maximum number of worker threads for parallel processing.
        """
        self.max_workers = max_workers
    
    def find_epub_files(self, input_path, recursive=True):
        """
        Find all EPUB files in the given path.
        
        Args:
            input_path (str): Directory path to scan for EPUB files.
            recursive (bool): Whether to search subdirectories recursively.
        
        Returns:
            list: List of EPUB file paths found.
        """
        epub_files = []
        
        if os.path.isfile(input_path):
            if input_path.lower().endswith('.epub'):
                return [input_path]
            else:
                return []
        
        if not os.path.isdir(input_path):
            raise ValueError(f"Input path does not exist: {input_path}")
        
        if recursive:
            # Search recursively
            pattern = os.path.join(input_path, '**', '*.epub')
            epub_files = glob.glob(pattern, recursive=True)
        else:
            # Search only in the current directory
            pattern = os.path.join(input_path, '*.epub')
            epub_files = glob.glob(pattern)
        
        return sorted(epub_files)
    
    def process_single_epub(self, epub_path, output_dir, options):
        """
        Process a single EPUB file.
        
        Args:
            epub_path (str): Path to EPUB file.
            output_dir (str): Output directory.
            options (dict): Processing options.
        
        Returns:
            dict: Processing result.
        """
        try:
            processor = EpubProcessor(epub_path, output_dir)
            
            result = {
                'epub_path': epub_path,
                'success': True,
                'files_created': [],
                'error': None
            }
            
            # Process based on options
            if options.get('single_markdown'):
                output_file = processor.export_single_markdown()
                result['files_created'].append(output_file)
            
            if options.get('single_text'):
                output_file = processor.export_single_text()
                result['files_created'].append(output_file)
            
            if options.get('chapters_markdown'):
                files = processor.export_chapters_markdown()
                result['files_created'].extend(files)
            
            if options.get('chapters_text'):
                files = processor.export_chapters_text()
                result['files_created'].extend(files)
            
            if options.get('json'):
                output_file = processor.export_json()
                result['files_created'].append(output_file)
            
            # Extract images if requested
            if options.get('extract_images'):
                images_saved = processor.extract_images()
                result['images_saved'] = images_saved
            
            return result
            
        except Exception as e:
            return {
                'epub_path': epub_path,
                'success': False,
                'files_created': [],
                'error': str(e)
            }
    
    def process_batch(self, input_path, output_dir, options, recursive=True, parallel=True):
        """
        Process multiple EPUB files in batch.
        
        Args:
            input_path (str): Directory containing EPUB files or single EPUB file.
            output_dir (str): Output directory for processed files.
            options (dict): Processing options.
            recursive (bool): Whether to search subdirectories.
            parallel (bool): Whether to process files in parallel.
        
        Returns:
            dict: Batch processing results.
        """
        # Find all EPUB files
        epub_files = self.find_epub_files(input_path, recursive)
        
        if not epub_files:
            return {
                'total_files': 0,
                'processed': 0,
                'failed': 0,
                'results': [],
                'message': f"No EPUB files found in: {input_path}"
            }
        
        print(f"Found {len(epub_files)} EPUB file(s) to process.")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        results = []
        
        if parallel and len(epub_files) > 1:
            # Process in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all jobs
                future_to_epub = {
                    executor.submit(self.process_single_epub, epub_path, output_dir, options): epub_path 
                    for epub_path in epub_files
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_epub):
                    epub_path = future_to_epub[future]
                    try:
                        result = future.result()
                        results.append(result)
                        
                        if result['success']:
                            print(f"✓ Processed: {os.path.basename(epub_path)}")
                        else:
                            print(f"✗ Failed: {os.path.basename(epub_path)} - {result['error']}")
                            
                    except Exception as e:
                        results.append({
                            'epub_path': epub_path,
                            'success': False,
                            'files_created': [],
                            'error': f"Processing error: {str(e)}"
                        })
                        print(f"✗ Error processing {os.path.basename(epub_path)}: {e}")
        else:
            # Process sequentially
            for epub_path in epub_files:
                print(f"Processing: {os.path.basename(epub_path)}...")
                result = self.process_single_epub(epub_path, output_dir, options)
                results.append(result)
                
                if result['success']:
                    print(f"✓ Completed: {os.path.basename(epub_path)}")
                else:
                    print(f"✗ Failed: {os.path.basename(epub_path)} - {result['error']}")
        
        # Summary
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        return {
            'total_files': len(epub_files),
            'processed': successful,
            'failed': failed,
            'results': results,
            'message': f"Batch processing complete: {successful}/{len(epub_files)} files processed successfully."
        }
    
    def get_processing_options(self):
        """
        Get available processing options.
        
        Returns:
            dict: Dictionary of available options and their descriptions.
        """
        return {
            'single_markdown': 'Export entire book as single markdown file',
            'single_text': 'Export entire book as single text file',
            'chapters_markdown': 'Export each chapter as separate markdown file',
            'chapters_text': 'Export each chapter as separate text file',
            'json': 'Export book data as JSON file',
            'extract_images': 'Extract and save images from EPUB files'
        }