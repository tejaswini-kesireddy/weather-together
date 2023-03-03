import logging
import os
from datetime import datetime

if not os.path.isdir("logs"):
    os.mkdir("logs")

DEFAULT_LOG_FORM = '%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(funcName)s - %(message)s'

handler = logging.FileHandler(filename=datetime.now().strftime(os.path.join('logs', 'weather_%d-%m-%Y.log')))
handler.setFormatter(logging.Formatter(fmt=DEFAULT_LOG_FORM))

# Logger levels: DEBUG, INFO, WARNING, ERROR, CRITICAL(FATAL)
logger = logging.getLogger(__name__)
logger.addHandler(hdlr=handler)
logger.setLevel(level=logging.DEBUG)

logger.info("Hello World")
