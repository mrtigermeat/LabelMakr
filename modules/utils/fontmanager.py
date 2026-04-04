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
            'en': ('Pixel Operator', 16, Path(ASSETS / 'PixelOperator.ttf')),
            'jp': ('PixelMPlus10', 16, Path(ASSETS / 'PixelMplus10-Regular.tff')),
            'ko': ('NeoDunggeunmo', 16, Path(ASSETS / 'neodgm.tff')),
            'zh': ('WenQuanYi Bitmap Song 16px', 18, Path(ASSETS / 'WenQuanYi.Bitmap.Song.16px.ttf'))
        }
        self.avail_fonts = ['en', 'jp', 'ko', 'zh']
    
    def load_temp_font(self, font_path) -> None:
        if font_path.exists():
            shutil.copy(font_path, TEMPDIR)
        subprocess.run(
            ['fc-cache', '-f', TEMPDIR],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logger.debug(f'Temporarily installed font {font_path} in {TEMPDIR}')

    def load_font(self, lang: str = 'en_US') -> None:
        OS = get_os()
        pattern = re.compile(r'[_].*')
        lang = re.sub(pattern, lang, '')
        # using 'in list' in case there are multiple langs with the same script (zh_ZH, zh_YUE)
        try:
            if lang in self.avail_fonts:
                if OS == 'win32':
                    pyglet.font.add_file(str(lang[2]))
                elif OS == 'linux':
                    self.load_temp_font(str(lang[2]))
                return (ctk.CTkFont(family=self.fonts[lang][0], size=self.fonts[lang][1]),
                        ctk.CTkFont(family=self.fonts[lang][0], size=self.fonts[lang][1]-2))
            else:
                return (ctk.CTkFont(family='monospace', size=12),
                        ctk.CTkFont(family='monospace', size=10))
        except Exception as e:
            logger.error(f'Unable to load font for lang {lang}:\n\n {e} \n\n')

