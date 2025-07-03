import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)


class Settings:
    # Bot configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    MINI_APP_URL = 'https://daha-git.vercel.app/'

    # API configuration
    USER_DATA_API_ENDPOINT = os.getenv("USER_DATA_API_ENDPOINT") or 'http://82.202.138.172:8000/api/users'
    API_TOKEN = os.getenv("API_TOKEN")

    # Admin configuration
    ADMIN_USER_IDS = [int(x) for x in os.getenv("ADMIN_USER_IDS", "").split(",") if x.strip()]

    @classmethod
    def validate(cls):
        """Проверяет обязательные настройки"""
        if not cls.BOT_TOKEN:
            raise ValueError("Ошибка: BOT_TOKEN не установлен в файле .env или в переменных окружения.")
        if not cls.WEBHOOK_URL:
            raise ValueError("Ошибка: WEBHOOK_URL не установлен в файле .env или в переменных окружения.")
        if not cls.MINI_APP_URL:
            raise ValueError("Ошибка: MINI_APP_URL не установлен в файле .env или в переменных окружения.")


settings = Settings()


class APIConfig:
    """Конфигурация для API клиента"""

    def __init__(self):
        self.BASE_URL = 'http://82.202.138.172:8000'
        self.API_KEY = 'key'
        self.TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))
        self.DEFAULT_LIMIT = int(os.getenv('API_DEFAULT_LIMIT', '100'))
        self.MAX_LIMIT = int(os.getenv('API_MAX_LIMIT', '100'))

    def validate(self) -> bool:
        """Валидация конфигурации"""
        if not self.BASE_URL:
            raise ValueError("Переменная окружения API_BASE_URL обязательна")
        return True


config = APIConfig()

# Маппинг фильтров бота на параметры API
FILTER_MAPPING = {
    'subjects': 'category_id',  # Предметы -> категории
    'difficulty': 'level',  # Сложность -> уровень
    'grade': 'grade_id'  # Класс -> ID класса
}

# Маппинг значений фильтров
SUBJECT_TO_CATEGORY = {
    'Искусственный интеллект': 1,
    'Программирование': 2,
    'Информационная безопасность': 3,
    'Робототехника': 4,
    'Предпринимательство': 5,
    'Финансовая грамотность': 6,
    'Наука': 7,
}

DIFFICULTY_TO_LEVEL = {
    'Начальный': 'BEGINNER',
    'Средний': 'INTERMEDIATE',
    'Продвинутый': 'ADVANCED',
}

GRADE_TO_ID = {
    7: 1,
    8: 2,
    9: 3,
    10: 4,
    11: 5
}
