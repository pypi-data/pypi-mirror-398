import logging
from typing import Any

from wallypub.conf.app import app_config
from wallypub.services.wallabag import Wallabag
from wallypub.utils.params import get_params_from_settings


def get_individual_entries(article_ids) -> []:
    """
    get_individual_entries takes in a list of article IDs and retrieves each from the /api/entries/:id endpoint
    :param article_ids:
    :return:
    """

    wallabag_instance = Wallabag()

    logging.info("adding articles to digest")
    entry_count = len(article_ids)
    entries = []
    for articleId in article_ids:
        wallabag_instance.authenticate()
        entry = wallabag_instance.get_entry(str(articleId))
        entries.append(entry)

    filtered_entries, empty_entries = filter_empty_articles(entries)
    deduped_entries, duplicate_entries = filter_duplicate_articles(filtered_entries)

    # ensure entries conform to configured to read times
    within_bounds_entries, out_of_bounds_entries = filter_on_read_times(deduped_entries)

    # These are blocking calls, consider async
    archive_articles(duplicate_entries)
    archive_articles(empty_entries)
    archive_articles(out_of_bounds_entries)

    while entry_count != len(within_bounds_entries):
        entry_delta = entry_count - len(within_bounds_entries)
        additional_entries = get_additional_entries(entry_delta, within_bounds_entries)
        within_bounds_entries.extend(additional_entries)

    # blocking calls, consider async
    archive_articles(within_bounds_entries)

    return within_bounds_entries


def get_recent_entries(params) -> []:
    """
    get_recent_entries takes in parameters for the /api/entries? endpoint
    :param params:
    :return:
    """
    wallabag_instance = Wallabag()
    wallabag_instance.authenticate()

    resp = wallabag_instance.get_entries(params)

    entry_count = len(resp["_embedded"]["items"])

    # add all items to entries array
    entries, empty_entries = filter_empty_articles(resp["_embedded"]["items"])
    deduped_entries, duplicate_entries = filter_duplicate_articles(entries)

    # ensure entries conform to configured to read times
    within_bounds_entries, out_of_bounds_entries = filter_on_read_times(deduped_entries)

    # These are blocking calls, consider async
    archive_articles(duplicate_entries)
    archive_articles(empty_entries)
    archive_articles(out_of_bounds_entries)

    # get additional entries until the count is equal to len(entries)
    while entry_count != len(within_bounds_entries):
        logging.debug("unique entries: {} ".format(len(within_bounds_entries)))
        # get delta
        entry_delta = entry_count - len(within_bounds_entries)
        logging.debug("entry delta: {}".format(entry_delta))
        additional_entries = get_additional_entries(entry_delta, within_bounds_entries)
        within_bounds_entries.extend(additional_entries)
        within_bounds_entries, duplicate_additional_entries = filter_duplicate_articles(
            within_bounds_entries
        )

        archive_articles(duplicate_additional_entries)

    # blocking call, consider refactoring to async
    archive_articles(within_bounds_entries)

    return within_bounds_entries


def archive_articles(entries):
    """
    archive_empty_articles is a helper function that takes in an array of entries and patches them with the archive
    parameters
    :param entries:
    :return:
    """
    patch_body = {
        "archive": 1,
    }
    for entry in entries:
        logging.debug("archiving entry: {}".format(entry["id"]))
        patch_article(patch_body, entry)


def patch_article(body, article):
    """
    patch_article takes in parameters for the PATCH /api/entries/{entry} endpoint and modifies the endpoint accordingly
    :return:
    """
    wallabag_instance = Wallabag()
    wallabag_instance.authenticate()

    resp = wallabag_instance.patch_entry(article["id"], body)

    return resp


def get_additional_entries(num_additional_entries, filtered_entries) -> list[Any]:
    """
    get_additional_entries takes in the number of additional entries requested and retrieves them
    it uses IDs from the filtered entries to ensure there are no duplicates
    :param filtered_entries:
    :param num_additional_entries:
    :return:
    """
    # these parameters pull least recent to avoid colliding with recent
    params = get_params_from_settings(app_config.AdditionalArticleParameters)
    params["perPage"] = num_additional_entries
    params["archive"] = "0"
    additional_entries = []
    # pull entries until
    while num_additional_entries != len(additional_entries):
        entry = get_recent_entries(params)

        # check that the retrieved entry ID doesn't match the recently pulled article.
        # entry will be in the first position because these parameters only pull 1 article.
        if not entry_in_array(entry[0], filtered_entries):
            if within_read_times(entry[0]["reading_time"]):
                logging.info("saving entry {}".format(entry[0]["id"]))
                additional_entries.append(entry[0])
            else:
                # archive 0 length article
                logging.info("archiving entry {}".format(entry[0]["id"]))
                archive_params = {
                    "archive": "1"
                }  # settings submitting a PATCH request to archive
                patch_article(archive_params, entry[0])

    return additional_entries


def within_read_times(read_time) -> bool:
    """within_read_times compares the read_time to the configured min and max read time and
    returns a boolean based on result."""
    if (
        app_config.Base.minimum_read_time
        < int(read_time)
        < app_config.Base.max_read_time
    ):
        return True
    return False


def filter_on_read_times(entries) -> ([], []):
    """filter_on_read_times removes articles from the bounded_entries list if within_read_times returns false"""

    # bounded_entries are entries that are greater than minimum_reading_time & less than max_read_time
    bounded_entries = [
        entry for entry in entries if within_read_times(entry["reading_time"])
    ]
    # unbounded_entries are entries that are less than minimum_reading_time & greater than max_read_time
    unbounded_entries = [
        entry for entry in entries if not within_read_times(entry["reading_time"])
    ]
    return bounded_entries, unbounded_entries


def filter_empty_articles(entries) -> ([], []):
    """
    filter_empty_articles removes articles with a read time of 0 from the array.
    Returns filtered_entries and empty_entries
    :param entries:
    :return:
    """

    filtered_entries = [entry for entry in entries if entry["reading_time"] > 0]
    empty_entries = [entry for entry in entries if entry["reading_time"] <= 0]

    return filtered_entries, empty_entries


def filter_duplicate_articles(entries) -> ([], []):
    """
    filter_duplicate_articles removes articles with the same id from the array.
    :param entries:
    :return:
    """
    ids = set()
    dup_ids = set()
    unique_entries = [
        entry
        for entry in entries
        if entry["id"] not in ids and not ids.add(entry["id"])
    ]
    duplicate_entries = [
        entry for entry in entries if entry["id"] in dup_ids or dup_ids.add(entry["id"])
    ]

    return unique_entries, duplicate_entries


def entry_in_array(new_entry, existing_entries) -> bool:
    """
    check_entry_in_array takes in the new_entry and the existing entries array and then checks if the id already exists
    :param existing_entries:
    :param new_entry:
    :return:
    """
    for entry in existing_entries:
        if entry["id"] is new_entry["id"]:
            return True

    return False
