import calendar
import datetime

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

VALID_COUNTRY_CODES = ("+1", "+52")


def validate_is_digit(value: str) -> None:
    """Raises :py:exc:`django.core.exceptions.ValidationError` if the value contained non-digit characters."""
    if not value.isdigit():
        raise ValidationError(
            _("Value can only contain digits, got '%(value)s'."),
            code="invalid",
            params={"value": value},
        )


def validate_e164_phone_number(value: str) -> None:
    """
    Raises :py:exc:`~django.core.exceptions.ValidationError` if the value is not a valid `E.164 <https://en.wikipedia.org/wiki/E.164>`_ formatted phone number.

    * Country Code: A 2-5 character code with a leading '+' indicating the phone number's destination country.
    * Area Code: The first 3 digits of the phone number.
    * Subscriber Number: The last 7 digits of the phone number.

    :param value: A phone number in `E.164 <https://en.wikipedia.org/wiki/E.164>`_ format.
    :type value: str
    :raises ~django.core.exceptions.ValidationError: If the phone number wasn't provided.
    :raises ~django.core.exceptions.ValidationError: If the phone number didn't start with a '+' character.
    :raises ~django.core.exceptions.ValidationError: If the phone number contained any number of spaces.
    :raises ~django.core.exceptions.ValidationError: If the phone number contained any number of hyphens.
    :raises ~django.core.exceptions.ValidationError: If the phone number was less than 12 characters in length.
    :raises ~django.core.exceptions.ValidationError: If the phone number was greater than 15 characters in length.
    :raises ~django.core.exceptions.ValidationError: If the country code was invalid.
    :raises ~django.core.exceptions.ValidationError: If the area code wasn't exactly 3 characters in length.
    :raises ~django.core.exceptions.ValidationError: If the area code wasn't a digit.
    :raises ~django.core.exceptions.ValidationError: If the subscriber number (non-area code number) wasn't exactly 7 characters in length.
    :raises ~django.core.exceptions.ValidationError: If the subscriber number (non-area code number) wasn't a digit.
    :returns: Nothing.
    :rtype: None

    """
    if not value:
        raise ValidationError(
            _("This field is required, got '%(value)s'"),
            code="invalid",
            params={"value": value},
        )
    if not value.startswith("+"):
        raise ValidationError(
            _("E.164 phone number must begin with a '+', got '%(char)s'."),
            code="invalid",
            params={"char": value[0]},
        )
    if " " in value:
        raise ValidationError(
            _("E.164 phone number cannot contain spaces, got '%(value)s'."),
            code="invalid",
            params={"value": value},
        )
    if "-" in value:
        raise ValidationError(
            _("E.164 phone number cannot contain hyphens, got '%(value)s'."),
            code="invalid",
            params={"value": value},
        )
    if len(value) < 12:
        raise ValidationError(
            _(
                "E.164 phone number cannot be less than 12 characters in length, got %(len)s."
            ),
            code="invalid",
            params={"len": len(value)},
        )
    if len(value) > 15:
        raise ValidationError(
            _(
                "E.164 phone number cannot be greater than 15 characters in length, got %(len)s."
            ),
            code="invalid",
            params={"len": len(value)},
        )

    country_code = value[:-10]
    area_code = value[-10:-7]
    subscriber_number = value[-7:]

    if len(country_code) < 2 or len(country_code) > 5:
        raise ValidationError(
            _(
                "E.164 phone number country code must be between 2 and 5 characters in length, got %(len)s."
            ),
            code="invalid",
            params={"len": len(country_code)},
        )
    if country_code not in VALID_COUNTRY_CODES:
        raise ValidationError(
            _(
                "E.164 phone number cannot contain an invalid country code, got '%(country_code)s'."
            ),
            code="invalid",
            params={"country_code": country_code},
        )
    if not len(area_code) == 3:
        raise ValidationError(
            _(
                "E.164 phone number must contain a 3-digit area code, got '%(area_code)s'."
            ),
            code="invalid",
            params={"area_code": area_code},
        )
    if not area_code.isdigit():
        raise ValidationError(
            _(
                "E.164 phone number must have a valid area code, got '%(area_code)s'."
            ),
            code="invalid",
            params={"area_code": area_code},
        )
    if not len(subscriber_number) == 7:
        raise ValidationError(
            _(
                "E.164 phone number must contain a 7-digit subscriber number, got '%(subscriber_number)s'."
            ),
            code="invalid",
            params={"subscriber_number": subscriber_number},
        )
    if not subscriber_number.isdigit():
        raise ValidationError(
            _(
                "E.164 phone number must have a valid subscriber number, got '%(subscriber_number)s'."
            ),
            code="invalid",
            params={"subscriber_number": subscriber_number},
        )


def validate_credit_card_number(value: str) -> None:
    """
    Raises :py:exc:`~django.core.exceptions.ValidationError` if the value is an invalid credit card number.

    Uses the `Luhn algorithm <https://en.wikipedia.org/wiki/Luhn_algorithm>`_ to validate the credit card number.

    :param value: A credit card number.
    :type value: str
    :raises ~django.core.exceptions.ValidationError: If the credit card number contained non-digit characters.
    :raises ~django.core.exceptions.ValidationError: If the credit card number failed the Luhn algorithm check.
    :returns: Nothing.
    :rtype: None

    """
    if not value.isdigit():
        raise ValidationError(
            _("Credit card number can only contain digits. Got '%(value)s'."),
            code="invalid",
            params={"value": value},
        )

    card_number = [int(num) for num in reversed(value)]
    even_digits = card_number[1::2]
    odd_digits = card_number[0::2]

    checksum = 0
    checksum += sum(
        [
            digit * 2 if digit * 2 <= 9 else (digit * 2) % 9 or 9
            for digit in even_digits
        ]
    )
    checksum += sum([digit for digit in odd_digits])

    if checksum % 10 != 0:
        raise ValidationError(_("Invalid credit card number."), code="invalid")


def validate_credit_card_expiry_month(value: str) -> None:
    """
    Raises :py:exc:`~django.core.exceptions.ValidationError` if the value is an invalid credit card expiration date month.

    :param value: A credit card expiration month.
    :type value: str
    :raises ~django.core.exceptions.ValidationError: If the expiration month contained non-digit characters.
    :raises ~django.core.exceptions.ValidationError: If the expiration month was negative.
    :raises ~django.core.exceptions.ValidationError: If the expiration month was an invalid (non-existent) month.
    :returns: Nothing.
    :rtype: None

    """
    if not value.isdigit():
        raise ValidationError(
            _("Expiration month can only contain digits, got '%(value)s'."),
            code="invalid",
            params={"value": value},
        )
    if not int(value) > 0:
        raise ValidationError(
            _(
                "Expiration month can only be a positive value, got '%(value)s'."
            ),
            code="invalid",
            params={"value": value},
        )

    try:
        calendar.Month(int(value))
    except ValueError:
        raise ValidationError(
            _("Expiration month must be between 1-12, got '%(value)s'."),
            code="invalid",
            params={"value": value},
        )


def validate_credit_card_expiry_year(value: str) -> None:
    """
    Raises :py:exc:`~django.core.exceptions.ValidationError` if the value is an invalid credit card expiration date year.

    :param value: A credit card expiration year.
    :type value: str
    :raises ~django.core.exceptions.ValidationError: If the expiration year contained non-digit characters.
    :raises ~django.core.exceptions.ValidationError: If the expiration year was negative.
    :raises ~django.core.exceptions.ValidationError: If the expiration year was a year in the past.
    :returns: Nothing.
    :rtype: None

    """
    if not value.isdigit():
        raise ValidationError(
            _("Expiration year can only contain digits, got '%(value)s'."),
            code="invalid",
            params={"value": value},
        )
    if not int(value) > 0:
        raise ValidationError(
            _(
                "Expiration year can only be a positive value, got '%(value)s'."
            ),
            code="invalid",
            params={"value": value},
        )

    input_year = datetime.datetime.strptime(value, "%y").year
    this_year = datetime.datetime.now().year

    if not input_year >= this_year:
        raise ValidationError(
            _("Expiration year cannot be in the past, got '%(value)s'."),
            code="invalid",
            params={"value": value},
        )
