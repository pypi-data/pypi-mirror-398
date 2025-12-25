from datetime import date

from celery import shared_task
from django.db.models import Exists, OuterRef
from tqdm import tqdm
from wbcore.contrib.currency.models import CurrencyFXRates
from wbcore.contrib.directory.models import Company
from wbcore.workers import Queue
from wbcrm.models import Account

from .models import CompanyPortfolioData, Updater


@shared_task(queue=Queue.BACKGROUND.value)
def update_all_portfolio_data(val_date: date | None = None):
    if not val_date:
        val_date = CurrencyFXRates.objects.latest("date").date
    updater = Updater(val_date)
    qs = Company.objects.annotate(
        has_account=Exists(Account.objects.filter(owner=OuterRef("pk"))),
        has_portfolio_data=Exists(CompanyPortfolioData.objects.filter(company=OuterRef("pk"))),
    )
    company_objs = []
    portfolio_data_objs = []
    for company in tqdm(qs, total=qs.count()):
        portfolio_data = CompanyPortfolioData.objects.get_or_create(company=company)[0]
        company.customer_status, company.tier = updater.update_company_data(portfolio_data)
        portfolio_data_objs.append(portfolio_data)
        company_objs.append(company)
    if company_objs:
        Company.objects.bulk_update(company_objs, ["customer_status", "tier"])
    if portfolio_data_objs:
        CompanyPortfolioData.objects.bulk_update(
            portfolio_data_objs, ["invested_assets_under_management_usd", "potential"]
        )
