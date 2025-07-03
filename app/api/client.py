import requests
import json
import os
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CourseAPIClient:
    """
    Клиент для работы с API курсов
    """

    def __init__(self, base_url: str, api_key: str):
        """
        Инициализация API клиента

        Args:
            base_url: Базовый URL API
            api_key: API ключ для аутентификации
        """
        logger.info(f"base_url = {base_url}, api_key = {api_key}")
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'DREAM apikey="{api_key}"',
            'Content-Type': 'application/json',
            'User-Agent': 'DAHA-Bot/1.0'
        })

    def get_courses(self,
                    category_id: Optional[int] = None,
                    level: Optional[str] = None,
                    grade_id: Optional[int] = None,
                    skip: int = 0,
                    limit: int = 100) -> Dict[str, Any]:
        """
        Получение курсов с фильтрацией

        Args:
            category_id: ID категории
            level: Уровень сложности
            grade_id: ID класса
            skip: Количество пропускаемых записей
            limit: Максимальное количество записей

        Returns:
            Словарь с данными курсов
        """
        endpoint = f"{self.base_url}/api/courses/"

        # Формируем параметры запроса
        params = {}
        if category_id is not None:
            params['category_id'] = category_id
        if level is not None:
            params['level'] = level
        if grade_id is not None:
            params['grade_id'] = grade_id
        if skip > 0:
            params['skip'] = skip
        if limit != 100:
            params['limit'] = min(limit, 100)

        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()

            # Получаем общее количество из заголовка
            total_count = response.headers.get('X-Count', '0')
            courses_data = response.json()

            return {
                'courses': courses_data,
                'total_count': int(total_count),
                'returned_count': len(courses_data) if isinstance(courses_data, list) else 0,
                'skip': skip,
                'limit': limit
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка API запроса: {e}")
            raise APIError(f"Не удалось получить курсы: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            raise APIError(f"Неверный формат ответа API: {e}")

    def get_all_courses(self,
                        category_id: Optional[int] = None,
                        level: Optional[str] = None,
                        grade_id: Optional[int] = None,
                        batch_size: int = 100) -> List[Dict[str, Any]]:
        """
        Получение всех курсов с пагинацией

        Args:
            category_id: ID категории
            level: Уровень сложности
            grade_id: ID класса
            batch_size: Размер пакета для запроса

        Returns:
            Список всех курсов
        """
        all_courses = []
        skip = 0

        while True:
            try:
                result = self.get_courses(
                    category_id=category_id,
                    level=level,
                    grade_id=grade_id,
                    skip=skip,
                    limit=batch_size
                )

                courses = result['courses']
                if not courses:
                    break

                all_courses.extend(courses)

                # Проверяем, есть ли еще данные
                if len(courses) < batch_size:
                    break

                skip += batch_size

            except Exception as e:
                logger.error(f"Ошибка при получении пакета курсов: {e}")
                break

        return all_courses


class APIError(Exception):
    """Кастомное исключение для ошибок API"""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
