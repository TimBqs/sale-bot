from telebot import types

from config import MAIN_ADMIN_ID
from db import *
from loader import bot


# Проверка, зарегистрирован ли уже пользователь
def is_user_registered(user_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        return cursor.fetchone() is not None
    conn.close()

# Регистрация нового пользователя
def register_new_user(user_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING", (user_id,))
        conn.commit()
    conn.close()

# Получение текущей акции
def get_current_promotion():
    conn = get_db_connection()  # Функция для подключения к базе данных
    promotion_data = None
    try:
        with conn.cursor() as cur:
            # Предполагается, что 'is_active' - это столбец, указывающий на то, активна ли акция.
            cur.execute("""
                SELECT id, text, media_paths, action_url, button_text
                FROM promotions
                WHERE is_active = TRUE
                LIMIT 1;""")  # Получаем только одну активную акцию
            row = cur.fetchone()
            if row:
                # Создаем словарь с данными акции
                promotion_data = {
                    'id': row[0],
                    'text': row[1],
                    'media_paths': row[2],
                    'action_url': row[3],
                    'button_text': row[4]
                }
    except Exception as e:
        print(f"Error retrieving current promotion: {e}")
    finally:
        conn.close()
    
    return promotion_data


# Отправка деталей акции пользователю
def send_promotion_details(chat_id, promotion):
    bot.send_message(chat_id, "Текущая акция: {}".format(promotion[1]))  # Индекс 1 предполагает, что это поле 'title'
    
def send_full_promotion(chat_id, promotion):
    # Создаем разметку для кнопки, если она есть
			markup = None
			if promotion.get('action_url'):
					markup = types.InlineKeyboardMarkup()
					button = types.InlineKeyboardButton(text=promotion.get('button_text', 'Перейти'), url=promotion['action_url'])
					markup.add(button)

			# Отправка фото или видео вместе с описанием акции.
			if promotion.get('media_paths'):  # Проверка наличия медиа
					if len(promotion['media_paths']) > 1:  # Если есть несколько медиа, отправляем их как группу
							media = [types.InputMediaPhoto(open(path, 'rb')) if 'jpg' in path else types.InputMediaVideo(open(path, 'rb'))
											for path in promotion['media_paths']]
							# Добавляем подпись и parse_mode только к первому элементу.
							if not markup:
								media[0].caption = promotion.get('text')
								media[0].parse_mode = 'HTML'
							try:
									bot.send_media_group(chat_id, media)
									if markup: 
										bot.send_message(chat_id, promotion['text'], reply_markup=markup, parse_mode="HTML")
							finally:
									# Закрытие файлов после отправки.
									for item in media:
											item.media.close()
					else:  # Если только одно медиа, отправляем его как отдельное сообщение.
							path = promotion['media_paths'][0]
							if 'mp4' in path:
									bot.send_video(chat_id, open(path, 'rb'), caption=promotion['text'], parse_mode='HTML', reply_markup=markup)
							else:
									bot.send_photo(chat_id, open(path, 'rb'), caption=promotion['text'], parse_mode='HTML', reply_markup=markup)
			else:
					# Если нет изображений или видео, отправляем просто текст
					bot.send_message(chat_id, promotion['text'], parse_mode='HTML', reply_markup=markup)




# Проверка, является ли пользователь администратором
def is_admin(user_id):
    conn = get_db_connection()
    is_main_admin = (user_id in MAIN_ADMIN_ID)
    if not is_main_admin:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(1) FROM administrators WHERE user_id = %s", (user_id,))
            is_admin = cursor.fetchone()[0] > 0
    conn.close()
    return is_main_admin or is_admin

def add_admin(user_id, admin_to_add):
    if user_id in MAIN_ADMIN_ID:  # Только главный админ может добавлять других админов
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO administrators (user_id, added_by) VALUES (%s, %s)", (admin_to_add, user_id))
            conn.commit()
        conn.close()

def remove_admin(user_id, admin_to_remove):
    if user_id == MAIN_ADMIN_ID:  # Только главный админ может удалять админов
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM administrators WHERE user_id = %s", (admin_to_remove,))
            conn.commit()
        conn.close()
        


