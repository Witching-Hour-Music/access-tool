import factory
from core.models.blockchain import NFTCollection
from tests.factories.base import BaseSQLAlchemyModelFactory


class NFTCollectionFactory(BaseSQLAlchemyModelFactory):
    class Meta:
        model = NFTCollection
        sqlalchemy_session_persistence = "flush"

    address = factory.Faker("pystr", min_chars=65, max_chars=65, prefix="0:")
    name = factory.Faker("word")
    description = factory.Faker("text")
    is_enabled = True
