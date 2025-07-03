import pytest
from unittest.mock import AsyncMock, MagicMock
from data.user_storage import user_storage  # Import the global instance


@pytest.fixture
def mock_update():
    """Fixture for a mock telegram.Update object."""
    update = MagicMock()
    update.effective_user.id = 12345
    update.effective_user.username = "testuser"
    update.message = AsyncMock()
    update.callback_query = AsyncMock()
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.message.reply_text = AsyncMock()
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture(autouse=True)
def clean_user_storage():
    """
    This fixture automatically cleans the global user_storage before each test,
    ensuring test isolation.
    """
    # Setup: Code that runs before each test
    user_storage.user_filters.clear()

    yield  # This is where the test itself runs

    # Teardown: Code that runs after each test (optional but good practice)
    user_storage.user_filters.clear()
