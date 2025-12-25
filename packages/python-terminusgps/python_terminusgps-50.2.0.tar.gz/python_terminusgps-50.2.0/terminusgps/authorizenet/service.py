from functools import cached_property

from authorizenet.apicontractsv1 import merchantAuthenticationType
from authorizenet.apicontrollersbase import APIOperationBase
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from lxml.objectify import ObjectifiedElement

if not settings.configured:
    from terminusgps import default_settings

    settings.configure(default_settings)


class AuthorizenetControllerExecutionError(Exception):
    """Raised when an Authorizenet API controller fails to execute."""

    def __init__(self, message: str, code: str, *args, **kwargs) -> None:
        super().__init__(message, *args, **kwargs)
        self._message: str = message
        self._code: str = code

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"

    @property
    def message(self) -> str:
        """An Authorizenet API error message."""
        return self._message

    @property
    def code(self) -> str:
        """An Authorizenet API error code."""
        return self._code


class AuthorizenetService:
    """Service for safely interacting with the Authorizenet API."""

    REQUIRED_SETTINGS = (
        "MERCHANT_AUTH_ENVIRONMENT",
        "MERCHANT_AUTH_LOGIN_ID",
        "MERCHANT_AUTH_TRANSACTION_KEY",
        "MERCHANT_AUTH_VALIDATION_MODE",
    )

    def __init__(self) -> None:
        """Raises :py:exc:`~django.core.exceptions.ImproperlyConfigured` if required settings weren't set."""
        for setting in self.REQUIRED_SETTINGS:
            if not hasattr(settings, setting):
                raise ImproperlyConfigured(f"'{setting}' setting is required.")

    def execute(
        self,
        request_tuple: tuple[ObjectifiedElement, type[APIOperationBase]],
        reference_id: str | None = None,
    ) -> ObjectifiedElement:
        """
        Adds required authentication data to the Authorizenet API request before executing it and returning its response.

        If ``reference_id`` was provided, it is added to the request before execution.

        :param request_tuple: A tuple containing an Authorizenet API request contract and a controller class to execute it with.
        :type request_tuple: tuple[~lxml.objectify.ObjectifiedElement, type[~authorizenet.apicontrollersbase.APIOperationBase]]
        :param reference_id: An optional reference id string for the API call. Default is :py:obj:`None`.
        :type reference_id: str | None
        :raises AuthorizenetControllerExecutionError: If the API call failed.
        :returns: An Authorizenet API response.
        :rtype: ~lxml.objectify.ObjectifiedElement

        """
        request, controller_cls = request_tuple[0], request_tuple[1]
        request.merchantAuthentication = self.merchantAuthentication
        if reference_id is not None:
            request.refId = reference_id

        controller = controller_cls(request)
        controller.setenvironment(self.environment)
        controller.execute()
        response = controller.getresponse()

        if response is None:
            raise AuthorizenetControllerExecutionError(
                message="No response from the Authorizenet API controller.",
                code="1",
            )
        elif response is not None and response.messages.resultCode != "Ok":
            raise AuthorizenetControllerExecutionError(
                message=response.messages.message[0]["text"].text,
                code=response.messages.message[0]["code"].text,
            )
        return response

    @cached_property
    def merchantAuthentication(self) -> merchantAuthenticationType:
        """Merchant authentication element for Authorizenet API requests."""
        return merchantAuthenticationType(
            name=str(settings.MERCHANT_AUTH_LOGIN_ID),
            transactionKey=str(settings.MERCHANT_AUTH_TRANSACTION_KEY),
        )

    @cached_property
    def environment(self) -> str:
        """Environment for Authorizenet API requests."""
        return str(settings.MERCHANT_AUTH_ENVIRONMENT)

    @cached_property
    def validationMode(self) -> str:
        """Validation mode for Authorizenet API requests."""
        return str(settings.MERCHANT_AUTH_VALIDATION_MODE)
