#!/usr/bin/env python3.12
# -*- coding: utf-8 -*-
"""2024-03-22 Fil - Future code Yandex.Practicum
AI-bot: Scenario generator
README.md for more

SQLite DB functions
"""
from time import time_ns
import logging
import sqlite3
from config import (
    MAX_PROJECT_TOKENS,  # макс. количество токенов на весь проект
    MAX_USERS,  # макс. количество пользователей на весь проект
    MAX_SESSIONS,  # макс. количество сессий у пользователя
    MAX_TOKENS_IN_SESSION  # макс. количество токенов за сессию пользователя
)


def create_db(db_file):
    db_connection = sqlite3.connect(db_file, check_same_thread=False)
    cursor = db_connection.cursor()

    # Создаем таблицу Sessions
    # Здесь для статистики хранятся настройки на момент запроса
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS Sessions ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'user_id INTEGER, '
        'genre TEXT, '
        'character TEXT, '
        'entourage TEXT, '
        't_start INT, '
        'task TEXT, '
        'answer TEXT'
        ')'
    )

    # Создаем таблицу Prompts
    # Словарь для хранения истории диалога пользователя и GPT
    # Он же хранится в user_data[user_id]['collection']
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS Prompts ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'user_id INTEGER, '
        'session_id INTEGER, '
        'role TEXT, '
        'content TEXT, '
        'tokens INT'
        ')'
    )

    # Создаем таблицу Tokenizer
    # Храним обращения к токенайзеру
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS Tokenizer ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT, '
        'user_id INTEGER, '
        'session_id INTEGER, '
        't_start INTEGER, '
        'content TEXT, '
        'tokens INT'
        ')'
    )

    # Создаем таблицу Full_Stories
    # Храним итоговые сочинения для смеха
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS Full_Stories ('
        'id INTEGER PRIMARY KEY, '
        'user_id INTEGER, '
        'session_id INTEGER, '
        'content TEXT'
        ')'
    )

    return db_connection


def is_limit_users(db_connection):
    """
    Не превысили количество пользователей?
    """
    global MAX_USERS

    cursor = db_connection.cursor()
    query = 'SELECT COUNT(DISTINCT user_id) FROM Sessions;'
    cursor.execute(query)
    res = cursor.fetchone()
    if res is None:
        return False
    print(f"is_limit_users {res[0]}")
    logging.warning(f"There are {res[0]} distinct users in Sessions")

    return res[0] >= MAX_USERS


def is_limit_sessions(db_connection, user_id):
    """
    Не превысили количество сессий?
    """
    global MAX_SESSIONS

    cursor = db_connection.cursor()
    query = 'SELECT COUNT(id) FROM Sessions WHERE user_id = ?;'
    cursor.execute(query, (user_id,))
    res = cursor.fetchone()
    if res is None:
        return False
    print(f"is_limit_sessions {res[0]}")
    logging.warning(f"User {user_id} has {res[0]} session(s)")

    return res[0] >= MAX_SESSIONS


def get_tokens_in_session(db_connection, user):
    """
    Сколько уже потрачено токенов в текущей сессии пользователя
    """
    cursor = db_connection.cursor()
    query = ('SELECT tokens FROM Prompts '
             'WHERE user_id = ? '
             'AND session_id = ? '
             'ORDER BY id DESC LIMIT 1;')

    try:
        cursor.execute(query, (user['user_id'], user['session_id'],))
        res = cursor.fetchone()

        # Считаем, что пустой результат - это отсутствие сессии, а не ошибка
        if res is None:
            print(f"get_tokens_in_session None = 0")
            logging.warning(f"get_tokens_in_session None = 0")
            return 0
        else:
            print(f"is_limit_tokens_in_session {res[0]}")
            logging.warning(f"User {user['user_id']} "
                            f"has {res[0]} tokens in current session")
            return res[0]
    except Exception as e:
        return 0


def is_limit_tokens_in_session(db_connection, user, t):
    """
    Можно ли ещё t токенов потратить?
    """
    global MAX_TOKENS_IN_SESSION

    return (MAX_TOKENS_IN_SESSION <=
            (get_tokens_in_session(db_connection, user) + t))


def create_user(db_connection, user):
    """
    Функция для добавления нового пользователя в базу данных.
    """
    cursor = db_connection.cursor()
    logging.warning(f"Insert session for user_id={user['user_id']}:... ")
    data = (
        user['user_id'],
        user['genre'],
        user['character'],
        user['entourage'],
        time_ns()
    )

    try:
        cursor.execute('INSERT INTO Sessions '
                       '(user_id, genre, character, entourage, t_start) '
                       'VALUES (?, ?, ?, ?, ?);',
                       data)
        db_connection.commit()
        logging.warning(f"... OK id={cursor.lastrowid}")
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        logging.warning("... Error")
        return False


def insert_tokenizer_info(db_connection, user, content, tokens):
    """
    Функция для добавления нового пользователя в базу данных.
    """
    cursor = db_connection.cursor()
    logging.warning(f"Asking tokenizer for user_id={user['user_id']}... ")
    data = (
        user['user_id'],
        user['session_id'],
        time_ns(),
        content,
        tokens
    )

    try:
        cursor.execute('INSERT INTO Tokenizer '
                       '(user_id, session_id, t_start, content, tokens) '
                       'VALUES (?, ?, ?, ?, ?);',
                       data)
        db_connection.commit()
        logging.warning(f"... OK id={cursor.lastrowid}")
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        logging.warning("... Error")
        return False


def insert_full_story(db_connection, user, content):
    """
    Функция для добавления итогового сочинения
    """
    cursor = db_connection.cursor()
    logging.warning(f"Saving full story of user_id={user['user_id']}... ")
    data = (
        user['user_id'],
        user['session_id'],
        content,
    )

    try:
        cursor.execute('INSERT INTO Full_Stories '
                       '(user_id, session_id, content) '
                       'VALUES (?, ?, ?);',
                       data)
        db_connection.commit()
        logging.warning(f"... OK id={cursor.lastrowid}")
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        logging.warning("... Error")
        return False


def get_full_story(db_connection):
    """
    Вернуть случайную историю, если есть
    """
    cursor = db_connection.cursor()
    query = ('SELECT content FROM Full_Stories '
             'ORDER BY RANDOM() LIMIT 1;')

    cursor.execute(query)
    res = cursor.fetchone()

    # Считаем, что пустой результат - это отсутствие сессии, а не ошибка
    if res is None:
        logging.warning(f"get_full_story None = 0")
        return "Нет готовых сочинений"
    else:
        logging.warning(f"Get Full Story")
        return res[0]


def insert_prompt(db_connection, user, role, content, tokens):
    """
    Функция для добавления нового промта в БД - для всех ролей
    Значение tokens - накопительная сумма для этой сессии этого пользователя!
    """
    cursor = db_connection.cursor()
    # В tokens накапливающуюся сумму, поэтому ищем последнюю известную
    logging.warning(f"Finding the last prompt session_id={user['session_id']}")
    tokens_prev = get_tokens_in_session(db_connection, user)

    logging.warning(f"Adding prompt user_id={user['user_id']}, role={role}... ")
    data = (
        user['user_id'],
        user['session_id'],
        role,
        content,
        tokens + tokens_prev
    )

    try:
        cursor.execute('INSERT INTO Prompts '
                       '(user_id, session_id, role, content, tokens) '
                       'VALUES (?, ?, ?, ?, ?);',
                       data)
        db_connection.commit()
        logging.warning(f"... OK id={cursor.lastrowid}")
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        logging.warning("... Error")
        return False


def get_tokens_info(db_connection, user):
    """
    Информация о токенах для пользователя
    """
    result = []

    result.append("\nКОНСТАНТЫ:")
    result.append(f"MAX_PROJECT_TOKENS = {MAX_PROJECT_TOKENS} - "
                  f"макс. количество токенов на весь проект")
    result.append(f"MAX_USERS = {MAX_USERS} - "
                  f"макс. количество пользователей на весь проект")
    result.append(f"MAX_SESSIONS = {MAX_SESSIONS} - "
                  f"макс. количество сессий у пользователя")
    result.append(f"MAX_TOKENS_IN_SESSION = {MAX_TOKENS_IN_SESSION} - "
                  f"макс. количество токенов за сессию пользователя")

    result.append("\nПЕРЕМЕННЫЕ (твои):")

    r = get_tokens_in_session(db_connection, user)
    result.append(f"{r} - токенов в твоей текущей сессии")

    cursor = db_connection.cursor()
    query = 'SELECT COUNT(id) FROM Sessions WHERE user_id = ?;'
    cursor.execute(query, (user['user_id'],))
    res = cursor.fetchone()
    if res is None:
        r = 0
    else:
        r = res[0]
    result.append(f"{r} - сессий у тебя")

    result.append("\nПЕРЕМЕННЫЕ (общие):")

    cursor = db_connection.cursor()
    query = 'SELECT COUNT(DISTINCT user_id) FROM Sessions WHERE 1;'
    cursor.execute(query)
    res = cursor.fetchone()
    if res is None:
        r = 0
    else:
        r = res[0]
    result.append(f"{r} - всего пользователей")

    cursor = db_connection.cursor()
    query = 'SELECT COUNT(id) FROM Sessions WHERE 1;'
    cursor.execute(query)
    res = cursor.fetchone()
    if res is None:
        r = 0
    else:
        r = res[0]
    result.append(f"{r} - всего сессий у всех пользователей")

    return result
