import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'


def logs():
    logging.basicConfig(
        level=logging.DEBUG,
        filename='main.log',
        filemode='w',
        format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
    )


logger = logging.getLogger('__name__')
logger.setLevel(logging.DEBUG)


def parse_homework_status(homework):
    try:
        homework_name = homework['homework_name']
        if homework['status'] == 'rejected':
            verdict = 'К сожалению в работе нашлись ошибки.'
        else:
            verdict = ('Ревьюеру всё понравилось, '
                       'можно приступать к следующему уроку.')
        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'
    except KeyError as e:
        logger.error(f'Не получено название или статус домашней работы: {e}',
                     exc_info=True)
        bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
        bot_client.send_message(chat_id=CHAT_ID, text=(
            'Не получено название или статус домашней работы: {e}'))


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(URL, headers=headers, params=params)
    except requests.exceptions.HTTPError as e:
        logger.error(f'Ошибка соединения с сервером: {e}', exc_info=True)
        bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
        bot_client.send_message(chat_id=CHAT_ID, text=(f'Ошибка соединения с '
                                                       f'сервером: {e}'))
    try:
        return homework_statuses.json()
    except TypeError or ValueError or OSError as e:
        logger.error(f'Ошибка при обработке json: {e}', exc_info=True)
        bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
        bot_client.send_message(chat_id=CHAT_ID, text=(f'Ошибка при обработке '
                                                       f'json: {e}'))


def send_message(message, bot_client):
    logger.info('Бот отправляет сообщение')
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    logger.debug('Запуск бота')
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(
                    new_homework.get('homeworks')[0]), bot_client)
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp)
            time.sleep(300)
        except Exception as e:
            logger.error(f'Бот столкнулся с ошибкой: {e}', exc_info=True)
            bot_client.send_message(
                chat_id=CHAT_ID, text=(f'Бот столкнулся с ошибкой: {e}'))
            time.sleep(5)


if __name__ == '__main__':
    logs()
    main()
