import pytest
from core.models.chat import TelegramChatUser
from core.models.user import User
from core.services.chat.user import TelegramChatUserService


@pytest.mark.asyncio
async def test_yield_all_for_chat_batching(db_session, chat_factory):
    # Setup
    chat = chat_factory()
    service = TelegramChatUserService(db_session)

    # Create 25 users
    users = []
    for i in range(25):
        user = User(telegram_id=1000 + i)
        db_session.add(user)
        db_session.flush()

        chat_user = TelegramChatUser(
            chat_id=chat.id, user_id=user.id, is_admin=False, is_managed=True
        )
        db_session.add(chat_user)
        users.append(chat_user)

    db_session.commit()

    # Test
    batches = []
    for batch in service.yield_all_for_chat(chat.id, batch_size=10):
        batches.append(batch)

    # Verify
    assert len(batches) == 3
    assert len(batches[0]) == 10
    assert len(batches[1]) == 10
    assert len(batches[2]) == 5

    all_yielded_users = [u for batch in batches for u in batch]
    assert len(all_yielded_users) == 25

    # Verify order
    user_ids = [u.user_id for u in all_yielded_users]
    assert user_ids == sorted(user_ids)
