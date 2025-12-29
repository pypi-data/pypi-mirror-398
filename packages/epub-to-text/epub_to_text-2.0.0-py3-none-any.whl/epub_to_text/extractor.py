# extractor.py
import os
import re
import base64
from pathlib import Path
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub

class EpubExtractor:
    def __init__(self, book, output_dir=None):
        """
        Initialize EpubExtractor with epub book object.
        
        Args:
            book: ebooklib.epub.EpubBook object
            output_dir: Directory to save images and other assets
        """
        self.book = book
        self.output_dir = output_dir
        self.chapters = self._extract_chapters()
        self.images = self._extract_images()
        self.book_metadata = self._extract_metadata()
    
    def _extract_metadata(self):
        """Extract book metadata like title, author, etc."""
        metadata = {}
        try:
            title = self.book.get_metadata('DC', 'title')
            metadata['title'] = title[0][0] if title else 'Unknown Title'
            
            author = self.book.get_metadata('DC', 'creator')
            metadata['author'] = author[0][0] if author else 'Unknown Author'
            
            language = self.book.get_metadata('DC', 'language')
            metadata['language'] = language[0][0] if language else 'en'
            
            description = self.book.get_metadata('DC', 'description')
            metadata['description'] = description[0][0] if description else ''
            
        except Exception as e:
            print(f"Warning: Could not extract some metadata: {e}")
            
        return metadata
    
    def _extract_images(self):
        """Extract all images from the EPUB file."""
        images = []
        for item in self.book.get_items():
            if item.get_type() == ebooklib.ITEM_IMAGE:
                images.append({
                    'filename': item.get_name(),
                    'content': item.get_content(),
                    'media_type': item.media_type
                })
        return images
    
    def _save_images(self, images_dir):
        """Save images to specified directory and return mapping."""
        if not self.images:
            return {}
            
        os.makedirs(images_dir, exist_ok=True)
        image_mapping = {}
        
        for img in self.images:
            # Clean filename
            filename = os.path.basename(img['filename'])
            if not filename:
                continue
                
            # Determine file extension from media type
            ext = ''
            if 'jpeg' in img['media_type'] or 'jpg' in img['media_type']:
                ext = '.jpg'
            elif 'png' in img['media_type']:
                ext = '.png'
            elif 'gif' in img['media_type']:
                ext = '.gif'
            elif 'svg' in img['media_type']:
                ext = '.svg'
            
            if not filename.endswith(ext) and ext:
                filename = os.path.splitext(filename)[0] + ext
            
            save_path = os.path.join(images_dir, filename)
            
            try:
                with open(save_path, 'wb') as f:
                    f.write(img['content'])
                    
                # Map original path to new relative path
                image_mapping[img['filename']] = f"images/{filename}"
                print(f"Saved image: {filename}")
                
            except Exception as e:
                print(f"Warning: Could not save image {filename}: {e}")
                
        return image_mapping
    
    def _extract_chapters(self):
        """Extract chapters with better title detection and content processing."""
        chapters = []
        chapter_num = 1
        
        for item in self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_body_content(), 'html.parser')
            
            # Try to find chapter title from various sources
            title = self._extract_chapter_title(soup, item.get_name(), chapter_num)
            
            # Clean and extract text content
            content = self._clean_html_content(soup)
            
            if content.strip():  # Only add non-empty chapters
                chapters.append({
                    'id': item.get_id(),
                    'filename': item.get_name(),
                    'title': title,
                    'content': content,
                    'html_content': str(soup),
                    'chapter_num': chapter_num
                })
                chapter_num += 1
                
        return chapters
    
    def _extract_chapter_title(self, soup, filename, chapter_num):
        """Extract chapter title from HTML content or filename."""
        # Try to find title in HTML
        for tag in ['h1', 'h2', 'h3', 'title']:
            title_elem = soup.find(tag)
            if title_elem and title_elem.get_text().strip():
                title = title_elem.get_text().strip()
                # Clean title
                title = re.sub(r'^Chapter\s*\d+\s*:?\s*', '', title, flags=re.IGNORECASE)
                if title:
                    return title
        
        # Try to extract from filename
        filename_base = os.path.splitext(os.path.basename(filename))[0]
        filename_base = re.sub(r'^chapter[-_]?\d*[-_]?', '', filename_base, flags=re.IGNORECASE)
        filename_base = filename_base.replace('_', ' ').replace('-', ' ').strip()
        
        if filename_base and filename_base.lower() not in ['index', 'cover', 'toc', 'contents']:
            return filename_base.title()
        
        # Default chapter title
        return f"Chapter {chapter_num}"
    
    def _clean_html_content(self, soup):
        """Clean HTML content and convert to clean text."""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean it
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _process_html_with_images(self, html_content, image_mapping):
        """Process HTML content to update image paths."""
        if not image_mapping:
            return html_content
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for img_tag in soup.find_all('img'):
            src = img_tag.get('src')
            if src and src in image_mapping:
                img_tag['src'] = image_mapping[src]
        
        return str(soup)
    
    def get_content_as_text(self):
        """Get all content as single text string."""
        return '\n\n'.join([chapter['content'] for chapter in self.chapters])
    
    def get_content_as_json(self):
        """Get content as JSON string."""
        import json
        return json.dumps({
            'metadata': self.book_metadata,
            'chapters': self.chapters,
            'total_chapters': len(self.chapters)
        }, indent=4, ensure_ascii=False)
    
    def get_chapters(self):
        """Get list of chapter data."""
        return self.chapters
    
    def get_images(self):
        """Get list of image data."""
        return self.images
    
    def get_metadata(self):
        """Get book metadata."""
        return self.book_metadata
