from typing import Dict, Set, List, Any, Optional
import logging
from api.client import CourseAPIClient, APIError
from config.settings import config, SUBJECT_TO_CATEGORY, DIFFICULTY_TO_LEVEL, GRADE_TO_ID

logger = logging.getLogger(__name__)


class CourseService:
    """Сервис для работы с курсами"""

    def __init__(self):
        """Инициализация сервиса"""
        self.api_client = None
        try:
            config.validate()
            self.api_client = CourseAPIClient(config.BASE_URL, config.API_KEY)
            logger.info("CourseService успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации CourseService: {e}")
            # Не поднимаем исключение, чтобы сервис мог работать в режиме fallback

    def _is_api_available(self) -> bool:
        """Проверяет доступность API клиента"""
        return self.api_client is not None

    def _convert_filters_to_api_params(self, filters: Dict[str, Set]) -> Dict[str, Any]:
        """
        Конвертирует фильтры бота в параметры API

        Args:
            filters: Фильтры пользователя из бота

        Returns:
            Параметры для API запроса
        """
        api_params = {}

        # Конвертируем предметы в category_id
        if filters.get("subjects"):
            subjects = filters["subjects"]
            # Берем первый предмет для простоты (можно расширить логику)
            for subject in subjects:
                if subject in SUBJECT_TO_CATEGORY:
                    api_params['category_id'] = SUBJECT_TO_CATEGORY[subject]
                    break

        # Конвертируем сложность в level
        if filters.get("difficulty"):
            difficulties = filters["difficulty"]
            # Берем первую сложность
            for difficulty in difficulties:
                if difficulty in DIFFICULTY_TO_LEVEL:
                    api_params['level'] = DIFFICULTY_TO_LEVEL[difficulty]
                    break

        # Конвертируем класс в grade_id
        if filters.get("grade"):
            grades = filters["grade"]
            # Берем первый класс
            for grade in grades:
                if isinstance(grade, str) and grade.isdigit():
                    grade = int(grade)
                if grade in GRADE_TO_ID:
                    api_params['grade_id'] = GRADE_TO_ID[grade]
                    break

        return api_params

    def _filter_courses_locally(self, courses: List[Dict], filters: Dict[str, Set]) -> List[Dict]:
        """
        Дополнительная фильтрация курсов на стороне клиента

        Args:
            courses: Список курсов от API
            filters: Фильтры пользователя

        Returns:
            Отфильтрованный список курсов
        """
        if not courses:
            return []

        results = []

        for course in courses:
            # Проверяем предметы (если API не поддерживает множественную фильтрацию)
            subjects_match = True
            if filters.get("subjects"):
                course_subjects = course.get("subjects", [])
                subjects_match = any(
                    subject in course_subjects
                    for subject in filters["subjects"]
                )

            # Проверяем сложность
            difficulty_match = True
            if filters.get("difficulty"):
                course_difficulty = course.get("difficulty", "")
                # Конвертируем обратно из API формата в формат бота
                api_to_bot_difficulty = {v: k for k, v in DIFFICULTY_TO_LEVEL.items()}
                bot_difficulty = api_to_bot_difficulty.get(course_difficulty, course_difficulty)
                difficulty_match = bot_difficulty in filters["difficulty"]

            # Проверяем класс
            grade_match = True
            if filters.get("grade"):
                course_grades = course.get("grade", [])
                user_grades = set()
                for grade in filters["grade"]:
                    if isinstance(grade, str) and grade.isdigit():
                        user_grades.add(int(grade))
                    elif isinstance(grade, int):
                        user_grades.add(grade)

                grade_match = any(
                    grade in course_grades
                    for grade in user_grades
                )

            if subjects_match and difficulty_match and grade_match:
                results.append(course)

        return results

    def _get_fallback_courses(self, filters: Dict[str, Set]) -> List[Dict[str, Any]]:
        """
        Fallback метод для получения курсов из mock данных

        Args:
            filters: Фильтры пользователя

        Returns:
            Список курсов из mock данных
        """
        # Импортируем mock данные как fallback
        try:
            from data.mock_courses import COURSES
            return self._filter_courses_locally(COURSES, filters)
        except ImportError:
            logger.warning("Mock данные курсов не найдены")
            return []

    def filter_courses(self, filters: Dict[str, Set]) -> List[Dict[str, Any]]:
        """
        Фильтрует курсы по заданным критериям через API

        Args:
            filters: Словарь с фильтрами пользователя

        Returns:
            Список отфильтрованных курсов
        """
        # Проверяем доступность API
        if not self._is_api_available():
            logger.warning("API недоступен, используем fallback данные")
            return self._get_fallback_courses(filters)

        try:
            # Конвертируем фильтры в параметры API
            api_params = self._convert_filters_to_api_params(filters)

            logger.info(f"Запрос курсов с параметрами: {api_params}")

            # Получаем курсы через API
            if api_params:
                # Если есть параметры для API, используем их
                result = self.api_client.get_courses(**api_params)
                courses = result['courses']
            else:
                # Если нет параметров API, получаем все курсы
                courses = self.api_client.get_all_courses()

            # Дополнительная фильтрация на стороне клиента
            filtered_courses = self._filter_courses_locally(courses, filters)

            logger.info(f"Найдено {len(filtered_courses)} курсов после фильтрации")

            return filtered_courses

        except APIError as e:
            logger.error(f"Ошибка API при фильтрации курсов: {e}")
            # Возвращаем fallback данные в случае ошибки API
            return self._get_fallback_courses(filters)
        except Exception as e:
            logger.error(f"Неожиданная ошибка при фильтрации курсов: {e}")
            # Возвращаем fallback данные в случае любой ошибки
            return self._get_fallback_courses(filters)

    def get_course_by_id(self, course_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение курса по ID

        Args:
            course_id: ID курса

        Returns:
            Данные курса или None
        """
        if not self._is_api_available():
            logger.warning("API недоступен для получения курса по ID")
            return None

        try:
            # Для получения конкретного курса нужно будет расширить API клиент
            # Пока получаем все курсы и ищем нужный
            all_courses = self.api_client.get_all_courses()
            for course in all_courses:
                if course.get('id') == course_id:
                    return course
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении курса {course_id}: {e}")
            return None


# Глобальный экземпляр сервиса
course_service = CourseService()
