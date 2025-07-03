"""Шаблоны сообщений для бота"""

WELCOME_MESSAGE = """Добро пожаловать в DAHA Bot!

Доступные команды:
/start - Показать это сообщение
/set_filters - Установить предпочтения курсов
/website - Получить ссылку на наш сайт"""

WEBSITE_MESSAGE = """Ссылка: https://daha-git.vercel.app/ 

Вы также можете получить доступ к нашим услугам через мини-приложение ⬇️"""

FILTER_SELECTION_MESSAGE = "Пожалуйста, выберите фильтры:"

NO_FILTERS_MESSAGE = "Вы не выбрали ни одного фильтра."

SEARCHING_COURSES_MESSAGE = "Поиск курсов..."

COURSES_FOUND_MESSAGE = "Найдены курсы, соответствующие вашим критериям."

NO_COURSES_FOUND_MESSAGE = "Курсы, соответствующие вашим фильтрам, не найдены."

NO_ADMIN_RIGHTS_MESSAGE = "У вас нет прав для выполнения этой команды."

NO_DATA_TO_PACKAGE_MESSAGE = "Нет данных для упаковки."

# Сообщения об ошибках
ERROR_PACKAGING_MESSAGE = "Ошибка при упаковке: {error}"

ERROR_USER_NOT_FOUND_MESSAGE = "Пользователь не найден для упаковки."

ERROR_FILTER_UPDATE_MESSAGE = "Ошибка при обновлении фильтра."

ERROR_COURSE_SEARCH_MESSAGE = "Произошла ошибка при поиске курсов. Попробуйте позже."

ERROR_GENERAL_MESSAGE = "Произошла неожиданная ошибка. Попробуйте позже."

ERROR_API_CONNECTION_MESSAGE = "Ошибка подключения к серверу. Попробуйте позже."

ERROR_INVALID_FILTER_MESSAGE = "Неверный тип фильтра."

ERROR_SAVE_FILTERS_MESSAGE = "Ошибка при сохранении фильтров. Попробуйте еще раз."

# Сообщения об успехе
SUCCESS_FILTERS_SAVED_MESSAGE = "Фильтры успешно сохранены!"

SUCCESS_PACKAGE_COMPLETE_MESSAGE = "Упаковка данных завершена успешно."

# Предупреждающие сообщения
WARNING_NO_COURSES_MESSAGE = "К сожалению, курсы по вашим критериям не найдены. Попробуйте изменить фильтры."

WARNING_EMPTY_FILTER_MESSAGE = "Выберите хотя бы один параметр для поиска курсов."

# Меню фильтров
FILTER_MENUS = {
    "filter_subjects": (
        "Выберите предметы",
        {
            "Искусственный интеллект",
            "Робототехника",
            "Программирование",
            "Кибербезопасность",
            "Предпринимательство",
            "Финансовая грамотность",
            "Наука"
        }
    ),
    "filter_difficulty": (
        "Выберите сложность",
        ["Начальный", "Средний", "Продвинутый"]
    ),
    "filter_grade": (
        "Выберите класс(-ы)",
        ["7", "8", "9", "10", "11"]
    ),
}

def format_package_result_message(results: dict, user_count: int) -> str:
    """Форматирует сообщение о результатах упаковки"""
    return (
        f"Ручная упаковка завершена:\n"
        f"Локально: {'✅' if results['local_export']['success'] else '❌'}\n"
        f"API: {'✅' if results['api_export']['success'] else '❌'}\n"
        f"Всего пользователей: {user_count}"
    )

def format_error_message(error_type: str, details: str = None) -> str:
    """Форматирует сообщение об ошибке"""
    base_message = f"Ошибка: {error_type}"
    if details:
        return f"{base_message}\nДетали: {details}"
    return base_message

def format_user_info_message(username: str, user_id: int, filters_count: int) -> str:
    """Форматирует информационное сообщение о пользователе"""
    return (
        f"Пользователь: @{username}\n"
        f"ID: {user_id}\n"
        f"Активных фильтров: {filters_count}"
    )
