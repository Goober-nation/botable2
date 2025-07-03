# bot/handlers.py

import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboards import BotKeyboards
# FIX: Updated imports to use the correct snake_case constants
from bot.messages import (
    WELCOME_MESSAGE,
    FILTER_SELECTION_MESSAGE,
    WEBSITE_MESSAGE,
    NO_ADMIN_RIGHTS_MESSAGE,
    NO_DATA_TO_PACKAGE_MESSAGE,
    ERROR_PACKAGING_MESSAGE,
    ERROR_USER_NOT_FOUND_MESSAGE,
    ERROR_INVALID_FILTER_MESSAGE,
    ERROR_FILTER_UPDATE_MESSAGE,
    ERROR_GENERAL_MESSAGE,
    SEARCHING_COURSES_MESSAGE,
    WARNING_EMPTY_FILTER_MESSAGE,
    COURSES_FOUND_MESSAGE,
    WARNING_NO_COURSES_MESSAGE,
    ERROR_COURSE_SEARCH_MESSAGE,
    ERROR_SAVE_FILTERS_MESSAGE,
    format_package_result_message,
    FILTER_MENUS
)
from data.user_storage import user_storage
# FIX from previous request: Import the instance 'course_filter', not the class
from data.courses import course_filter, CourseFilter
from utils.packager import Packager
from config.settings import settings
from api.client import CourseAPIClient

logger = logging.getLogger(__name__)
packager = Packager(api_endpoint=settings.USER_DATA_API_ENDPOINT)

class BotHandlers:
    """
    Handles all interactions for the Telegram bot.
    """
    @staticmethod
    async def package_user_data_async(user_id: int):
        """Packages and sends data for a single user."""
        try:
            user_data = user_storage.get_user(user_id)
            if not user_data:
                logger.warning(f"User data not found for packaging: {user_id}")
                raise ValueError(ERROR_USER_NOT_FOUND_MESSAGE)

            user_data_to_package = {user_id: user_data}

            results = packager.package_and_send(
                user_data_to_package,
                save_local=True,
                send_api=bool(settings.USER_DATA_API_ENDPOINT)
            )
            logger.info(
                f"Packaging for user {user_id} complete. "
                f"Local: {'✅' if results.get('local_export_success') else '❌'}, "
                f"API: {'✅' if results.get('api_export_success') else '❌'}"
            )
            return results
        except Exception as e:
            logger.error(f"Failed to package user data for {user_id}: {e}")
            raise

    @staticmethod
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles the /start command."""
        try:
            user_id = update.effective_user.id
            username = update.effective_user.username
            user_storage.create_or_update_user(user_id, username)
            keyboard = BotKeyboards.get_main_menu_keyboard()
            await update.message.reply_text(WELCOME_MESSAGE, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Error in /start command: {e}")
            await update.message.reply_text(ERROR_GENERAL_MESSAGE)

    @staticmethod
    async def set_filters_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles the /set_filters command."""
        try:
            user_id = update.effective_user.id
            username = update.effective_user.username
            user_storage.create_or_update_user(user_id, username)
            keyboard = BotKeyboards.get_filter_selection_keyboard()
            await update.message.reply_text(FILTER_SELECTION_MESSAGE, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Error in /set_filters command: {e}")
            await update.message.reply_text(ERROR_GENERAL_MESSAGE)

    @staticmethod
    async def website_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles the /website command."""
        try:
            keyboard = BotKeyboards.get_website_keyboard()
            await update.message.reply_text(WEBSITE_MESSAGE, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Error in /website command: {e}")
            await update.message.reply_text(ERROR_GENERAL_MESSAGE)

    @staticmethod
    async def manual_package_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles the manual packaging command for admins."""
        try:
            if update.effective_user.id not in settings.ADMINUSERIDS:
                await update.message.reply_text(NO_ADMIN_RIGHTS_MESSAGE)
                return

            all_users = user_storage.get_all_users()
            if not all_users:
                await update.message.reply_text(NO_DATA_TO_PACKAGE_MESSAGE)
                return

            headers = {"Authorization": f"Bearer {settings.APITOKEN}"} if settings.APITOKEN else None
            results = packager.package_and_send(
                all_users,
                save_local=True,
                send_api=bool(settings.USER_DATA_API_ENDPOINT),
                headers=headers
            )
            message = format_package_result_message(results, len(all_users))
            await update.message.reply_text(message)

        except Exception as e:
            logger.error(f"Error during manual packaging: {e}")
            error_message = ERROR_PACKAGING_MESSAGE.format(error=str(e))
            await update.message.reply_text(error_message)

    @staticmethod
    async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles all button callbacks from inline keyboards."""
        query = update.callback_query
        try:
            await query.answer()
            user_id = update.effective_user.id
            username = update.effective_user.username
            data = query.data

            user_storage.create_or_update_user(user_id, username)
            user_data = user_storage.get_user(user_id)

            if not user_data:
                await query.edit_message_text(ERROR_USER_NOT_FOUND_MESSAGE)
                return

            if data in FILTER_MENUS:
                await BotHandlers.handle_filter_menu_query(query, data, user_data)
            elif data.startswith("select_"):
                await BotHandlers.handle_filter_selection_query(query, data, user_id)
            elif data == "back_to_main_filters":
                keyboard = BotKeyboards.get_filter_selection_keyboard()
                await query.edit_message_text(FILTER_SELECTION_MESSAGE, reply_markup=keyboard)
            elif data == "save_all_filters":
                await BotHandlers.handle_save_filters_query(query, user_id)
            else:
                await query.edit_message_text(ERROR_INVALID_FILTER_MESSAGE)

        except Exception as e:
            logger.error(f"Error in button_callback: {e}")
            try:
                await query.edit_message_text(ERROR_GENERAL_MESSAGE)
            except Exception:
                await query.message.reply_text(ERROR_GENERAL_MESSAGE)

    @staticmethod
    async def handle_filter_menu_query(query, data: str, user_data: dict):
        """Displays options for a specific filter category."""
        try:
            # FIX: Correctly unpack the title from the FILTER_MENUS tuple
            menu_title, _ = FILTER_MENUS.get(data)
            current_filter_key = data.split('_')[1]
            current_filters = user_data.get(current_filter_key, set())
            keyboard = BotKeyboards.get_filter_options_keyboard(current_filter_key, current_filters)
            await query.edit_message_text(text=menu_title, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Error updating filter menu: {e}")
            await query.edit_message_text(ERROR_FILTER_UPDATE_MESSAGE)

    @staticmethod
    async def handle_filter_selection_query(query, data: str, user_id: int):
        """Updates user's filter selection."""
        try:
            _, filter_key, value = data.split('_', 2)
            user_storage.update_user_filter(user_id, filter_key, value)

            updated_user_data = user_storage.get_user(user_id)
            if not updated_user_data:
                await query.edit_message_text(ERROR_USER_NOT_FOUND_MESSAGE)
                return

            current_filters = updated_user_data.get(filter_key, set())
            menu_key = f"filter_{filter_key}"
            if menu_key not in FILTER_MENUS:
                await query.edit_message_text(ERROR_INVALID_FILTER_MESSAGE)
                return

            # FIX: Correctly unpack the title from the FILTER_MENUS tuple
            menu_title, _ = FILTER_MENUS[menu_key]
            keyboard = BotKeyboards.get_filter_options_keyboard(filter_key, current_filters)
            await query.edit_message_text(text=menu_title, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Error handling filter selection: {e}")
            await query.edit_message_text(ERROR_FILTER_UPDATE_MESSAGE)

    @staticmethod
    async def handle_save_filters_query(query, user_id: int):
        """Saves filters, packages data, and fetches courses."""
        try:
            user_data = user_storage.get_user(user_id)
            if not user_data:
                await query.edit_message_text(ERROR_USER_NOT_FOUND_MESSAGE)
                return

            filters: dict = {
                "subjects": user_data.get("subjects"),
                "difficulty": user_data.get("difficulty"),
                "grade": user_data.get("grade"),
            }

            if not any(filters.values()):
                await query.edit_message_text(WARNING_EMPTY_FILTER_MESSAGE)
                return

            await query.edit_message_text(SEARCHING_COURSES_MESSAGE)
            logger.info(f"User {user_id} saved filters, starting data packaging...")

            try:
                await BotHandlers.package_user_data_async(user_id)
            except Exception as package_error:
                logger.error(f"Data packaging failed for user {user_id}: {package_error}")

            try:
                # FIX from previous request: Call the instance method on the 'course_filter' instance
                filtered_courses = course_filter.filter_courses(filters)

                if filtered_courses:
                    for course in filtered_courses:
                        course_text = CourseFilter.format_course_message(course)
                        keyboard = BotKeyboards.get_course_keyboard(course.get("link"))
                        await query.message.reply_text(course_text, reply_markup=keyboard)
                    await query.edit_message_text(COURSES_FOUND_MESSAGE)
                else:
                    await query.edit_message_text(WARNING_NO_COURSES_MESSAGE)
            except Exception as search_error:
                logger.error(f"Unexpected error when filtering courses: {search_error}")
                await query.edit_message_text(ERROR_COURSE_SEARCH_MESSAGE)

        except Exception as e:
            logger.error(f"Error saving filters for user {user_id}: {e}")
            await query.edit_message_text(ERROR_SAVE_FILTERS_MESSAGE)
