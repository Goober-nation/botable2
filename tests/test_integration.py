import pytest
from unittest.mock import patch, AsyncMock

from bot.handlers import BotHandlers
from data.user_storage import user_storage
from bot.messages import *
from unittest.mock import ANY

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


# 1. Test the /start command flow
async def test_start_command_flow(mock_update):
    """Tests that /start command creates a user and sends a welcome message."""
    user_id = mock_update.effective_user.id

    # Ensure user does not exist before the test
    if user_id in user_storage.user_filters:
        del user_storage.user_filters[user_id]

    await BotHandlers.start_command(mock_update, None)

    # Assert user was created in storage
    assert user_id in user_storage.user_filters
    # Assert the correct welcome message was sent
    mock_update.message.reply_text.assert_called_once_with(WELCOME_MESSAGE,reply_markup=ANY)


# 2. Test the full filter selection and search flow
@patch('bot.handlers.BotHandlers.package_user_data_async', new_callable=AsyncMock)
async def test_full_filter_and_search_flow(mock_package_data, mock_update):
    """Tests selecting a filter, saving, and getting course results."""
    user_id = mock_update.effective_user.id
    user_storage.create_or_update_user(user_id, "search_user")
    user_storage.update_user_filter(user_id, "difficulty", "Начальный")
    user_storage.update_user_filter(user_id, "subjects", "Финансовая грамотность")

    mock_update.callback_query.data = "save_all_filters"

    await BotHandlers.button_callback(mock_update, None)

    # Assert that data packaging was triggered
    mock_package_data.assert_called_once_with(user_id)

    # Assert the flow of messages
    mock_update.callback_query.edit_message_text.assert_any_call(SEARCHING_COURSES_MESSAGE)
    mock_update.callback_query.edit_message_text.assert_called_with(COURSES_FOUND_MESSAGE)

    # Assert that course results were sent
    mock_update.callback_query.message.reply_text.assert_called()
    first_call_args = mock_update.callback_query.message.reply_text.call_args[0][0]
    assert "Личные финансы для подростков" in first_call_args  # Example check


# 3. Test an admin successfully using the /package command
@patch('bot.handlers.packager.package_and_send')
async def test_admin_package_command(mock_package_send, mock_update):
    """Tests that an admin can trigger a manual packaging of all user data."""
    # Configure settings for this test
    with patch('bot.handlers.settings.ADMIN_USER_IDS', [12345]):
        # Add some data to storage
        user_storage.create_or_update_user(1, "user1")
        user_storage.create_or_update_user(2, "user2")

        await BotHandlers.manual_package_command(mock_update, None)

        # Assert that the packager was called with all users
        mock_package_send.assert_called_once()
        sent_data = mock_package_send.call_args[0][0]
        assert len(sent_data) == user_storage.get_user_count()

        # Assert a success message was sent back
        mock_update.message.reply_text.assert_called_once()
        assert "Ручная упаковка завершена" in mock_update.message.reply_text.call_args[0][0]


# 4. Test a non-admin attempting to use the /package command
@patch('bot.handlers.packager.package_and_send')
async def test_non_admin_package_command_fails(mock_package_send, mock_update):
    """Tests that a non-admin receives an error and cannot package data."""
    # Configure settings for this test
    with patch('bot.handlers.settings.ADMIN_USER_IDS', [99999]):  # Admin is someone else
        await BotHandlers.manual_package_command(mock_update, None)

        # Assert that the packager was NOT called
        mock_package_send.assert_not_called()

        # Assert the 'no rights' message was sent
        mock_update.message.reply_text.assert_called_once_with(NO_ADMIN_RIGHTS_MESSAGE)


# 5. Test finding no courses
async def test_no_courses_found_flow(mock_update):
    """Tests the message flow when no courses match the selected filters."""
    user_id = mock_update.effective_user.id
    user_storage.create_or_update_user(user_id, "no_course_user")
    # A filter combination that is known to return no results
    user_storage.update_user_filter(user_id, "subjects", "Робототехника")
    user_storage.update_user_filter(user_id, "difficulty", "Продвинутый")

    mock_update.callback_query.data = "save_all_filters"

    await BotHandlers.button_callback(mock_update, None)

    # Assert that the "no courses found" message is displayed
    mock_update.callback_query.edit_message_text.assert_called_with(WARNING_NO_COURSES_MESSAGE)
    # Assert no course results were sent
    mock_update.callback_query.message.reply_text.assert_not_called()
