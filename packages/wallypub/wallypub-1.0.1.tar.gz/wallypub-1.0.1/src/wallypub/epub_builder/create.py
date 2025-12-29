import logging
from datetime import datetime
from pathlib import Path

import pypub

import wallypub.conf.app as conf
from wallypub import img
from wallypub.conf.app import app_config
from wallypub.conf.constants import EXTENSION_EPUB, DEFAULT_COVER_IMAGE_FILE_NAME
from wallypub.epub_builder.from_wallabag import (
    get_individual_entries,
    get_recent_entries,
)
from wallypub.epub_builder.formatter import (
    merge_entries_to_chapters,
    ENTRY_STYLES,
    add_back_matter,
)
from wallypub.utils.date import get_string_date
import glob

# initialize config settings for the entire digest
cfg = conf.AppConfig().Digest
date = datetime.today()


def initialize_epub() -> pypub.Epub:
    """
    initialize_epub returns a pypub.Epub object.
    :return:
    """

    if cfg.cover_file == DEFAULT_COVER_IMAGE_FILE_NAME:
        cover_generator = img.CoverGenerator()
        cover_generator.generate_default()
        cover_generator.save()

    # get dates
    string_date = get_string_date()

    digest_cover = cfg.filepath + "/" + cfg.cover_file
    digest_internal_title = cfg.title + "\n" + string_date
    digest = pypub.Epub(
        digest_internal_title, creator=cfg.author, date=date, cover=digest_cover
    )
    return digest


def get_file_title():
    """
    get_file_title returns a file title.
    :return:
    """
    digest_file_title = cfg.title + "_" + date.strftime("%Y%m%d")
    return digest_file_title


def from_submitted_ids(article_ids):
    """
    from_submitted_ids creates pypub.Epub object based on Wallabag article_ids and saves
    it to the location configured in the file to the location configured in the environment variables.
    :param article_ids:
    :return:
    """

    digest = initialize_epub()
    merge_entries_to_chapters(
        digest, get_individual_entries(article_ids), **ENTRY_STYLES["wallabag"]
    )
    if app_config.Digest.back_matter:
        add_back_matter(digest)
    save_digest(digest)


def from_entries(params):
    """
    from_entries creates Epub object based on the passed in Wallabag parameters and saves
    the file to the location configured in the environment variables.
    :return:
    """
    logging.info("getting recent wallabag entries")

    digest = initialize_epub()
    entries = get_recent_entries(params)

    merge_entries_to_chapters(digest, entries, **ENTRY_STYLES["wallabag"])
    if app_config.Digest.back_matter:
        add_back_matter(digest)
    save_digest(digest)


def save_digest(digest: pypub.Epub):
    """
    save_digest saves the epub to the directory configured in the environment variables
    :param digest:
    :return:
    """
    file_title = get_file_title()
    collision_safe_file_title = avoid_file_collisions(file_title)
    out_path = cfg.output_path + "/" + collision_safe_file_title + EXTENSION_EPUB
    Path(cfg.output_path).mkdir(parents=True, exist_ok=True)
    logging.info("saving epub to {}".format(out_path))
    digest.create(out_path)


def avoid_file_collisions(file_title: str):
    """
    avoid_file_collisions checks if a filename already exists and appends a number to the end of the file_title.
    If a number already exists, the function counts up and appends that number.
    The file_title is returned as a string.
    :param file_title:
    :return:
    """
    start_marker = "-"
    end_marker = EXTENSION_EPUB
    # get all epub files in the output directory
    epub_files = []
    for file in glob.glob(cfg.output_path + "/" + "*" + EXTENSION_EPUB):
        epub_files.append(file)

    # check title against all epub files
    matching_epub_files = []
    for file in epub_files:
        if file_title in file:
            matching_epub_files.append(file)

    # if there are no matching files, we have what we need, return file_title
    if len(matching_epub_files) == 0:
        return file_title

    if len(matching_epub_files) == 1:
        return file_title + "-" + str(1)

    # gather all appended numbers
    iter_list = []

    # remove the file that has no iterations appended.
    matching_epub_files.remove(cfg.output_path + "/" + file_title + EXTENSION_EPUB)
    for match in matching_epub_files:
        after_start = match.split(start_marker)[1]
        iteration = after_start.split(end_marker)[0]
        iter_list.append(
            # convert to int so that max() does not perform lexagrpahical comparison
            int(iteration)
        )

    # append the highest number to the current title
    last_iteration = max(iter_list)
    current_iteration = int(last_iteration)
    current_iteration += 1
    file_title = file_title + "-" + str(current_iteration)
    return file_title
