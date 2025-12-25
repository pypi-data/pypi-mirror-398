from authorizenet import apicontractsv1, apicontrollers
from authorizenet.apicontrollersbase import APIOperationBase
from lxml.objectify import ObjectifiedElement

__all__ = [
    "create_customer_payment_profile",
    "get_customer_payment_profile",
    "validate_customer_payment_profile",
    "update_customer_payment_profile",
    "delete_customer_payment_profile",
]


def create_customer_payment_profile(
    customer_profile_id: int,
    payment: apicontractsv1.paymentType,
    address: apicontractsv1.customerAddressType,
    default: bool = False,
    validation: str | None = None,
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `createCustomerPaymentProfileRequest <https://developer.authorize.net/api/reference/index.html#customer-profiles-create-customer-payment-profile>`_.

    :param customer_profile_id: An Authorizenet customer profile id.
    :type customer_profile_id: int
    :param payment: An Authorizenet payment element.
    :type payment: ~authorizenet.apicontractsv1.paymentType
    :param address: An Authorizenet address element.
    :type address: ~authorizenet.apicontractsv1.customerAddressType
    :param default: Whether to set the payment profile as default. Default is :py:obj:`False`.
    :type default: bool
    :param validation: Validation mode to use when validating the payment profile. If not provided, the payment profile is not validated. Default is :py:obj:`None`.
    :type validation: str | None
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.createCustomerPaymentProfileRequest()
    request.customerProfileId = str(customer_profile_id)
    request.paymentProfile = apicontractsv1.customerPaymentProfileType()
    request.paymentProfile.payment = payment
    request.paymentProfile.billTo = address
    request.paymentProfile.defaultPaymentProfile = str(default).lower()

    if validation is not None:
        request.validationMode = str(validation)
    return request, apicontrollers.createCustomerPaymentProfileController


def get_customer_payment_profile(
    customer_profile_id: int,
    payment_profile_id: int,
    include_issuer_info: bool = False,
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `getCustomerPaymentProfileRequest <https://developer.authorize.net/api/reference/index.html#customer-profiles-get-customer-payment-profile>`_.

    :param customer_profile_id: An Authorizenet customer profile id.
    :type customer_profile_id: int
    :param payment_profile_id: An Authorizenet customer payment profile id.
    :type payment_profile_id: int
    :param include_issuer_info: Whether to include issuer info in the response. Default is False.
    :type include_issuer_info: bool
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.getCustomerPaymentProfileRequest()
    request.customerProfileId = str(customer_profile_id)
    request.customerPaymentProfileId = str(payment_profile_id)
    request.includeIssuerInfo = str(include_issuer_info).lower()
    return request, apicontrollers.getCustomerPaymentProfileController


def validate_customer_payment_profile(
    customer_profile_id: int, payment_profile_id: int, validation: str
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `validateCustomerPaymentProfileRequest <https://developer.authorize.net/api/reference/index.html#customer-profiles-validate-customer-payment-profile>`_.

    :param customer_profile_id: An Authorizenet customer profile id.
    :type customer_profile_id: int
    :param payment_profile_id: An Authorizenet customer payment profile id.
    :type payment_profile_id: int
    :param validation: Validation mode to use when validating the payment profile.
    :type validation: str
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.validateCustomerPaymentProfileRequest()
    request.customerProfileId = str(customer_profile_id)
    request.customerPaymentProfileId = str(payment_profile_id)
    request.validationMode = validation
    return request, apicontrollers.validateCustomerPaymentProfileController


def update_customer_payment_profile(
    customer_profile_id: int,
    payment_profile_id: int,
    payment: apicontractsv1.paymentType | None = None,
    address: apicontractsv1.customerAddressType | None = None,
    default: bool | None = None,
    validation: str | None = None,
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `updateCustomerPaymentProfileRequest <https://developer.authorize.net/api/reference/index.html#customer-profiles-update-customer-payment-profile>`_.

    :param customer_profile_id: An Authorizenet customer profile id.
    :type customer_profile_id: int
    :param payment_profile_id: An Authorizenet customer payment profile id.
    :type payment_profile_id: int
    :param payment: An Authorizenet payment element.
    :type payment: ~authorizenet.apicontractsv1.paymentType | None
    :param address: An Authorizenet address element.
    :type address: ~authorizenet.apicontractsv1.customerAddressType | None
    :param default: Whether to set the payment profile as default. If not provided, the payment profile's default state is not updated. Default is :py:obj:`None`.
    :type default: bool | None
    :param validation: Validation mode to use when validating the payment profile. If not provided, the payment profile is not validated. Default is :py:obj:`None`.
    :type validation: str | None
    :raises ValueError: If neither payment nor address was provided.
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    if any([payment is None, address is None, default is None]):
        raise ValueError(
            f"At least one of 'payment', 'address' or 'default' is required, got '{payment}', '{address}' and '{default}'."
        )

    request = apicontractsv1.updateCustomerPaymentProfileRequest()
    request.customerProfileId = str(customer_profile_id)
    request.paymentProfile = apicontractsv1.customerPaymentProfileExType()
    request.paymentProfile.customerPaymentProfileId = str(payment_profile_id)

    if payment is not None:
        request.paymentProfile.payment = payment
    if address is not None:
        request.paymentProfile.billTo = address
    if default is not None:
        request.paymentProfile.defaultPaymentProfile = str(default).lower()
    if validation is not None:
        request.validationMode = str(validation)
    return request, apicontrollers.updateCustomerPaymentProfileController


def delete_customer_payment_profile(
    customer_profile_id: int, payment_profile_id: int
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `deleteCustomerPaymentProfileRequest <https://developer.authorize.net/api/reference/index.html#customer-profiles-delete-customer-payment-profile>`_.

    :param customer_profile_id: An Authorizenet customer profile id.
    :type customer_profile_id: int
    :param payment_profile_id: An Authorizenet customer payment profile id.
    :type payment_profile_id: int
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.deleteCustomerPaymentProfileRequest()
    request.customerProfileId = str(customer_profile_id)
    request.customerPaymentProfileId = str(payment_profile_id)
    return request, apicontrollers.deleteCustomerPaymentProfileController
