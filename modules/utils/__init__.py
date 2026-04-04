import re
import sys
import yaml
import pyglet
from pathlib import Path
from loguru import logger
import customtkinter as ctk
from tkinter import filedialog

pyglet.options['win32_gdi_font'] = True

def get_logger(level="INFO") -> logger:
    logger_format = "{time:HH:mm:ss} | <lvl>{level}</lvl> | <lvl>{message}</lvl>"
    logger.remove()
    logger.add(sys.stdout, format=logger_format, level=level)
    return logger

logger = get_logger()

from modules.utils.constants import ASSETS

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

def get_os():
    if sys.platform in ['linux', 'linux2']:
        return 'linux'
    elif sys.platform == 'darwin':
        return 'osx'
    elif sys.platform == 'win32':
        return 'win32'
    else:
        logger.error(f'{sys.platform} is not supported by LabelMakr.')
        return None
        

