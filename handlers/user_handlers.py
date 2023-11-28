import os

from config import MAIN_ADMIN_ID, promotion_drafts
from db import *
from functions import *
from loader import bot


# Обработчики команд
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    if not is_user_registered(user_id):
        register_new_user(user_id)
    current_promotion = get_current_promotion()
    if current_promotion:
        # Текст, фото, видео и кнопка (если есть) должны быть отправлены пользователю
        send_full_promotion(message.chat.id, current_promotion)
    else:
        bot.send_message(message.chat.id, "В настоящее время нет активных акций.")

# Обработчик для начала обновления акции
@bot.message_handler(commands=['update_promotion'])
def ask_for_promotion_details(message):
    if message.from_user.id == MAIN_ADMIN_ID or is_admin(message.from_user.id):
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Да', 'Нет')
        msg = bot.send_message(message.chat.id, "Вы собираетесь обновить акцию. Продолжить?", reply_markup=markup)
        bot.register_next_step_handler(msg, process_promotion_update_confirmation)

def process_photo(message):
    chat_id = message.chat.id
    # Список для хранения путей к фотографиям
    if 'image_paths' not in promotion_drafts[chat_id]:
        promotion_drafts[chat_id]['image_paths'] = []

    # Логика сохранения изображения
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Путь для сохранения изображения
    save_path = os.path.join('images', f"{file_id}.jpg")
    with open(save_path, 'wb') as new_file:
        new_file.write(downloaded_file)
    
    # Сохраняем путь в черновике акции
    promotion_drafts[chat_id]['image_paths'].append(save_path)

    bot.reply_to(message, "Изображение сохранено.")

def process_video(message):
    chat_id = message.chat.id
    # Список для хранения путей к видео
    if 'video_paths' not in promotion_drafts[chat_id]:
        promotion_drafts[chat_id]['video_paths'] = []

    # Логика сохранения видео
    file_id = message.video.file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Путь для сохранения видео
    save_path = os.path.join('videos', f"{file_id}.mp4")
    with open(save_path, 'wb') as new_file:
        new_file.write(downloaded_file)
    
    # Сохраняем путь в черновике акции
    promotion_drafts[chat_id]['video_paths'].append(save_path)

    bot.reply_to(message, "Видео сохранено.")

def save_promotion_to_db(draft, admin_chat_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO promotions (text, image_paths, video_paths, action_url, button_text, is_active) 
            VALUES (%s, %s, %s, %s, %s, TRUE) 
            RETURNING id;
        """, (draft['text'], draft.get('image_paths', []), draft.get('video_paths', []), draft.get('action_url'), draft.get('button_text')))
        promotion_id = cursor.fetchone()[0]
        conn.commit()
    conn.close()
    
    # Отправка сообщения администратору о сохранении акции
    bot.send_message(admin_chat_id, f"Акция с ID {promotion_id} сохранена и активирована.")
def process_promotion_update_confirmation(message):
    if message.text == 'Да':
        msg = bot.send_message(message.chat.id, "Введите текст акции:")
        bot.register_next_step_handler(msg, process_promotion_message)
    elif message.text == 'Нет':
        bot.send_message(message.chat.id, "Обновление акции отменено.")
    else:
        msg = bot.send_message(message.chat.id, "Пожалуйста, выберите 'Да' или 'Нет'.")
        bot.register_next_step_handler(msg, process_promotion_update_confirmation)  # регистрируем обработчик заново

def apply_formatting(text, entities):
    # Сортируем сущности в обратном порядке, чтобы изменения не смещали последующие индексы
    print(entities)
    entities = sorted(entities, key=lambda e: e.offset, reverse=True)
    

    # Проходим по каждой сущности и применяем форматирование
    for entity in entities:
        # Если сущность начинается с эмодзи, корректируем смещение
        start = entity.offset
        if (start > 0):
         start -= 1
         end = start + 1 + entity.length
        else: 
         end = start + entity.length

        # Применяем форматирование с учетом коррекции
        if entity.type == 'bold':
            text = text[:start] + '<b>' + text[start:end] + '</b>' + text[end:]
        elif entity.type == 'italic':
            text = text[:start] + '<i>' + text[start:end] + '</i>' + text[end:]
        elif entity.type == 'code':
            text = text[:start] + '<code>' + text[start:end] + '</code>' + text[end:]
        elif entity.type == 'pre':
            text = text[:start] + '<pre>' + text[start:end] + '</pre>' + text[end:]
        elif entity.type == 'text_link':
            text = text[:start] + f'<a href="{entity.url}">' + text[start:end] + '</a>' + text[end:]

    return text



def process_promotion_message(message):
    chat_id = message.chat.id
    entities = message.entities or message.caption_entities
    formatted_text = message.text or message.caption

    if entities:
        formatted_text = apply_formatting(formatted_text, entities)

    promotion_drafts[chat_id] = {'text': formatted_text}

    msg = bot.send_message(chat_id, "Прикрепите фото\видео акции или отправьте 'далее', если фото\видео нет.")
    bot.register_next_step_handler(msg, process_media)

    
def process_media(message):
    chat_id = message.chat.id
    if 'media_paths' not in promotion_drafts[chat_id]:
        promotion_drafts[chat_id]['media_paths'] = []

    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
    elif message.content_type == 'video':
        file_id = message.video.file_id
    else:
        # Если пользователь ввел "далее", переходим к следующему шагу
        if message.text and message.text.lower() == 'далее':
            msg = bot.send_message(chat_id, "Хотите ли вы прикрепить ссылку? Отправьте 'да' или 'нет'.")
            bot.register_next_step_handler(msg, process_promotion_url_decision)  
            return
        else:
            msg = bot.send_message(chat_id, "Пожалуйста, загрузите фото или видео, или введите 'далее', чтобы продолжить.")
            bot.register_next_step_handler(msg, process_media)  

            return

    # Логика сохранения медиафайла одинакова для фото и видео
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Определяем расширение файла и каталог на основе типа контента
    file_extension = 'jpg' if message.content_type == 'photo' else 'mp4'
    folder = 'images' if message.content_type == 'photo' else 'videos'
    save_path = os.path.join(folder, f"{file_id}.{file_extension}")

    with open(save_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    # Добавляем путь к медиа в черновик акции
    promotion_drafts[chat_id]['media_paths'].append(save_path)
    bot.reply_to(message, f"{'Фото' if message.content_type == 'photo' else 'Видео'} сохранено. Отправьте 'далее', чтобы продолжить.")
    msg = bot.send_message(chat_id, "Пожалуйста, загрузите фото или видео, или введите 'далее', чтобы продолжить.")
    bot.register_next_step_handler(msg, process_media)  


def process_promotion_url_decision(message):
    chat_id = message.chat.id
    if message.text.lower() == 'да':
        msg = bot.send_message(chat_id, "Введите URL:")
        bot.register_next_step_handler(msg, process_promotion_url)
    else:
        confirm_and_send_or_restart(message)

def process_promotion_url(message):
    chat_id = message.chat.id
    promotion_drafts[chat_id]['action_url'] = message.text
    msg = bot.send_message(chat_id, "Введите название кнопки для URL:")
    bot.register_next_step_handler(msg, process_promotion_button_title)

def process_promotion_button_title(message):
    chat_id = message.chat.id
    promotion_drafts[chat_id]['button_text'] = message.text
    confirm_and_send_or_restart(message)

def confirm_and_send_or_restart(message):
    chat_id = message.chat.id
    draft = promotion_drafts.get(chat_id)
    if draft:
        # Создаем разметку для подтверждения
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Да', 'Нет')
        promotion_details = f"Текст акции: {draft.get('text')}\n"
        promotion_details += f"URL: {draft.get('action_url', 'Не указан')}\n"
        promotion_details += f"Название кнопки: {draft.get('button_text', 'Не указано')}\n"
        bot.send_message(chat_id, promotion_details)
        msg = bot.send_message(chat_id, "Все верно? Вы хотите отправить акцию?", parse_mode='HTML',reply_markup=markup)
        bot.register_next_step_handler(msg, final_confirmation)

def final_confirmation(message):
    chat_id = message.chat.id
    draft = promotion_drafts.get(chat_id)
    if message.text == 'Да':
        # Окончательная логика сохранения и отправки акции
# Сохраняем акцию в базе данных
        save_promotion_to_db(draft, chat_id)
        # Логика отправки акции всем пользователям
        send_promotion_to_all_users(chat_id)
        promotion_drafts.pop(chat_id, None)  # Удаляем черновик после отправки    
    elif message.text == 'Нет':
        # Возврат к началу процесса обновления акции
        ask_for_promotion_details(message)
    else:
        # Повторный запрос подтверждения, если введен неверный ответ
        msg = bot.send_message(chat_id, "Пожалуйста, выберите 'Да' или 'Нет' для подтверждения.")
        bot.register_next_step_handler(msg, final_confirmation)  # регистрируем обработчик заново

        
				# Деактивация всех акций перед активацией новой
def deactivate_all_promotions_except(new_promotion_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # Деактивируем все акции, кроме новой
        cursor.execute("UPDATE promotions SET is_active = FALSE WHERE id != %s", (new_promotion_id,))
        conn.commit()
    conn.close()

# Функция для сохранения акции в базу данных
def save_promotion_to_db(draft, admin_chat_id):
    conn = get_db_connection()
    # Эта функция вызывается перед сохранением и активацией новой акции
    with conn.cursor() as cursor:
        
        cursor.execute("""
            INSERT INTO promotions (text, media_paths, action_url, button_text, is_active) 
            VALUES (%s, %s, %s, %s, TRUE) 
            RETURNING id;
        """, (draft['text'], draft.get('media_paths'), draft.get('action_url'), draft.get('button_text')))
        promotion_id = cursor.fetchone()[0]
        conn.commit()
    conn.close()
    
    deactivate_all_promotions_except(promotion_id)
    bot.send_message(admin_chat_id, f"Акция с ID {promotion_id} сохранена и активирована.")

# Функция отправки акции всем пользователям
def send_promotion_to_all_users(admin_chat_id):
    conn = get_db_connection()
    promotion = get_current_promotion()  
    if not promotion:
        bot.send_message(admin_chat_id, "Нет активных акций для рассылки.")
        return

    with conn.cursor() as cursor:
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        for user in users:
            try:
                send_full_promotion(user[0], promotion)
                bot.send_message(admin_chat_id, "Акция разослана всем пользователям.")
            except Exception as e:
                print(f"Не удалось отправить сообщение пользователю {user[0]}: {e}")
                bot.send_message(admin_chat_id, "Возникла ошибка при отправке акции")
    conn.close()
    