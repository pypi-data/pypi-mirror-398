import os
from epub_to_text.reader import EpubReader
from epub_to_text.extractor import EpubExtractor
from epub_to_text.converter import ContentConverter

class EpubContentFeedAI:
    def __init__(self, epub_file_path, output_dir=None):
        self.epub_file_path = epub_file_path
        self.output_dir = output_dir or self._create_default_output_dir()
        self.reader = EpubReader(epub_file_path)
        self.book_title = self._sanitize_filename(self.reader.book.get_metadata('DC', 'title')[0][0])
        self.epub_items = self.reader.get_items()
        self.extractor = EpubExtractor(self.epub_items)

    def _create_default_output_dir(self):
        base_dir = os.path.dirname(self.epub_file_path)
        output_dir = os.path.join(base_dir, 'export')
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    @staticmethod
    def _sanitize_filename(name):
        import re
        return re.sub(r'[^a-zA-Z0-9_\-]', '_', name)

    def to_text(self):
        content_text = self.extractor.get_content_as_text()
        output_file = os.path.join(self.output_dir, f"{self.book_title}.txt")
        ContentConverter.save_as_text(content_text, output_file)
        return output_file

    def to_json(self):
        content_json = self.extractor.get_content_as_json()
        output_file = os.path.join(self.output_dir, f"{self.book_title}.json")
        ContentConverter.save_as_json(content_json, output_file)
        return output_file

    def to_markdown(self):
        content_text = self.extractor.get_content_as_text()
        content_markdown = ContentConverter.convert_to_markdown(content_text)
        output_file = os.path.join(self.output_dir, f"{self.book_title}.md")
        ContentConverter.save_as_text(content_markdown, output_file)
        return output_file
