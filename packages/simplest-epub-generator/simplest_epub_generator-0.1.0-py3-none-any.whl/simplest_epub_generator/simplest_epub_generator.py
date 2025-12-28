import random
import re

from pathlib import Path
from typing import List, Set

from ebooklib import epub


class Chapter:
    """Class representing a chapter in an EPUB book."""

    TAG_PATTERN = re.compile(r"<[^>]+>")
    URL_PATTERN = re.compile(r"<img[^>]+src=\s?[\"'](.+?)['\"][^>]+>")

    def __init__(
        self,
        title: str,
        text: str,
        is_html: bool = False,
        lang: str = "eng",
    ) -> None:
        """
        Initialize a Chapter instance.

        Parameters:
            title: str - chapter title.
            text: str - chapter text.
            is_html: bool = False - whether the title and text are in HTML format.
            lang: str - language of the chapter.
        """
        self.lang: str = lang
        self.title: str = title
        self.html_content: str = ""
        if is_html:
            self.title = self.remove_tags(title)
            self.html_content = title + text
        else:
            self.html_content = f"<h1>{title}</h1>"
            _p_list = [f"<p>{paragraph}</p>" for paragraph in text.split("\n")]
            self.html_content += "".join(_p_list)

    def remove_tags(self, html: str) -> str:
        """
        Remove HTML-tags from text.

        Parameters:
            html: str - HTML code from which tags will be removed.

        Return:
            : str - clean text.
        """
        return re.sub(self.TAG_PATTERN, "", html)

    def get_image_paths(self) -> Set[str]:
        """
        Extract image paths from the chapter's HTML content.

        Return:
            : Set[str] - list of image paths.
        """
        return set(self.URL_PATTERN.findall(self.html_content))


class Epub:
    """Class representing an EPUB book."""

    def __init__(self, book_name: str, lang: str = "eng", author: str = "") -> None:
        """
        Initialize an Epub instance.

        Parameters:
            book_name: str - the book name.
            lang: str = "eng" - the book language.
            author: str - the author of the book.
        """
        self._book = epub.EpubBook()
        self.book_name: str = book_name
        if self.book_name.endswith(".epub"):
            self.book_name = self.book_name[:-5]

        self.lang: str = lang
        self.author: str = author
        self._epub_links: List[epub.Link] = []
        self._epub_chapters: List[epub.EpubHtml] = []
        self._new_image_paths: dict = dict()

    def _generate_meta(self):
        """Generate metadata."""
        random.seed(self.book_name)
        self._book.set_identifier(f"id{random.randint(0, 999999):0>6}")
        self._book.set_title(self.book_name)
        self._book.set_language(self.lang)
        self._book.add_author(self.author)

    def _add_chapter_images(self, chapter: Chapter) -> None:
        """
        Add chapter images to the book.

        Parameters:
            chapter: Chapter - the book chapter.
        """
        image_id = len(self._new_image_paths.keys())
        new_images = chapter.get_image_paths()
        for img_path in new_images:
            if img_path in self._new_image_paths:
                new_name = self._new_image_paths[img_path]
            else:
                new_name = f"{image_id}{Path(img_path).suffix}"
                image_id += 1
                self._new_image_paths[img_path] = new_name

                with open(img_path, "rb") as img_file:
                    img_data = img_file.read()
                img_item = epub.EpubImage(
                    file_name=new_name,
                    media_type=f"image/{Path(img_path).suffix[1:]}",
                    content=img_data,
                )
                self._book.add_item(img_item)
            chapter.html_content = chapter.html_content.replace(img_path, new_name)

    def add_chapter(self, chapter: Chapter) -> None:
        """
        Add the chapter to the book.

        Parameters:
            chapter: Chapter - the book chapter.
        """
        self._add_chapter_images(chapter)
        epub_chapter: epub.EpubHtml = epub.EpubHtml(
            title=chapter.title, file_name=f"{chapter.title}.xhtml", lang=chapter.lang
        )
        epub_chapter.content = chapter.html_content
        self._epub_chapters.append(epub_chapter)
        self._book.add_item(epub_chapter)

        epub_link: epub.Link = epub.Link(
            epub_chapter.file_name, epub_chapter.title, epub_chapter.title
        )
        self._epub_links.append(epub_link)

    def add_chapters(self, chapters: List[Chapter]) -> None:
        """
        Add chapters to the book.

        Parameters:
            chapters: List[Chapter] - the book chapters.
        """
        for chapter in chapters:
            self.add_chapter(chapter)

    def write_file(self, path: Path):
        """
        Write the book to a file.

        Parameters:
            path: Path - the path to the file.
        """
        self._generate_meta()
        # Title
        self._book.toc = self._epub_links
        # Add NavMap (for EPUB3)
        nav = epub.EpubNav()
        nav_items = [
            f'<li><a href="{epub_link.href}">{epub_link.title}</a></li>'
            for epub_link in self._epub_links
        ]
        nav.content = f"""
        <nav epub:type="toc">
            <ol>
                {'\n'.join(nav_items)}
            </ol>
        </nav>
        """
        self._book.add_item(nav)
        # Spine - sequence of items.
        self._book.spine = [nav] + self._epub_chapters
        # Save file.
        epub.write_epub(path, self._book, {})
