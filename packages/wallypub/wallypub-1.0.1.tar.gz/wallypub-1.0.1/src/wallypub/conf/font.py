import logging
import os
import subprocess
import tarfile
from pathlib import Path


from wallypub.conf.constants import GNU_FREE_FONT_URI, font_dir, DEFAULT_FONT

system_font_dir = "/usr/share/fonts/"


def is_font_installed() -> bool:
    """ """
    if os.path.isfile(system_font_dir + "/" + DEFAULT_FONT):
        return True
    return False


def install_default_font():
    """
    Install default font installs the GNU FreeFont .ttf which can be found:
    https://www.gnu.org/software/freefont/
    """

    Path(font_dir).mkdir(parents=True, exist_ok=True)

    default_font_location = font_dir + "/" + "freefont-20100919/sfd/FreeMono.ttf"
    zipped_name = font_dir + "/" + "freefont-ttf.tar.gz"

    # download tarfile to memory
    logging.info("Downloading font from {}...".format(GNU_FREE_FONT_URI))
    cmd = ["wget", GNU_FREE_FONT_URI]
    cmd.extend(["-O", zipped_name])

    try:
        subprocess.run(cmd, check=True)
        logging.info("Download completed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error("Download failed. Err: {}".format(e))

    tar = tarfile.open(zipped_name)
    tar.extractall(path=font_dir + "/freefont-20100919")
    tar.close()

    logging.info(
        "Installing font from {} to {}...".format(
            default_font_location, system_font_dir
        )
    )
    subprocess.call(["sudo", "cp", default_font_location, system_font_dir])

    logging.info("clearing font manager cache...")
    logging.info("Removing temporary files...")
    os.remove(zipped_name)


def list_system_fonts(scroll, search):
    cmd = [
        "bash",
        "-c",
        "fc-list | grep -oP '(?<=/usr/share/fonts/)(.*?)(?=:)' | xargs -n1 basename | sort -u",
    ]
    if scroll:
        cmd = [
            "bash",
            "-c",
            "fc-list | grep -oP '(?<=/usr/share/fonts/)(.*?)(?=:)' | xargs -n1 basename | sort -u | less",
        ]
    if search != "":
        cmd = [
            "bash",
            "-c",
            "fc-list | grep -oP '(?<=/usr/share/fonts/)(.*?)(?=:)' | xargs -n1 basename | sort -u | grep {}".format(
                search
            ),
        ]
    subprocess.run(cmd, check=True)
