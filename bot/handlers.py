import logging
from telegram import Update
from telegram.ext import ContextTypes


from bot.keyboards import BotKeyboards
from bot.messages import *
from data.user_storage import user_storage
from data.courses import CourseFilter
from utils.packager import Packager
from config.settings import settings
from api.client import CourseAPIClient

logger = logging.getLogger(__name__)

# Инициализируем упаковщик
packager = Packager(api_endpoint=settings.USER_DATA_API_ENDPOINT)


class BotHandlers:
    """Класс с обработчиками команд бота"""

    @staticmethod
    async def package_user_data_async(user_id: int):
        """Асинхронная функция для упаковки данных конкретного пользователя"""
        try:
            user_data = user_storage.get_user(user_id)
            if not user_data:
                logger.warning(f"Пользователь {user_id} не найден для упаковки")
                raise ValueError(ERROR_USER_NOT_FOUND_MESSAGE)

            user_data_to_package = {user_id: user_data}

            results = packager.package_and_send(
                user_data_to_package,
                save_local=True,
                send_api=bool(settings.USER_DATA_API_ENDPOINT),
            )

            logger.info(f"Упаковка данных пользователя {user_id} завершена: "
                        f"Локально: {'✅' if results['local_export']['success'] else '❌'}, "
                        f"API: {'✅' if results['api_export']['success'] else '❌'}")

            return results

        except Exception as e:
            logger.error(f"Ошибка при упаковке данных пользователя {user_id}: {e}")
            raise

    @staticmethod
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        try:
            user_id = update.effective_user.id
            username = update.effective_user.username

            user_storage.create_or_update_user(user_id, username)

            keyboard = BotKeyboards.get_main_menu_keyboard()
            await update.message.reply_text(WELCOME_MESSAGE, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Ошибка в команде /start: {e}")
            await update.message.reply_text(ERROR_GENERAL_MESSAGE)

    @staticmethod
    async def set_filters_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /set_filters"""
        try:
            user_id = update.effective_user.id
            username = update.effective_user.username

            user_storage.create_or_update_user(user_id, username)

            keyboard = BotKeyboards.get_filter_selection_keyboard()
            await update.message.reply_text(FILTER_SELECTION_MESSAGE, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Ошибка в команде /set_filters: {e}")
            await update.message.reply_text(ERROR_GENERAL_MESSAGE)

    @staticmethod
    async def website_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /website"""
        try:
            keyboard = BotKeyboards.get_website_keyboard()
            await update.message.reply_text(WEBSITE_MESSAGE, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Ошибка в команде /website: {e}")
            await update.message.reply_text(ERROR_GENERAL_MESSAGE)

    @staticmethod
    async def manual_package_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /package для ручной упаковки"""
        try:
            if update.effective_user.id not in settings.ADMIN_USER_IDS:
                await update.message.reply_text(NO_ADMIN_RIGHTS_MESSAGE)
                return

            all_users = user_storage.get_all_users()
            if not all_users:
                await update.message.reply_text(NO_DATA_TO_PACKAGE_MESSAGE)
                return

            results = packager.package_and_send(
                all_users,
                save_local=True,
                send_api=bool(settings.USER_DATA_API_ENDPOINT),
                headers={"Authorization": f"Bearer {settings.API_TOKEN}"} if settings.API_TOKEN else None
            )

            message = format_package_result_message(results, len(all_users))
            await update.message.reply_text(message)

        except Exception as e:
            logger.error(f"Ошибка в команде /package: {e}")
            error_message = ERROR_PACKAGING_MESSAGE.format(error=str(e))
            await update.message.reply_text(error_message)

    @staticmethod
    async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик нажатий на inline кнопки"""
        query = update.callback_query

        try:
            await query.answer()

            user_id = update.effective_user.id
            username = update.effective_user.username
            data = query.data

            # Создаем или обновляем пользователя
            user_storage.create_or_update_user(user_id, username)
            user_data = user_storage.get_user(user_id)

            if not user_data:
                await query.edit_message_text(ERROR_USER_NOT_FOUND_MESSAGE)
                return

            # Обработка меню фильтров
            if data in FILTER_MENUS:
                await BotHandlers._handle_filter_menu(query, data, user_data)

            # Обработка выбора опций фильтра
            elif data.startswith("select_"):
                await BotHandlers._handle_filter_selection(query, data, user_id)

            # Возврат к главному меню фильтров
            elif data == "back_to_main_filters":
                keyboard = BotKeyboards.get_filter_selection_keyboard()
                await query.edit_message_text(FILTER_SELECTION_MESSAGE, reply_markup=keyboard)

            # Сохранение фильтров и поиск курсов
            elif data == "save_all_filters":
                await BotHandlers._handle_save_filters(query, user_id)

            else:
                await query.edit_message_text(ERROR_INVALID_FILTER_MESSAGE)

        except Exception as e:
            logger.error(f"Ошибка в обработчике кнопок: {e}")
            try:
                await query.edit_message_text(ERROR_GENERAL_MESSAGE)
            except:
                # Если не можем отредактировать сообщение, отправляем новое
                await query.message.reply_text(ERROR_GENERAL_MESSAGE)

    @staticmethod
    async def _handle_filter_menu(query, data: str, user_data: dict):
        """Обработка меню фильтров"""
        try:
            menu_title, _ = FILTER_MENUS[data]
            current_filter_key = data.split('_')[1]
            current_filters = user_data.get(current_filter_key, set())

            keyboard = BotKeyboards.get_filter_options_keyboard(current_filter_key, current_filters)
            await query.edit_message_text(text=menu_title, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Ошибка в обработке меню фильтров: {e}")
            await query.edit_message_text(ERROR_FILTER_UPDATE_MESSAGE)

    @staticmethod
    async def _handle_filter_selection(query, data: str, user_id: int):
        """Обработка выбора опций фильтра"""
        try:
            _, filter_key, value = data.split("_", 2)
            user_storage.update_user_filter(user_id, filter_key, value)

            # Обновляем клавиатуру
            updated_user_data = user_storage.get_user(user_id)
            if not updated_user_data:
                await query.edit_message_text(ERROR_USER_NOT_FOUND_MESSAGE)
                return

            current_filters = updated_user_data.get(filter_key, set())

            if f"filter_{filter_key}" not in FILTER_MENUS:
                await query.edit_message_text(ERROR_INVALID_FILTER_MESSAGE)
                return

            menu_title, _ = FILTER_MENUS[f"filter_{filter_key}"]
            keyboard = BotKeyboards.get_filter_options_keyboard(filter_key, current_filters)
            await query.edit_message_text(text=menu_title, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Ошибка в обработке выбора фильтра: {e}")
            await query.edit_message_text(ERROR_FILTER_UPDATE_MESSAGE)

    @staticmethod
    async def _handle_save_filters(query, user_id: int):
        """Обработка сохранения фильтров и поиска курсов"""
        try:
            user_data = user_storage.get_user(user_id)

            filters = dict(subjects = user_data.get("subjects"), difficulty = user_data.get("difficulty"), grade = user_data.get("grade"))
            if not user_data:
                await query.edit_message_text(ERROR_USER_NOT_FOUND_MESSAGE)
                return

            # Проверяем, выбрал ли пользователь хотя бы один фильтр
            if not any(filters):
                await query.edit_message_text(WARNING_EMPTY_FILTER_MESSAGE)
                return

            await query.edit_message_text(SEARCHING_COURSES_MESSAGE)

            # Упаковываем данные пользователя
            logger.info(f"Пользователь {user_id} сохранил фильтры, запускаем упаковку данных")
            try:
                await BotHandlers.package_user_data_async(user_id)
            except Exception as package_error:
                logger.error(f"Ошибка упаковки для пользователя {user_id}: {package_error}")
                # Продолжаем поиск курсов даже если упаковка не удалась

            # Ищем курсы
            try:
                filtered_courses = CourseFilter.filter_courses(user_data, filters)

                if filtered_courses:
                    # Отправляем найденные курсы
                    for course in filtered_courses:
                        course_text = CourseFilter.format_course_message(course)
                        keyboard = BotKeyboards.get_course_keyboard(course['link'])
                        await query.message.reply_text(course_text, reply_markup=keyboard)

                    await query.edit_message_text(COURSES_FOUND_MESSAGE)
                else:
                    await query.edit_message_text(WARNING_NO_COURSES_MESSAGE)

            except Exception as search_error:
                logger.error(f"Ошибка поиска курсов: {search_error}")
                await query.edit_message_text(ERROR_COURSE_SEARCH_MESSAGE)

        except Exception as e:
            logger.error(f"Ошибка в сохранении фильтров: {e}")
            await query.edit_message_text(ERROR_SAVE_FILTERS_MESSAGE)





