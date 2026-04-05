import os
import tempfile
from pathlib import Path

from modules.utils import get_logger

logger = get_logger(os.environ['LM_MODE'])

ASSETS = Path('./gui/assets')
STRINGS = Path('./gui/strings')
CORPUS = Path('./corpus')
MODELS = Path('./models')
IMG = Path('./gui/assets/img')

TEMPDIR = Path(tempfile.gettempdir())

logger.debug(f'TEMPDIR is {str(TEMPDIR)}')