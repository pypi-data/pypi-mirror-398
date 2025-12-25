from contextlib import suppress
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.module_loading import import_string
from dynamic_preferences.registries import global_preferences_registry
from wbcore.contrib.currency.models import CurrencyFXRates
from wbcore.contrib.directory.models import Company, CustomerStatus
from wbcore.models import WBModel

from wbportfolio.models import Claim, Product


def get_total_assets_under_management(val_date: date) -> Decimal:
    cache_key = f"total_assets_under_management:{val_date.isoformat()}"
    return cache.get_or_set(
        cache_key,
        lambda: sum([product.get_total_aum_usd(val_date) for product in Product.active_objects.all()]),
        60 * 60 * 24,
    )


def get_lost_client_customer_status():
    global_preferences = global_preferences_registry.manager()
    return global_preferences["wbportfolio__lost_client_customer_status"]


def get_returning_client_customer_status():
    global_preferences = global_preferences_registry.manager()
    return global_preferences["wbportfolio__returning_client_customer_status"]


def get_tpm_customer_status():
    global_preferences = global_preferences_registry.manager()
    return global_preferences["wbportfolio__tpm_customer_status"]


def get_client_customer_status():
    global_preferences = global_preferences_registry.manager()
    return global_preferences["wbportfolio__client_customer_status"]


class Updater:
    def __init__(self, val_date: date):
        self.val_date = val_date
        self.total_assets_under_management = get_total_assets_under_management(val_date)

    def update_company_data(self, company_portfolio_data) -> tuple[str, str]:
        # save company portfolio data
        if (
            invested_assets_under_management_usd := company_portfolio_data.get_assets_under_management_usd(
                self.val_date
            )
        ) is not None:
            company_portfolio_data.invested_assets_under_management_usd = invested_assets_under_management_usd
        if (potential := company_portfolio_data.get_potential(self.val_date)) is not None:
            company_portfolio_data.potential = potential

        # update the company object itself
        tier = company_portfolio_data.get_tiering(self.total_assets_under_management)
        customer_status = company_portfolio_data.get_customer_status()
        return customer_status, tier


class CompanyPortfolioData(models.Model):
    class InvestmentDiscretion(models.TextChoices):
        FULLY_DISCRETIONAIRY = "FULLY_DISCRETIONAIRY", "Fully Discretionairy"
        MOSTLY_DISCRETIONAIRY = "MOSTLY_DISCRETIONAIRY", "Mostly Discretionairy"
        MIXED = "MIXED", "Mixed"
        MOSTLY_ADVISORY = "MOSTLY_ADVISORY", "Mostly Advisory"
        FULLY_ADVISORY = "FULLY_ADVISORY", "Fully Advisory"

    potential_help_text = """
        The potential reflects how much potential a company (regardless whether client/propective) has. The formula to calculate the potential is:

        AUM * Asset Allocation Percent * Asset Allocation Max Investment - Invested AUM.
    """

    company = models.OneToOneField(
        to="directory.Company", related_name="portfolio_data", on_delete=models.CASCADE, unique=True
    )

    assets_under_management_currency = models.ForeignKey(
        to="currency.Currency",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name="AUM Currency",
    )

    assets_under_management = models.DecimalField(
        max_digits=17,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="AUM",
        help_text="The Assets under Management (AUM) that is managed by this company or this person's primary employer.",
    )

    investment_discretion = models.CharField(
        max_length=21,
        choices=InvestmentDiscretion.choices,
        default=InvestmentDiscretion.MIXED,
        help_text="What discretion this company or this person's primary employer has to invest its assets.",
        verbose_name="Investment Discretion",
    )
    potential_currency = models.ForeignKey(
        to="currency.Currency",
        related_name="wbportfolio_potential_currencies",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    # Dynamic fields
    invested_assets_under_management_usd = models.DecimalField(
        max_digits=17,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="The invested Assets under Management (AUM).",
        verbose_name="Invested AUM ($)",
    )

    potential = models.DecimalField(
        decimal_places=2, max_digits=19, null=True, blank=True, help_text=potential_help_text
    )

    def update(self):
        with suppress(CurrencyFXRates.DoesNotExist):
            val_date = CurrencyFXRates.objects.latest("date").date
            self.company.customer_status, self.company.tier = Updater(val_date).update_company_data(self)

    def get_assets_under_management_usd(self, val_date: date) -> Decimal:
        return Claim.objects.filter(status=Claim.Status.APPROVED).filter_for_customer(
            self.company
        ).annotate_asset_under_management_for_date(val_date).aggregate(
            invested_aum_usd=models.Sum("asset_under_management_usd")
        )["invested_aum_usd"] or Decimal(0)

    def _get_default_potential(self, val_date: date) -> Decimal:
        if self.assets_under_management:
            with suppress(CurrencyFXRates.DoesNotExist):
                fx = CurrencyFXRates.objects.get(currency=self.assets_under_management_currency, date=val_date).value

                aum_usd = self.assets_under_management / fx
                aum_potential = Decimal(0)
                for asset_allocation in self.company.asset_allocations.all():
                    aum_potential += aum_usd * asset_allocation.percent * asset_allocation.max_investment
                invested_aum = self.invested_assets_under_management_usd or Decimal(0.0)

                return aum_potential - invested_aum

    def get_potential(self, val_date: date) -> Decimal:
        if module_path := getattr(settings, "PORTFOLIO_COMPANY_DATA_POTENTIAL_METHOD", None):
            with suppress(ModuleNotFoundError):
                return import_string(module_path)(self, val_date)
        return self._get_default_potential(val_date)

    def _get_default_tiering(self, total_asset_under_management: Decimal) -> Company.Tiering:
        if self.company.customer_status and self.company.customer_status in [
            get_client_customer_status(),
            get_tpm_customer_status(),
        ]:
            invested_aum = self.invested_assets_under_management_usd or Decimal(0)
            match invested_aum / total_asset_under_management:
                case share if share >= 0.1:  # noqa: F821
                    return Company.Tiering.ONE
                case share if share >= 0.05:  # noqa: F821
                    return Company.Tiering.TWO
                case share if share >= 0.02:  # noqa: F821
                    return Company.Tiering.THREE
                case share if share >= 0.01:  # noqa: F821
                    return Company.Tiering.FOUR
                case _:
                    return Company.Tiering.FIVE

        elif self.assets_under_management and self.assets_under_management_currency:
            fx = self.assets_under_management_currency.fx_rates.latest("date").value

            match self.assets_under_management / fx:
                case aum if aum >= 10_000_000_000:  # noqa: F821
                    return Company.Tiering.ONE
                case aum if aum >= 5_000_000_000:  # noqa: F821
                    return Company.Tiering.TWO
                case aum if aum >= 1_000_000_000:  # noqa: F821
                    return Company.Tiering.THREE
                case aum if aum >= 500_000_000:  # noqa: F821
                    return Company.Tiering.FOUR
                case _:
                    return Company.Tiering.FIVE

        return None

    def get_tiering(self, total_asset_under_management: Decimal) -> Decimal:
        if module_path := getattr(settings, "PORTFOLIO_COMPANY_DATA_TIERING_METHOD", None):
            with suppress(ModuleNotFoundError):
                return import_string(module_path)(self, total_asset_under_management)
        return self._get_default_tiering(total_asset_under_management)

    def get_customer_status(self) -> CustomerStatus:
        if aum := self.invested_assets_under_management_usd:
            if aum > 0 and self.company.customer_status == get_lost_client_customer_status():
                return get_returning_client_customer_status()

            if aum > 0 and self.company.customer_status not in [
                get_tpm_customer_status(),
                get_returning_client_customer_status(),
            ]:
                return get_client_customer_status()

        if (
            not self.invested_assets_under_management_usd
            and self.company.customer_status == get_client_customer_status()
        ):
            return get_lost_client_customer_status()

        return self.company.customer_status

    def __str__(self) -> str:
        return f"{self.company}"

    class Meta:
        verbose_name = "Company Portfolio Data"
        verbose_name_plural = "Company Portfolio Data"


class AssetAllocationType(WBModel):
    name = models.CharField(max_length=255)
    default_max_investment = models.DecimalField(
        decimal_places=4,
        max_digits=5,
        default=0.1,
        help_text="The default percentage this allocation is counted towards the potential.",
    )

    def __str__(self) -> str:
        return f"{self.name}"

    class Meta:
        verbose_name = "Asset Allocation Type"
        verbose_name_plural = "Asset Allocation Types"

    @classmethod
    def get_endpoint_basename(cls):
        return "company_portfolio:assetallocationtype"

    @classmethod
    def get_representation_endpoint(cls):
        return "company_portfolio:assetallocationtyperepresentation-list"

    @classmethod
    def get_representation_value_key(cls):
        return "id"

    @classmethod
    def get_representation_label_key(cls):
        return "{{name}}"


class AssetAllocation(models.Model):
    company = models.ForeignKey(to="directory.Company", related_name="asset_allocations", on_delete=models.CASCADE)
    asset_type = models.ForeignKey(
        to="company_portfolio.AssetAllocationType", related_name="asset_allocations", on_delete=models.PROTECT
    )
    percent = models.DecimalField(decimal_places=4, max_digits=5)
    max_investment = models.DecimalField(
        decimal_places=4,
        max_digits=5,
        null=True,
        blank=True,
        help_text="The percentage this allocation is counted towards the potential. Defaults to the default provided in the asset type.",
    )
    comment = models.TextField(default="")

    def save(self, *args, **kwargs):
        # If max investment is none, we are using the default one given by the asset_type
        if self.max_investment is None:
            self.max_investment = self.asset_type.default_max_investment

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.company}: {self.percent:.2%} {self.asset_type}"

    class Meta:
        verbose_name = "Asset Allocation"
        verbose_name_plural = "Asset Allocations"

    @classmethod
    def get_endpoint_basename(cls):
        return "company_portfolio:assetallocation"

    @classmethod
    def get_representation_value_key(cls):
        return "id"

    @classmethod
    def get_representation_label_key(cls):
        return "{{company}}: {{percent}} {{asset_type}}"


class GeographicFocus(models.Model):
    company = models.ForeignKey(to="directory.Company", related_name="geographic_focuses", on_delete=models.CASCADE)
    country = models.ForeignKey(to="geography.Geography", on_delete=models.PROTECT, verbose_name="Location")
    percent = models.DecimalField(decimal_places=4, max_digits=5)
    comment = models.TextField(default="")

    def __str__(self) -> str:
        return f"{self.company}: {self.percent:.2%} {self.country}"

    class Meta:
        verbose_name = "Geographic Focus"
        verbose_name_plural = "Geographic Focuses"

    @classmethod
    def get_endpoint_basename(cls):
        return "company_portfolio:geographicfocus"

    @classmethod
    def get_representation_value_key(cls):
        return "id"

    @classmethod
    def get_representation_label_key(cls):
        return "{{company}}: {{percent}} {{country}}"


@receiver(post_save, sender=AssetAllocation)
@receiver(post_save, sender=GeographicFocus)
def post_save_company_data(sender, instance, created, **kwargs):
    company = instance.company
    portfolio_data, created = CompanyPortfolioData.objects.get_or_create(company=company)
    if not created:
        portfolio_data.update()
        portfolio_data.save()
        portfolio_data.company.save()


@receiver(post_save, sender="directory.Company")
def handle_company_portfolio_data(sender, instance, created, **kwargs):
    # create default asset allocation type (equity 50/50)
    if not instance.asset_allocations.exists():
        equity_asset_type = AssetAllocationType.objects.get_or_create(name="Equity")[0]
        AssetAllocation.objects.create(
            company=instance,
            asset_type=equity_asset_type,
            percent=0.5,
            max_investment=0.5,
        )
    if created:
        portfolio_data, created = CompanyPortfolioData.objects.get_or_create(company=instance)
        if not created:
            portfolio_data.update()
            portfolio_data.save()
            portfolio_data.company.save()
