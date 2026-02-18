import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from core.actions.chat.base import ManagedChatBaseAction
from core.models.user import User
from core.models.chat import TelegramChat


class MockManagedChatAction(ManagedChatBaseAction):
    pass


@pytest.fixture
def mock_deps(db_session):
    pass


def test_managed_chat_action_permissions(db_session):
    user = User(id=1)
    chat = TelegramChat(id=1, slug="test")

    # We need to mock services that are initialized in __init__
    # Since we cannot easily mock local variables in __init__, we have to mock strictly dependencies.
    # Or we can subclass and override __init__ but we want to test __init__ logic (specifically __get_target_chat).

    # __init__ does:
    # self.telegram_chat_service = TelegramChatService(db_session)
    # self.telegram_chat_user_service = TelegramChatUserService(db_session)
    # ...
    # self._chat = self.__get_target_chat(requestor=requestor, chat_slug=chat_slug)

    # We can mock TelegramChatService and TelegramChatUserService classes in the module
    with pytest.MonkeyPatch.context() as m:
        m.setattr("core.actions.chat.base.TelegramChatService", MagicMock())
        m.setattr("core.actions.chat.base.TelegramChatUserService", MagicMock())
        m.setattr("core.actions.chat.base.TelegramChatRuleGroupService", MagicMock())
        m.setattr("core.actions.chat.base.AuthorizationAction", MagicMock())

        # Setup mocks
        mock_chat_service_instance = MagicMock()
        mock_chat_service_instance.get_by_slug.return_value = chat
        m.setattr(
            "core.actions.chat.base.TelegramChatService",
            lambda s: mock_chat_service_instance,
        )

        mock_user_service_instance = MagicMock()
        m.setattr(
            "core.actions.chat.base.TelegramChatUserService",
            lambda s: mock_user_service_instance,
        )

        # Test success: user is manager admin
        mock_user_service_instance.is_chat_manager_admin.return_value = True

        action = MockManagedChatAction(db_session, user, "test")
        assert action.chat == chat

        # Test fail: user is NOT manager admin
        mock_user_service_instance.is_chat_manager_admin.return_value = False

        with pytest.raises(HTTPException) as excinfo:
            MockManagedChatAction(db_session, user, "test")
        assert excinfo.value.status_code == 403
