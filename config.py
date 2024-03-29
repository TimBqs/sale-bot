import os

from dotenv import load_dotenv

load_dotenv()
 
# Главный администратор
MAIN_ADMIN_ID = [1264496790 ,int(os.environ.get('MAIN_ADMIN_ID'))]

# Состояния для процесса обновления акции
STATE_PROMOTION_MESSAGE = 1
STATE_PROMOTION_IMAGE = 2
STATE_PROMOTION_VIDEO = 3
STATE_PROMOTION_URL = 4
STATE_PROMOTION_CONFIRMATION = 5

# Временное хранилище данных о новой акции
promotion_drafts = {}


# Создание экземпляра бота
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Подключение к базе данных
db_params = {
    'dbname': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'host': os.environ.get('DB_HOST'),
	'port': os.environ.get('DB_PORT')
}