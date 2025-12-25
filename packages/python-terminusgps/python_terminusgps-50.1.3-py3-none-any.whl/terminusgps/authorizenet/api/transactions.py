from decimal import Decimal

from authorizenet import apicontractsv1, apicontrollers
from authorizenet.apicontrollersbase import APIOperationBase
from lxml.objectify import ObjectifiedElement

__all__ = [
    "charge_credit_card",
    "authorize_credit_card",
    "capture_authorized_amount",
    "refund_credit_card",
    "charge_customer_profile",
]


def build_transaction(
    amount: Decimal, **kwargs
) -> apicontractsv1.transactionRequestType:
    """Returns a transaction element for a transaction request."""
    transaction_request = apicontractsv1.transactionRequestType()
    transaction_request.amount = amount

    if payment := kwargs.get("payment"):
        transaction_request.payment = payment
    if address := kwargs.get("address"):
        transaction_request.billTo = address
    if order := kwargs.get("order"):
        transaction_request.order = order
    if customer_data := kwargs.get("customer_data"):
        transaction_request.customerData = customer_data
    if settings := kwargs.get("settings"):
        transaction_request.transactionSettings = settings
    if line_items := kwargs.get("line_items"):
        transaction_request.lineItems = line_items

    return transaction_request


def charge_credit_card(
    amount: Decimal,
    credit_card: apicontractsv1.creditCardType,
    address: apicontractsv1.customerAddressType,
    order: apicontractsv1.orderType | None = None,
    customer_data: apicontractsv1.customerDataType | None = None,
    settings: apicontractsv1.ArrayOfSetting | None = None,
    line_items: apicontractsv1.ArrayOfLineItem | None = None,
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `Charges a credit card <https://developer.authorize.net/api/reference/index.html#payment-transactions-charge-a-credit-card>`_.

    :param amount: Dollar amount to charge.
    :type amount: ~decimal.Decimal
    :param credit_card: A credit card.
    :type credit_card: ~authorizenet.apicontractsv1.creditCardType
    :param address: A customer address.
    :type address: ~authorizenet.apicontractsv1.customerAddressType
    :param order: Order information. Default is :py:obj:`None`.
    :type order: ~authorizenet.apicontractsv1.orderType | None
    :param customer_data: Customer data. Default is :py:obj:`None`.
    :type customer_data: ~authorizenet.apicontractsv1.customerDataType | None
    :param settings: Transaction settings. Default is :py:obj:`None`.
    :type settings: ~authorizenet.apicontractsv1.ArrayOfSetting | None
    :param line_items: An array of line items. Default is :py:obj:`None`.
    :type line_items: ~authorizenet.apicontractsv1.ArrayOfLineItem | None
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.createTransactionRequest()
    payment = apicontractsv1.paymentType()
    payment.creditCard = credit_card
    request.transactionRequest = build_transaction(
        amount=amount,
        payment=payment,
        address=address,
        order=order,
        customer_data=customer_data,
        settings=settings,
        line_items=line_items,
    )

    request.transactionRequest.transactionType = (
        apicontractsv1.transactionTypeEnum.authCaptureTransaction
    )
    return request, apicontrollers.createTransactionController


def authorize_credit_card(
    amount: Decimal,
    credit_card: apicontractsv1.creditCardType,
    address: apicontractsv1.customerAddressType,
    order: apicontractsv1.orderType | None = None,
    customer_data: apicontractsv1.customerDataType | None = None,
    settings: apicontractsv1.ArrayOfSetting | None = None,
    line_items: apicontractsv1.ArrayOfLineItem | None = None,
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `Authorizes a credit card <https://developer.authorize.net/api/reference/index.html#payment-transactions-authorize-a-credit-card>`_.

    :param amount: Dollar amount to authorize.
    :type amount: ~decimal.Decimal
    :param credit_card: A credit card.
    :type credit_card: ~authorizenet.apicontractsv1.creditCardType
    :param address: A customer address.
    :type address: ~authorizenet.apicontractsv1.customerAddressType
    :param order: Additional order information. Default is :py:obj:`None`.
    :type order: ~authorizenet.apicontractsv1.orderType | None
    :param customer_data: Additional customer data. Default is :py:obj:`None`.
    :type customer_data: ~authorizenet.apicontractsv1.customerDataType | None
    :param settings: Transaction settings. Default is :py:obj:`None`.
    :type settings: ~authorizenet.apicontractsv1.ArrayOfSetting | None
    :param line_items: An array of line items. Default is :py:obj:`None`.
    :type line_items: ~authorizenet.apicontractsv1.ArrayOfLineItem | None
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.createTransactionRequest()
    payment = apicontractsv1.paymentType()
    payment.creditCard = credit_card
    request.transactionRequest = build_transaction(
        amount=amount,
        payment=payment,
        address=address,
        order=order,
        customer_data=customer_data,
        settings=settings,
        line_items=line_items,
    )

    request.transactionRequest.transactionType = (
        apicontractsv1.transactionTypeEnum.authOnlyTransaction
    )
    return request, apicontrollers.createTransactionController


def capture_authorized_amount(
    amount: Decimal,
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `Captures a previously authorized amount <https://developer.authorize.net/api/reference/index.html#payment-transactions-capture-a-previously-authorized-amount>`_.

    :param amount: Dollar amount to capture.
    :type amount: ~decimal.Decimal
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.createTransactionRequest()
    request.transactionRequest = build_transaction(amount)
    request.transactionRequest.transactionType = (
        apicontractsv1.transactionTypeEnum.priorAuthCaptureTransaction
    )
    return request, apicontrollers.createTransactionController


def refund_credit_card(
    amount: Decimal, credit_card: apicontractsv1.creditCardType
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `Refunds a credit card <https://developer.authorize.net/api/reference/index.html#payment-transactions-refund-a-transaction>`_.

    :param amount: Dollar amount to refund.
    :type amount: ~decimal.Decimal
    :param credit_card: Destination credit card.
    :type credit_card: ~authorizenet.apicontractsv1.creditCardType
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.createTransactionRequest()
    payment = apicontractsv1.paymentType()
    payment.creditCard = credit_card
    request.transactionRequest = build_transaction(
        amount=amount, payment=payment
    )

    request.transactionRequest.transactionType = (
        apicontractsv1.transactionTypeEnum.refundTransaction
    )
    return request, apicontrollers.createTransactionController


def void_transaction(
    reference_id: str,
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `Voids a transaction <https://developer.authorize.net/api/reference/index.html#payment-transactions-void-a-transaction>`_.

    :param reference_id: Transaction reference id.
    :type reference_id: str
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    request = apicontractsv1.createTransactionRequest()
    request.transactionRequest = apicontractsv1.transactionRequestType()
    request.transactionRequest.refTransId = reference_id
    request.transactionRequest.transactionType = (
        apicontractsv1.transactionTypeEnum.voidTransaction
    )
    return request, apicontrollers.createTransactionController


def charge_customer_profile(
    customer_profile_id: int,
    payment_profile_id: int,
    amount: Decimal,
    line_items: apicontractsv1.ArrayOfLineItem | None = None,
) -> tuple[ObjectifiedElement, type[APIOperationBase]]:
    """
    `Charges a customer profile <https://developer.authorize.net/api/reference/index.html#payment-transactions-charge-a-customer-profile>`_.

    :param customer_profile_id: An Authorizenet customer profile id.
    :type customer_profile_id: int
    :param payment_profile_id: An Authorizenet payment profile id.
    :type payment_profile_id: int
    :param amount: Amount to change the customer profile.
    :type amount: ~decimal.Decimal
    :param line_items: An array of line items. Default is :py:obj:`None`.
    :type line_items: ~apicontractsv1.ArrayOfLineItem | None
    :returns: A tuple containing an Authorizenet API request element and controller class.
    :rtype: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]

    """
    profile = apicontractsv1.customerProfilePaymentType()
    profile.customerProfileId = str(customer_profile_id)
    profile.paymentProfile = apicontractsv1.paymentProfile()
    profile.paymentProfile.paymentProfileId = str(payment_profile_id)
    request = apicontractsv1.createTransactionRequest()
    request.transactionRequest = apicontractsv1.transactionRequestType()
    request.transactionRequest.amount = amount
    request.transactionRequest.profile = profile
    request.transactionRequest.transactionType = (
        apicontractsv1.transactionTypeEnum.authCaptureTransaction
    )
    if line_items is not None:
        request.transactionRequest.lineItems = line_items
    return request, apicontrollers.createTransactionController
