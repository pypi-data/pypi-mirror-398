import factory
from faker import Faker
from pandas._libs.tslibs.offsets import BDay
from wbcore.contrib.authentication.factories import UserFactory
from wbcore.contrib.currency.factories import CurrencyFactory

from wbportfolio.factories import PortfolioFactory
from wbportfolio.models import OrderProposal

fake = Faker()


class OrderProposalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderProposal

    trade_date = factory.LazyAttribute(lambda o: (fake.date_object() + BDay(1)).date())
    comment = factory.Faker("paragraph")
    portfolio = factory.LazyAttribute(lambda o: PortfolioFactory.create(currency=CurrencyFactory.create(key="USD")))
    creator = factory.LazyAttribute(lambda o: UserFactory.create().profile)
    approver = factory.LazyAttribute(lambda o: UserFactory.create().profile)
