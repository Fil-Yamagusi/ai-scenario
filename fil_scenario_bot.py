#!/usr/bin/env python3.12
# -*- coding: utf-8 -*-
"""2024-03-20 Fil - Future code Yandex.Practicum
AI-bot: Scenario generator
README.md for more

Fil FC AI Scenario generator
@fil_fc_ai_sc_bot
https://t.me/fil_fc_ai_sc_bot
"""
__version__ = '0.1'
__author__ = 'Firip Yamagusi'

import random
from time import time_ns, time, strftime
from random import choice

import logging
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, Message

from fil_scenarion_db import (
    create_db,
    is_limit_users,
    is_limit_sessions,
    get_tokens_in_session,
    is_limit_tokens_in_session,
    create_user,
    insert_tokenizer_info,
    insert_prompt,
    insert_full_story,
    get_full_story,
    get_tokens_info,
)

from fil_scenario_gpt import (
    count_tokens,
    ask_gpt,
    create_system_prompt
)

from config import TOKEN_SC, MAX_TOKENS_IN_SESSION

bot_name = "Fil FC AI Scenario generator | @fil_fc_ai_sc_bot"

# Файл БД
db_file = "fil_scenario.db"
db_conn = create_db(db_file)

# Файл лог
log_file = "fil_scenario_log.txt"
if True:
    # Настройки для опубликованного бота
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt="%F %T",
        filename=log_file,
        filemode="w",
    )
else:
    # Настройки пока тестирую
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt="%F %T",
    )

logging.warning(f"The bot has been started: {bot_name}")

# Для понимания в консоли
print(f"Bot has been started: {bot_name}\nTOKEN = {TOKEN_SC}")

bot = TeleBot(TOKEN_SC)

# Словарь для хранения настроек пользователя
user_data = {}

# Пустое меню, может пригодиться
hideKeyboard = ReplyKeyboardRemove()

# Меню для настроек сценария
Settings = {
    "Античный миф": {
        "characters":
            ["Многоголовая гидра", "Хитроумный Геракл",
             "Елена Прекрасная", "Афина Премудрая"],
        "entourages":
            ["гора Олимп", "Царство Аида", "Земли Гипербореев", "остров Крит"]
    },
    "Соцреализм": {
        "characters":
            ["Пионер Тимур", "Близняшка Оля",
             "Однорогая Коза", "Мишка Квакин"],
        "entourages":
            ["Яблоневый сад", "Берег реки", "Дачный посёлок", "Штаб на чердаке"]
    },
    "Абсурдизм": {
        "characters":
            ["Влюбчивая ворона", "Шестирукий Громозека",
             "Гиноид Аня", "Андроид Гена"],
        "entourages":
            ["Очередь за квасом", "Лысая гора", "Масонская ложа", "Поле Чудес"]
    },
}

# Меню выбора жанра. Можем заранее сделать, а вложенные - в настройках
mu_genges = ReplyKeyboardMarkup(
    row_width=3,
    resize_keyboard=True)
mu_genges.add(*list(Settings.keys()))

# Меню выбора жанра. Можем заранее сделать, а вложенные - в настройках
mu_generate = ReplyKeyboardMarkup(
    row_width=1,
    resize_keyboard=True)
mu_generate.add(*['The end'])


def check_user(m):
    """
    Проверка наличия записи для данного пользователя
    Проверка ограничений разных пользователей (MAX_USERS)
    """
    global user_data, db_conn

    user_id = m.from_user.id

    if user_id not in user_data:
        user_data[user_id] = {}
        user_data[user_id]['user_id'] = user_id
        # Словарь для хранения истории диалога пользователя и GPT

        user_data[user_id]['task'] = ""
        user_data[user_id]['answer'] = ""
        user_data[user_id]['busy'] = False
        user_data[user_id]['t_start'] = 0
        user_data[user_id]['t_result'] = 0


@bot.message_handler(commands=['start'])
def handle_start(m: Message):
    """
    Обработчик команды /start
    """
    user_id = m.from_user.id
    check_user(m)
    bot.send_message(
        user_id,
        '✌🏻 <b>Привет! Я бот с искусственным интеллектом</b>\n\n'
        'Помогаю сочинять сценарии для математических задачек.\n'
        'Выбери жанр, персонажа и сеттинг в настройках: /settings',
        parse_mode="HTML",
        reply_markup=hideKeyboard)


@bot.message_handler(commands=['help'])
def handle_help(m: Message):
    """
    Обработчик команды /help
    """
    user_id = m.from_user.id
    check_user(m)
    bot.send_message(
        user_id,
        'Сложное домашнее задание.\n'
        'Для подробного написания справки времени нет\n'
        'Прастити.',
        parse_mode="HTML",
        reply_markup=hideKeyboard)


@bot.message_handler(commands=['debug'])
def handle_debug(m: Message):
    """
    Часть домашнего задания - СИКРЕТНЫЙ вывод отладочной информации
    """
    user_id = m.from_user.id
    check_user(m)
    logging.warning(f"{user_id}: get tokens statistics from TG-bot")

    try:
        with open(log_file, "rb") as f:
            bot.send_document(user_id, f)
    except Exception:
        logging.error(
            f"{user_id}: cannot send log-file to tg-user")
        bot.send_message(
            user_id,
            f'Не могу найти лог-файл',
            reply_markup=hideKeyboard)


@bot.message_handler(commands=['tokens'])
def handle_tokens(m: Message):
    """
    Часть домашнего задания - информация о токенах
    """
    global db_conn
    user_id = m.from_user.id
    check_user(m)
    logging.warning(f"{user_id}: Любопытный пользователь спрашивает про токены")

    bot.send_message(
        user_id,
        f'УРА! ТЕБЕ ДОБАВИЛИ {random.randint(1, 99) * 1000} ТОКЕНОВ! '
        f'ЖМИ КОМАНДУ ЕЩЁ РАЗ! (шутка)',
        reply_markup=hideKeyboard)

    bot.send_message(
        user_id,
        f'{"\n".join(get_tokens_info(db_conn, user_data[user_id]))}',
        reply_markup=hideKeyboard)


@bot.message_handler(commands=['random'])
def handle_random(m: Message):
    """
    Обработчик команды /random - случайная полная история
    """
    global db_conn
    user_id = m.from_user.id
    check_user(m)
    logging.warning(f"{user_id}: Getting random full story")

    bot.send_message(
        user_id,
        f'Вот случайная история из созданных ранее:\n\n'
        f'{get_full_story(db_conn)} \n\n'
        f'Ещё? /random',
        parse_mode="HTML",
        reply_markup=hideKeyboard)


@bot.message_handler(commands=['settings'])
def handle_settings(m: Message):
    """
    Обработчик команды /settings
    """
    user_id = m.from_user.id
    check_user(m)
    bot.send_message(
        user_id,
        'Выбери сначала жанр, потом персонажа, потом антураж',
        parse_mode="HTML",
        reply_markup=mu_genges)
    bot.register_next_step_handler(m, settings_genre)


def settings_genre(m: Message):
    """
    Выбор и установка жанра
    """
    global db_conn, mu_genges, user_data
    user_id = m.from_user.id
    check_user(m)
    if m.text in list(Settings.keys()):
        user_data[user_id]['genre'] = m.text
        genre = user_data[user_id]['genre']
        characters = list(Settings[genre]['characters'])
        mu_characters = ReplyKeyboardMarkup(
            row_width=2,
            resize_keyboard=True)
        mu_characters.add(*characters)

        bot.send_message(
            user_id,
            'Теперь выбери персонажа',
            parse_mode="HTML",
            reply_markup=mu_characters)
        bot.register_next_step_handler(m, settings_characters)
    else:
        bot.send_message(
            user_id,
            'Выбери правильный жанр из списка!',
            parse_mode="HTML",
            reply_markup=mu_genges)
        bot.register_next_step_handler(m, settings_genre)

    return


def settings_characters(m: Message):
    """
    Выбор и установка персонажа
    """
    global db_conn, mu_genges, user_data
    user_id = m.from_user.id
    check_user(m)
    genre = user_data[user_id]['genre']
    characters = list(Settings[genre]['characters'])
    entourages = list(Settings[genre]['entourages'])

    mu_characters = ReplyKeyboardMarkup(
        row_width=2,
        resize_keyboard=True)
    mu_characters.add(*characters)

    mu_entourages = ReplyKeyboardMarkup(
        row_width=2,
        resize_keyboard=True)
    mu_entourages.add(*entourages)

    if m.text in characters:
        user_data[user_id]['character'] = m.text
        bot.send_message(
            user_id,
            'Теперь выбери антураж',
            parse_mode="HTML",
            reply_markup=mu_entourages)
        bot.register_next_step_handler(m, settings_entourages)
    else:
        bot.send_message(
            user_id,
            'Выбери персонажа из списка!',
            parse_mode="HTML",
            reply_markup=mu_characters)
        bot.register_next_step_handler(m, settings_characters)

    return


def settings_entourages(m: Message):
    """
    Выбор и установка антуража
    """
    global db_conn, mu_genges, user_data
    user_id = m.from_user.id
    check_user(m)
    genre = user_data[user_id]['genre']
    entourages = list(Settings[genre]['entourages'])

    mu_entourages = ReplyKeyboardMarkup(
        row_width=2,
        resize_keyboard=True)
    mu_entourages.add(*entourages)

    if m.text in entourages:
        user_data[user_id]['entourage'] = m.text
        bot.send_message(
            user_id,
            'Отлично, полный набор настроек!\n\n'
            f'Жанр: <b>{user_data[user_id]['genre']}</b>\n'
            f'Персонаж: <b>{user_data[user_id]['character']}</b>\n'
            f'Антураж: <b>{user_data[user_id]['entourage']}</b>\n\n'
            'Пора генерить сценарий! /generate\n'
            '(Помни про ограничения сессий и токенов)',
            parse_mode="HTML",
            reply_markup=hideKeyboard)
        return
    else:
        bot.send_message(
            user_id,
            'Выбери из списка!',
            parse_mode="HTML",
            reply_markup=mu_entourages)
        bot.register_next_step_handler(m, settings_entourages)

    return


@bot.message_handler(commands=['generate'])
def handle_generate(m: Message):
    """
    Обработчик команды /generate - приступить к новой сессии
    """
    global db_conn, user_data, MAX_TOKENS_IN_SESSION
    user_id = m.from_user.id
    check_user(m)

    # Нельзя больше заданного количества пользователей
    if is_limit_users(db_conn):
        logging.warning(f"MAX_USERS limit exceeded, user_id: {user_id}")
        bot.send_message(
            user_id,
            '<b>Превышено количество пользователей бота!</b>\n'
            'Для вас доступен только просмотр статистики токенов: /tokens',
            parse_mode="HTML",
            reply_markup=hideKeyboard)
        return False

    # Нельзя больше заданного количества сессий на пользователя
    if is_limit_sessions(db_conn, user_id):
        logging.warning(f"MAX_SESSIONS limit exceeded, user_id: {user_id}")
        bot.send_message(
            user_id,
            '<b>Превышено количество сессий на одного пользователя!</b>\n'
            'Для вас доступен только просмотр статистики токенов: /tokens',
            parse_mode="HTML",
            reply_markup=hideKeyboard)
        return False

    if ('genre' not in user_data[user_id]
            or 'character' not in user_data[user_id]
            or 'entourage' not in user_data[user_id]):
        bot.send_message(
            user_id,
            'Для начала новой сессии перейди в настройки: /settings\n'
            'Там выбери сначала жанр, потом персонажа, потом антураж.',
            parse_mode="HTML",
            reply_markup=hideKeyboard)
    else:
        bot.send_message(
            user_id,
            f'Жанр: <b>{user_data[user_id]['genre']}</b>\n'
            f'Персонаж: <b>{user_data[user_id]['character']}</b>\n'
            f'Антураж: <b>{user_data[user_id]['entourage']}</b>\n\n'
            f''
            f'Ограничение токенов в этой сессии: {MAX_TOKENS_IN_SESSION}',
            parse_mode="HTML",
            reply_markup=hideKeyboard)

        session_id = create_user(db_conn, user_data[user_id])

        if session_id:
            user_data[user_id]['session_id'] = session_id
            logging.warning(f"New session id={session_id} "
                            f"has been created: user_id={user_id}")

            user_data[user_id]['collection'] = []
            bot.send_message(
                user_id,
                'Введи начало задачи (одно-два предложения). '
                'Бот-сценарист продолжит сюжет. Потом снова ты.\n\n'
                'Когда надоест - напиши: <b>The end</b>',
                parse_mode="HTML",
                reply_markup=mu_generate)
            bot.register_next_step_handler(m, handle_ask_gpt)

        else:
            logging.error(f"Cannot create new session: user_id={user_id}")
            bot.send_message(
                user_id,
                '<b>Не получилось создать новую сессию!\n'
                'Общение с GPT невозможно без этого.</b>',
                parse_mode="HTML",
                reply_markup=hideKeyboard)
            return False


# @bot.message_handler(content_types=["text"])
def handle_ask_gpt(m: Message):
    """
    Генерация сценария
    """
    global user_data, db_conn
    user_id = m.from_user.id
    check_user(m)

    prompt_user_prefix = ("Продолжи описание, но не пиши никакой "
                          "пояснительный текст от себя: ")

    # Если попросил остановить генерацию
    if m.text.lower() == 'the end':
        full_story = ""
        for row in user_data[user_id]['collection']:
            if row['role'] == 'system':
                continue
            full_story += row['content'].replace(prompt_user_prefix, "") + " "
        insert_full_story(db_conn, user_data[user_id], full_story)

        user_data[user_id]['collection'].clear()
        user_data[user_id]['genre'] = ""
        user_data[user_id]['character'] = ""
        user_data[user_id]['entourage'] = ""
        bot.send_message(
            user_id,
            f'<b>The end? Так быстро? ну ок...</b>\n\n'
            f'Вот итоговый текст, получился с помощью бота:\n\n'
            f'<i>{full_story}</i>\n\n'
            f'Попробуй другие настройки для нового сценария! /settings',
            parse_mode="HTML",
            reply_markup=hideKeyboard)
        bot.register_next_step_handler(m, handle_settings)
        return False

    # Системный промт этой сессии добавляем в пустую коллекцию
    if not len(user_data[user_id]['collection']):
        prompt_system = create_system_prompt(user_data[user_id])

        t_system = count_tokens(prompt_system)
        # FAKE
        # t_system = 90
        insert_tokenizer_info(db_conn, user_data[user_id],
                              prompt_system, t_system)
        logging.warning(f"Count tokens: user={user_id}, t_system={t_system}")
        user_data[user_id]['collection'].append(
            {
                "role": "system",
                "content": prompt_system,
            }
        )
        logging.info("Adding system prompt")
        insert_prompt(db_conn,
                      user_data[user_id],
                      "system",
                      prompt_system,
                      t_system)

    # Обрабатываем сообщение от пользователя
    # bot.send_message(
    #     user_id,
    #     'Сейчас спрошу, сколько это токенов...',
    #     parse_mode="HTML",
    #     reply_markup=hideKeyboard)

    prompt_user = prompt_user_prefix + m.text
    t = count_tokens(prompt_user)
    # FAKE:
    # t = 10
    insert_tokenizer_info(db_conn, user_data[user_id],
                          prompt_user, t)
    logging.warning(
        f"Count tokens: user={user_id}, t={t}, content={prompt_user}")

    # Если в сессии не хватает токенов, то извиниться.
    if is_limit_tokens_in_session(db_conn, user_data[user_id], t):
        bot.send_message(
            user_id,
            f'<b>ОШИБКА</b>\n'
            f'Токенайзер насчитал токенов (FAKE): <b>{t}</b>\n'
            f'Это больше, чем осталось токенов в сессии. '
            f'Попробуйте более короткий запрос.',
            parse_mode="HTML",
            reply_markup=mu_generate)
        logging.warning(f"Not enough tokens ({t}): user_id={user_id}")
        bot.register_next_step_handler(m, handle_ask_gpt)
        return

    # Если токенов в сессии хватает, то:
    # Запрос пользователя добавляем в коллекцию
    user_data[user_id]['collection'].append(
        {
            "role": "user",
            "content": prompt_user,
        }
    )
    logging.info("Adding user prompt")
    insert_prompt(db_conn,
                  user_data[user_id],
                  "user",
                  prompt_user,
                  t)

    res_gpt = ask_gpt(user_data[user_id])
    print(res_gpt)
    t_res = count_tokens(res_gpt)
    insert_tokenizer_info(db_conn, user_data[user_id],
                          res_gpt, t_res)
    user_data[user_id]['collection'].append(
        {
            "role": "assistant",
            "content": res_gpt,
        }
    )
    logging.info("Adding user prompt")
    insert_prompt(db_conn,
                  user_data[user_id],
                  "assistant",
                  res_gpt,
                  t_res)

    bot.send_message(
        user_id,
        f'<b>Ответ от GPT</b>:\n\n'
        f'{res_gpt}',
        parse_mode="HTML",
        reply_markup=mu_generate)
    bot.register_next_step_handler(m, handle_ask_gpt)


# Запуск бота
bot.infinity_polling()

# Закрывайте за собой все файлы и БД
db_conn.close()
