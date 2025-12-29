"""
This package is for generating cover images
"""

import logging
from pathlib import Path

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from wallypub.conf.app import app_config
from wallypub.img.color import (
    get_random_color,
    return_complimentary_color,
    get_hex_value,
)
from wallypub.utils.date import get_string_date


class CoverGenerator:
    # default size is 1.6:1 or 8:5 aspect ratio (used on e-readers/tablets), assuming it's vertical
    def __init__(self, size=(900, 1440)):
        self.size = size
        self.image = None
        self.draw = None
        self.title_font = None
        self.date_font = None
        self.outfile = None

    def generate_default(self):
        """
        generates a default cover image with the digest title & date
        the text on the cover will be a complimentary color
        to the randomly generated background color

        There are numerous magic numbers in this file. These came about through
        experimentation. Would that I could remember the exact reason I landed upon
        these values.
        :return:
        """

        cfg = app_config

        self.outfile = cfg.Digest.cover_file

        string_date = get_string_date()

        bg_color = get_random_color()
        bg_hex_color = get_hex_value(bg_color)
        text_color = return_complimentary_color(bg_hex_color)
        self.image = Image.new("RGB", size=self.size, color=bg_color)
        self.draw = ImageDraw.Draw(self.image)

        title_width, title_height = self.size
        title_w = self.draw.textlength(cfg.Digest.title)
        title_h = 40 * 1
        date_w = self.draw.textlength(string_date)
        date_h = 40 * 1

        self.title_font = ImageFont.truetype(app_config.Digest.title_font, 40)
        self.date_font = ImageFont.truetype(app_config.Digest.date_font, 30)
        self.draw.text(
            ((title_width - title_w) / 3, (title_height - title_h) / 2),
            cfg.Digest.title,
            text_color,
            font=self.title_font,
        )
        self.draw.text(
            ((title_width - date_w) / 3, (title_height - date_h) / 1.8),
            string_date,
            text_color,
            font=self.date_font,
        )

    def save(self):
        if self.image is not None:
            filepath = app_config.Digest.filepath + "/" + app_config.Digest.cover_file
            logging.info("saving cover image to {}".format(filepath))
            Path(app_config.Digest.filepath).mkdir(parents=True, exist_ok=True)
            self.image.save(filepath)
