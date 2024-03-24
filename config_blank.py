#
# Для телеграм бота
TOKEN_SC = '7027815461:AAE6nBpvKUyAEMRJp61rxJQLFsAQmpqr654'

#
# Для ограничений токенов
MAX_PROJECT_TOKENS = 10000  # макс. количество токенов на весь проект
MAX_USERS = 5  # макс. количество пользователей на весь проект
MAX_SESSIONS = 5  # макс. количество сессий у пользователя
MAX_TOKENS_IN_SESSION = 777  # макс. количество токенов за сессию пользователя

#
# Для функции count_tokens
MAX_MODEL_TOKENS = 25  # запрос к токенизатору, мы же не просим генерировать?

#
# Для функции ask_gpt
MAX_ANSWER_TOKENS = 25  # Ограничить длину ответа GPT для экономии

#
# Для общения с Yandex.GPT
GPT_MODEL = 'yandexgpt-lite'
FOLDER_ID = ''
IAM_TOKEN = ''
