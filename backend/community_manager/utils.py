from telethon.tl.types import (
    ChannelParticipantAdmin,
    ChannelParticipantCreator,
    ChannelParticipant,
)

from core.constants import REQUIRED_ADMIN_PRIVILEGES


def is_chat_participant_admin(
    chat_participant: ChannelParticipant,
) -> bool:
    """
    Check if the given chat participant is an admin or creator.
    :param chat_participant: The chat participant to check.
    :return: True if the participant is an admin or creator, False otherwise.
    """
    return isinstance(
        chat_participant,
        (ChannelParticipantAdmin, ChannelParticipantCreator),
    )


def is_chat_participant_manager_admin(
    chat_participant: ChannelParticipant
    | ChannelParticipantAdmin
    | ChannelParticipantCreator,
) -> bool:
    """
    Check if the given chat participant is an admin with manager privileges.
    :param chat_participant: The chat participant to check.
    :return: True if the participant is an admin with manager privileges, False otherwise.
    """
    if not is_chat_participant_admin(chat_participant):
        return False

    return all(
        getattr(chat_participant.admin_rights, right)
        for right in REQUIRED_ADMIN_PRIVILEGES
    )
