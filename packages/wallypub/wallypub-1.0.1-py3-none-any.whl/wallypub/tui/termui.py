#
# Wallypub, generate epubs from your Wallabag
#
from getpass import getpass

import logging
from pathlib import Path

import click
import keyring
import platformdirs
from InquirerPy import inquirer

from wallypub.epub_builder.create import from_entries, from_submitted_ids
from wallypub import img
from wallypub.tui.choice_builder import choice_builder
from wallypub.tui.update_config import config_hierarchical_select
from wallypub.utils.params import get_params_from_settings
from wallypub.conf.app import AppConfig, app_config
from wallypub.conf.constants import (
    SERVICE_NAME,
    WALLABAG_CLIENT_SECRET_KEY,
    WALLABAG_PASS_KEY,
    APP_NAME,
    APP_AUTHOR_NAME,
    SETTINGS_FILE,
)

from wallypub.services.wallabag import Wallabag


from wallypub.conf.font import list_system_fonts


@click.group(
    epilog="See https://glasshoundcomputing.com/wallypub/user-guide.html for more details",
)
def wallypub():
    """Wallypub creates epub files from Wallabag backlogs"""
    Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR_NAME)).mkdir(
        parents=True, exist_ok=True
    )
    logging.basicConfig(
        level=app_config.Base.log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(
                platformdirs.user_data_dir(APP_NAME, APP_AUTHOR_NAME) + "/debug.log"
            ),
            logging.StreamHandler(),
        ],
    )


@wallypub.command()
def config_edit():
    """prompts user to update settings values

    see detailed information: https://glasshoundcomputing.com/wallypub/user-guide.html#page-39

    back_matter accepts True or False
    log_level accepts an integer that correlates as follows:
    ```
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0
    ```
    """
    config_hierarchical_select()


@wallypub.command()
def config_init():
    """
    walks the user through the first time configuration

    The first time configuration assumes some defaults, opting to only
    setup the requirements to generate a digest. Additional settings can be adjusted
    through the config-edit command.

    If the default font is not installed, wallypub will install that in your system fonts.
    """
    cfg = app_config
    if cfg.Digest.title != "" or cfg.Digest.author != "" or cfg.Wallabag.username != "":
        while True:
            if (
                input(
                    "It looks Wallypub has already been configured, this will \n"
                    "overwrite your existing configuration, continue? [y/n] "
                )
                == "y"
            ):
                break
            else:
                logging.info("retaining existing configuration.")
                exit()
    else:
        cfg = AppConfig()
    cfg.interactive_setup()
    logging.info("configuring  secrets...")

    wallabag_pass = getpass("Wallabag password: ")
    keyring.set_password(SERVICE_NAME, WALLABAG_PASS_KEY, wallabag_pass)

    wallabag_client_secret = getpass("Wallabag client_secret: ")
    keyring.set_password(
        SERVICE_NAME, WALLABAG_CLIENT_SECRET_KEY, wallabag_client_secret
    )

    logging.info("Configuration complete")


@wallypub.command()
def config_secrets_edit():
    """prompts user to update secret values in keyring"""
    secrets = inquirer.select(
        message="Select secret value(s) to update [press space to select multiple values]",
        choices=choice_builder(WALLABAG_PASS_KEY, WALLABAG_CLIENT_SECRET_KEY),
        multiselect=True,
        transformer=lambda result: f"{len(result)} secrets{'s' if len(result) > 1 else ''} selected",
    ).execute()

    for s in secrets:
        updated_secret = getpass("Update {}: ".format(s))
        keyring.set_password(SERVICE_NAME, s, updated_secret)


@wallypub.command()
def config_secrets_show():
    """displays the sensitive variables from the keyring"""
    wallabag_pass = keyring.get_password(SERVICE_NAME, WALLABAG_PASS_KEY)
    wallabag_client_secret = keyring.get_password(
        SERVICE_NAME, WALLABAG_CLIENT_SECRET_KEY
    )
    print(
        "wallabag password: {} \n wallabag client secret: {}".format(
            wallabag_pass, wallabag_client_secret
        )
    )


@wallypub.command()
def config_show():
    """displays the settings to the console"""
    print("reading {}".format(platformdirs.user_config_dir(APP_NAME, APP_AUTHOR_NAME)))
    f = open(
        platformdirs.user_config_dir(APP_NAME, APP_AUTHOR_NAME) + "/" + SETTINGS_FILE
    )
    file_contents = f.read()
    print(file_contents)


@wallypub.command()
@click.argument("ids")
def digest_by_ids(ids: str):
    """generate EPUB from comma-separated Wallabag IDs

    The IDs should correlate with Wallabag entries.
    When viewing from the web, the entry ID can be found in the URL
    In https://app.wallabag.it/view/32247628 the ID would be 32247628
    """
    try:
        items = [item.strip() for item in ids.split(",")]
        # check for empty items
        if any(not item for item in items):
            raise ValueError("List cannot contain empty items.")
        from_submitted_ids(items)
    except ValueError as e:
        logging.error(str(e))


@wallypub.command()
def digest_cover_create():
    """procedurally generate a cover image for your digest

    digest_cover_create exists mostly to have a means of independently test that image
    generation works on the machine.

    Wallypub will automatically generate a new cover if the configured filename in the cover_file setting matches
    the default name of "cover.jpg", this remains true even if you configure another directory as the location
    for the static files. Recommendation is to call the file something "custom_cover.ext" or "name_of_digest.ext".
    """
    generator = img.CoverGenerator()
    generator.generate_default()
    generator.save()


@wallypub.command()
def digest_recent():
    """generate EPUB from recent Wallabag entries"""
    params = get_params_from_settings(app_config.ArticleParameters)
    from_entries(params)


@wallypub.command()
def donate():
    """
    prints link to Glass Hound Computing's donation page
    """
    print(
        "support wallypub by donating money @ https://buymeacoffee.com/glasshoundcomputing"
    )


@wallypub.command()
@click.argument("url")
@click.option("--tags", "tags", help="comma separated string")
def entry_add(url, tags):
    """
    add an entry to your Wallabag instance

    The `--tags` flag for `entry-add` needs to be wrapped in a string `""` to get comma separation if you intend on using spaces
    within your tags.
    """

    wallabag_instance = Wallabag()
    wallabag_instance.authenticate()
    wallabag_instance.add_entry(url, tags)


@wallypub.command()
@click.option(
    "--scroll",
    "scroll",
    flag_value=True,
    help="allows you to scroll through system fonts q to quit",
)
@click.option("--search", "search", help="fuzzy search for font names")
def system_fonts_show(scroll, search):
    """displays installed system fonts"""
    list_system_fonts(scroll, search)
