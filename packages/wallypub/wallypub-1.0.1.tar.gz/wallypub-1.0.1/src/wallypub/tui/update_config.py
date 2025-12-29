"""
update_config.py holds the logic for the update-config command. This command
got a little unwieldy and for peace of mind and ease of reading, the code was
moved into functions here. This file is the first pass. It is very WET, need to come back
and refactor.
"""

from InquirerPy import inquirer

from wallypub.conf.app import app_config, save_app_config, WallabagURLParameters
from wallypub.tui.choice_builder import choice_builder

CONFIG_SECTIONS = {
    "Base": {
        "config_obj": app_config.Base,
        "keys": app_config.Base.model_dump().keys(),
    },
    "Digest": {
        "config_obj": app_config.Digest,
        "keys": app_config.Digest.model_dump().keys(),
    },
    "Wallabag": {
        "config_obj": app_config.Wallabag,
        "keys": app_config.Wallabag.model_dump().keys(),
    },
    "Article Parameters": {
        "config_obj": app_config.ArticleParameters,
        "keys": app_config.ArticleParameters.model_dump().keys(),
    },
    "Additional Article Parameters": {
        "config_obj": app_config.AdditionalArticleParameters,
        "keys": app_config.AdditionalArticleParameters.model_dump().keys(),
    },
}


def update_setting(setting_name):
    pass


def update_config_section():
    """update_config_section is a helper function to generate a selector for the
    different settings sections"""
    settings_keys = app_config.model_dump().keys()
    choices = choice_builder(*settings_keys)
    selection = inquirer.select(
        message="Select settings you would like to update",
        choices=choices,
        multiselect=True,
        transformer=lambda result: f"{len(result)} setting{'s' if len(result) > 1 else ''} selected",
    ).execute()
    for s in selection:
        update_setting(s)


def config_hierarchical_select():
    """
    config_hierarchical_select presents multistep process for updating the configuration file
    that walks us through the nested hierarchy.
    """
    settings_keys = CONFIG_SECTIONS.keys()
    selection = inquirer.select(
        message="Select settings you would like to update",
        choices=choice_builder(*settings_keys),
        multiselect=False,
        transformer=lambda result: f"{len(result)} setting{'s' if len(result) > 1 else ''} selected",
    ).execute()

    # would love to find a way to use the constants in the cases but the IDE complained about that
    match selection:
        case "Base":
            base_settings_keys = app_config.Base.model_dump().keys()
            choices = choice_builder(*base_settings_keys)
            selection = inquirer.select(
                message="Select base settings you would like to update",
                choices=choices,
                multiselect=True,
                transformer=lambda result: f"{len(result)} setting{'s' if len(result) > 1 else ''} selected",
            ).execute()
            for s in selection:
                base_settings_select(s)

        case "Digest":
            digest_settings_keys = app_config.Digest.model_dump().keys()
            choices = choice_builder(*digest_settings_keys)
            selection = inquirer.select(
                message="Select digest settings you would like to update",
                choices=choices,
                multiselect=True,
                transformer=lambda result: f"{len(result)} setting{'s' if len(result) > 1 else ''} selected",
            ).execute()

            for s in selection:
                digest_settings_select(s)

        case "Wallabag":
            wallabag_settings_keys = app_config.Wallabag.model_dump().keys()
            choices = choice_builder(*wallabag_settings_keys)
            selection = inquirer.select(
                message="Select Wallabag settings you would like to update",
                choices=choices,
                multiselect=True,
                transformer=lambda result: f"{len(result)} setting{'s' if len(result) > 1 else ''} selected",
            ).execute()

            for s in selection:
                wallabag_settings_select(s)
        case "Article Parameters":
            article_parameters_settings_keys = (
                app_config.ArticleParameters.model_dump().keys()
            )
            choices = choice_builder(*article_parameters_settings_keys)
            selection = inquirer.select(
                message="Select article parameters settings you would like to update",
                choices=choices,
                multiselect=True,
                transformer=lambda result: f"{len(result)} setting{'s' if len(result) > 1 else ''} selected",
            ).execute()

            for s in selection:
                parameters_settings_select(app_config.ArticleParameters, s)
        case "Additional Article Parameters":
            additional_parameters_settings_keys = (
                app_config.AdditionalArticleParameters.model_dump().keys()
            )
            choices = choice_builder(*additional_parameters_settings_keys)
            selection = inquirer.select(
                message="Select additional article parameters settings you would like to update",
                choices=choices,
                multiselect=True,
                transformer=lambda result: f"{len(result)} setting{'s' if len(result) > 1 else ''} selected",
            ).execute()

            for s in selection:
                parameters_settings_select(app_config.AdditionalArticleParameters, s)


def base_settings_select(selection):
    updated_value = input("Update {}: ".format(selection))
    match selection:
        case "application_directory":
            app_config.Base.set_application_directory(updated_value)
        case "log_level":
            app_config.Base.set_log_level(int(updated_value))
        case "max_read_time":
            app_config.Base.set_max_read_time(int(updated_value))
        case "minimum_read_time":
            app_config.Base.set_minimum_read_time(int(updated_value))

    save_app_config(app_config)


def digest_settings_select(selection):
    updated_value = input("Update {}: ".format(selection))
    match selection:
        case "title":
            app_config.Digest.set_title(updated_value)
        case "filepath":
            app_config.Digest.set_filepath(updated_value)
        case "author":
            app_config.Digest.set_author(updated_value)
        case "output_path":
            app_config.Digest.set_output_path(updated_value)
        case "cover_file":
            app_config.Digest.set_cover_file(updated_value)
        case "title_font":
            app_config.Digest.set_title_font(updated_value)
        case "date_font":
            app_config.Digest.set_date_font(updated_value)
        case "back_matter":
            bool_val = False
            if updated_value == "True":
                bool_val = True
            app_config.Digest.set_back_matter(bool_val)

    save_app_config(app_config)


def wallabag_settings_select(selection):
    updated_value = input("Update {}: ".format(selection))
    match selection:
        case "client_id":
            app_config.Wallabag.set_client_id(updated_value)
        case "username":
            app_config.Wallabag.set_username(updated_value)
        case "url":
            app_config.Wallabag.set_url(updated_value)

    save_app_config(app_config)


def parameters_settings_select(settings: WallabagURLParameters, selection):
    updated_value = input("Update {}: ".format(selection))
    match selection:
        case "archive":
            settings.set_archive(updated_value)
        case "starred":
            settings.set_starred(updated_value)
        case "sort":
            settings.set_sort(updated_value)
        case "order":
            settings.set_order(updated_value)
        case "page":
            settings.set_page(updated_value)
        case "perPage":
            settings.set_per_page(updated_value)
        case "tags":
            settings.set_tags(updated_value)
        case "since":
            settings.set_since(updated_value)
        case "public":
            settings.set_public(updated_value)
        case "detail":
            settings.set_detail(updated_value)
        case "domain_name":
            settings.set_domain_name(updated_value)

    save_app_config(app_config)
