import factory

from core.models.rule import (
    TelegramChatJetton,
    TelegramChatNFTCollection,
    TelegramChatToncoin,
)
from tests.factories.jetton import JettonFactory
from tests.factories.nft import NFTCollectionFactory
from tests.factories.rule.base import (
    TelegramChatRuleBaseFactory,
    TelegramChatThresholdRuleMixin,
)


class TelegramChatJettonRuleFactory(
    TelegramChatRuleBaseFactory, TelegramChatThresholdRuleMixin
):
    class Meta:
        model = TelegramChatJetton

    address = factory.SelfAttribute("jetton.address")
    jetton = factory.SubFactory(JettonFactory)


class TelegramChatNFTCollectionRuleFactory(
    TelegramChatRuleBaseFactory, TelegramChatThresholdRuleMixin
):
    class Meta:
        model = TelegramChatNFTCollection

    address = factory.SelfAttribute("nft_collection.address")
    nft_collection = factory.SubFactory(NFTCollectionFactory)
    asset = None


class TelegramChatToncoinRuleFactory(
    TelegramChatRuleBaseFactory, TelegramChatThresholdRuleMixin
):
    class Meta:
        model = TelegramChatToncoin
