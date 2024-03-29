import logging

import handlers
from loader import *

logging.basicConfig(level=logging.INFO)
# Запуск бота
if __name__ == '__main__':
    try:
        run_bot()
    except Exception as e:
        logging.error(f"Unhandled exception: {e}", exc_info=True)

