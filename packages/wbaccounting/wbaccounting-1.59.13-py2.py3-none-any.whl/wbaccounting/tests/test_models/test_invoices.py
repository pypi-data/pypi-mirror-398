import pytest
from pytest_factoryboy.fixture import LazyFixture
from wbcore.contrib.authentication.models import User

from wbaccounting.models import EntryAccountingInformation, Invoice


@pytest.mark.django_db
class TestInvoice:
    def test_str(self, invoice: Invoice):
        assert str(invoice) == invoice.title

    @pytest.mark.parametrize(
        "method,return_value",
        [
            ("get_endpoint_basename", "wbaccounting:invoice"),
            ("get_representation_value_key", "id"),
            ("get_representation_label_key", "{{title}} ({{invoice_date}})"),
            ("get_representation_endpoint", "wbaccounting:invoicerepresentation-list"),
        ],
    )
    def test_wbmodel_methods(self, method: str, return_value: str):
        assert getattr(Invoice, method)() == return_value

    @pytest.mark.parametrize("user__is_superuser", [False])
    def test_filter_for_user_no_superuser(self, invoice: Invoice, user: User):
        invoices = Invoice.objects.filter_for_user(user)  # type: ignore
        assert invoice not in invoices

    @pytest.mark.parametrize("user__is_superuser", [True])
    def test_filter_for_user_superuser(self, invoice: Invoice, user: User):
        invoices = Invoice.objects.filter_for_user(user)  # type: ignore
        assert invoice in invoices

    @pytest.mark.parametrize("user__is_superuser", [False])
    @pytest.mark.parametrize("user__user_permissions", [(["wbaccounting.view_invoice"])])
    @pytest.mark.parametrize("invoice__counterparty", [LazyFixture("entry")])
    @pytest.mark.parametrize("entry_accounting_information__entry", [LazyFixture("entry")])
    @pytest.mark.parametrize("entry_accounting_information__counterparty_is_private", [False])
    def test_filter_for_user_public_counterparty(
        self, invoice: Invoice, user: User, entry_accounting_information: EntryAccountingInformation
    ):
        invoices = Invoice.objects.filter_for_user(user)  # type: ignore
        assert invoice in invoices

    @pytest.mark.parametrize("user__is_superuser", [False])
    @pytest.mark.parametrize("user__user_permissions", [(["wbaccounting.view_entryaccountinginformation"])])
    @pytest.mark.parametrize("invoice__counterparty", [LazyFixture("entry")])
    @pytest.mark.parametrize("entry_accounting_information__entry", [LazyFixture("entry")])
    @pytest.mark.parametrize("entry_accounting_information__counterparty_is_private", [True])
    def test_filter_for_user_private_counterparty(
        self, user: User, invoice: Invoice, entry_accounting_information: EntryAccountingInformation
    ):
        invoices = Invoice.objects.filter_for_user(user)  # type: ignore
        assert invoice not in invoices

    @pytest.mark.parametrize("user__is_superuser", [False])
    @pytest.mark.parametrize("user__user_permissions", [(["wbaccounting.view_entryaccountinginformation"])])
    @pytest.mark.parametrize("invoice__counterparty", [LazyFixture("entry")])
    @pytest.mark.parametrize("entry_accounting_information__entry", [LazyFixture("entry")])
    @pytest.mark.parametrize("entry_accounting_information__counterparty_is_private", [True])
    def test_filter_for_user_private_counterparty_with_exempt(
        self, invoice: Invoice, user: User, entry_accounting_information: EntryAccountingInformation
    ):
        entry_accounting_information.exempt_users.add(user)
        entry_accounting_information_list = EntryAccountingInformation.objects.filter_for_user(user)  # type: ignore
        assert entry_accounting_information in entry_accounting_information_list
