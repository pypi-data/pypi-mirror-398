""" "
This file contains the logic for transforming the retrieved text into an epub.
"""

from importlib import resources
import logging

import pypub

from typing import Optional, Callable

from wallypub.conf.constants import DEFAULT_ENCODING, DEFAULT_BACKMATTER_FILE

# ENTRY_STYLES is an extensible constant that allows us to add other source types.
ENTRY_STYLES = {
    "wallabag": {
        "title_key": "title",
        "content_key": "content",
        "author_key": "published_by",
        "guid_key": "domain_name",
        "published_key": "published_at",
        "link_key": "url",
        "content_processor": None,
    },
}


def add_article_info(author, published_by, date, link):
    """
    add_article_info inserts article metadata into formatted HTML
    :param author:
    :param published_by:
    :param date:
    :param link:
    :return:
    """
    # check for multiple authors
    if type(author) is list:
        author = ", ".join(map(str, author))

    html_string = f"""
    <div>
      <p><b>Author:</b> <span id="author">{author}</span></p>
      <p><b>Published By:</b> <span id="published_by">{published_by}</span></p>
      <p><b>Date:</b> <span id="date">{date}</span></p>
      <p><b>URL:</b> <a id="link" href="{link}">{link}</a></p>
    </div>
    """
    return html_string


def get_template_str(template_name: str) -> str:
    """
    retrieves a template file within the package
    :param template_name:
    :return:
    """

    template_path = (
        resources.files("wallypub").joinpath("templates").joinpath(template_name)
    )

    return template_path.read_text(encoding=DEFAULT_ENCODING)


def add_back_matter(digest: pypub.Epub):
    """
    add_back_matter inserts back matter metadata & images into formatted HTML
    :param digest:
    :return:
    """
    logging.debug("adding backmatter")
    html_string = get_template_str(DEFAULT_BACKMATTER_FILE)
    html_bytes = html_string.encode(DEFAULT_ENCODING)

    chapter = pypub.create_chapter_from_html(html_bytes)
    chapter.title = "back matter"

    digest.add_chapter(chapter)


def merge_entries_to_chapters(
    digest: pypub.Epub,
    entries: list,
    *,
    title_key: str = "title",
    content_key: str = "content",
    author_key: str | None = None,
    guid_key: str | None = None,
    published_key: str | None = None,
    link_key: str | None = None,
    content_processor: Optional[Callable] | None,
) -> pypub.Epub:
    for entry in entries:
        title = entry[title_key]

        if author_key or guid_key or published_key or link_key:
            article_info = add_article_info(
                entry.get(author_key, ""),
                entry.get(guid_key, ""),
                entry.get(published_key, ""),
                entry.get(link_key),
            )
        else:
            article_info = ""

        content = content_processor(entry) if content_processor else entry[content_key]
        html_bytes = bytes(article_info + content, DEFAULT_ENCODING)

        chapter = pypub.create_chapter_from_html(html_bytes)
        chapter.title = title
        digest.add_chapter(chapter)

    return digest
