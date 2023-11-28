from config import MAIN_ADMIN_ID
from functions import *
from loader import bot


@bot.message_handler(commands=['add_admin'])
def handle_add_admin(message):
    if message.from_user.id == MAIN_ADMIN_ID:
        try:
            admin_to_add = int(message.text.split()[1])  # Получаем ID пользователя для добавления
            response = add_admin(message.from_user.id, admin_to_add)
            bot.send_message(message.chat.id, response)
        except (IndexError, ValueError):
            bot.send_message(message.chat.id, "Используйте: /add_admin <user_id>")
    else:
        bot.send_message(message.chat.id, "Только главный администратор может добавлять администраторов.")

@bot.message_handler(commands=['remove_admin'])
def handle_remove_admin(message):
    if message.from_user.id == MAIN_ADMIN_ID:
        try:
            admin_to_remove = int(message.text.split()[1])  # Получаем ID пользователя для удаления
            response = remove_admin(message.from_user.id, admin_to_remove)
            bot.send_message(message.chat.id, response)
        except (IndexError, ValueError):
            bot.send_message(message.chat.id, "Используйте: /remove_admin <user_id>")
    else:
        bot.send_message(message.chat.id, "Только главный администратор может удалять администраторов.")