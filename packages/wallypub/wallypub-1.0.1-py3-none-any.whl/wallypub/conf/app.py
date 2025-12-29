import logging
from pathlib import Path

import toml
from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
    TomlConfigSettingsSource,
)

import platformdirs

from wallypub.conf.constants import (
    DEFAULT_WALLABAG_URL,
    API_CLIENT_DOC_LOCATION,
    APP_AUTHOR_NAME,
    APP_NAME,
    SETTINGS_FILE,
    DEFAULT_FONT,
    static_dir,
)
from wallypub.conf.font import is_font_installed, install_default_font

config_dir = platformdirs.user_config_dir(APP_NAME, APP_AUTHOR_NAME)
cover_file = "cover.jpg"
config_path = (
    platformdirs.user_config_dir(APP_NAME, APP_AUTHOR_NAME) + "/" + SETTINGS_FILE
)


class BaseConfig(BaseModel):
    application_directory: str = platformdirs.user_data_dir(APP_NAME, APP_AUTHOR_NAME)
    log_level: int = logging.INFO
    max_read_time: int = 120
    minimum_read_time: int = 0

    def set_log_level(self, log_level: int):
        self.log_level = log_level

    def set_minimum_read_time(self, minimum_read_time: int):
        self.minimum_read_time = minimum_read_time

    def set_max_read_time(self, max_read_time: int):
        self.max_read_time = max_read_time

    def set_application_directory(self, application_directory: str):
        self.application_directory = application_directory


class DigestConfig(BaseModel):
    title: str = ""
    filepath: str = static_dir
    author: str = ""
    output_path: str = platformdirs.user_documents_dir() + "/" + APP_NAME
    cover_file: str = cover_file
    title_font: str = DEFAULT_FONT
    date_font: str = DEFAULT_FONT
    back_matter: bool = True

    def set_title(self, title: str):
        self.title = title

    def set_filepath(self, filepath: str):
        self.filepath = filepath

    def set_author(self, author: str):
        self.author = author

    def set_output_path(self, output_path: str):
        self.output_path = output_path

    def set_cover_file(self, file: str):
        self.cover_file = file

    def set_title_font(self, font: str):
        self.title_font = font

    def set_date_font(self, font: str):
        self.date_font = font

    def set_back_matter(self, enabled: bool):
        self.back_matter = enabled


class WallabagConfig(BaseModel):
    """
    Class that holds the configuration variables for interacting with the Wallabag API.
    """

    client_id: str = ""
    username: str = ""
    url: str = DEFAULT_WALLABAG_URL

    def set_username(self, username: str):
        self.username = username

    def set_client_id(self, client_id: str):
        self.client_id = client_id

    def set_url(self, url: str):
        self.url = url


class WallabagURLParameters(BaseModel):
    """
    Class that holds the url parameters in the API.
    """

    archive: str = "0"
    starred: str = "0"
    sort: str = "created"
    order: str = "desc"
    page: str = "1"
    perPage: str = "10"
    tags: str = ""
    since: str = ""
    public: str = ""
    detail: str = "full"
    domain_name: str = ""

    def set_archive(self, archive: str):
        self.archive = archive

    def set_starred(self, starred: str):
        self.starred = starred

    def set_sort(self, sort: str):
        self.sort = sort

    def set_order(self, order: str):
        self.order = order

    def set_page(self, page: str):
        self.page = page

    def set_per_page(self, per_page: str):
        self.perPage = per_page

    def set_tags(self, tags: str):
        self.tags = tags

    def set_since(self, since: str):
        self.since = since

    def set_public(self, public: str):
        self.public = public

    def set_detail(self, detail: str):
        self.detail = detail

    def set_domain_name(self, domain_name: str):
        self.domain_name = domain_name


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        toml_file=config_path,
        extra="ignore",  # this is included as part of the below workaround
    )

    AdditionalArticleParameters: WallabagURLParameters = WallabagURLParameters(
        sort="asc", order="", page="", perPage="", detail=""
    )
    ArticleParameters: WallabagURLParameters = WallabagURLParameters()
    Base: BaseConfig = BaseConfig()
    Digest: DigestConfig = DigestConfig()
    Wallabag: WallabagConfig = WallabagConfig()

    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (TomlConfigSettingsSource(settings_cls),)

    def interactive_setup(self) -> None:
        logging.info("configuring your digest..")
        digest_data = {
            "title": input("What would you like to name this epub? "),
            "author": input("Who should be credited for this epub? "),
        }
        self.Digest = DigestConfig(**digest_data)
        logging.info("Configuring your Wallabag API client...")
        while True:
            if input("Have you configured a Wallabag API client before? [y/n] ") == "y":
                break
            else:
                logging.info(
                    "Read this {} before continuing.".format(API_CLIENT_DOC_LOCATION)
                )
                input("Press any key to continue...")
                break
        wallabag_data = {
            "username": input("Wallabag username: "),
            "client_id": input("Wallabag client_id: "),
        }
        self.Wallabag = WallabagConfig(**wallabag_data)
        if not is_font_installed():
            if (
                input(
                    "Default font is not installed, would you like to install it? [y/n] "
                )
                == "y"
            ):
                install_default_font()
        save_app_config(self)


# singleton config for the application
app_config = AppConfig()


def save_app_config(conf: AppConfig):
    """save_app_config persists the configuration file to user config"""
    Path(platformdirs.user_config_dir(APP_NAME, APP_AUTHOR_NAME)).mkdir(
        parents=True, exist_ok=True
    )
    with open(config_path, "w+") as f:
        config_dict = conf.model_dump()
        toml.dump(config_dict, f)
