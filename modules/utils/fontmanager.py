import os
import re
import shutil
import subprocess
import pyglet
from pathlib import Path
import customtkinter as ctk

from modules.utils import get_logger, get_os
from modules.utils.constants import ASSETS, TEMPDIR

logger = get_logger(os.environ['LM_MODE'])
OS = get_os()

class FontManager:
    def __init__(self):
        pyglet.font.add_file(str(Path(ASSETS / 'PixelOperator.ttf')))
        pyglet.font.add_file(str(Path(ASSETS / 'PixelMplus10-Regular.ttf')))
        pyglet.font.add_file(str(Path(ASSETS / 'neodgm.ttf')))
        pyglet.font.add_file(str(Path(ASSETS / 'WenQuanYi.Bitmap.Song.16px.ttf')))

        self.fonts = {
            # 'lang_code_first_2': ('Font name', size, Path(ASSETS / 'fontname.tff/otf'))
            'en': ['Pixel Operator', 16, Path(ASSETS / 'PixelOperator.ttf')],
            'jp': ['PixelMPlus10', 16, Path(ASSETS / 'PixelMplus10-Regular.tff')],
            'ko': ['NeoDunggeunmo', 16, Path(ASSETS / 'neodgm.tff')],
            'zh': ['WenQuanYi Bitmap Song 16px', 18, Path(ASSETS / 'WenQuanYi.Bitmap.Song.16px.ttf')]
        }
        self.avail_fonts = ['en', 'jp', 'ko', 'zh']
    
    def load_temp_font(self, font_path) -> None:
        if font_path.exists():
            logger.debug('FONT EXISTS')
            font_name = os.path.split(str(font_path))[-1]
            temp_font_path = TEMPDIR / font_name
            shutil.copy(font_path, temp_font_path)
        subprocess.run(
            ['fc-cache', '-f', temp_font_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logger.debug(f'Temporarily installed font {font_path} in {TEMPDIR}')

    def load_font(self, lang: str = 'en_US') -> None:
        OS = get_os()
        lang = lang[:2]
        assert len(lang) == 2, logger.error(f'Issue with langcode: {lang}')
        # using 'in list' in case there are multiple langs with the same script (zh_ZH, zh_YUE)
        try:
            if lang in self.avail_fonts:
                if OS == 'win32':
                    pyglet.font.add_file(self.fonts[lang][2])
                elif OS == 'linux':
                    self.load_temp_font(self.fonts[lang][2])
                font = ctk.CTkFont(family=self.fonts[lang][0], size=self.fonts[lang][1])
                font_sm = ctk.CTkFont(family=self.fonts[lang][0], size=self.fonts[lang][1]-2)
                logger.debug(f"{font.cget('family')}")
                return font, font_sm
            else:
                font = ctk.CTkFont(family='monospace', size=12)
                font_sm = ctk.CTkFont(family='monospace', size=10)
                return font, font_sm
        except Exception as e:
            logger.error(f'Unable to load font for lang {lang}:\n\n {e} \n\n')

if __name__ == '__main__':
    print(1)