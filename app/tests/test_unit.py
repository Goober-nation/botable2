import pytest
from unittest.mock import patch, MagicMock

# Import the components to be tested
from data.courses import CourseFilter
from data.user_storage import UserStorage
from utils.packager import Packager
from bot.keyboards import BotKeyboards
from bot.messages import format_package_result_message


# 1. Test Course Filtering Logic
def test_course_filtering():
    """Tests if the CourseFilter correctly filters courses based on criteria."""
    # Test filtering by a single subject
    filters = {"subjects": {"Программирование"}}
    results = CourseFilter.filter_courses(filters)
    assert len(results) > 0
    assert all("Программирование" in course["subjects"] for course in results)

    # Test filtering by difficulty and grade that yields a specific result
    filters = {"difficulty": {"Продвинутый"}, "grade": {"11"}}
    results = CourseFilter.filter_courses(filters)
    assert any(course['name'] == "Криптография и защита данных" for course in results)

    # Test filtering that should yield no results
    filters = {"subjects": {"Робототехника"}, "difficulty": {"Продвинутый"}}
    results = CourseFilter.filter_courses(filters)
    assert len(results) == 0


# 2. Test User Creation and Update
def test_user_storage_creation_and_update():
    """Tests creating a new user and updating an existing one."""
    storage = UserStorage()
    user_id = 123

    # Create a new user
    storage.create_or_update_user(user_id, "first_user")
    assert user_id in storage.user_filters
    assert storage.user_filters[user_id]["username"] == "first_user"
    created_at = storage.user_filters[user_id]["created_at"]

    # Update the same user
    storage.create_or_update_user(user_id, "updated_user")
    assert storage.user_filters[user_id]["username"] == "updated_user"
    assert storage.user_filters[user_id]["created_at"] == created_at  # Should not change


# 3. Test User Filter Management
def test_user_filter_update():
    """Tests adding and removing a filter for a user."""
    storage = UserStorage()
    user_id = 456
    storage.create_or_update_user(user_id, "filter_user")

    # Add a filter
    storage.update_user_filter(user_id, "subjects", "Наука")
    assert "Наука" in storage.user_filters[user_id]["subjects"]

    # Remove the same filter
    storage.update_user_filter(user_id, "subjects", "Наука")
    assert "Наука" not in storage.user_filters[user_id]["subjects"]


# 4. Test Data Packaging Logic (with mocked API call)
@patch('utils.packager.requests.post')
def test_packager_sends_correct_data(mock_post):
    """Tests that the Packager formats data correctly and attempts to send it."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    packager = Packager(api_endpoint="http://fake-api.com/data")
    user_data = {
        789: {"username": "api_user", "subjects": {"Финансовая грамотность"}, "difficulty": set()}
    }

    result = packager.package_and_send(user_data)

    # Assert that the API call was made
    mock_post.assert_called_once()
    # Assert that the payload sent to the API is correctly structured
    sent_json = mock_post.call_args.kwargs['json']
    assert sent_json['total_users'] == 1
    assert sent_json['users']['789']['username'] == "api_user"
    # Assert that the set was converted to a list for JSON
    assert sent_json['users']['789']['subjects'] == ["Финансовая грамотность"]
    assert result['api_export']['success'] is True


# 5. Test Keyboard Generation Logic
def test_keyboard_generation_with_selection():
    """Tests that a keyboard correctly shows selected items with a checkmark."""
    # Test a keyboard where one subject is already selected
    user_selections = {"Программирование", "Наука"}
    keyboard = BotKeyboards.get_filter_options_keyboard("subjects", user_selections)

    buttons_text = [btn.text for row in keyboard.inline_keyboard for btn in row]

    # Assert that selected items have a checkmark
    assert "✅ Программирование" in buttons_text
    assert "✅ Наука" in buttons_text
    # Assert that an unselected item does not
    assert "Робототехника" in buttons_text
    assert "⬅️ Назад" in buttons_text
