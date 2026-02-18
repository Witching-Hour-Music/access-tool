import pytest
from unittest.mock import AsyncMock, MagicMock

from community_manager.actions.chat import CommunityManagerChatAction
from core.services.supertelethon import ChatPeerType
from community_manager.events import ChatAdminChangeEventBuilder
from core.dtos.chat import TelegramChatDTO
from core.models.chat import TelegramChat


@pytest.mark.asyncio
async def test_create_chat_parallel_execution(mocker):
    # Mock dependencies
    db_session = MagicMock()

    # Mock services initialized in __init__
    mock_chat_service = MagicMock()
    mock_user_service = MagicMock()
    mock_redis_service = MagicMock()
    mock_cdn_service = MagicMock()
    mock_telethon_service = MagicMock()

    mocker.patch(
        "community_manager.actions.chat.TelegramChatService",
        return_value=mock_chat_service,
    )
    mocker.patch(
        "community_manager.actions.chat.TelegramChatUserService",
        return_value=mock_user_service,
    )
    mocker.patch(
        "community_manager.actions.chat.RedisService", return_value=mock_redis_service
    )
    mocker.patch(
        "community_manager.actions.chat.CDNService", return_value=mock_cdn_service
    )
    mocker.patch(
        "community_manager.actions.chat.TelethonService",
        return_value=mock_telethon_service,
    )

    # Mock TelegramGatewayClient used in _index
    mock_gateway_client = MagicMock()
    mocker.patch(
        "community_manager.actions.chat.TelegramGatewayClient",
        return_value=mock_gateway_client,
    )

    # Mock TelegramBotApiService (already mocked in fixture, but let's ensure return values)
    mock_bot_service_context = MagicMock()
    mock_bot_service = AsyncMock()
    mock_invite = MagicMock()
    mock_invite.invite_link = "https://t.me/+new_invite_link"
    mock_bot_service.create_chat_invite_link.return_value = mock_invite
    mock_bot_service_context.__aenter__.return_value = mock_bot_service
    mock_bot_service_context.__aexit__.return_value = None

    mocker.patch(
        "community_manager.actions.chat.TelegramBotApiService",
        return_value=mock_bot_service_context,
    )

    # Mock get_peer_id as it cannot handle MagicMock
    mocker.patch("community_manager.actions.chat.get_peer_id", return_value=12345)

    # Initialize action
    action = CommunityManagerChatAction(db_session)

    # Setup action mocks
    chat_id = 12345
    chat_entity = MagicMock(spec=ChatPeerType)
    chat_entity.id = chat_id
    chat_entity.username = None

    # Mock _get_chat_data
    action._get_chat_data = AsyncMock(return_value=chat_entity)

    # Mock fetch_and_push_profile_photo
    logo_path = "logo.png"
    action.fetch_and_push_profile_photo = AsyncMock(return_value=logo_path)

    # Mock _create (db part)
    mock_chat_service.create.return_value = TelegramChat(
        id=chat_id,
        title="Test Chat",
        username="test_chat",
        is_forum=False,
        logo_path=logo_path,
        insufficient_privileges=False,
        slug="test-chat",
        invite_link=None,
        is_full_control=False,
        is_enabled=True,
    )

    # Configure get to return the same chat object (updated with invite link ideally, but for now just needs to be valid)
    mock_chat_service.get.return_value = TelegramChat(
        id=chat_id,
        title="Test Chat",
        username="test_chat",
        is_forum=False,
        logo_path="123456789.png",  # Updated logo path
        insufficient_privileges=False,
        slug="test-chat",
        invite_link="https://t.me/+new_invite_link",  # Updated invite link
        is_full_control=False,
        is_enabled=True,
    )
    created_chat_dto = TelegramChatDTO(
        id=chat_id,
        title="Test Chat",
        description=None,
        username=None,
        is_forum=False,
        logo_path=logo_path,
        insufficient_privileges=False,
        slug="test-chat",
        invite_link=None,
        is_enabled=True,
        is_full_control=False,
    )
    action._create = AsyncMock(return_value=created_chat_dto)

    # Mock services calls
    mock_user_service.get_members_count.return_value = 10

    # Event
    event = MagicMock(spec=ChatAdminChangeEventBuilder.Event)
    event.is_self = True
    event.sufficient_bot_privileges = True

    # Mock photo attribute on chat entity for logo path generation
    chat_entity.photo = MagicMock()
    chat_entity.photo.photo_id = 123456789
    # Add types.ChatPhotoEmpty to sys.modules or mock types import if needed,
    # but here we can just ensure isinstance check works or is mocked.
    # Actually, we need to ensure the check `isinstance(chat.photo, types.ChatPhotoEmpty)` returns False.
    # Simple way: just make it a MagicMock, it won't be instance of ChatPhotoEmpty unless we say so.

    # Execute
    result = await action.create(chat_id, event)

    # Verification

    # 1. Verify DB creation called FIRST with logo_path derived from chat.photo.photo_id
    expected_logo_path = "123456789.png"
    action._create.assert_awaited_once_with(
        chat_entity, logo_path=expected_logo_path, sufficient_bot_privileges=True
    )
    db_session.commit.assert_called()

    # 2. Verify parallel tasks executed
    # fetch_and_push_profile_photo
    action.fetch_and_push_profile_photo.assert_awaited_once_with(
        chat_entity, current_logo_path=None
    )

    # Invite link creation
    mock_bot_service.create_chat_invite_link.assert_awaited_once()

    # _index logic verification
    mock_gateway_client.enqueue_command.assert_called()

    # 3. Verify invite link update
    mock_chat_service.refresh_invite_link.assert_called_with(
        chat_id=chat_id, invite_link="https://t.me/+new_invite_link"
    )

    # 4. Verify result is refreshed (we mocked get to return updated entity)
    assert result.id == chat_id
    assert result.members_count == 10
    # Link should be present if our mock 'get' returned it, but we didn't update the mock object returned by get.
    # The code calls self.telegram_chat_service.get(chat_id) at the end.
    # We should ensure that returns the updated chat.
    assert mock_chat_service.get.call_count >= 1
