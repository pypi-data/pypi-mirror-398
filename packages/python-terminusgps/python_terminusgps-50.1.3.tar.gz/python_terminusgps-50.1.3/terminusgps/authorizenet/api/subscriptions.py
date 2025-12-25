from authorizenet import apicontractsv1, apicontrollers
from authorizenet.apicontrollersbase import APIOperationBase
from lxml.objectify import ObjectifiedElement

__all__ = [
    "create_subscription",
    "get_subscription",
    "get_subscription_status",
    "update_subscription",
    "cancel_subscription",
]


def create_subscription(
    subscription: apicontractsv1.ARBSubscriptionType,
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `ARBCreateSubscriptionRequest <https://developer.authorize.net/api/reference/index.html#recurring-billing-create-a-subscription>`_.

    :param subscription: An Authorizenet ARBSubscriptionType element.
    :type subscription: ~authorizenet.apicontractsv1.ARBSubscriptionType
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.ARBCreateSubscriptionRequest()
    request.subscription = subscription
    return request, apicontrollers.ARBCreateSubscriptionController


def get_subscription(
    subscription_id: int, include_transactions: bool = True
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `ARBGetSubscriptionRequest <https://developer.authorize.net/api/reference/index.html#recurring-billing-get-subscription>`_.

    :param subscription_id: An Authorizenet subscription id.
    :type subscription_id: int
    :param include_transactions: Whether to include the subscription transaction list in the response. Default is True.
    :type include_transactions: bool
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.ARBGetSubscriptionRequest()
    request.subscriptionId = str(subscription_id)
    request.includeTransactions = str(include_transactions).lower()
    return request, apicontrollers.ARBGetSubscriptionController


def get_subscription_status(
    subscription_id: int,
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `ARBGetSubscriptionStatusRequest <https://developer.authorize.net/api/reference/index.html#recurring-billing-get-subscription-status>`_.

    :param subscription_id: An Authorizenet subscription id.
    :type subscription_id: int
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.ARBGetSubscriptionStatusRequest()
    request.subscriptionId = str(subscription_id)
    return request, apicontrollers.ARBGetSubscriptionStatusController


def update_subscription(
    subscription_id: int, subscription: apicontractsv1.ARBSubscriptionType
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `ARBUpdateSubscriptionRequest <https://developer.authorize.net/api/reference/index.html#recurring-billing-update-a-subscription>`_.

    :param subscription_id: An Authorizenet subscription id.
    :type subscription_id: int
    :param subscription: An Authorizenet ARBSubscriptionType element.
    :type subscription: ~authorizenet.apicontractsv1.ARBSubscriptionType
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.ARBUpdateSubscriptionRequest()
    request.subscriptionId = str(subscription_id)
    request.subscription = subscription
    return request, apicontrollers.ARBUpdateSubscriptionController


def cancel_subscription(
    subscription_id: int,
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `ARBCancelSubscriptionRequest <https://developer.authorize.net/api/reference/index.html#recurring-billing-cancel-a-subscription>`_.

    :param subscription_id: An Authorizenet subscription id.
    :type subscription_id: int
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.ARBCancelSubscriptionRequest()
    request.subscriptionId = str(subscription_id)
    return request, apicontrollers.ARBCancelSubscriptionController
