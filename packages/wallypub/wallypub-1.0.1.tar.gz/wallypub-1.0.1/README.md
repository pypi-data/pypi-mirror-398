# Wallypub
[![Please don't upload to GitHub](https://nogithub.codeberg.page/badge-sq.svg)](https://nogithub.codeberg.page)

Wallypub is a CLI companion tool for Wallabag that allows you to turn Wallabag articles into a dedicated epub.

## Installation

### Python

https://pypi.org/project/wallypub/

`pip install wallypub`

```
pip install wallypub
```

More details on installation can be found in the [user guide](https://glasshoundcomputing.com/wallypub/user-guide.html).

## Usage 

```text

Usage: main.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  config-edit          prompts user to update settings values
  config-init          walks the user through the first time configuration
  config-secrets-edit  prompts user to update secret values in keyring
  config-secrets-show  displays the sensitive variables from the keyring
  config-show          displays the settings to the console
  digest-by-ids        generate EPUB from comma-separated Wallabag IDs
  digest-cover-create  procedurally generate a cover image for your digest
  digest-recent        generate EPUB from recent Wallabag articles
  donate               prints link to Glass Hound Computing's donation page
  entry-add            add an entry to your Wallabag instance
  system-fonts-show    displays installed system fonts
```

If you would like an in depth guide to using Wallypub, please see the [user guide](https://glasshoundcomputing.com/wallypub/user-guide).


## Contributing 

If you would like to get involved, see the [CONTRIBUTING](docs/CONTRIBUTING.md) guide. If you are a developer, also read through the [Developer Guide](docs/developer_guide/setup.md) documents. 

