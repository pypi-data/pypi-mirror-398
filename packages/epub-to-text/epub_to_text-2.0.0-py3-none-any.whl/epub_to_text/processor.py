# processor.py
import os
from epub_to_text.reader import EpubReader
from epub_to_text.extractor import EpubExtractor
from epub_to_text.converter import ContentConverter

class EpubProcessor:
    """
    High-level processor for EPUB files with enhanced features.
    """
    
    def __init__(self, epub_file_path, output_dir=None):
        """
        Initialize EpubProcessor.
        
        Args:
            epub_file_path (str): Path to EPUB file.
            output_dir (str): Output directory (optional).
        """
        self.epub_file_path = epub_file_path
        self.output_dir = output_dir or self._create_default_output_dir()
        
        # Initialize components
        self.reader = EpubReader(epub_file_path)
        self.book = self.reader.get_book()
        self.extractor = EpubExtractor(self.book, self.output_dir)
        
        # Get basic info
        self.book_title = self._sanitize_filename(
            self.extractor.get_metadata().get('title', 'Unknown_Book')
        )
        self.chapters = self.extractor.get_chapters()
        self.metadata = self.extractor.get_metadata()
        self.images = self.extractor.get_images()
    
    def _create_default_output_dir(self):
        """Create default output directory."""
        base_dir = os.path.dirname(self.epub_file_path)
        output_dir = os.path.join(base_dir, 'exported_books')
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    @staticmethod
    def _sanitize_filename(name):
        """Sanitize filename."""
        import re
        if not name:
            return "unknown"
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
        return re.sub(r'_+', '_', sanitized.strip())
    
    def extract_images(self):
        """
        Extract and save images from EPUB.
        
        Returns:
            dict: Image mapping from original paths to saved paths.
        """
        if not self.images:
            return {}
        
        book_dir = os.path.join(self.output_dir, self.book_title)
        images_dir = os.path.join(book_dir, 'images')
        
        return self.extractor._save_images(images_dir)
    
    def export_single_text(self):
        """
        Export entire book as single text file.
        
        Returns:
            str: Path to saved file.
        """
        output_file = os.path.join(self.output_dir, f"{self.book_title}.txt")
        
        ContentConverter.save_single_file(
            self.chapters,
            output_file,
            self.book_title,
            self.metadata,
            format_type="text"
        )
        
        return output_file
    
    def export_single_markdown(self):
        """
        Export entire book as single markdown file.
        
        Returns:
            str: Path to saved file.
        """
        output_file = os.path.join(self.output_dir, f"{self.book_title}.md")
        
        # Extract images first for proper linking
        images_mapping = self.extract_images()
        
        ContentConverter.save_single_file(
            self.chapters,
            output_file,
            self.book_title,
            self.metadata,
            format_type="markdown",
            images_mapping=images_mapping
        )
        
        return output_file
    
    def export_chapters_text(self):
        """
        Export each chapter as separate text files.
        
        Returns:
            list: List of saved file paths.
        """
        return ContentConverter.save_chapters_separately(
            self.chapters,
            self.output_dir,
            self.book_title,
            format_type="text"
        )
    
    def export_chapters_markdown(self):
        """
        Export each chapter as separate markdown files.
        
        Returns:
            list: List of saved file paths.
        """
        # Extract images first for proper linking
        images_mapping = self.extract_images()
        
        return ContentConverter.save_chapters_separately(
            self.chapters,
            self.output_dir,
            self.book_title,
            format_type="markdown",
            images_mapping=images_mapping
        )
    
    def export_json(self):
        """
        Export book data as JSON file.
        
        Returns:
            str: Path to saved file.
        """
        output_file = os.path.join(self.output_dir, f"{self.book_title}.json")
        content = self.extractor.get_content_as_json()
        ContentConverter.save_as_json(content, output_file)
        return output_file
    
    def get_summary(self):
        """
        Get summary information about the EPUB file.
        
        Returns:
            dict: Summary information.
        """
        return {
            'file_path': self.epub_file_path,
            'title': self.metadata.get('title', 'Unknown'),
            'author': self.metadata.get('author', 'Unknown'),
            'language': self.metadata.get('language', 'Unknown'),
            'total_chapters': len(self.chapters),
            'total_images': len(self.images),
            'chapter_titles': [ch.get('title', f"Chapter {ch.get('chapter_num', 'Unknown')}") 
                             for ch in self.chapters]
        }