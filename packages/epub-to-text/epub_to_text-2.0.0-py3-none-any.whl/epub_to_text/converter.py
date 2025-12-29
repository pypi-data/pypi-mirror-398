# converter.py
import os
import json
import re
from pathlib import Path

class ContentConverter:
    
    @staticmethod
    def save_as_text(content, output_file):
        """
        Saves the content as a text file.
        
        Args:
            content (str): The content to save.
            output_file (str): The path to the output file.
        """
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

    @staticmethod
    def save_as_json(content, output_file):
        """
        Saves the content as a JSON file.
        
        Args:
            content (str): The content to save.
            output_file (str): The path to the output file.
        """
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

    @staticmethod
    def convert_to_markdown(content, title="", images_mapping=None):
        """
        Converts HTML content to Markdown format.
        
        Args:
            content (str): The HTML content to convert.
            title (str): Optional title to add at the beginning.
            images_mapping (dict): Mapping of original image paths to new paths.
        
        Returns:
            str: The content in Markdown format.
        """
        from bs4 import BeautifulSoup
        
        # Start with title if provided
        markdown = ""
        if title:
            markdown = f"# {title}\n\n"
        
        # If content is already plain text, return as is
        if not content.strip().startswith('<'):
            return markdown + content
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Convert common HTML elements to markdown
        for tag in soup.find_all():
            if tag.name == 'h1':
                tag.string = f"# {tag.get_text()}\n\n"
            elif tag.name == 'h2':
                tag.string = f"## {tag.get_text()}\n\n"
            elif tag.name == 'h3':
                tag.string = f"### {tag.get_text()}\n\n"
            elif tag.name == 'h4':
                tag.string = f"#### {tag.get_text()}\n\n"
            elif tag.name == 'h5':
                tag.string = f"##### {tag.get_text()}\n\n"
            elif tag.name == 'h6':
                tag.string = f"###### {tag.get_text()}\n\n"
            elif tag.name == 'p':
                tag.string = f"{tag.get_text()}\n\n"
            elif tag.name == 'br':
                tag.string = "\n"
            elif tag.name == 'strong' or tag.name == 'b':
                tag.string = f"**{tag.get_text()}**"
            elif tag.name == 'em' or tag.name == 'i':
                tag.string = f"*{tag.get_text()}*"
            elif tag.name == 'img':
                src = tag.get('src', '')
                alt = tag.get('alt', 'Image')
                # Update image path if mapping provided
                if images_mapping and src in images_mapping:
                    src = images_mapping[src]
                tag.string = f"![{alt}]({src})\n\n"
            elif tag.name == 'blockquote':
                lines = tag.get_text().strip().split('\n')
                quoted = '\n'.join([f"> {line}" for line in lines])
                tag.string = f"{quoted}\n\n"
            elif tag.name in ['ul', 'ol']:
                items = []
                for li in tag.find_all('li'):
                    items.append(f"- {li.get_text().strip()}")
                tag.string = '\n'.join(items) + "\n\n"
        
        # Get the text and clean up
        text = soup.get_text()
        
        # Clean up extra newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return markdown + text.strip()
    
    @staticmethod
    def save_chapters_separately(chapters, output_dir, book_title, format_type="markdown", images_mapping=None):
        """
        Save each chapter as a separate file.
        
        Args:
            chapters (list): List of chapter dictionaries.
            output_dir (str): Directory to save chapter files.
            book_title (str): Book title for folder naming.
            format_type (str): Format type ('markdown', 'text', or 'html').
            images_mapping (dict): Mapping for image paths.
        
        Returns:
            list: List of saved file paths.
        """
        # Sanitize book title for folder name
        safe_title = ContentConverter._sanitize_filename(book_title)
        chapters_dir = os.path.join(output_dir, safe_title)
        os.makedirs(chapters_dir, exist_ok=True)
        
        saved_files = []
        
        for chapter in chapters:
            chapter_title = chapter.get('title', f"Chapter {chapter.get('chapter_num', 'Unknown')}")
            safe_chapter_title = ContentConverter._sanitize_filename(chapter_title)
            
            if format_type == "markdown":
                filename = f"{chapter['chapter_num']:02d}_{safe_chapter_title}.md"
                filepath = os.path.join(chapters_dir, filename)
                
                # Convert to markdown with images
                content = ContentConverter.convert_to_markdown(
                    chapter.get('html_content', chapter['content']), 
                    chapter_title, 
                    images_mapping
                )
                
            elif format_type == "text":
                filename = f"{chapter['chapter_num']:02d}_{safe_chapter_title}.txt"
                filepath = os.path.join(chapters_dir, filename)
                content = f"{chapter_title}\n{'=' * len(chapter_title)}\n\n{chapter['content']}"
                
            elif format_type == "html":
                filename = f"{chapter['chapter_num']:02d}_{safe_chapter_title}.html"
                filepath = os.path.join(chapters_dir, filename)
                content = chapter.get('html_content', f"<h1>{chapter_title}</h1>\n<p>{chapter['content']}</p>")
            
            else:
                continue
            
            ContentConverter.save_as_text(content, filepath)
            saved_files.append(filepath)
            print(f"Saved: {filename}")
        
        return saved_files
    
    @staticmethod
    def save_single_file(chapters, output_file, book_title, metadata=None, format_type="markdown", images_mapping=None):
        """
        Save all chapters as a single file.
        
        Args:
            chapters (list): List of chapter dictionaries.
            output_file (str): Path to output file.
            book_title (str): Book title.
            metadata (dict): Book metadata.
            format_type (str): Format type ('markdown', 'text', or 'html').
            images_mapping (dict): Mapping for image paths.
        """
        content_parts = []
        
        if format_type == "markdown":
            # Add book title
            content_parts.append(f"# {book_title}\n")
            
            # Add metadata if available
            if metadata:
                content_parts.append("## Book Information\n")
                if metadata.get('author'):
                    content_parts.append(f"**Author:** {metadata['author']}\n")
                if metadata.get('language'):
                    content_parts.append(f"**Language:** {metadata['language']}\n")
                if metadata.get('description'):
                    content_parts.append(f"**Description:** {metadata['description']}\n")
                content_parts.append("\n---\n")
            
            # Add chapters
            for chapter in chapters:
                chapter_title = chapter.get('title', f"Chapter {chapter.get('chapter_num', '')}")
                chapter_content = ContentConverter.convert_to_markdown(
                    chapter.get('html_content', chapter['content']),
                    f"## {chapter_title}",
                    images_mapping
                )
                content_parts.append(chapter_content)
                content_parts.append("\n---\n")
        
        elif format_type == "text":
            content_parts.append(f"{book_title}\n{'=' * len(book_title)}\n\n")
            
            if metadata:
                content_parts.append("Book Information:\n")
                if metadata.get('author'):
                    content_parts.append(f"Author: {metadata['author']}\n")
                if metadata.get('language'):
                    content_parts.append(f"Language: {metadata['language']}\n")
                content_parts.append("\n" + "-" * 50 + "\n\n")
            
            for chapter in chapters:
                chapter_title = chapter.get('title', f"Chapter {chapter.get('chapter_num', '')}")
                content_parts.append(f"{chapter_title}\n{'-' * len(chapter_title)}\n\n")
                content_parts.append(chapter['content'])
                content_parts.append(f"\n\n{'-' * 50}\n\n")
        
        final_content = ''.join(content_parts)
        ContentConverter.save_as_text(final_content, output_file)
    
    @staticmethod
    def _sanitize_filename(name):
        """Sanitize filename by removing/replacing invalid characters."""
        if not name:
            return "untitled"
        
        # Replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
        # Remove multiple underscores and leading/trailing spaces
        sanitized = re.sub(r'_+', '_', sanitized.strip())
        # Limit length
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        return sanitized or "untitled"
