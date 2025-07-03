from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class UserStorage:
    """Класс для управления данными пользователей"""

    def __init__(self):
        self.user_filters: Dict[int, Dict[str, Any]] = {}

    def create_or_update_user(self, user_id: int, username: str = None) -> Dict[str, Any]:
        """
        Создает или обновляет данные пользователя

        Args:
            user_id: ID пользователя Telegram
            username: Имя пользователя Telegram

        Returns:
            Данные пользователя
        """
        username = username or "Не указан"

        if user_id not in self.user_filters:
            self.user_filters[user_id] = {
                "username": username,
                "user_id": user_id,
                "subjects": set(),
                "difficulty": set(),
                "grade": set(),
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
            logger.info(f"Создан новый пользователь: {user_id}")
        else:
            # Обновляем существующего пользователя
            self.user_filters[user_id]["username"] = username
            self.user_filters[user_id]["last_updated"] = datetime.now().isoformat()

        return self.user_filters[user_id]

    def get_user(self, user_id: int) -> Dict[str, Any]:
        """
        Получает данные пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Данные пользователя или None
        """
        return self.user_filters.get(user_id)

    def update_user_filter(self, user_id: int, filter_key: str, value: str) -> None:
        """
        Обновляет фильтр пользователя

        Args:
            user_id: ID пользователя
            filter_key: Ключ фильтра (subjects, difficulty, grade)
            value: Значение для добавления/удаления
        """
        if user_id in self.user_filters:
            user_filter_set = self.user_filters[user_id].setdefault(filter_key, set())

            if value in user_filter_set:
                user_filter_set.remove(value)
                logger.info(f"Удален фильтр {filter_key}:{value} для пользователя {user_id}")
            else:
                user_filter_set.add(value)
                logger.info(f"Добавлен фильтр {filter_key}:{value} для пользователя {user_id}")

            self.user_filters[user_id]["last_updated"] = datetime.now().isoformat()

    def get_all_users(self) -> Dict[int, Dict[str, Any]]:
        """
        Получает данные всех пользователей

        Returns:
            Словарь со всеми пользователями
        """
        return self.user_filters.copy()

    def get_user_count(self) -> int:
        """
        Получает количество пользователей

        Returns:
            Количество пользователей
        """
        return len(self.user_filters)


# Глобальный экземпляр хранилища пользователей
user_storage = UserStorage()
