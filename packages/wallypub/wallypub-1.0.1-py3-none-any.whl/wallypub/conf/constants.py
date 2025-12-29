import platformdirs

APP_NAME = "Wallypub"
APP_AUTHOR_NAME = "Glass Hound Computing"
SETTINGS_FILE = "settings.toml"
DEFAULT_COVER_IMAGE_FILE_NAME = "cover.jpg"
DEFAULT_BACKMATTER_FILE = "backmatter.html"
API_CLIENT_DOC_LOCATION = "https://doc.wallabag.org/developer/api/oauth/"
# WALLABAG_PASS_KEY AND WALLABAG_CLIENT_SECRET_KEY are passed to the username portion
# of the keyring functions. "username" acts as sort of the key in the k/v store the library uses.
WALLABAG_PASS_KEY = "wallabag_password"
WALLABAG_CLIENT_SECRET_KEY = "wallabag_client_secret"
DEFAULT_WALLABAG_URL = "app.wallabag.it"
SERVICE_NAME = "wallypub"
EXTENSION_EPUB = ".epub"
DEFAULT_ENCODING = "utf-8"
DEFAULT_FONT = "FreeMono.ttf"
"""
Using a mirror here for the font. While developing, the GNU link was not working. 
Ideally, this gets resolved and the URI can revert to the one maintained at gnu.org

https://ftp.gnu.org/gnu/freefont/freefont-ttf.tar.gz
"""
GNU_FREE_FONT_URI = "https://ftp.rediris.es/mirror/GNU/freefont//freefont-ttf.tar.gz"

static_dir = platformdirs.user_data_dir(APP_NAME, APP_AUTHOR_NAME) + "/static"
font_dir = static_dir + "/fonts"
