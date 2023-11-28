import signal
from config import BOT_TOKEN
import telebot
bot = telebot.TeleBot(BOT_TOKEN)


def run_bot():
    try:
        bot.infinity_polling(30)
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
        bot.stop_polling()
        run_bot()

def shutdown_bot(signum, frame):
    print("Завершаю работу бота...")
    bot.stop_polling()

signal.signal(signal.SIGINT, shutdown_bot)
signal.signal(signal.SIGTERM, shutdown_bot)