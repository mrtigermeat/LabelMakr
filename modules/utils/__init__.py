import re
import sys
import yaml
import pyglet
from pathlib import Path
from loguru import logger
import customtkinter as ctk
from tkinter import filedialog

from modules.utils.constants import ASSETS

pyglet.options['win32_gdi_font'] = True

def get_logger(level="INFO") -> logger:
    logger_format = "{time:HH:mm:ss} | <lvl>{level}</lvl> | <lvl>{message}</lvl>"
    logger.remove()
    logger.add(sys.stdout, format=logger_format, level=level)
    return logger

logger = get_logger()

def load_config(path: Path) -> dict:
    output = {}
    if path.exists():
        with open(path, 'r', encoding='utf-8') as c:
            try:
                output.update(yaml.safe_load(c))
                return output
            except yaml.YAMLError as e:
                logger.error(f'Unable to open file {path}: \n {e} \n\n')
                return output

class FontManager:
    def __init__(self):
        pyglet.font.add_file(str(Path(ASSETS / 'PixelOperator.ttf')))
        pyglet.font.add_file(str(Path(ASSETS / 'PixelMplus10-Regular.ttf')))
        pyglet.font.add_file(str(Path(ASSETS / 'neodgm.ttf')))
        pyglet.font.add_file(str(Path(ASSETS / 'WenQuanYi.Bitmap.Song.16px.ttf')))

        self.fonts = {
            # 'lang_code_first_2': ('Font name', size)
            'en': ('Pixel Operator', 16),
            'jp': ('PixelMPlus10', 16),
            'ko': ('NeoDunggeunmo', 16),
            'zh': ('WenQuanYi Bitmap Song 16px', 18)
        }
        self.avail_fonts = ['en', 'jp', 'ko', 'zh']

    def load_font(self, lang: str = 'en_US') -> None:
        pattern = re.compile(r'[_].*')
        lang = re.sub(pattern, lang, '')
        # using 'in list' in case there are multiple langs with the same script (zh_ZH, zh_YUE)
        try:
            if lang in self.avail_fonts:
                return (ctk.CTkFont(family=self.fonts[lang][0], size=self.fonts[lang][-1]),
                        ctk.CTkFont(family=self.fonts[lang][0], size=self.fonts[lang-1]-2))
            else:
                return (ctk.CTkFont(family='monospace', size=12),
                        ctk.CTkFont(family='monospace', size=10))
        except Exception as e:
            logger.error(f'Unable to load font for lang {lang}:\n\n {e} \n\n')

