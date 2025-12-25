from authorizenet import apicontractsv1, apicontrollers
from authorizenet.apicontrollersbase import APIOperationBase
from lxml.objectify import ObjectifiedElement

__all__ = [
    "create_customer_profile",
    "delete_customer_profile",
    "get_customer_profile",
    "get_customer_profile_by_email",
    "get_customer_profile_by_merchant_id",
    "get_customer_profile_ids",
    "update_customer_profile",
]


def create_customer_profile(
    merchant_id: str, email: str, description: str = ""
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `createCustomerProfileRequest <https://developer.authorize.net/api/reference/index.html#customer-profiles-create-customer-profile>`_.

    :param merchant_id: A merchant designated customer id.
    :type merchant_id: str
    :param email: A customer email address.
    :type email: str
    :param description: An optional customer description.
    :type description: str
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.createCustomerProfileRequest()
    request.profile = apicontractsv1.customerProfileType()
    request.profile.merchantCustomerId = merchant_id
    request.profile.description = description
    request.profile.email = email
    return request, apicontrollers.createCustomerProfileController


def get_customer_profile(
    customer_profile_id: int, include_issuer_info: bool = False
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `getCustomerProfileRequest <https://developer.authorize.net/api/reference/index.html#customer-profiles-get-customer-profile>`_.

    :param customer_profile_id: Authorizenet customer profile id.
    :type customer_profile_id: int
    :param include_issuer_info: Whether to include issuer info in the response. Default is :py:obj:`False`.
    :type include_issuer_info: bool
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.getCustomerProfileRequest()
    request.customerProfileId = str(customer_profile_id)
    request.includeIssuerInfo = str(include_issuer_info).lower()
    return request, apicontrollers.getCustomerProfileController


def get_customer_profile_by_email(
    email: str, include_issuer_info: bool = False
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `getCustomerProfileRequest <https://developer.authorize.net/api/reference/index.html#customer-profiles-get-customer-profile>`_.

    :param email: Merchant designated customer profile email address.
    :type email: str
    :param include_issuer_info: Whether to include issuer info in the response. Default is :py:obj:`False`.
    :type include_issuer_info: bool
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.getCustomerProfileRequest()
    request.email = str(email)
    request.includeIssuerInfo = str(include_issuer_info).lower()
    return request, apicontrollers.getCustomerProfileController


def get_customer_profile_by_merchant_id(
    merchant_id: str, include_issuer_info: bool = False
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `getCustomerProfileRequest <https://developer.authorize.net/api/reference/index.html#customer-profiles-get-customer-profile>`_.

    :param merchant_id: Merchant designated customer profile id.
    :type merchant_id: str
    :param include_issuer_info: Whether to include issuer info in the response. Default is :py:obj:`False`.
    :type include_issuer_info: bool
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.getCustomerProfileRequest()
    request.merchantCustomerId = str(merchant_id)
    request.includeIssuerInfo = str(include_issuer_info).lower()
    return request, apicontrollers.getCustomerProfileController


def get_customer_profile_ids() -> tuple[
    ObjectifiedElement, type[APIOperationBase]
]:
    """
    `getCustomerProfileIdsRequest <https://developer.authorize.net/api/reference/index.html#customer-profiles-get-customer-profile-ids>`_.

    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.getCustomerProfileIdsRequest()
    return request, apicontrollers.getCustomerProfileIdsController


def update_customer_profile(
    profile: apicontractsv1.customerProfileExType,
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `updateCustomerProfileRequest <https://developer.authorize.net/api/reference/index.html#customer-profiles-update-customer-profile>`_.

    :param profile: An Authorizenet customer profile ex element.
    :type profile: ~authorizenet.apicontractsv1.customerProfileExType
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.updateCustomerProfileRequest()
    request.profile = profile
    return request, apicontrollers.updateCustomerProfileController


def delete_customer_profile(
    customer_profile_id: int,
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `deleteCustomerProfileRequest <https://developer.authorize.net/api/reference/index.html#customer-profiles-delete-customer-profile>`_.

    :param customer_profile_id: An Authorizenet customer profile id.
    :type customer_profile_id: int
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.deleteCustomerProfileRequest()
    request.customerProfileId = str(customer_profile_id)
    return request, apicontrollers.deleteCustomerProfileController
