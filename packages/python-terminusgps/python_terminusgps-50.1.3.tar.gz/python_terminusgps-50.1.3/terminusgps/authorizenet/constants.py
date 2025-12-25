from authorizenet import apicontractsv1
from authorizenet.constants import constants as anet_constants
from django.db import models
from django.utils.translation import gettext_lazy as _


class BankAccountType(models.TextChoices):
    CHECKING = "checking", _("Checking account")
    """Checking account."""
    SAVINGS = "savings", _("Savings account")
    """Savings account."""
    BUSINESS_CHECKING = "businessChecking", _("Business checking account")
    """Business checking account."""


class ECheckType(models.TextChoices):
    PPD = "PPD", _("Prearranged Payment and Deposit Entry")
    """Prearranged Payment and Deposit Entry."""
    TEL = "TEL", _("Telephone-Initiated Entry")
    """Telephone-Initiated Entry."""
    WEB = "WEB", _("Web-Initiated Entry")
    """Web-Initiated Entry."""


class CreditCardType(models.TextChoices):
    AMEX = apicontractsv1.cardTypeEnum.AmericanExpress, _("American Express")
    """American express card."""
    DINERS = apicontractsv1.cardTypeEnum.DinersClub, _("Diners Club")
    """Diners club card."""
    DISCOVER = apicontractsv1.cardTypeEnum.Discover, _("Discover")
    """Disover card."""
    JCB = apicontractsv1.cardTypeEnum.JCB, _("JCB")
    """JCB card."""
    MASTERCARD = apicontractsv1.cardTypeEnum.MasterCard, _("Mastercard")
    """Mastercard card."""
    VISA = apicontractsv1.cardTypeEnum.Visa, _("Visa")
    """Visa card."""


class CurrencyCode(models.TextChoices):
    USD = "USD", _("United States Dollar")
    """US dollar."""
    CAD = "CAD", _("Canadian Dollar")
    """Canadian dollar."""
    GBP = "GBP", _("Great British Pound")
    """Great British pound."""
    DKK = "DKK", _("Danish Krone")
    """Danish krone."""
    NOK = "NOK", _("Norwegian Krone")
    """Norwegian krone."""
    PLN = "PLN", _("Polish Złoty")
    """Polish zloty."""
    SEK = "SEK", _("Swedish Krona")
    """Swedish krona."""
    EUR = "EUR", _("Euro")
    """Euro."""
    AUD = "AUD", _("Australian Dollar")
    """Australian dollar."""
    NZD = "NZD", _("New Zealand Dollar")
    """New Zealand dollar."""


class SubscriptionStatus(models.TextChoices):
    """An Authorizenet subscription status."""

    ACTIVE = "active", _("Active")
    """Active status."""
    EXPIRED = "expired", _("Expired")
    """Expired status."""
    SUSPENDED = "suspended", _("Suspended")
    """Suspended status."""
    CANCELED = "canceled", _("Canceled")
    """Canceled status."""
    TERMINATED = "terminated", _("Terminated")
    """Terminated status."""
    UNKNOWN = "unknown", _("Unknown")
    """Unknown status."""


class SubscriptionIntervalUnit(models.TextChoices):
    """An Authorizenet subscription interval unit."""

    DAYS = apicontractsv1.ARBSubscriptionUnitEnum.days, _("Days")
    """Days interval unit."""
    MONTHS = apicontractsv1.ARBSubscriptionUnitEnum.months, _("Months")
    """Months interval unit."""


class Environment(models.TextChoices):
    """An Authorizenet execution environment."""

    SANDBOX = anet_constants.SANDBOX, _("Sandbox Environment")
    """Sandbox environment."""
    PRODUCTION = anet_constants.PRODUCTION, _("Production Environment")
    """Production environment."""


class ValidationMode(models.TextChoices):
    """An Authorizenet validation mode."""

    TEST = "testMode", _("Test Mode")
    """Test mode."""
    LIVE = "liveMode", _("Live Mode")
    """Live mode."""
