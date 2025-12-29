# reader.py
import ebooklib
from ebooklib import epub

class EpubReader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.book = self._read_epub()

    def _read_epub(self):
        """
        Reads the EPUB file and returns the book object.
        
        Returns:
            epub.EpubBook: The book object containing the EPUB content.
        Raises:
            FileNotFoundError: If the file is not found.
            Exception: For any other errors during reading the EPUB file.
        """
        try:
            return epub.read_epub(self.file_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"File {self.file_path} not found.")
        except Exception as e:
            raise Exception(f"An error occurred while reading the EPUB file: {e}")

    def get_items(self):
        """
        Retrieves document items from the EPUB book.
        
        Returns:
            list: A list of document items from the EPUB book.
        """
        return list(self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
    
    def get_book(self):
        """
        Get the epub book object.
        
        Returns:
            epub.EpubBook: The book object.
        """
        return self.book
