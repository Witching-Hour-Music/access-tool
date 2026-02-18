import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from community_manager.actions.chat import CommunityManagerUserChatAction
from core.models.chat import TelegramChatUser, TelegramChat
from core.models.user import User


@pytest.mark.asyncio
async def test_kick_chat_member_admin_protection(db_session):
    action = CommunityManagerUserChatAction(db_session)
    chat = TelegramChat(id=1, title="Test Chat", is_full_control=True)
    user = User(id=1, telegram_id=123)
    chat_user = TelegramChatUser(
        user_id=1, chat_id=1, is_admin=True, is_managed=True, chat=chat, user=user
    )

    # Mock bot_api_service to ensure it is NOT called
    action.bot_api_service = AsyncMock()

    await action.kick_chat_member(chat_user)

    action.bot_api_service.kick_chat_member.assert_not_called()


@pytest.mark.asyncio
async def test_kick_chat_member_normal_user(db_session):
    action = CommunityManagerUserChatAction(db_session)
    chat = TelegramChat(id=1, title="Test Chat", is_full_control=True)
    user = User(id=1, telegram_id=123)
    chat_user = TelegramChatUser(
        user_id=1, chat_id=1, is_admin=False, is_managed=True, chat=chat, user=user
    )

    # Mock bot_api_service context manager
    # We need to mock the class instantiated in the method: TelegramBotApiService
    with patch("community_manager.actions.chat.TelegramBotApiService") as MockService:
        mock_service_instance = AsyncMock()
        MockService.return_value.__aenter__.return_value = mock_service_instance

        # Mock delete
        # telegram_chat_user_service is synchronous
        action.telegram_chat_user_service = MagicMock()

        await action.kick_chat_member(chat_user)

        mock_service_instance.kick_chat_member.assert_awaited_once()
